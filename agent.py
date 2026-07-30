"""News Agent — query engine that searches and summarises RSS articles."""

from __future__ import annotations

import re
import string
from collections import Counter
from html import unescape

import feedparser

# ---------------------------------------------------------------------------
# Feed registry (mirrors app.py so each module stays self-contained)
# ---------------------------------------------------------------------------
FEEDS = {
    "BBC News": "http://feeds.bbci.co.uk/news/rss.xml",
    "Reuters": "https://feeds.reuters.com/reuters/topNews",
    "CNN": "http://rss.cnn.com/rss/edition.rss",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "Tech - The Verge": "https://www.theverge.com/rss/index.xml",
    "Tech - Ars Technica": "http://feeds.arstechnica.com/arstechnica/index",
    "Science - NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
}

# Words that carry no topical meaning
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "has", "have", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "not", "no", "it", "its", "as", "he",
    "she", "they", "we", "you", "i", "this", "that", "these", "those",
    "after", "before", "into", "over", "under", "about", "up", "out", "more",
    "said", "says", "new", "his", "her", "their", "our", "your", "my",
    "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "than", "then", "so", "if", "all", "also", "just", "who", "what",
    "when", "where", "which", "how", "s", "re", "t", "ve", "ll", "d",
}

MAX_PER_FEED = 20


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return unescape(text).strip()


def _tokenize(text: str) -> list[str]:
    text = _strip_html(text).lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return [w for w in text.split() if w not in _STOPWORDS and len(w) > 2]


def _score(article: dict, keywords: list[str]) -> int:
    haystack = (
        (article.get("title") or "")
        + " "
        + (article.get("summary") or "")
    ).lower()
    return sum(haystack.count(kw) for kw in keywords)


# ---------------------------------------------------------------------------
# Core data fetch
# ---------------------------------------------------------------------------

def fetch_all_articles(limit_per_feed: int = MAX_PER_FEED) -> list[dict]:
    articles: list[dict] = []
    for source_name, url in FEEDS.items():
        parsed = feedparser.parse(url)
        for entry in parsed.entries[:limit_per_feed]:
            articles.append(
                {
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", "#"),
                    "summary": _strip_html(
                        entry.get("summary", entry.get("description", ""))
                    ),
                    "published": entry.get("published", entry.get("updated", "")),
                    "source": source_name,
                }
            )
    return articles


# ---------------------------------------------------------------------------
# Agent capabilities
# ---------------------------------------------------------------------------

def search(query: str, articles: list[dict] | None = None, top_n: int = 8) -> dict:
    """Return articles most relevant to *query*."""
    if articles is None:
        articles = fetch_all_articles()

    keywords = _tokenize(query)
    if not keywords:
        return {"intent": "search", "query": query, "articles": [], "message": "I couldn't find any keywords in your query."}

    scored = [(a, _score(a, keywords)) for a in articles]
    scored = [(a, s) for a, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)
    results = [a for a, _ in scored[:top_n]]

    if results:
        msg = f"Found {len(results)} article(s) matching **{query}**:"
    else:
        msg = f"No articles found for **{query}**. Try different keywords."

    return {"intent": "search", "query": query, "articles": results, "message": msg}


def digest(articles: list[dict] | None = None, top_n: int = 10) -> dict:
    """Return top headlines across all sources (one per source)."""
    if articles is None:
        articles = fetch_all_articles()

    seen_sources: set[str] = set()
    top: list[dict] = []
    for a in articles:
        if a["source"] not in seen_sources:
            top.append(a)
            seen_sources.add(a["source"])
        if len(top) >= top_n:
            break

    return {
        "intent": "digest",
        "articles": top,
        "message": f"Here's your news digest — top story from each of the {len(top)} sources:",
    }


def trending(articles: list[dict] | None = None, top_n: int = 10) -> dict:
    """Return the most frequently mentioned keywords across all articles."""
    if articles is None:
        articles = fetch_all_articles()

    counter: Counter = Counter()
    for a in articles:
        counter.update(_tokenize(a["title"]))
        counter.update(_tokenize(a.get("summary", "")))

    topics = [word for word, _ in counter.most_common(top_n * 3) if len(word) > 3][:top_n]

    return {
        "intent": "trending",
        "topics": topics,
        "articles": [],
        "message": "🔥 Trending topics right now: " + ", ".join(f"**{t}**" for t in topics),
    }


def sources(articles: list[dict] | None = None) -> dict:
    """List all available news sources."""
    names = list(FEEDS.keys())
    return {
        "intent": "sources",
        "topics": names,
        "articles": [],
        "message": "Available news sources: " + ", ".join(f"**{n}**" for n in names),
    }


# ---------------------------------------------------------------------------
# Intent dispatcher
# ---------------------------------------------------------------------------

_DIGEST_TRIGGERS = {"digest", "summary", "summarize", "summarise", "overview", "top stories", "top news", "headlines"}
_TRENDING_TRIGGERS = {"trend", "trending", "popular", "hot", "buzz", "viral"}
_SOURCE_TRIGGERS = {"source", "sources", "feeds", "list"}
_HELP_TRIGGERS = {"help", "what can you do", "commands", "?"}


def run(query: str, articles: list[dict] | None = None) -> dict:
    """Main agent entry-point — detect intent and dispatch."""
    q = query.strip().lower()

    if any(t in q for t in _HELP_TRIGGERS):
        return {
            "intent": "help",
            "articles": [],
            "message": (
                "I can help you with:\n"
                "- **Search**: ask about any topic, e.g. *climate*, *AI*, *Ukraine*\n"
                "- **Digest**: say *digest* or *top stories* for a cross-source overview\n"
                "- **Trending**: say *trending* or *what's hot* for the buzziest keywords\n"
                "- **Sources**: say *sources* to list all available feeds"
            ),
        }

    if any(t in q for t in _SOURCE_TRIGGERS):
        return sources(articles)

    if any(t in q for t in _TRENDING_TRIGGERS):
        return trending(articles)

    if any(t in q for t in _DIGEST_TRIGGERS):
        return digest(articles, top_n=8)

    # Default: keyword search
    return search(query, articles)
