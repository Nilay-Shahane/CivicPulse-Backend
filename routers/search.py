from fastapi import APIRouter
from schemas.search import SearchRequest
from services.scraper import get_youtube_comments, get_reddit_comments
from services.translator import translate_batch
from ml.sentiment import analyze_batch
from services.aggregator import compute_stats

router = APIRouter()

@router.post("/search")
def search_policy(data: SearchRequest):

    yt_comments = get_youtube_comments(data.query)
    reddit_comments = get_reddit_comments(data.query)

    combined = yt_comments + reddit_comments

    combined = translate_batch(combined)
    combined = analyze_batch(combined)

    stats = compute_stats(combined)

    return {
        "query": data.query,
        "stats": stats
    }