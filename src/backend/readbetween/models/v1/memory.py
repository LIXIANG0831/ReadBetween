from typing import List, Dict, Any

from pydantic import BaseModel, Field


class MemoryQuery(BaseModel):
    condition: str = Field(...,examples=["WHERE n.user_id = $user_id"], description="cypher语句")
    condition_parameters: Dict[str, Any] = Field({}, examples=[{"user_id": "34516e93-7861-4ebf-8f2d-eedadbe99528"}], description="参数")
