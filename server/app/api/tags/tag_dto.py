from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class TagDTO(BaseModel):
    id: int
    name: Optional[str]  
    last_push: datetime