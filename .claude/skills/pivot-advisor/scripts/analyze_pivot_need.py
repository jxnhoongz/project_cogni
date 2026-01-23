#!/usr/bin/env python3
"""
Analyze if channel strategy needs pivoting.

Usage:
    python analyze_pivot_need.py --weeks 4
"""

import argparse
import json
from datetime import datetime

# Mock historical data - in production, pull from metrics files
MOCK_WEEKLY_METRICS = [
    {"week": 1, "ctr": 4.5, "avg_view_pct": 62, "subscribers": 45, "views": 3200},
    {"week": 2, "ctr": 4.2, "avg_view_pct": 58, "subscribers": 38, "views": 2900},
    {"week": 3, "ctr": 3.8, "avg_view_pct": 55, "subscribers": 25, "views": 2400},
    {"week": 4, "ctr": 3.5, "avg_view_pct": 52, "subscribers": 18, "views": 2100},
]

PIVOT_THRESHOLDS = {
    "ctr_decline": 0.20,  # 20% decline triggers review
    "sub_stall": 40,  # <40 subs in 4 weeks = stall
    "view_pct_floor": 30,  # <30% avg view = problem
    "growth_stall_weeks": 4  # Weeks of stagnation
}


def calculate_trend(values: list) -> float:
    """Calculate trend as percentage change from first to last."""
    if len(values) < 2 or values[0] == 0:
        return 0
    return round((values[-1] - values[0]) / values[0], 2)


def detect_patterns(metrics: list) -> dict:
    """Detect failure patterns in metrics."""
    patterns = []

    # CTR trend
    ctrs = [m["ctr"] for m in metrics]
    ctr_trend = calculate_trend(ctrs)
    if ctr_trend < -PIVOT_THRESHOLDS["ctr_decline"]:
        patterns.append("declining_ctr")

    # View duration trend
    view_pcts = [m["avg_view_pct"] for m in metrics]
    view_trend = calculate_trend(view_pcts)
    if view_pcts[-1] < PIVOT_THRESHOLDS["view_pct_floor"]:
        patterns.append("low_retention")

    # Subscriber growth
    total_subs = sum(m["subscribers"] for m in metrics)
    if total_subs < PIVOT_THRESHOLDS["sub_stall"]:
        patterns.append("subscriber_stall")

    # Views trend
    views = [m["views"] for m in metrics]
    views_trend = calculate_trend(views)
    if views_trend < -0.30:
        patterns.append("declining_views")

    return {
        "patterns": patterns,
        "ctr_trend": ctr_trend,
        "view_trend": view_trend,
        "views_trend": views_trend,
        "total_subscribers": total_subs
    }


def get_recommendations(patterns: list) -> list:
    """Get recommendations based on detected patterns."""
    recs = []

    if "declining_ctr" in patterns:
        recs.append("Test new hook styles (contrarian, question, story)")
        recs.append("Review thumbnail contrast and text")

    if "low_retention" in patterns:
        recs.append("Tighten scripts - cut filler")
        recs.append("Check pacing in first 30 seconds")

    if "subscriber_stall" in patterns:
        recs.append("Review content-audience fit")
        recs.append("Consider niching down (e.g., habits books only)")

    if "declining_views" in patterns:
        recs.append("Check posting consistency")
        recs.append("Review topic selection - align with trends")

    if not recs:
        recs.append("Continue current strategy")

    return recs


def get_urgency(patterns: list) -> str:
    """Determine urgency level."""
    if len(patterns) >= 3:
        return "high"
    elif len(patterns) >= 2:
        return "medium"
    elif len(patterns) >= 1:
        return "low"
    return "none"


def analyze_pivot_need(weeks: int) -> dict:
    """Analyze if pivot is needed."""
    metrics = MOCK_WEEKLY_METRICS[:weeks]

    analysis = detect_patterns(metrics)
    patterns = analysis["patterns"]
    recommendations = get_recommendations(patterns)
    urgency = get_urgency(patterns)

    # Root cause hypothesis
    if "declining_ctr" in patterns and "low_retention" in patterns:
        hypothesis = "Content-audience mismatch - hooks attract wrong viewers"
    elif "declining_ctr" in patterns:
        hypothesis = "Hook patterns becoming stale or thumbnails not standing out"
    elif "low_retention" in patterns:
        hypothesis = "Scripts too long or pacing issues"
    elif "subscriber_stall" in patterns:
        hypothesis = "Topic selection not resonating with target audience"
    else:
        hypothesis = "No significant issues detected"

    return {
        "issue_detected": len(patterns) > 0,
        "patterns": patterns,
        "metrics": {
            "ctr_trend": analysis["ctr_trend"],
            "view_trend": analysis["view_trend"],
            "subscriber_growth": analysis["total_subscribers"],
            "weeks_analyzed": weeks
        },
        "root_cause_hypothesis": hypothesis,
        "recommended_actions": recommendations,
        "urgency": urgency,
        "analyzed_at": datetime.utcnow().isoformat() + "Z"
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze pivot need")
    parser.add_argument("--weeks", type=int, default=4)
    args = parser.parse_args()

    result = analyze_pivot_need(args.weeks)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()