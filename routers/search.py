from fastapi import APIRouter
from schemas.search import SearchRequest
from services.scraper import get_youtube_comments, get_reddit_comments
from services.translator import translate_batch
from ml.sentiment import analyze_batch
from services.aggregator import compute_stats
import pandas as pd

# Import your new functions
from services.visualization_service import (
    generate_pie_chart, generate_bar_chart, generate_trend_chart,
    generate_word_cloud, generate_ngram_chart, 
    get_emotion_distribution, extract_topics, calculate_actionable_insights
)

router = APIRouter()

def run_sentiment_pipeline(query: str):
    yt_comments = get_youtube_comments(query)
    reddit_comments = get_reddit_comments(query)

    combined = yt_comments + reddit_comments
    combined = translate_batch(combined)
    combined = analyze_batch(combined)

    df_final = pd.DataFrame(combined)
    df_final.rename(columns={"sentiment_label": "sentiment"}, inplace=True)
    
    # Extract just the text column as a list for the NLP algorithms
    # Safely try to get 'text', falling back to 'comment' or 'body'
    if 'text' in df_final.columns:
        texts = df_final['text'].tolist()
    elif 'comment' in df_final.columns:
        texts = df_final['comment'].tolist()
    elif 'body' in df_final.columns:
        texts = df_final['body'].tolist()
    else:
        # If all else fails, extract safely from the dictionaries directly
        texts = [str(c.get('text') or c.get('comment') or c.get('body') or "") for c in combined]

    stats = compute_stats(combined)

    # Base Visualizations
    pie_chart = generate_pie_chart(stats)
    bar_chart = generate_bar_chart(stats)
    
    # Advanced NLP Visualizations
    word_cloud_img = generate_word_cloud(texts)
    bigram_chart = generate_ngram_chart(texts, n=2)
    
    # Advanced Data Metrics (Text/JSON based, not images)
    emotions = get_emotion_distribution(texts)
    topics = extract_topics(texts, n_topics=3)
    actionable_items = calculate_actionable_insights(texts)

    return {
        "query": query,
        "stats": {
            **stats,
            "emotions": emotions,
            "topics": topics,
            "actionable_insights": actionable_items
        },
        "visualizations": {
            "sentiment_pie_chart": pie_chart,
            "sentiment_bar_chart": bar_chart,
            "word_cloud": word_cloud_img,
            "bigram_chart": bigram_chart
        }
    }

@router.post("/search")
def search_policy(data: SearchRequest):
    return run_sentiment_pipeline(data.query)