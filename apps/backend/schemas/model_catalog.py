from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ModelCatalogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    model_id: str
    display_name: str
    family: str
    parameter_count_b: float
    supports_instruct: bool
