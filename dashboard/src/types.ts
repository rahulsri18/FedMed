export interface GlobalMetrics {
  loss: number;
  dice: number;
  rounds_total?: number;
}

export interface NodeTelemetry {
  id: number;
  name?: string;
  status: 'active' | 'training' | 'uploading' | 'offline' | string;
  dice: number;
  upload_ms: number;
  bytes: number;
}

export interface PrivacyBudget {
  epsilon: number;
  delta: number;
  epsilon_spent: number;
}

export interface TelemetryPayload {
  round: number;
  phase: 'training' | 'encrypting' | 'uploading' | 'aggregating' | 'evaluating' | 'idle' | string;
  global: GlobalMetrics;
  nodes: NodeTelemetry[];
  privacy: PrivacyBudget;
  encrypted: boolean;
}

export interface ScanMetadata {
  id: string;
  name: string;
  diagnosis?: string;
  modalities: string[];
  dimensions: number[];
  assigned_hospital: number;
  tumor_volume_cm3?: number;
}

export interface ConnectionStatus {
  connected: boolean;
  isMock: boolean;
  url?: string;
}

export interface ConvergenceRecord {
  round: number;
  dice: number;
  loss: number;
  encrypted?: boolean;
}
