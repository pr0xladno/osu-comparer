import sys
import asyncio
import logging
from tqdm.asyncio import tqdm_asyncio
from api import get_top_plays, get_user_id_by_name, get_user_score_on_beatmap
from compare import compare_scores

DEFAULT_LIMIT = 100 # amount of scores to fetch

if getattr(sys, "frozen", False):
    logging.basicConfig(level=logging.CRITICAL)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


async def run_comparison():
    try:
        username_a = input("Insert your username (or type 'exit' to quit): ")
        if username_a.lower() == "exit":
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
    
    user_input = input(f"Insert the amount of scores to be fetched (max: {DEFAULT_LIMIT}): ")

    try:
        limit = int(user_input) if user_input.strip() else DEFAULT_LIMIT
    except ValueError:
        print("Invalid input, using default value.")
        limit = DEFAULT_LIMIT

    print(f"Fetching top plays for {username_b}...")
    scores_b = await get_top_plays(user_id_b, limit=limit)
    beatmaps_b = [score.beatmap for score in scores_b]

    print(f"Fetching scores for {username_a} on {len(beatmaps_b)} beatmaps...")
    tasks = [get_user_score_on_beatmap(user_id_a, beatmap.id) for beatmap in beatmaps_b]
    scores_a = await tqdm_asyncio.gather(*tasks, desc="Fetching user scores", total=len(tasks))
    
    await compare_scores(username_a, username_b, scores_a, scores_b)
    return True


async def main():
    print("Welcome to osu! score comparer!\n")
    while await run_comparison():
        print("\n--- Next Comparison ---\n")


if __name__ == "__main__":
    asyncio.run(main())
    logging.info("Done")
