# News Agent

A lightweight Flask web app that aggregates live news headlines from multiple RSS feeds and exposes an **AI-powered agent chat** interface at `localhost:5000/agent`.

## Features

- **Headlines view** (`/`) — browse live headlines per source
- **Agent Chat** (`/agent`) — converse with the news agent:
  - 🔍 **Search** — ask about any topic: *"climate change"*, *"AI"*, *"Ukraine"*
  - 📋 **Digest** — say *"digest"* for a cross-source top-story overview
  - 🔥 **Trending** — say *"trending"* to see the buzziest keywords right now
  - 📡 **Sources** — say *"sources"* to list all available feeds
- No API key required — powered by public RSS feeds

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Then open [http://localhost:5000/](http://localhost:5000/) for headlines or [http://localhost:5000/agent](http://localhost:5000/agent) for the agent chat.

## Debug mode

```bash
FLASK_DEBUG=1 python app.py
```

## Project structure

```
app.py          — Flask routes (headlines + agent API)
agent.py        — News agent: search, digest, trending, intent detection
templates/
  index.html    — Headlines UI
  agent.html    — Agent chat UI
requirements.txt
```