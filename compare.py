from typing import List
from tqdm.asyncio import tqdm_asyncio
from ossapi import Score
from api import fetch_beatmap_info
from utils import make_score_url
from models import Comparison


async def compare_scores(username_a: str, username_b: str, scores_a: List[Score], scores_b: List[Score]):

    comparisons: List[Comparison] = []
    for score_a, score_b in zip(scores_a, scores_b):
        if score_a is None or score_a.pp is None:
            comparisons.append(Comparison(type="missing", score_b=score_b))
            continue
        if score_a.pp < score_b.pp:
            comparisons.append(Comparison(type="weaker", score_a=score_a, score_b=score_b))
        # elif score_a.pp > score_b.pp:
        #     comparisons.append(Comparison(type="stronger", score_a=score_a, score_b=score_b))

    tasks = [fetch_beatmap_info(comp.score_b.beatmap) for comp in comparisons]
    beatmapsets = await tqdm_asyncio.gather(*tasks, desc="Fetching beatmap info", total=len(tasks))

    for comp, bmset in zip(comparisons, beatmapsets):
        score_a = comp.score_a
        score_b = comp.score_b
        bm = score_b.beatmap

        mods_str_a = "".join(mod.acronym for mod in score_a.mods) if score_a and score_a.mods else "NM"
        mods_str_b = "".join(mod.acronym for mod in score_b.mods) if score_b.mods else "NM"

        if comp.type == "missing":
            print(f"{username_a} has NO score on:")
        elif comp.type == "weaker":
            print(f"{username_a}'s score is WEAKER than {username_b} on:")
        elif comp.type == "stronger":
            print(f"{username_a}'s score is STRONGER than {username_b} on:")

        print(f"{bmset.artist} - {bmset.title} [{bm.version}]")
        if score_a:
            print(f"{username_a}: {score_a.pp:.2f}pp, {score_a.accuracy*100:.2f}%, Mods: {mods_str_a}")
        print(f"{username_b}: {score_b.pp:.2f}pp, {score_b.accuracy*100:.2f}%, Mods: {mods_str_b}")
        if score_a:
            print(f"{username_a} link: {make_score_url(score_a)}")
        print(f"{username_b} link: {make_score_url(score_b)}")
        print(f"Beatmap link: https://osu.ppy.sh/b/{bm.id}\n")
