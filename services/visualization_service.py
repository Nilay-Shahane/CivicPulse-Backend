from fastapi import APIRouter
from schemas.search import SearchRequest
from services.scraper import get_youtube_comments, get_reddit_comments
from services.translator import translate_batch
from ml.sentiment import analyze_batch
from services.aggregator import compute_stats
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from wordcloud import WordCloud
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from nrclex import NRCLex
from transformers import pipeline

router = APIRouter()

# --------------------------------------------------
# UTILS & LAZY LOADING
# --------------------------------------------------

# Utility function to convert matplotlib plot → base64 image
def plot_to_base64():
    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    plt.clf()  
    plt.close('all') 
    buffer.close() 
    return f"data:image/png;base64,{img_base64}"

# Lazy-load the massive transformer model so FastAPI starts instantly
_zero_shot_classifier = None
def get_classifier():
    global _zero_shot_classifier
    if _zero_shot_classifier is None:
        _zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    return _zero_shot_classifier

# --------------------------------------------------
# VISUALIZATIONS & NLP
# --------------------------------------------------

def generate_pie_chart(stats):
    if sum([stats.get("negative_count", 0), stats.get("neutral_count", 0), stats.get("positive_count", 0)]) == 0:
        return None

    labels = ['Negative', 'Neutral', 'Positive']
    counts = [
        stats.get("negative_count", 0),
        stats.get("neutral_count", 0),
        stats.get("positive_count", 0)
    ]
    colors = ['#a669b6', '#0090ab', '#3b5dd3']

    plt.figure(figsize=(6,6))
    plt.pie(counts, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, textprops={'fontsize': 11})
    plt.title("Sentiment Composition")
    
    return plot_to_base64()

def generate_bar_chart(stats):
    labels = ['Negative', 'Neutral', 'Positive']
    counts = [
        stats.get("negative_count", 0),
        stats.get("neutral_count", 0),
        stats.get("positive_count", 0)
    ]
    colors = ['#a669b6', '#0090ab', '#3b5dd3']

    plt.figure(figsize=(7,5))
    bars = plt.bar(labels, counts, color=colors)

    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, str(count), ha='center', fontsize=10)

    plt.title("Sentiment Distribution")
    plt.xlabel("Sentiment Type")
    plt.ylabel("Number of Comments")

    return plot_to_base64()

def generate_trend_chart(df_final):
    if df_final.empty or 'date' not in df_final.columns:
        return None

    df_final['date'] = pd.to_datetime(df_final['date'], errors='coerce', utc=True)
    df_trend = df_final.dropna(subset=['date', 'sentiment'])

    if df_trend.empty:
        return None

    df_trend['month'] = df_trend['date'].dt.to_period('M')
    monthly_counts = df_trend.groupby(['month','sentiment']).size().unstack(fill_value=0)

    for i in [0,1,2]:
        if i not in monthly_counts.columns:
            monthly_counts[i] = 0

    x_dates = monthly_counts.index.to_timestamp()

    plt.figure(figsize=(10,6))
    plt.stackplot(
        x_dates,
        monthly_counts[0],
        monthly_counts[1],
        monthly_counts[2],
        labels=['Negative','Neutral','Positive'],
        colors=['#6a6fbf', '#b3b3b3', '#7fd1d1'],
        alpha=0.9
    )

    plt.legend()
    plt.title("Sentiment Trend")

    return plot_to_base64()

def generate_word_cloud(text_list):
    if not text_list:
        return None
        
    text = " ".join(str(t) for t in text_list if pd.notna(t))
    if not text.strip():
        return None
        
    wordcloud = WordCloud(
        width=800, height=400, 
        background_color='white', 
        colormap='viridis',
        max_words=100
    ).generate(text)
    
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    
    return plot_to_base64()

def generate_ngram_chart(text_list, n=2, top_k=10):
    if not text_list:
        return None
        
    try:
        vec = CountVectorizer(ngram_range=(n, n), stop_words='english').fit(text_list)
        bag_of_words = vec.transform(text_list)
        sum_words = bag_of_words.sum(axis=0)
        
        words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
        words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)[:top_k]
        
        if not words_freq:
            return None
            
        df = pd.DataFrame(words_freq, columns=['Phrase', 'Frequency'])
        
        plt.figure(figsize=(8, 5))
        plt.barh(df['Phrase'][::-1], df['Frequency'][::-1], color='#0090ab')
        plt.title(f"Top {n}-Word Phrases")
        plt.xlabel("Frequency")
        
        return plot_to_base64()
    except ValueError:
        # Happens if text_list only contains stop words or is effectively empty
        return None

