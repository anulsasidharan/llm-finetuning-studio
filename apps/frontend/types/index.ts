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
