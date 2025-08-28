from typing import List
from ossapi import Score
from osu_comparer.models import Comparison

async def compare_scores(
    scores_a: List[Score],
    scores_b: List[Score],
    beatmapsets: List = None
) -> List[Comparison]:

    comparisons: List[Comparison] = []
    for i, (score_a, score_b) in enumerate(zip(scores_a, scores_b)):
        if score_a is None or score_a.pp is None:
            comp = Comparison(type="MISSING", score_b=score_b)
        elif score_a.pp < score_b.pp:
            comp = Comparison(type="WEAKER", score_a=score_a, score_b=score_b)
        else:
            comp = Comparison(type="STRONGER", score_a=score_a, score_b=score_b)

        if beatmapsets:
            comp.beatmapset = beatmapsets[i]
            
        comparisons.append(comp)

    await calculate_pp_delta(comparisons)

    return comparisons

async def calculate_pp_delta(comparisons: List[Comparison]) -> None:
    for comp in comparisons:
        if comp.type == "MISSING":
            comp.pp_delta = comp.score_b.pp
        else:
            comp.pp_delta = comp.score_b.pp - comp.score_a.pp