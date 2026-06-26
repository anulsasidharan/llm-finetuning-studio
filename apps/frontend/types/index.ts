import type { components } from "./api-schema";

export type UserResponse = components["schemas"]["UserResponse"];
export type TokenResponse = components["schemas"]["TokenResponse"];
export type DatasetResponse = components["schemas"]["DatasetResponse"];
export type FineTuneJobResponse = components["schemas"]["FineTuneJobResponse"];
export type FineTuneJobConfigResponse = components["schemas"]["FineTuneJobConfigResponse"];
export type ModelCatalogResponse = components["schemas"]["ModelCatalogResponse"];
export type ExperimentResponse = components["schemas"]["ExperimentResponse"];
export type ExperimentRunResponse = components["schemas"]["ExperimentRunResponse"];
export type ExperimentCompareResponse = components["schemas"]["ExperimentCompareResponse"];
export type ExperimentRunCompareEntry = components["schemas"]["ExperimentRunCompareEntry"];
export type GpuPricingResponse = components["schemas"]["GpuPricingResponse"];
export type CostEstimateRequest = components["schemas"]["CostEstimateRequest"];
export type CostEstimateResponse = components["schemas"]["CostEstimateResponse"];
export type GpuPricingSyncResponse = components["schemas"]["GpuPricingSyncResponse"];
export type GpuPricingSyncVendorResult = components["schemas"]["GpuPricingSyncVendorResult"];
export type EvalJobResponse = components["schemas"]["EvalJobResponse"];
export type EvalCompareCreate = components["schemas"]["EvalCompareCreate"];
export type EvalBenchmarkCreate = components["schemas"]["EvalBenchmarkCreate"];
export type ModelRegistryResponse = components["schemas"]["ModelRegistryResponse"];
export type ModelRegistryCreate = components["schemas"]["ModelRegistryCreate"];
export type PushHFRequest = components["schemas"]["PushHFRequest"];
export type ExportGGUFRequest = components["schemas"]["ExportGGUFRequest"];

export type DatasetFormat = DatasetResponse["format"];
export type FineTuneJobStatus = FineTuneJobResponse["status"];
export type Methodology = FineTuneJobResponse["methodology"];
export type EvalType = EvalJobResponse["eval_type"];
export type EvalJobStatus = EvalJobResponse["status"];
export type EvalBenchmark = EvalCompareCreate["benchmarks"] extends (infer T)[] | null | undefined
  ? T
  : never;

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
