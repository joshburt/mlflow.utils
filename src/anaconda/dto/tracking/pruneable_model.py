from ...dto.base_model import BaseModel


class PruneableModel(BaseModel):
    name: str
    version: str
