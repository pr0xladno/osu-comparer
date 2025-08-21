import asyncio
import logging
import os
from ossapi import OssapiAsync, Beatmap, Beatmapset, Score
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

api = OssapiAsync(int(CLIENT_ID), CLIENT_SECRET)

semaphore = asyncio.Semaphore(20)  # 20 concurrent requests (for avoiding rate limit)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


async def get_top_plays(user_id: int) -> list[Score]:
    """Get the top plays for the specified user

    Args:
        user_id (int): The user ID

    Returns:
        list[Score]: A list of the user's top plays
    """
    return await api.user_scores(user_id=user_id, type="best", limit=20)


def make_score_url(s: Score) -> str:
    """Create a URL to the score on the osu! website

    Args:
        s (Score): The score

    Returns:
        str: The URL to the score
    """
    if s.id is not None:
        return f"https://osu.ppy.sh/scores/{s.id}"
    if s.legacy_score_id is not None:
        mode = s.mode.value if hasattr(s.mode, "value") else str(s.mode)
        return f"https://osu.ppy.sh/scores/{mode}/{s.legacy_score_id}"
    return "N/A"


async def get_user_id_by_name(username: str) -> int:
    """Get the user ID for the specified username

    Args:
        username (str): The username

    Returns:
        int: The user ID
    """
    return await api.user(username)


async def fetch_beatmap_info(beatmap: Beatmap) -> Beatmapset:
    """Get the beatmapset for the specified beatmap

    Args:
        beatmap (Beatmap): The beatmap

    Returns:
        Beatmapset: The beatmapset
    """
    return await beatmap.beatmapset()


async def get_user_score_on_beatmap(user_id: int, beatmap_id: int) -> Score | None:
    """Get the user's score on the specified beatmap

    Args:
        user_id (int): The user ID
        beatmap_id (int): The beatmap ID

    Returns:
        (Score | None): The user's score, or None if no score is found
    """
    try:
        score = await api.beatmap_user_score(user_id=user_id, beatmap_id=beatmap_id)
        return score.score  # a BeatmapUserScore quirk
    except ValueError:
        logging.debug(f"Unable to fetch score for {user_id}/{beatmap_id}")
        return None


async def main():
    username_a: str = str(input("Insert your username: "))
    username_b: str = str(input("Insert the other user's username: "))

    user_id_a: int = await get_user_id_by_name(username_a)
    user_id_b: int = await get_user_id_by_name(username_b)

    scores_b: list[Score] = await get_top_plays(user_id_b)
    beatmaps_b = [score.beatmap for score in scores_b]

    score_tasks = [
        get_user_score_on_beatmap(user_id_a, beatmap.id) for beatmap in beatmaps_b
    ]
    scores_a = await asyncio.gather(*score_tasks)

    comparisons = []
    for score_a, score_b in zip(scores_a, scores_b):
        if score_a is None:
            comparisons.append(("missing", score_b))
        elif score_a.pp < score_b.pp:
            comparisons.append(("weaker", score_a, score_b))
        else:
            continue

    beatmapset_tasks = [
        fetch_beatmap_info(item[1].beatmap if item[0] == "missing" else item[2].beatmap)
        for item in comparisons
    ]
    beatmapsets = await asyncio.gather(*beatmapset_tasks)

    for comp, bmset in zip(comparisons, beatmapsets):
        if comp[0] == "missing":
            score_b = comp[1]
            bm = score_b.beatmap
            mods_str = (
                "".join(mod.acronym for mod in score_b.mods) if score_b.mods else "NM"
            )
            print(f"{username_a} has NO score on:")
            print(f"{bmset.artist} - {bmset.title} [{bm.version}]")
            print(
                f"{username_b}: {score_b.pp:.2f}pp, {score_b.accuracy*100:.2f}%, Mods: {mods_str}"
            )
            print(f"Score link: {make_score_url(score_b)}")
            print(f"Beatmap link: https://osu.ppy.sh/b/{bm.id}\n")
        elif comp[0] == "weaker":
            score_a, score_b = comp[1], comp[2]
            bm = score_b.beatmap
            mods_str_a = (
                "".join(mod.acronym for mod in score_a.mods) if score_a.mods else "NM"
            )
            mods_str_b = (
                "".join(mod.acronym for mod in score_b.mods) if score_b.mods else "NM"
            )
            print(f"{username_a}'s score is WEAKER than {username_b} on:")
            print(f"{bmset.artist} - {bmset.title} [{bm.version}]")
            print(
                f"{username_a}: {score_a.pp:.2f}pp, {score_a.accuracy*100:.2f}%, Mods: {mods_str_a}"
            )
            print(
                f"{username_b}: {score_b.pp:.2f}pp, {score_b.accuracy*100:.2f}%, Mods: {mods_str_b}"
            )
            print(f"{username_a} link: {make_score_url(score_a)}")
            print(f"{username_b} link: {make_score_url(score_b)}")
            print(f"Beatmap link: https://osu.ppy.sh/b/{bm.id}\n")


asyncio.run(main())

logging.info("Done")
