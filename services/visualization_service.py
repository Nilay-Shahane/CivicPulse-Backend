import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import base64
from io import BytesIO


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


# --------------------------------------------------
# PIE CHART
# --------------------------------------------------

def generate_pie_chart(stats):

    labels = ['Negative', 'Neutral', 'Positive']
    counts = [
        stats["negative_count"],
        stats["neutral_count"],
        stats["positive_count"]
    ]

    colors = ['#a669b6', '#0090ab', '#3b5dd3']

    plt.figure(figsize=(6,6))

    plt.pie(
        counts,
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        textprops={'fontsize': 11}
    )

    plt.title("Sentiment Composition")

    return plot_to_base64()


# --------------------------------------------------
# BAR CHART
# --------------------------------------------------

def generate_bar_chart(stats):

    labels = ['Negative', 'Neutral', 'Positive']
    counts = [
        stats["negative_count"],
        stats["neutral_count"],
        stats["positive_count"]
    ]

    colors = ['#a669b6', '#0090ab', '#3b5dd3']

    plt.figure(figsize=(7,5))

    bars = plt.bar(labels, counts, color=colors)

    for bar, count in zip(bars, counts):
        plt.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.5,
            str(count),
            ha='center',
            fontsize=10
        )

    plt.title("Sentiment Distribution")
    plt.xlabel("Sentiment Type")
    plt.ylabel("Number of Comments")

    return plot_to_base64()


# --------------------------------------------------
# TREND CHART
# --------------------------------------------------

def generate_trend_chart(df_final):

    if df_final.empty:
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