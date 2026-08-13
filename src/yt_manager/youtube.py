from googleapiclient.discovery import build


class YouTubeResearchClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY is required")
        self.youtube = build("youtube", "v3", developerKey=api_key, cache_discovery=False)

    def recent_videos(self, channel_id: str, max_results: int = 15) -> list[dict]:
        channel = self.youtube.channels().list(
            part="snippet,contentDetails",
            id=channel_id,
        ).execute()
        if not channel.get("items"):
            raise ValueError(f"YouTube channel not found: {channel_id}")

        item = channel["items"][0]
        channel_title = item["snippet"]["title"]
        uploads_id = item["contentDetails"]["relatedPlaylists"]["uploads"]

        playlist = self.youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_id,
            maxResults=min(max_results, 50),
        ).execute()

        raw = playlist.get("items", [])
        video_ids = [x["contentDetails"]["videoId"] for x in raw]
        if not video_ids:
            return []

        stats = self.youtube.videos().list(
            part="statistics,snippet",
            id=",".join(video_ids),
        ).execute()
        stats_by_id = {x["id"]: x for x in stats.get("items", [])}

        videos = []
        for playlist_item in raw:
            video_id = playlist_item["contentDetails"]["videoId"]
            video = stats_by_id.get(video_id)
            if not video:
                continue
            videos.append({
                "video_id": video_id,
                "channel_id": channel_id,
                "channel_title": channel_title,
                "title": video["snippet"]["title"],
                "published_at": video["snippet"]["publishedAt"],
                "views": int(video.get("statistics", {}).get("viewCount", 0)),
                "url": f"https://www.youtube.com/watch?v={video_id}",
            })
        return videos
