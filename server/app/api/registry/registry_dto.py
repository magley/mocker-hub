import enum
from typing import List
from pydantic import BaseModel

class RegistryActionOperation(str, enum.Enum):
    pull = "pull"
    push = "push"
    delete = "delete"

class RegistryAction(BaseModel):
    username: str
    repo_canonical_name: str
    operations: List[RegistryActionOperation]

class DeleteTagDTO(BaseModel):
    repo_id: int
    tag_name: str

class DeleteResponseDTO(BaseModel):
    message: str