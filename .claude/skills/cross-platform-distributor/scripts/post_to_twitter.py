#!/usr/bin/env python3
"""
Post content to Twitter/X.

Usage:
    python post_to_twitter.py --video-url URL --teaser "Text" --hashtags "#tag1 #tag2"

Requires:
    - TWITTER_API_KEY, TWITTER_API_SECRET environment variables
    - TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET environment variables
    - tweepy package (pip install tweepy)
"""

import argparse
import json
import os
from datetime import datetime

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False


def post_to_twitter(video_url: str, teaser: str, hashtags: str) -> dict:
    """Post to Twitter with video link."""

    if not TWEEPY_AVAILABLE:
        return {
            "mock": True,
            "message": "tweepy not installed - mock response",
            "would_post": f"{teaser}\n\n{hashtags}\n\n{video_url}"
        }

    # Get credentials
    api_key = os.environ.get("TWITTER_API_KEY")
    api_secret = os.environ.get("TWITTER_API_SECRET")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_secret = os.environ.get("TWITTER_ACCESS_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        return {
            "error": "Missing Twitter credentials",
            "required": ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"]
        }

    # Authenticate
    auth = tweepy.OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_token, access_secret)
    api = tweepy.API(auth)

    # Compose tweet
    tweet_text = f"{teaser}\n\n{hashtags}\n\n{video_url}"

    # Ensure under 280 characters
    if len(tweet_text) > 280:
        # Truncate teaser
        max_teaser = 280 - len(f"\n\n{hashtags}\n\n{video_url}") - 3
        teaser = teaser[:max_teaser] + "..."
        tweet_text = f"{teaser}\n\n{hashtags}\n\n{video_url}"

    # Post
    try:
        status = api.update_status(tweet_text)
        return {
            "platform": "twitter",
            "post_id": str(status.id),
            "url": f"https://twitter.com/i/status/{status.id}",
            "posted_at": datetime.utcnow().isoformat() + "Z",
            "text": tweet_text
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Post to Twitter")
    parser.add_argument("--video-url", required=True)
    parser.add_argument("--teaser", required=True)
    parser.add_argument("--hashtags", default="")
    args = parser.parse_args()

    result = post_to_twitter(args.video_url, args.teaser, args.hashtags)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()