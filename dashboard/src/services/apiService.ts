import { TelemetryPayload, ScanMetadata, ConnectionStatus, ConvergenceRecord } from '../types';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname
  ? `http://${window.location.hostname}:8000`
  : 'http://localhost:8000';

const WS_BASE_URL = typeof window !== 'undefined' && window.location.hostname
  ? `ws://${window.location.hostname}:8000`
  : 'ws://localhost:8000';

export class FedMedService {
  private ws: WebSocket | null = null;
  private onDataCallback: ((data: TelemetryPayload) => void) | null = null;
  private onStatusCallback: ((status: ConnectionStatus) => void) | null = null;
  private mockInterval: number | null = null;
  private isMocking = false;
  private reconnectTimer: number | null = null;
  private currentMockRound = 1;

  constructor(
    onData: (data: TelemetryPayload) => void,
    onStatus: (status: ConnectionStatus) => void
  ) {
    this.onDataCallback = onData;
    this.onStatusCallback = onStatus;
  }

  public connect(url: string = `${WS_BASE_URL}/ws/telemetry`): void {
    if (this.ws) {
      try { this.ws.close(); } catch (_) {}
    }

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.isMocking = false;
        if (this.mockInterval) {
          clearInterval(this.mockInterval);
          this.mockInterval = null;
        }
        if (this.onStatusCallback) {
          this.onStatusCallback({ connected: true, isMock: false, url });
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const data: TelemetryPayload = JSON.parse(event.data);
          if (this.onDataCallback) {
            this.onDataCallback(data);
          }
        } catch (e) {
          console.error('[FedMed WS] Failed to parse message:', e);
        }
      };

      this.ws.onerror = () => {
        if (!this.isMocking) {
          this.startMockFallback();
        }
      };

      this.ws.onclose = () => {
        if (!this.isMocking) {
          this.startMockFallback();
        }
        // Attempt reconnect after 5s
        if (!this.reconnectTimer) {
          this.reconnectTimer = window.setTimeout(() => {
            this.reconnectTimer = null;
            if (this.isMocking) {
              this.connect(url);
            }
          }, 5000);
        }
      };
    } catch (_) {
      this.startMockFallback();
    }
  }

  private startMockFallback(): void {
    this.isMocking = true;
    if (this.onStatusCallback) {
      this.onStatusCallback({ connected: true, isMock: true });
    }
    this.emitMockData();

    if (this.mockInterval) clearInterval(this.mockInterval);
    this.mockInterval = window.setInterval(() => {
      this.emitMockData();
    }, 2400);
  }

  private emitMockData(): void {
    const r = this.currentMockRound;
    const phases: Array<TelemetryPayload['phase']> = ['training', 'encrypting', 'uploading', 'aggregating', 'evaluating'];
    const phase = phases[r % phases.length];

    const payload: TelemetryPayload = {
      round: r,
      phase,
      global: {
        loss: Number(Math.max(0.14, 0.46 / (1.0 + r * 0.15)).toFixed(4)),
        dice: Number(Math.min(0.93, 0.69 + r * 0.032).toFixed(4)),
      },
      nodes: [
        {
          id: 1,
          name: "St. Jude Medical Silo",
          status: 'active',
          dice: Number(Math.min(0.92, 0.72 + r * 0.028).toFixed(4)),
          upload_ms: 780 + Math.floor(Math.sin(r) * 35),
          bytes: 5242880,
        },
        {
          id: 2,
          name: "Charité Berlin Silo",
          status: 'active',
          dice: Number(Math.min(0.94, 0.75 + r * 0.031).toFixed(4)),
          upload_ms: 890 + Math.floor(Math.cos(r) * 45),
          bytes: 5242880,
        },
        {
          id: 3,
          name: "Mayo Clinic Oncology",
          status: 'active',
          dice: Number(Math.min(0.95, 0.77 + r * 0.026).toFixed(4)),
          upload_ms: 750 + Math.floor(Math.sin(r * 2) * 25),
          bytes: 5242880,
        },
      ],
      privacy: {
        epsilon: 5.0,
        delta: 1e-5,
        epsilon_spent: Number(Math.min(5.0, 0.8 + r * 0.35).toFixed(2)),
      },
      encrypted: true,
    };

    if (this.onDataCallback) {
      this.onDataCallback(payload);
    }
    this.currentMockRound = (this.currentMockRound % 15) + 1;
  }

  public disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    if (this.mockInterval) {
      clearInterval(this.mockInterval);
      this.mockInterval = null;
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  // REST API Methods
  public async fetchScans(): Promise<ScanMetadata[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/scans`);
      if (res.ok) return await res.json();
    } catch (_) {}
    return [
      {
        id: "BraTS2021_00001",
        name: "Patient 001 - High-Grade Glioblastoma",
        diagnosis: "Glioblastoma Multiforme (WHO Grade IV) - Right Temporal",
        modalities: ["FLAIR", "T1ce", "T2", "T1"],
        dimensions: [64, 64, 64],
        assigned_hospital: 1,
        tumor_volume_cm3: 18.4,
      },
      {
        id: "BraTS2021_00002",
        name: "Patient 002 - Astrocytoma IDH-Mutant",
        diagnosis: "Astrocytoma IDH-Mutant (WHO Grade III) - Left Frontal",
        modalities: ["FLAIR", "T1ce", "T2", "T1"],
        dimensions: [64, 64, 64],
        assigned_hospital: 2,
        tumor_volume_cm3: 12.1,
      },
      {
        id: "BraTS2021_00003",
        name: "Patient 003 - Oligodendroglioma",
        diagnosis: "Oligodendroglioma 1p/19q-codeleted (WHO Grade II)",
        modalities: ["FLAIR", "T1ce", "T2", "T1"],
        dimensions: [64, 64, 64],
        assigned_hospital: 3,
        tumor_volume_cm3: 8.7,
      },
    ];
  }

  public async triggerDropout(nodeId: number): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/control/dropout/${nodeId}`, { method: 'POST' });
      return res.ok;
    } catch (_) {
      return false;
    }
  }

  public async triggerReconnect(nodeId: number): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/control/reconnect/${nodeId}`, { method: 'POST' });
      return res.ok;
    } catch (_) {
      return false;
    }
  }

  public async toggleEncryption(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/control/toggle-encryption`, { method: 'POST' });
      return res.ok;
    } catch (_) {
      return false;
    }
  }

  public async stepRound(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/control/step-round`, { method: 'POST' });
      return res.ok;
    } catch (_) {
      return false;
    }
  }

  public async selectScan(scanId: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/control/select-scan/${scanId}`, { method: 'POST' });
      return res.ok;
    } catch (_) {
      return false;
    }
  }

  public static getSliceUrl(
    scanId: string,
    axis: string,
    index: number,
    modality: string = 'FLAIR',
    wl: number = 0.5,
    ww: number = 1.0
  ): string {
    return `${API_BASE_URL}/scans/${scanId}/slice/${axis}/${index}?modality=${modality}&wl=${wl}&ww=${ww}`;
  }

  public static getMaskUrl(
    scanId: string,
    axis: string,
    index: number,
    wt: boolean = true,
    tc: boolean = true,
    et: boolean = true,
    opacity: number = 0.75
  ): string {
    return `${API_BASE_URL}/scans/${scanId}/mask/${axis}/${index}?wt=${wt}&tc=${tc}&et=${et}&opacity=${opacity}`;
  }
}
