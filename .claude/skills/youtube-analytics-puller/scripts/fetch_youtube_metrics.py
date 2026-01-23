#!/usr/bin/env python3
"""
Fetch YouTube Analytics metrics for a video.

Usage:
    python fetch_youtube_metrics.py --video-id VIDEO_ID --period 7d

Requires:
    - YouTube Analytics API enabled
    - OAuth credentials (same as uploader)
"""

import argparse
import json
from datetime import datetime, timedelta

# Mock data for demonstration - replace with actual API calls
MOCK_METRICS = {
    "views": 1247,
    "estimatedMinutesWatched": 892,
    "averageViewDuration": 57,
    "averageViewPercentage": 68.5,
    "likes": 143,
    "dislikes": 5,
    "comments": 12,
    "shares": 8,
    "subscribersGained": 15,
    "subscribersLost": 2,
    "impressions": 29690,
    "impressionClickThroughRate": 4.2
}


def calculate_success_score(metrics: dict) -> float:
    """Calculate success score from CTR and avg view %."""
    ctr = metrics.get("impressionClickThroughRate", 0) / 100  # Convert to decimal
    avg_view = metrics.get("averageViewPercentage", 0) / 100

    # Weighted score: CTR × 0.4 + avg_view × 0.6
    score = (ctr * 10) * 0.4 + avg_view * 0.6  # CTR scaled up since it's typically 2-10%
    return min(round(score, 2), 1.0)


def get_status(score: float) -> str:
    """Get performance status from score."""
    if score > 0.7:
        return "performing"
    elif score > 0.5:
        return "average"
    else:
        return "underperforming"


def fetch_metrics(video_id: str, period: str) -> dict:
    """Fetch metrics for a video."""
    # In real implementation, this would call YouTube Analytics API
    # For now, return mock data
    metrics = MOCK_METRICS.copy()

    success_score = calculate_success_score(metrics)
    status = get_status(success_score)

    return {
        "video_id": video_id,
        "period": period,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "metrics": {
            "views": metrics["views"],
            "ctr": metrics["impressionClickThroughRate"],
            "avg_view_duration_pct": metrics["averageViewPercentage"],
            "avg_view_duration_sec": metrics["averageViewDuration"],
            "likes": metrics["likes"],
            "comments": metrics["comments"],
            "shares": metrics.get("shares", 0),
            "subscribers_gained": metrics.get("subscribersGained", 0)
        },
        "success_score": success_score,
        "status": status,
        "flags": get_flags(metrics)
    }


def get_flags(metrics: dict) -> list:
    """Get warning flags for metrics."""
    flags = []

    if metrics.get("impressionClickThroughRate", 0) < 2:
        flags.append("low_ctr")

    if metrics.get("averageViewPercentage", 0) < 30:
        flags.append("low_retention")

    if metrics.get("views", 0) < 100:
        flags.append("low_views")

    return flags


def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube metrics")
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--period", default="7d", help="Period: 1d, 7d, 28d")
    args = parser.parse_args()

    result = fetch_metrics(args.video_id, args.period)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()