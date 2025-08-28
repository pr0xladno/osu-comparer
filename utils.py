from ossapi import Score

def make_score_url(score: Score) -> str:
    """Create a URL to the score on the osu! website

    Args:
        s (Score): The score

    Returns:
        str: The URL to the score
    """
    if score.id is not None:
        return f"https://osu.ppy.sh/scores/{score.id}"
    if score.legacy_score_id is not None:
        mode = score.mode.value if hasattr(score.mode, "value") else str(score.mode)
        return f"https://osu.ppy.sh/scores/{mode}/{score.legacy_score_id}"
    return "N/A"

def mods_to_str(mods) -> str:
    if mods:
        return "".join(mod.acronym for mod in mods)
    return "NM"