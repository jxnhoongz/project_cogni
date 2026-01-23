#!/usr/bin/env python3
"""
Analyze A/B test results and determine winner.

Usage:
    python analyze_ab_test.py --experiment hook_style
"""

import argparse
import json
from pathlib import Path

DEFAULT_JOBS_DIR = Path(__file__).parent.parent.parent.parent.parent / "cognilab" / "jobs"

# Mock experiment data - in production, this would be pulled from job files
MOCK_EXPERIMENTS = {
    "hook_style": {
        "question": {"videos": ["S_01", "S_04", "S_07"], "total_views": 3750, "total_impressions": 117187, "clicks": 3750},
        "contrarian": {"videos": ["S_02", "S_05", "S_08"], "total_views": 3540, "total_impressions": 73750, "clicks": 3540},
        "story": {"videos": ["S_03", "S_06", "S_09"], "total_views": 3960, "total_impressions": 101538, "clicks": 3960},
    }
}


def calculate_ctr(clicks: int, impressions: int) -> float:
    """Calculate CTR percentage."""
    if impressions == 0:
        return 0
    return round((clicks / impressions) * 100, 2)


def chi_square_test(observed: list, expected: list) -> float:
    """Simple chi-square calculation for significance."""
    if len(observed) != len(expected):
        return 0

    chi_sq = sum((o - e) ** 2 / e for o, e in zip(observed, expected) if e > 0)

    # Rough p-value approximation (for 2 degrees of freedom)
    # chi_sq > 5.99 => p < 0.05 => 95% confidence
    # chi_sq > 9.21 => p < 0.01 => 99% confidence
    if chi_sq > 9.21:
        return 0.99
    elif chi_sq > 5.99:
        return 0.95
    elif chi_sq > 4.61:
        return 0.90
    elif chi_sq > 3.22:
        return 0.85
    else:
        return 0.50


def analyze_experiment(experiment_name: str) -> dict:
    """Analyze experiment results."""
    if experiment_name not in MOCK_EXPERIMENTS:
        return {"error": f"Experiment not found: {experiment_name}"}

    data = MOCK_EXPERIMENTS[experiment_name]

    # Calculate metrics per variant
    variants = {}
    ctrs = []
    total_impressions = sum(v["total_impressions"] for v in data.values())

    for variant_name, variant_data in data.items():
        ctr = calculate_ctr(variant_data["clicks"], variant_data["total_impressions"])
        variants[variant_name] = {
            "ctr": ctr,
            "views": variant_data["total_views"],
            "impressions": variant_data["total_impressions"],
            "video_count": len(variant_data["videos"])
        }
        ctrs.append(ctr)

    # Find winner
    best_variant = max(variants.items(), key=lambda x: x[1]["ctr"])
    winner_name = best_variant[0]
    winner_ctr = best_variant[1]["ctr"]

    # Calculate confidence (simplified)
    avg_ctr = sum(ctrs) / len(ctrs)
    observed = [v["ctr"] for v in variants.values()]
    expected = [avg_ctr] * len(observed)
    confidence = chi_square_test(observed, expected)

    # Check minimum sample
    min_views = min(v["views"] for v in variants.values())
    sufficient_sample = min_views >= 1000

    return {
        "experiment": experiment_name,
        "variants": variants,
        "winner": winner_name if confidence >= 0.85 and sufficient_sample else None,
        "confidence": confidence,
        "sufficient_sample": sufficient_sample,
        "min_views_per_variant": min_views,
        "recommendation": f"Use {winner_name} hooks more often" if confidence >= 0.85 else "Need more data"
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze A/B test")
    parser.add_argument("--experiment", required=True)
    args = parser.parse_args()

    result = analyze_experiment(args.experiment)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()