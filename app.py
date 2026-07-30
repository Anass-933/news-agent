import os

import feedparser
from flask import Flask, jsonify, render_template, request

import agent as news_agent

app = Flask(__name__)

FEEDS = {
    "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
    "Reuters": "https://feeds.reuters.com/reuters/topNews",
    "CNN": "http://rss.cnn.com/rss/edition.rss",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "Tech - The Verge": "https://www.theverge.com/rss/index.xml",
    "Tech - Ars Technica": "http://feeds.arstechnica.com/arstechnica/index",
    "Science - NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
}

DEFAULT_FEED = "BBC News"


def fetch_articles(feed_url: str, limit: int = 20) -> list[dict]:
    parsed = feedparser.parse(feed_url)
    articles = []
    for entry in parsed.entries[:limit]:
        articles.append(
            {
                "title": entry.get("title", "No title"),
                "link": entry.get("link", "#"),
                "summary": entry.get("summary", entry.get("description", "")),
                "published": entry.get("published", entry.get("updated", "")),
                "source": parsed.feed.get("title", ""),
            }
        )
    return articles


@app.route("/")
def index():
    source = request.args.get("source", DEFAULT_FEED)
    if source not in FEEDS:
        source = DEFAULT_FEED
    articles = fetch_articles(FEEDS[source])
    return render_template(
        "index.html",
        articles=articles,
        feeds=list(FEEDS.keys()),
        current_source=source,
    )


@app.route("/agent")
def agent_page():
    return render_template("agent.html", feeds=list(FEEDS.keys()))


@app.route("/api/agent", methods=["POST"])
def agent_api():
    data = request.get_json(force=True, silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"message": "Please enter a query.", "articles": [], "intent": "error"})
    result = news_agent.run(query)
    return jsonify(result)


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=5000)