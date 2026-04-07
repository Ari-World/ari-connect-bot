# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ari Connect is a Discord bot that enables global chat functionality across multiple Discord servers through a lobby-based system. Users can connect their server channels to shared lobbies, allowing cross-server communication via webhooks.

## Development Commands

### Installation
```bash
pip install -r requirements.txt
```

### Running the Bot
```bash
python -m ari
```

The bot entry point is `ari/__main__.py`, which initializes the event loop and starts the bot.

## Configuration

The bot requires a `.env` file in the root directory with the following variables:

```
DISCORD_API_TOKEN=<your_bot_token>
DISCORD_COMMAND_PREFIX=<prefix_like_!>
MONGO_DB_URL=<mongodb_connection_string>

# Logging Configuration
LOG_GUILD_ID=<guild_id_for_logs>
LOG_CHAT_ID=<channel_id>
LOG_SYSTEM_ID=<channel_id>
LOG_MOD_ID=<channel_id>
LOG_PLAYER_REPORT_ID=<channel_id>

CACHE_THRESHOLD=<number>
GENERAL_LOBBY_NAME=<default_lobby_name>
FENDERBOT_USER_ID=<optional_bot_user_id>
```

Configuration is loaded via `ari/core/data_mananger.py` using `load_basic_configuration()`.

## Architecture

### Core Bot Structure

- **Bot Class**: `ari/core/bot.py` - Main bot class `Ari` extends `commands.Bot`
  - Overrides `process_commands()` to allow specific bot users (FenderBot integration)
  - Manages graceful shutdown with exit codes defined in `ari/core/_cli.py`
  - Uses `StaticDatabase` singleton for MongoDB connection

- **Entry Point**: `ari/__main__.py` - Application lifecycle management
  - Creates event loop and handles shutdown signals
  - Exception handlers for bot crashes and interrupts
  - Exit codes: SHUTDOWN (0), CRITICAL (1), RESTART (26), CONFIGURATION_ERROR (78)

### Database Layer

- **Driver**: `ari/core/_driver/_mongo.py` - MongoDB connection using Motor (async)
  - `StaticDatabase` is a singleton class with classmethod accessors
  - Collections: `open_world` (guilds), `muted_world_users`, `lobbies`, `malicious_urls`, `malicious_words`, `moderators`

- **Repository Pattern**: `ari/core/cogs/global_chat/global_chat_repository.py`
  - Repositories handle CRUD operations for each collection
  - `Repository` class coordinates all repositories and maintains in-memory cache sync
  - Changes to database are immediately reflected in `self.init.guild_data`, `self.init.moderator`, etc.

### Global Chat Feature

The main feature is organized as a cog in `ari/core/cogs/global_chat/`:

- **global_chat.py** - Main cog that orchestrates sub-modules:
  - Initializes on `cog_load()` by loading data from DB into memory
  - Registers sub-cogs: `Global` (commands), `Moderation`, `EventListeners`
  - Creates message cache for lobbies via `CacheManager`

- **global_chat_initialization.py** - Loads all data from DB into memory structures:
  - `guild_data` - List of guilds with their channels and webhook URLs
  - `server_lobbies` - Dictionary mapping lobby names to list of channels
  - `muted_users`, `malicious_urls`, `malicious_words`, `moderator` - Security/moderation data

- **global_chat_listeners.py** - Discord event handlers:
  - `on_message_delete`, `on_message_edit`, `on_message`
  - Relays messages across all channels in the same lobby using webhooks
  - Message types: REPLY, DELETE, UPDATE, SEND

- **global_chat_commands.py** - User-facing commands:
  - `connect` - Links a channel to a lobby (creates webhook)
  - Lobby selection with auto-connect feature

- **global_chat_moderation.py** - Moderation features and commands

- **global_chat_cache_manager.py** - Manages message caching per lobby for edit/delete operations

### Command Structure

- **Core Commands**: `ari/core/core_commands.py` - `Core` cog with basic bot commands
- **Dev Commands**: `ari/core/dev_commands.py` - `Dev` cog for developer tools
- **Help System**: Custom `MyHelpCommand` class for help command
- **Hybrid Commands**: Bot supports both prefix commands and slash commands via `@commands.hybrid_command`

### Key Design Patterns

1. **Dual Cache System**:
   - Database (MongoDB) is source of truth
   - In-memory cache (`guild_data`, `server_lobbies`, etc.) for fast access
   - Repository methods update both DB and cache atomically

2. **Lobby System**:
   - `server_lobbies` is a dict: `{lobby_name: [list of channel_ids]}`
   - Each channel has a webhook URL for sending messages
   - Messages sent to one channel are relayed to all channels in the same lobby

3. **Webhook-Based Messaging**:
   - Each connected channel has a webhook for impersonating message authors
   - Webhooks stored in guild documents: `{channel_id, lobby_name, webhook, activity}`

4. **Bot Processing Override**:
   - Normally bots ignore other bots' messages
   - `BotBase.process_commands()` allows FenderBot (configurable) to use commands

## Important Notes

- The bot expects Python 3.12.x (tested with 3.12.5)
- MongoDB connection is required for bot to function
- Webhook management is critical - deleting channels also deletes associated webhooks
- The cog manager (`ari/core/cog_manager.py`) is mostly commented out - cogs are manually added in `bot.py:_pre_connect()`
- Logging uses Python's logging module with custom initialization in `ari/custom_logging.py`
