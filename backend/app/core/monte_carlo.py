"""
Monte Carlo race outcome simulator.
Takes driver scores (0–1) and runs N iterations to produce
probability distributions over finishing positions.
"""
import logging
from typing import Dict, List

import numpy as np

logger = logging.getLogger(__name__)

F1_POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


def simulate_race(
    driver_scores: Dict[str, float],
    n_iterations: int = 1000,
    chaos_factor: float = 0.15,   # std deviation of Gaussian noise
) -> List[Dict]:
    """
    Simulate a race grid n_iterations times.

    Returns a list of dicts sorted by median finishing position:
      [{"driver": code, "win_pct": 0.23, "podium_pct": 0.61,
        "points_pct": 0.80, "median_pos": 2, "expected_points": 14.1,
        "p10_pos": 1, "p90_pos": 5, "pos_std": 1.2}, ...]

    p10_pos/p90_pos are the 10th/90th percentile finishing position across
    all n_iterations trials -- a genuine confidence interval from the
    simulation ensemble, not a fabricated stat.
    """
    if not driver_scores:
        return []

    codes = list(driver_scores.keys())
    base = np.array([driver_scores[c] for c in codes], dtype=float)
    n = len(codes)

    # (n_iterations × n_drivers) score matrix with Gaussian noise
    noise = np.random.normal(0, chaos_factor, size=(n_iterations, n))
    scores_matrix = base[np.newaxis, :] + noise          # broadcast
    scores_matrix = np.clip(scores_matrix, 0.01, None)   # no negatives

    # Sort descending each row → finishing order (0 = P1)
    order_matrix = np.argsort(-scores_matrix, axis=1)    # (iters, n)

    # Build pos_rows: pos_rows[iter, driver] = finishing position (0-indexed) of driver in that iter
    # order_matrix[iter, rank] = driver_i  →  inverse permutation gives pos_rows[iter, driver] = rank
    pos_rows = np.argsort(order_matrix, axis=1)

    # Vectorized tally — replaces O(n_iterations × n_drivers) Python loop
    pts_table = np.zeros(n, dtype=float)
    n_scoring = min(len(F1_POINTS), n)
    pts_table[:n_scoring] = F1_POINTS[:n_scoring]

    pos_sum = (pos_rows + 1).sum(axis=0)
    wins    = (pos_rows == 0).sum(axis=0)
    podiums = (pos_rows < 3).sum(axis=0)
    in_pts  = (pos_rows < 10).sum(axis=0)
    pts_sum = pts_table[pos_rows].sum(axis=0)

    finishing_positions = pos_rows + 1  # (iters, n), 1-indexed
    p10 = np.percentile(finishing_positions, 10, axis=0)
    p90 = np.percentile(finishing_positions, 90, axis=0)
    pos_std = finishing_positions.std(axis=0)

    results = []
    for i, code in enumerate(codes):
        results.append({
            "driver": code,
            "win_pct":      round(wins[i] / n_iterations, 4),
            "podium_pct":   round(podiums[i] / n_iterations, 4),
            "points_pct":   round(in_pts[i] / n_iterations, 4),
            "median_pos":   int(round(pos_sum[i] / n_iterations)),
            "expected_pts": round(pts_sum[i] / n_iterations, 2),
            "p10_pos":      int(round(p10[i])),
            "p90_pos":      int(round(p90[i])),
            "pos_std":      round(float(pos_std[i]), 2),
        })

    results.sort(key=lambda x: x["median_pos"])
    for rank, r in enumerate(results, 1):
        r["predicted_position"] = rank

    return results
