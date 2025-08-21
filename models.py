from typing import Optional
from ossapi import Beatmapset, Score
from pydantic import BaseModel


class BeatmapComparison(BaseModel):
    type: str  # "missing" or "weaker"
    beatmapset: Beatmapset
    score_a: Optional[Score] = None
    score_b: Optional[Score] = None