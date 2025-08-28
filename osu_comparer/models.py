from pydantic import BaseModel, ConfigDict
from ossapi import Score, Beatmapset
from typing import Literal, Optional


class Comparison(BaseModel):
    type: Literal["MISSING", "WEAKER", "STRONGER"]
    score_a: Optional[Score] = None
    score_b: Score
    beatmapset: Optional[Beatmapset] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
