# Code Smells & Refactoring Guide

This document identifies code smells, anti-patterns, and provides a roadmap for refactoring the Ari Connect bot toward a cleaner, feature-based architecture.

## Critical Issues

### 1. Naming Inconsistencies

**Current Problems:**
- `Intialization` → Should be `Initialization` ([global_chat_initialization.py](ari/core/cogs/global_chat/global_chat_initialization.py:17))
- `data_mananger` → Should be `data_manager` ([ari/core/data_mananger.py](ari/core/data_mananger.py))
- Method naming inconsistent: `getAllLobby()`, `getLobbyConnections()` (camelCase) mixed with `get_user_level()` (snake_case)
- `openworldThanksMessage` → Should be `open_world_thanks_message`

**Impact:** Makes codebase harder to navigate, violates PEP 8 conventions

**Fix Priority:** HIGH - These are easy to fix with find/replace

### 2. Wildcard Imports

**Location:** [global_chat_initialization.py:13](ari/core/cogs/global_chat/global_chat_initialization.py:13)
```python
from ...data_mananger import *
```

**Problems:**
- Pollutes namespace
- Makes dependencies unclear
- Prevents IDE autocomplete
- Can cause name conflicts

**Better Approach:**
```python
from ...data_manager import (
    getLoggingGuildID,
    getChatLogChannelID,
    getGeneralLobby
)
```

### 3. God Object Anti-Pattern

**Location:** [global_chat_initialization.py](ari/core/cogs/global_chat/global_chat_initialization.py)

The `Intialization` class violates Single Responsibility Principle by handling:
- Data initialization
- Logging configuration
- User validation
- Malicious content detection
- Guild/lobby queries
- Report logging
- Message formatting

**Recommended Split:**
```
Initialization → DataLoader (pure data loading)
               → ValidationService (malicious content, user checks)
               → LobbyService (lobby queries)
               → LoggingService (all logging methods)
```

### 4. Missing Abstraction Layer

**Current:** Direct database access throughout codebase
```python
self.db = StaticDatabase
self.collection = db.guilds_collection()
```

**Problem:** Tight coupling to MongoDB, hard to test, no way to switch databases

**Better:** Abstract repository pattern
```python
class ILobbyRepository(ABC):
    @abstractmethod
    async def find_all(self) -> List[Lobby]: pass

    @abstractmethod
    async def find_by_id(self, lobby_id: str) -> Optional[Lobby]: pass
```

### 5. Inconsistent Error Handling

**Location:** [global_chat_repository.py:112-123](ari/core/cogs/global_chat/global_chat_repository.py:112)

```python
try:
    await self.collection.insert_one({...})
    return True
except:  # Bare except clause!
    return False
```

**Problems:**
- Bare `except` catches ALL exceptions (including KeyboardInterrupt)
- Swallows errors silently
- Returns boolean instead of raising/logging

**Better:**
```python
try:
    result = await self.collection.insert_one(data)
    return result.inserted_id
except DuplicateKeyError as e:
    log.warning(f"Moderator already exists: {e}")
    raise ModeratorAlreadyExistsError(data["level"])
except PyMongoError as e:
    log.error(f"Database error creating moderator: {e}")
    raise
```

### 6. Hardcoded Values

**Locations:**
- Guild IDs in code: [_events.py:139](ari/core/_events.py:139) `bot.get_guild(939025934483357766)`
- Channel IDs in code: [_events.py:140](ari/core/_events.py:140) `get_channel(1245210888290439300)`
- Emoji IDs in code: [utils_cog.py:107](ari/core/cogs/utils/utils_cog.py:107)

**Problem:** Not configurable, requires code changes for different environments

**Solution:** Move to configuration or database

### 7. Mixed Concerns

**Example:** [global_chat_initialization.py](ari/core/cogs/global_chat/global_chat_initialization.py)

Business logic (lobby counting) mixed with:
- Data access (direct cache queries)
- Presentation logic (embed creation)
- Infrastructure (logging, Discord API calls)

**Proper Separation:**
```
Presentation Layer (Cogs/Commands) → Formats output, handles user input
Service Layer (Business Logic)     → Core logic, validations
Repository Layer (Data Access)     → Database operations
Domain Layer (Models)               → Pure data structures
```

### 8. Missing Domain Models

