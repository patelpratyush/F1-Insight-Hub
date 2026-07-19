"""
Honest "model performance" metric for the rating engine.

There's no held-out test set (it isn't a trained model), so accuracy here
means something specific and real: how often the rating engine's driver
ordering agrees with the actual current championship order. That's a rank
concordance, not a claim about predicting future races.
"""
from itertools import combinations
from typing import Dict


def rating_concordance(
    scores: Dict[str, float],
    driver_standings: Dict[str, Dict],
) -> Dict:
    """
    Compare the rating engine's driver ordering (by score) against the
    actual championship order (by points) for every pair of drivers with
    a standings entry.

    Returns {"concordant_pct": float 0-1, "compared_pairs": int}.
    """
    ranked = [
        (code, s.get("points", 0))
        for code, s in driver_standings.items()
        if code in scores
    ]
    if len(ranked) < 2:
        return {"concordant_pct": None, "compared_pairs": 0}

    concordant = 0
    total = 0
    for (code_a, pts_a), (code_b, pts_b) in combinations(ranked, 2):
        if pts_a == pts_b:
            continue
        total += 1
        actual_a_better = pts_a > pts_b
        rated_a_better = scores[code_a] > scores[code_b]
        if actual_a_better == rated_a_better:
            concordant += 1

    if total == 0:
        return {"concordant_pct": None, "compared_pairs": 0}

    return {
        "concordant_pct": round(concordant / total, 4),
        "compared_pairs": total,
    }
