from pydantic import BaseModel, ConfigDict
from ossapi import Score
from typing import Literal, Optional


class Comparison(BaseModel):
    type: Literal["missing", "weaker", "stronger"]
    score_a: Optional[Score] = None
    score_b: Score
    
    model_config = ConfigDict(arbitrary_types_allowed=True)