
import requests
import json
import os
import re

from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("API_KEY")
CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE", "MrBeast")

MAX_RESULTS = 50

if not API_KEY:
    raise ValueError("API_KEY is missing from .env")


# Convert YouTube ISO 8601 duration to seconds
def duration_to_seconds(duration):
    pattern = r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.fullmatch(pattern, duration)

    if not match:
        return None

    days, hours, minutes, seconds = (
        int(value or 0) for value in match.groups()
    )

    return days * 86400 + hours * 3600 + minutes * 60 + seconds


# Reusable API request handler
def youtube_request(endpoint, params):
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}"

    response = requests.get(
        url,
        params={**params, "key": API_KEY},
        timeout=30
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f"YouTube API error: {response.status_code}")
        print(response.text[:1000])
        raise

    return response.json()


# Step 1: Retrieve uploads playlist
def get_playlist_id():
    data = youtube_request(
        "channels",
        {
            "part": "contentDetails",
            "forHandle": CHANNEL_HANDLE
        }
    )

    if not data.get("items"):
        raise ValueError("Channel not found")

    playlist_id = data["items"][0]["contentDetails"][
        "relatedPlaylists"
    ]["uploads"]

    print(f"Channel Playlist ID: {playlist_id}")
    return playlist_id


# Step 2: Retrieve all video IDs
def get_video_ids(playlist_id):
    video_ids = []
    page_token = None

    while True:
        params = {
            "part": "contentDetails",
            "playlistId": playlist_id,
            "maxResults": MAX_RESULTS
        }

        if page_token:
            params["pageToken"] = page_token

        data = youtube_request("playlistItems", params)

        for item in data.get("items", []):
            video_id = item.get(
                "contentDetails", {}
            ).get("videoId")

            if video_id:
                video_ids.append(video_id)

        page_token = data.get("nextPageToken")

        if not page_token:
            break

    print(f"Found {len(video_ids)} video IDs")
    return video_ids


# Step 3: Extract metadata and calculate metrics
def extract_video_data(video_ids):
    extracted_data = []

    # Use a single snapshot time for this extraction
    collected_at = datetime.now(timezone.utc)

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]

        data = youtube_request(
            "videos",
            {
                "part": "snippet,contentDetails,statistics",
                "id": ",".join(batch)
            }
        )

        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            details = item.get("contentDetails", {})

            views = int(statistics.get("viewCount", 0))
            likes_raw = statistics.get("likeCount")
            comments_raw = statistics.get("commentCount")

            likes = (
                int(likes_raw) if likes_raw is not None else None
            )
            comments = (
                int(comments_raw) if comments_raw is not None else None
            )

            published_at = datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            )

            age_days = max(
                1,
                (collected_at - published_at).total_seconds() / 86400
            )

            duration_seconds = duration_to_seconds(
                details.get("duration", "PT0S")
            )

            engagement_rate = None

            if views > 0 and likes is not None and comments is not None:
                engagement_rate = round(
                    (likes + comments) / views * 100, 2
                )

            video_data = {
                "video_id": item["id"],
                "channel": CHANNEL_HANDLE,
                "title": snippet.get("title"),
                "published_at": snippet["publishedAt"],
                "collected_at": collected_at.isoformat(),
                "duration_seconds": duration_seconds,
                "view_count": views,
                "like_count": likes,
                "comment_count": comments,
                "engagement_rate": engagement_rate,
                "video_age_days": round(age_days, 2),
                "avg_views_per_day": round(views / age_days, 2)
            }

            extracted_data.append(video_data)

    return extracted_data


# Step 4: Save timestamped snapshots
def save_data_to_json(extracted_data):
    data_dir = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d_%H-%M-%S-%f"
    )

    file_path = data_dir / f"YT_data_{timestamp}.json"

    with open(file_path, "w", encoding="utf-8") as outfile:
        json.dump(
            extracted_data,
            outfile,
            indent=4,
            ensure_ascii=False
        )

    print(f"Saved {len(extracted_data)} videos to {file_path}")


# Step 5: Run the pipeline
if __name__ == "__main__":
    playlist_id = get_playlist_id()
    video_ids = get_video_ids(playlist_id)
    video_data = extract_video_data(video_ids)

    save_data_to_json(video_data)

    print("YouTube extraction completed successfully!")
