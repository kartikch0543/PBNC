import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.warning import WarningCode


class ExtractionWarningResponse(BaseModel):
    """Schema for QA review items."""
    id: uuid.UUID
    document_id: uuid.UUID
    question_id: Optional[uuid.UUID] = None
    warning_code: WarningCode
    message: str
    source_page: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