def get_emotion_distribution(text_list):
    # 1. Check if the list itself is empty
    if not text_list:
        return {}
        
    # 2. Join the text and strip away any blank spaces
    text = " ".join(str(t) for t in text_list if pd.notna(t)).strip()
    
    # 3. If the final text is completely empty (no real words), stop here
    if not text:
        return {}
        
    emotion_analyzer = NRCLex(text)
    
    # 4. Bulletproof check: Did NRCLex actually create the attribute?
    if not hasattr(emotion_analyzer, 'raw_emotion_scores'):
        return {}
        
    raw_emotions = emotion_analyzer.raw_emotion_scores
    emotions_only = {k: v for k, v in raw_emotions.items() if k not in ['positive', 'negative']}
    
    return emotions_only
def extract_topics(text_list, n_topics=3, n_words=5):
    if not text_list:
        return []
        
    try:
        vec = CountVectorizer(max_df=0.9, min_df=2, stop_words='english')
        doc_term_matrix = vec.fit_transform(text_list)
        
        lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
        lda.fit(doc_term_matrix)
        
        topics = []
        feature_names = vec.get_feature_names_out()
        
        for topic_idx, topic in enumerate(lda.components_):
            top_words = [feature_names[i] for i in topic.argsort()[:-n_words - 1:-1]]
            topics.append({
                "topic_id": topic_idx + 1,
                "keywords": top_words
            })
            
        return topics
    except ValueError:
        return []

def calculate_actionable_insights(text_list, sample_size=20):
    if not text_list:
        return []
        
    classifier = get_classifier() # Loads model only when this function is actually called
    sorted_texts = sorted(text_list, key=len, reverse=True)[:sample_size]
    actionable_comments = []
    labels = ["constructive suggestion", "complaint", "general opinion"]
    
    for text in sorted_texts:
        if not text.strip():
            continue
            
        result = classifier(text, labels)
        top_label = result['labels'][0]
        
        if top_label == "constructive suggestion" and result['scores'][0] > 0.6:
            actionable_comments.append(text)
            
    return actionable_comments

# --------------------------------------------------
# MAIN PIPELINE & ROUTER
# --------------------------------------------------

def run_sentiment_pipeline(query: str):
    yt_comments = get_youtube_comments(query)
    reddit_comments = get_reddit_comments(query)

    combined = yt_comments + reddit_comments
    
    # Early exit if nothing was scraped to save processing time
    if not combined:
        return {
            "query": query,
            "stats": {},
            "visualizations": {},
            "message": "No data found for this query."
        }

    combined = translate_batch(combined)
    combined = analyze_batch(combined)

    df_final = pd.DataFrame(combined)
    
    if 'sentiment_label' in df_final.columns:
        df_final.rename(columns={"sentiment_label": "sentiment"}, inplace=True)
    
    if 'text' in df_final.columns:
        texts = df_final['text'].dropna().tolist()
    elif 'comment' in df_final.columns:
        texts = df_final['comment'].dropna().tolist()
    elif 'body' in df_final.columns:
        texts = df_final['body'].dropna().tolist()
    else:
        texts = [str(c.get('text') or c.get('comment') or c.get('body') or "") for c in combined]

    stats = compute_stats(combined)

    # Visualizations
    pie_chart = generate_pie_chart(stats)
    bar_chart = generate_bar_chart(stats)
    trend_chart = generate_trend_chart(df_final) # <--- Now active
    word_cloud_img = generate_word_cloud(texts)
    bigram_chart = generate_ngram_chart(texts, n=2)
    
    # NLP Data
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
            "sentiment_trend_chart": trend_chart, # <--- Added to payload
            "word_cloud": word_cloud_img,
            "bigram_chart": bigram_chart
        }
    }

@router.post("/search")
def search_policy(data: SearchRequest):
    return run_sentiment_pipeline(data.query)