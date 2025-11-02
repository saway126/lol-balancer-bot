from typing import List
import math

def team_mmr_from_members(member_mmrs: List[int]) -> int:
    if not member_mmrs:
        return 1200
    return round(sum(member_mmrs) / len(member_mmrs))

def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))

def update_elo(rating_a: int, rating_b: int, score_a: float, k: float = 24.0):
    ea = expected_score(rating_a, rating_b)
    new_a = rating_a + k * (score_a - ea)
    # eb = expected_score(rating_b, rating_a) == 1 - ea
    new_b = rating_b + k * ((1 - score_a) - (1 - ea))
    return round(new_a), round(new_b)


def distribute_team_delta_equal(member_mmrs: List[int], team_delta: int) -> List[int]:
    """Distribute a team-level MMR delta equally to members.

    This is a simple scheme: each member gets round(team_delta / n).
    The remainder is added to the highest-MMR members to keep totals consistent.
    """
    n = len(member_mmrs)
    if n == 0:
        return []
    base = team_delta // n
    remainder = team_delta - base * n
    # sort indices by mmr descending to give remainder to higher mmr players
    indexed = sorted(enumerate(member_mmrs), key=lambda x: x[1], reverse=True)
    deltas = [base] * n
    for i in range(remainder):
        idx = indexed[i][0]
        deltas[idx] += 1
    return [member_mmrs[i] + deltas[i] for i in range(n)]


def dynamic_k_factor(games_played: int) -> float:
    """Return a K-factor based on games played; fewer games => higher K for faster rating adjustment."""
    if games_played < 10:
        return 40.0
    if games_played < 30:
        return 30.0
    return 24.0
