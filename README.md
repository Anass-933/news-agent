# News Agent

A lightweight Flask web app that aggregates live news headlines from multiple RSS feeds and displays them at `localhost:5000/`.

## Features

- Fetches real-time headlines from BBC News, Reuters, CNN, Al Jazeera, The Verge, Ars Technica, and NASA
- Clean, responsive UI with source-switching navigation
- No API key required — powered by public RSS feeds

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Then open [http://localhost:5000/](http://localhost:5000/) in your browser.

## Usage

Use the navigation bar at the top to switch between news sources. Each card links to the full article.