from typing import Optional

from ...dto.base_model import BaseModel
from .pruneable_model import PruneableModel
from .pruneable_run import PruneableRun


class Pruneable(BaseModel):
    run: Optional[PruneableRun]
    model: Optional[PruneableModel]
