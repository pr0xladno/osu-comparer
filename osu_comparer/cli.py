import asyncio
import sys
import logging
from tqdm.asyncio import tqdm_asyncio
from osu_comparer.api import (
    fetch_beatmap_info,
    get_top_plays,
    get_user_id_by_name,
    get_user_score_on_beatmap,
)
from osu_comparer.compare import compare_scores
from osu_comparer.utils import make_score_url, mods_to_str
from osu_comparer.models import Comparison

DEFAULT_LIMIT = 100


async def run_comparison():
    try:
        username_a = input("Insert your username (or type 'q' to quit): ")
        if username_a.lower() == "q":
            return False
        user_id_a = await get_user_id_by_name(username_a)
    except ValueError as e:
        logging.error(e)
        return True

    try:
        username_b = input("Insert the other user's username: ")
        user_id_b = await get_user_id_by_name(username_b)
    except ValueError as e:
        logging.error(e)
        return True

    user_input = input(
        f"Insert the amount of scores to be fetched (max: {DEFAULT_LIMIT}): "
    )

    try:
        limit = int(user_input) if user_input.strip() else DEFAULT_LIMIT
    except ValueError:
        print("Invalid input, using default value.")
        limit = DEFAULT_LIMIT

    print(f"Fetching top plays for {username_b}...")
    scores_b = await get_top_plays(user_id_b, limit=limit)
    beatmaps_b = [score.beatmap for score in scores_b]

    print(f"Fetching scores for {username_a} on {len(beatmaps_b)} beatmaps...")
    
    tasks_scores = [get_user_score_on_beatmap(user_id_a, bm.id) for bm in beatmaps_b]
    scores_a = await tqdm_asyncio.gather(*tasks_scores, desc="Fetching user scores", total=len(tasks_scores))

    beatmap_tasks = [fetch_beatmap_info(score_b.beatmap) for score_b in scores_b]
    beatmapsets = await tqdm_asyncio.gather(
        *beatmap_tasks, desc="Fetching beatmap info", total=len(beatmap_tasks)
    )

    comparisons = await compare_scores(scores_a, scores_b, beatmapsets=beatmapsets)

    for comp in comparisons:
        print_comparison(username_a, username_b, comp)
    return True


def print_comparison(username_a, username_b, comp: Comparison):
    score_a = comp.score_a
    score_b = comp.score_b
    bm = score_b.beatmap
    bmset = comp.beatmapset

    mods_str_a = mods_to_str(score_a)
    mods_str_b = mods_to_str(score_b)

    if comp.type == "MISSING":
        print(f"{username_a} has NO score on:")
    else:
        print(f"{username_a}'s score is {comp.type} than {username_b} on:")

    print(f"{bmset.artist} - {bmset.title} [{bm.version}]")
    if score_a:
        print(
            f"{username_a}: {score_a.pp:.2f}pp, {score_a.accuracy*100:.2f}%, Mods: {mods_str_a}"
        )
    print(
        f"{username_b}: {score_b.pp:.2f}pp, {score_b.accuracy*100:.2f}%, Mods: {mods_str_b}"
    )
    if score_a:
        print(f"{username_a} link: {make_score_url(score_a)}")
    print(f"{username_b} link: {make_score_url(score_b)}")
    print(f"Beatmap link: https://osu.ppy.sh/b/{bm.id}\n")


async def main():
    print("Welcome to osu!comparer!\n")
    while await run_comparison():
        print("\n--- Next Comparison ---\n")


if __name__ == "__main__":

    if getattr(sys, "frozen", False):
        logging.basicConfig(level=logging.CRITICAL)
    else:
        logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
    logging.info("Done")
