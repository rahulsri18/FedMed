/**
 * dashboard/src/services/mockTelemetry.js
 * Owner: M5 (Dashboard & Visualization Lead)
 * 
 * Provides live telemetry feed:
 * 1. Tries connecting to real FastAPI WebSocket: ws://localhost:8000/ws/telemetry
 * 2. If backend is not running, falls back automatically to local mock generator
 *    matching the exact FedMed schema.
 */

export class TelemetryService {
  constructor(onDataCallback, onStatusChange) {
    this.onData = onDataCallback;
    this.onStatus = onStatusChange;
    this.ws = null;
    this.mockInterval = null;
    this.currentRound = 1;
    this.maxRounds = 10;
    this.isUsingMock = false;
  }

  connect(url = "ws://localhost:8000/ws/telemetry") {
    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.isUsingMock = false;
        if (this.onStatus) this.onStatus({ connected: true, isMock: false });
        if (this.mockInterval) clearInterval(this.mockInterval);
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.onData(payload);
        } catch (e) {
          console.error("Failed to parse WebSocket JSON payload:", e);
        }
      };

      this.ws.onerror = () => {
        // Fallback to mock generator
        if (!this.isUsingMock) {
          this.startMockFeed();
        }
      };

      this.ws.onclose = () => {
        if (!this.isUsingMock) {
          this.startMockFeed();
        }
      };
    } catch (e) {
      this.startMockFeed();
    }
  }

  startMockFeed() {
    this.isUsingMock = true;
    if (this.onStatus) this.onStatus({ connected: true, isMock: true });

    // Emit initial telemetry immediately
    this.emitMockPayload();

    if (this.mockInterval) clearInterval(this.mockInterval);
    this.mockInterval = setInterval(() => {
      this.emitMockPayload();
    }, 2800);
  }

  emitMockPayload() {
    const r = this.currentRound;
    const isAggregating = r % 2 === 0;

    const payload = {
      round: r,
      phase: isAggregating ? "aggregating" : "training",
      global: {
        loss: Number((0.48 / (1.0 + r * 0.16)).toFixed(2)),
        dice: Number(Math.min(0.92, 0.65 + r * 0.038).toFixed(2)),
      },
      nodes: [
        {
          id: 1,
          name: "St. Jude Children's",
          status: "active",
          dice: Number((0.71 + r * 0.031).toFixed(2)),
          upload_ms: 812 + Math.floor(Math.sin(r) * 35),
          bytes: 5242880,
        },
        {
          id: 2,
          name: "Charité Berlin",
          status: "active",
          dice: Number((0.73 + r * 0.033).toFixed(2)),
          upload_ms: 920 + Math.floor(Math.cos(r) * 40),
          bytes: 5242880,
        },
        {
          id: 3,
          name: "Mayo Clinic Oncology",
          status: "active",
          dice: Number((0.75 + r * 0.029).toFixed(2)),
          upload_ms: 780 + Math.floor(Math.sin(r * 2) * 25),
          bytes: 5242880,
        },
      ],
      privacy: {
        epsilon: 5.0,
        delta: 1e-5,
        epsilon_spent: Number(Math.min(5.0, 0.9 + r * 0.38).toFixed(1)),
      },
      encrypted: true,
    };

    this.onData(payload);
    this.currentRound = (this.currentRound % this.maxRounds) + 1;
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
    if (this.mockInterval) {
      clearInterval(this.mockInterval);
    }
  }
}
