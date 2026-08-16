# Ari Connect - Your Ultimate Global Chat Hub

🚀 Say goodbye to server-hopping and hello to seamless connectivity! Our specially designed bot brings gaming communities together like never before.

[Join and show some support](https://discord.gg/HnjyK33cJp)

[Inv the bot](https://discord.com/oauth2/authorize?client_id=895242125208342548)
### Features Include:
- Global Chat Compatibility: Connect with gamers worldwide in one place.
- Anywhere, Anytime Access: Stay connected on-the-go.
- Private Lobbies: Secure spaces for inter-server conversations

## Setup

### Prerequisites
- Python 3.12.x
- pip
- A MongoDB instance (local or hosted) and its connection URL
- A Discord bot application/token ([Discord Developer Portal](https://discord.com/developers/applications))

### Install dependencies

```
pip install -r requirements.txt
```

### Configure

Copy `.env.sample` to a new file named `.env` **inside the `ari/` folder**
(next to `__main__.py` — not at the repo root):

```
cp .env.sample ari/.env
```

Then fill in the values. `DISCORD_API_TOKEN` and `MONGO_DB_URL` are
required; everything else has a sensible default or is optional (see the
comments in `.env.sample`, or `ari/core/config.py`'s `AppConfig` for the
authoritative list of what the bot actually reads).

### Run the bot

```
cd ari
python __main__.py
```

Note: this is **not** `python -m ari` from the repo root — the codebase's
imports assume `ari/` itself is on `sys.path`, which only happens when you
run the entry point as a plain script from inside `ari/`. See `CLAUDE.md`
for why.

## Testing

```
pytest
```

Run from the **repo root** (not `ari/`) — `pytest.ini` points pytest at
the `ari/` package. No `.env`, database, or live Discord connection is
needed to run the test suite: it covers the business-logic layer
(`services/`, `state.py`, pure presenters) using hand-written fakes, not
a live bot. Discord-facing behavior (cogs, event listeners, UI) is
verified manually against a real bot token instead — there's no
Discord-mocking test harness in this repo.

## Architecture

See [`CLAUDE.md`](CLAUDE.md) at the repo root for the full architecture
guide: the `core`/`features`/`integrations` package layout, the internal
shape of a feature, and how to add a new one.

### License
