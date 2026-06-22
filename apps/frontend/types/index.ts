import type { components } from "./api-schema";

export type UserResponse = components["schemas"]["UserResponse"];
export type TokenResponse = components["schemas"]["TokenResponse"];
export type DatasetResponse = components["schemas"]["DatasetResponse"];
export type FineTuneJobResponse = components["schemas"]["FineTuneJobResponse"];
export type FineTuneJobConfigResponse = components["schemas"]["FineTuneJobConfigResponse"];
export type ModelCatalogResponse = components["schemas"]["ModelCatalogResponse"];

export type DatasetFormat = DatasetResponse["format"];
export type FineTuneJobStatus = FineTuneJobResponse["status"];
export type Methodology = FineTuneJobResponse["methodology"];

// WS /ws/training/{job_id} payloads (apps/backend/websocket/training_hub.py) — hand-written,
// not OpenAPI-generated, since WebSocket messages aren't part of the REST schema.
export type TrainingMetricsUpdate = {
  type: "metrics_update";
  job_id: string;
  step: number;
  epoch: number | null;
  train_loss: number | null;
  eval_loss: number | null;
  gpu_utilization_pct: number | null;
  vram_used_gb: number | null;
  tokens_per_second: number | null;
};

export type TrainingStatusChange = {
  type: "status_change";
  job_id: string;
  status: FineTuneJobStatus;
};

export type TrainingSocketMessage = TrainingMetricsUpdate | TrainingStatusChange;