**Current:** Dictionary soup everywhere
```python
guild_document = {"server_id": 123, "channels": [...]}
```

**Problems:**
- No type safety
- Easy to make typos ("sever_id" won't error)
- No validation
- Hard to refactor

**Better:** Separate **Entities** (business logic) from **Models** (database)

See [DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md) for full details.

```python
# Domain Entity (business logic)
@dataclass
class Guild:
    guild_id: int
    name: str
    channels: List[Channel]

    def add_channel(self, channel: Channel) -> None:
        """Business rule with validation"""
        if channel in self.channels:
            raise ChannelAlreadyExistsError()
        self.channels.append(channel)

# Data Model (database representation)
class GuildModel:
    def __init__(self, server_id: int, server_name: str, channels: List[dict]):
        self.server_id = server_id  # DB field name
        self.server_name = server_name
        self.channels = channels

    def to_document(self) -> dict:
        return {"server_id": self.server_id, ...}

# Mapper (converts between them)
class GuildMapper:
    @staticmethod
    def to_entity(model: GuildModel) -> Guild:
        return Guild(
            guild_id=model.server_id,  # Map field names
            name=model.server_name,
            channels=[...]
        )
```

### 9. Code Duplication

**Multiple similar loops:**
- `getAllLobby()` loops through guilds/channels
- `getLobbyConnections()` loops through guilds/channels
- `getAllGuildUnderLobby()` loops through guilds/channels
- `get_lobby_count()` loops through guilds/channels

**Solution:** Extract common query logic to service methods

### 10. No Dependency Injection

**Current:**
```python
class Repository:
    def __init__(self):
        self.db = StaticDatabase  # Hardcoded dependency
```

**Problem:** Can't mock for testing, tight coupling

**Better:**
```python
class Repository:
    def __init__(self, database: IDatabase):
        self.db = database  # Injected dependency
```

---

## Feature-Based Architecture Refactoring

### Current Structure Problem

All global chat functionality is crammed into one module:
```
ari/core/cogs/global_chat/
├── global_chat.py              # Manager (56 lines)
├── global_chat_commands.py     # Commands (494 lines)
├── global_chat_settings.py     # Settings (648 lines) ⚠️
├── global_chat_moderation.py   # Moderation (589 lines) ⚠️
├── global_chat_listeners.py    # Listeners (412 lines)
├── global_chat_initialization.py  # God object (263 lines)
├── global_chat_repository.py   # Multiple repos (139 lines)
└── global_chat_cache_manager.py
```

**Problems:**
- Files are getting too large (648 lines in settings!)
- Everything is tightly coupled
- Hard to find specific functionality
- No clear feature boundaries

### Proposed Feature-Based Structure

Reorganize into discrete, self-contained features:

```
ari/
├── core/
│   ├── bot.py
│   ├── config.py
│   └── database/
│       ├── connection.py
│       └── repositories/
│           └── base.py
│
├── shared/
│   ├── models/          # Domain models used across features
│   │   ├── guild.py
│   │   ├── lobby.py
│   │   └── user.py
│   ├── services/        # Shared services
│   │   ├── logging_service.py
│   │   └── validation_service.py
│   └── exceptions/
│       └── custom_exceptions.py
│
└── features/            # Feature-based organization
    │
    ├── lobbies/         # Lobby management feature
    │   ├── models/
    │   │   ├── lobby.py
    │   │   └── lobby_config.py
    │   ├── repositories/
    │   │   ├── lobby_repository.py
    │   │   └── lobby_config_repository.py
    │   ├── services/
    │   │   ├── lobby_service.py      # Business logic
    │   │   └── lobby_query_service.py
    │   ├── commands/
    │   │   ├── lobby_commands.py     # User commands
    │   │   └── lobby_settings_commands.py
    │   └── __init__.py
    │
    ├── messaging/       # Message broadcasting feature
    │   ├── models/
    │   │   └── message_cache.py
    │   ├── services/
    │   │   ├── message_broadcaster.py
    │   │   ├── webhook_manager.py
    │   │   └── cache_manager.py
    │   ├── listeners/
    │   │   ├── message_listener.py
    │   │   ├── edit_listener.py
    │   │   └── delete_listener.py
    │   └── __init__.py
    │
    ├── connections/     # Guild connection management
    │   ├── models/
    │   │   └── guild_connection.py
    │   ├── repositories/
    │   │   └── connection_repository.py
    │   ├── services/
    │   │   └── connection_service.py
    │   ├── commands/
    │   │   └── connection_commands.py  # Join/leave lobby
    │   └── __init__.py
    │
    ├── moderation/      # Moderation feature
    │   ├── models/
    │   │   ├── moderator.py
    │   │   ├── muted_user.py
    │   │   └── malicious_content.py
    │   ├── repositories/
    │   │   ├── moderator_repository.py
    │   │   └── blacklist_repository.py
    │   ├── services/
    │   │   ├── moderation_service.py
    │   │   └── content_filter_service.py
    │   ├── commands/
    │   │   ├── moderator_commands.py
    │   │   └── blacklist_commands.py
    │   └── __init__.py
    │
    ├── reporting/       # User reporting feature
    │   ├── models/
    │   │   └── report.py
    │   ├── services/
    │   │   └── report_service.py
    │   ├── commands/
    │   │   └── report_commands.py
    │   └── __init__.py
    │
    └── logging/         # Activity logging feature
        ├── services/
        │   ├── chat_logger.py
        │   ├── system_logger.py
        │   └── mod_logger.py
        └── __init__.py
```

### Benefits of Feature-Based Architecture

1. **Clear Boundaries**: Each feature is self-contained
2. **Easier Navigation**: "Where's the mute command?" → `features/moderation/commands/`
3. **Parallel Development**: Different devs can work on different features
4. **Testability**: Test features in isolation
5. **Reusability**: Shared code in `shared/`, feature-specific in features
6. **Scalability**: Add new features without touching existing ones

---

## Refactoring Roadmap

### Phase 1: Foundation (Week 1-2)

1. **Fix naming issues**
   - Rename `data_mananger` → `data_manager`
   - Rename `Intialization` → `Initialization`
   - Standardize all methods to snake_case

2. **Add domain models**
   - Create `models/lobby.py`, `models/guild.py`, `models/channel.py`
   - Replace dictionaries with dataclasses/Pydantic
   - Add validation logic to models

3. **Remove wildcard imports**
   - Make all imports explicit
   - Fix circular dependencies

4. **Add proper error handling**
   - Replace bare `except` with specific exceptions
   - Create custom exception classes
   - Add logging to all error cases

### Phase 2: Extract Services (Week 3-4)

1. **Create service layer**
   ```python
   LobbyService      # Lobby business logic
   ValidationService # Content/user validation
   LoggingService    # All logging operations
   CacheService      # Message caching
   ```

2. **Move business logic from `Initialization`**
   - Extract query methods to `LobbyService`
   - Extract validation to `ValidationService`
   - Extract logging to `LoggingService`

3. **Dependency injection**
   - Use constructor injection for dependencies
   - Create service factory/container

### Phase 3: Repository Pattern (Week 5)

1. **Abstract repository interfaces**
   ```python
   ILobbyRepository
   IGuildRepository
   IModeratorRepository
   ```

2. **Implement concrete repositories**
   - Move database logic to repositories
   - Return domain models, not dictionaries
   - Add proper error handling

3. **Remove direct DB access from services**

### Phase 4: Feature Reorganization (Week 6-8)

1. **Create feature structure** (see tree above)

2. **Migrate incrementally**
   - Start with smallest feature (reporting)
   - Test thoroughly
   - Move to next feature

3. **Update imports and dependencies**

4. **Remove old structure**

### Phase 5: Configuration & Testing (Week 9-10)

1. **Centralize configuration**
   - Move hardcoded values to config
   - Support multiple environments
   - Add config validation

2. **Add unit tests**
   - Test services in isolation
   - Mock repositories
   - Aim for 70%+ coverage

3. **Add integration tests**
   - Test feature workflows end-to-end

---

## Quick Wins (Do These First)

### 1. Fix Naming (30 minutes)
```bash
# Rename files and update imports
git mv ari/core/data_mananger.py ari/core/data_manager.py
# Find and replace "data_mananger" → "data_manager"
# Find and replace "Intialization" → "Initialization"
```

### 2. Remove Wildcard Imports (1 hour)
Make imports explicit in [global_chat_initialization.py](ari/core/cogs/global_chat/global_chat_initialization.py:13)

### 3. Add Type Hints (2 hours)
```python
def get_lobby_count(self, lobby_name: str) -> int:
async def find_all(self) -> List[Dict[str, Any]]:
```

### 4. Extract Constants (1 hour)
```python
# ari/core/constants.py
LOGGING_GUILD_ID = 939025934483357766
LOGGING_CHANNEL_ID = 1245210888290439300
```

### 5. Fix Bare Except Clauses (1 hour)
Replace all `except:` with `except Exception as e:`

---

## Architecture Principles to Follow

### 1. Dependency Inversion Principle
High-level modules should not depend on low-level modules. Both should depend on abstractions.

**Bad:**
```python
class LobbyService:
    def __init__(self):
        self.repo = MongoLobbyRepository()  # Depends on concrete implementation
```

**Good:**
```python
class LobbyService:
    def __init__(self, repo: ILobbyRepository):
        self.repo = repo  # Depends on abstraction
```

### 2. Single Responsibility Principle
Each class should have one reason to change.

**Current:** `Initialization` changes when:
- Data loading changes
- Validation logic changes
- Logging format changes
- Query logic changes

**Target:** Separate classes for each responsibility

### 3. Open/Closed Principle
Open for extension, closed for modification.

**Example:** Plugin-based cog loading
```python
class CogRegistry:
    def register(self, cog_class: Type[commands.Cog]):
        # New features can be added without modifying core
```

### 4. Interface Segregation
Don't force clients to depend on interfaces they don't use.

**Bad:**
```python
class IRepository:
    async def find_all(self): pass
    async def find_one(self): pass
    async def create(self): pass
    async def update(self): pass  # Not all repos need update
    async def delete(self): pass  # Not all repos need delete
```

**Good:**
```python
class IReadRepository:
    async def find_all(self): pass
    async def find_one(self): pass

class IWriteRepository:
    async def create(self): pass
    async def update(self): pass
    async def delete(self): pass
```

### 5. Don't Repeat Yourself (DRY)
Extract common patterns.

**Current:** 4 different methods loop through guilds/channels
**Target:** One parameterized method

---

## Testing Strategy

### Unit Tests
```python
# tests/features/lobbies/services/test_lobby_service.py
@pytest.mark.asyncio
async def test_create_lobby_validates_name():
    mock_repo = Mock(spec=ILobbyRepository)
    service = LobbyService(mock_repo)

    with pytest.raises(InvalidLobbyNameError):
        await service.create_lobby("")
```

### Integration Tests
```python
# tests/integration/test_lobby_workflow.py
@pytest.mark.asyncio
async def test_join_lobby_workflow(bot, guild, channel):
    # Test full join lobby flow
    await bot.process_command("/join general")
    assert channel.id in bot.lobbies["general"].channels
```

### Test Coverage Goals
- Services: 90%
- Repositories: 80%
- Commands: 70%
- Overall: 75%

---

## Migration Strategy

### Strangler Fig Pattern

Don't rewrite everything at once. Gradually replace old code:

1. **New code uses new architecture**
2. **Old code continues to work**
3. **Gradually migrate old code**
4. **Remove old code when fully migrated**

**Example:**
```python
# Old way (keep working)
from ari.core.cogs.global_chat.global_chat_initialization import Intialization

# New way (use for new features)
from ari.features.lobbies.services import LobbyService

# Adapter during transition
class InitializationAdapter:
    def __init__(self, lobby_service: LobbyService):
        self.lobby_service = lobby_service

    def get_lobby_count(self, name: str) -> int:
        # Delegate to new service
        return self.lobby_service.count_connections(name)
```

---

## Summary

**Immediate Actions:**
1. Fix naming (data_mananger, Intialization)
2. Remove wildcard imports
3. Fix bare except clauses
4. Add type hints

**Short-term (1-2 months):**
1. Extract service layer
2. Implement repository pattern
3. Add domain models
4. Write tests

**Long-term (3-6 months):**
1. Migrate to feature-based architecture
2. Add comprehensive testing
3. Implement CI/CD
4. Add monitoring/metrics

**Success Metrics:**
- Test coverage > 75%
- Cyclomatic complexity < 10 per method
- Files < 300 lines
- No wildcard imports
- All public APIs have type hints
