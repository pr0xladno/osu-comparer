import os
from pathlib import Path
import sys
from ossapi import GameMode, OssapiAsync, Beatmap, Beatmapset, Score
from dotenv import load_dotenv

def load_env():
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path.cwd()

    env_path = base_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        print(".env file not found, relying on system environment variables.")
        
load_env()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

api = OssapiAsync(int(CLIENT_ID), CLIENT_SECRET)


async def get_top_plays(
    user_id: int, limit: int = 100, mode: GameMode = GameMode.OSU
) -> list[Score]:
    """Get the top plays for the specified user

    Args:
        user_id (int): The user ID
        limit (int, optional): The maximum number of scores to return. Defaults to 200.
        mode (GameMode, optional): The game mode to fetch scores for. Defaults to GameMode.osu.

    Returns:
        List[Score]: A list of the user's top plays
    """
    return await api.user_scores(user_id=user_id, type="best", limit=limit, mode=mode)


async def get_user_id_by_name(username: str) -> int:
    """Get the user ID for the specified username

    Args:
        username (str): The username

    Returns:
        int: The user ID
    """
    try:
        return await api.user(username)
    except ValueError:
        raise ValueError(f"User {username} not found")


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
        Score | None: The user's score, or None if no score is found
    """
    try:
        score = await api.beatmap_user_score(user_id=user_id, beatmap_id=beatmap_id)
        return score.score  # a BeatmapUserScore quirk
    except ValueError:
        return None
