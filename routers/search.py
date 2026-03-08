from fastapi import APIRouter
from schemas.search import SearchRequest
from services.scraper import get_youtube_comments, get_reddit_comments
from services.translator import translate_batch
from ml.sentiment import analyze_batch
from services.aggregator import compute_stats
from services.visualization_service import (generate_pie_chart,generate_bar_chart,generate_trend_chart)
import pandas as pd

router = APIRouter()

def run_sentiment_pipeline(query: str):
    yt_comments = get_youtube_comments(query)
    reddit_comments = get_reddit_comments(query)

    combined = yt_comments + reddit_comments
    combined = translate_batch(combined)
    combined = analyze_batch(combined)

    df_final = pd.DataFrame(combined)
    df_final.rename(columns={"sentiment_label": "sentiment"}, inplace=True)

    stats = compute_stats(combined)

    pie_chart = generate_pie_chart(stats)
    bar_chart = generate_bar_chart(stats)

    return {
        "query": query,
        "stats": stats,
        "visualizations": {
            "sentiment_pie_chart": pie_chart,
            "sentiment_bar_chart": bar_chart,
        }
    }


@router.post("/search")
def search_policy(data: SearchRequest):
    return run_sentiment_pipeline(data.query)