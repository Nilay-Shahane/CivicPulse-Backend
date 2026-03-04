from googleapiclient.discovery import build
import praw
from datetime import datetime
from core.config import *

def get_youtube_service():
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)

def get_video_ids(query):
    youtube = get_youtube_service()
    response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        order="relevance",
        maxResults=MAX_VIDEOS_TO_CHECK
    ).execute()

    return [item["id"]["videoId"] for item in response.get("items", [])]

def get_youtube_comments(query):
    youtube = get_youtube_service()
    video_ids = get_video_ids(query)

    comments = []

    for video_id in video_ids:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100
        ).execute()

        for item in response.get("items", []):
            c = item["snippet"]["topLevelComment"]["snippet"]

            comments.append({
                "source": "YouTube",
                "author": c["authorDisplayName"],
                "comment": c["textDisplay"],
                "date": c["publishedAt"]
            })

            if len(comments) >= MAX_YT_COMMENTS:
                return comments

    return comments


def get_reddit_comments(query):
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD,
        user_agent=REDDIT_USER_AGENT
    )

    subreddit = reddit.subreddit("india")
    search_results = subreddit.search(query, limit=MAX_REDDIT_POSTS)

    comments = []

    for submission in search_results:
        submission.comments.replace_more(limit=0)

        for comment in submission.comments.list():
            if comment.body.strip() and comment.body not in ["[deleted]", "[removed]"]:

                comments.append({
                    "source": "Reddit",
                    "author": comment.author.name if comment.author else "deleted",
                    "comment": comment.body,
                    "date": datetime.fromtimestamp(comment.created_utc)
                })

                if len(comments) >= TARGET_REDDIT_COMMENTS:
                    return comments

    return comments