# Architecture Migration Example

This document shows a concrete example of how to migrate from the current architecture to the proposed feature-based architecture.

## Example: Lobby Feature Migration

### Current Architecture (❌ Problems)

**File:** `ari/core/cogs/global_chat/global_chat_commands.py` (494 lines)

Everything mixed together:
```python
class Global(commands.Cog):
    def __init__(self, bot, init, repos):
        self.bot = bot
        self.init = init  # God object with everything
        self.repos = repos  # Direct database access

    @commands.hybrid_command()
    async def join(self, ctx, lobby_name: str):
        # ❌ Business logic mixed with presentation
        # ❌ Direct database queries
        # ❌ No validation separation
        # ❌ Error handling mixed with business logic

        # Validation (should be in service)
        if not lobby_name:
            return await ctx.send("Invalid lobby name")

        # Database query (should be in repository)
        lobby = None
        for l in self.init.lobby_data:
            if l['lobbyname'] == lobby_name:
                lobby = l
                break

        if not lobby:
            return await ctx.send("Lobby not found")

        # Business logic (should be in service)
        count = 0
        for guild in self.init.guild_data:
            for channel in guild['channels']:
                if channel['lobby_name'] == lobby_name:
                    count += 1

        if count >= lobby['limit']:
            return await ctx.send("Lobby is full")

        # Database operation (should be in repository)
        # ... complex database update logic here ...

        # Presentation (OK here)
        await ctx.send(f"Joined {lobby_name}!")
```

**Problems:**
1. 494 lines in one file - too large
2. Presentation + Business logic + Data access all mixed
3. Using dictionaries instead of models
4. No testability - can't test without database
5. Duplicate code - lobby counting logic appears in multiple commands

---

### Proposed Architecture (✅ Clean)

Split into feature layers with clear responsibilities:

#### 1. Domain Entity (Pure Business Logic)
**File:** `ari/domain/entities/lobby.py`

**Note:** We separate **Entity** (business logic) from **Model** (database). See [DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md) for details.

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Lobby:
    """
    Domain Entity - Pure business logic, NO database concerns.

    Uses domain language (max_connections, not "limit")
    """
    lobby_id: str
    name: str
    description: str
    max_connections: int  # Domain term, not database field name
    is_public: bool
    created_at: datetime
    created_by: str

    def is_full(self, current_connections: int) -> bool:
        """Business rule: check if lobby is at capacity"""
        return current_connections >= self.max_connections

    def can_accept_connection(self, current_connections: int) -> bool:
        """Business rule: can accept new connection?"""
        return current_connections < self.max_connections

    def validate(self) -> None:
        """Business rule: validate lobby properties"""
        if not self.name or len(self.name) < 3:
            raise InvalidLobbyError("Name must be at least 3 characters")
        if len(self.name) > 50:
            raise InvalidLobbyError("Name too long")
        if not self.name.replace("-", "").replace("_", "").isalnum():
            raise InvalidLobbyError("Name must be alphanumeric")
        if self.max_connections < 1 or self.max_connections > 1000:
            raise InvalidLobbyError("Invalid max connections")

class InvalidLobbyError(Exception):
    pass

class LobbyFullError(Exception):
    pass

class LobbyNotFoundError(Exception):
    pass
```

#### 2. Data Model (Database Representation)
**File:** `ari/infrastructure/database/models/lobby_model.py`
```python
from typing import Dict, Any, Optional
from datetime import datetime

class LobbyModel:
    """
    Data Model - MongoDB representation only.
    Uses database field names: lobbyname, limit (not domain names)
    """
    def __init__(
        self,
        lobby_id: str,
        lobbyname: str,  # Database field name
        description: str,
        limit: int,  # Database field name
        is_public: bool,
        created_at: datetime,
        created_by: str,
        _id: Optional[str] = None
    ):
        self.lobby_id = lobby_id
        self.lobbyname = lobbyname
        self.description = description
        self.limit = limit
        self.is_public = is_public
        self.created_at = created_at
        self.created_by = created_by
        self._id = _id

    def to_document(self) -> Dict[str, Any]:
        """Convert to MongoDB document"""
        return {
            "lobby_id": self.lobby_id,
            "lobbyname": self.lobbyname,
            "description": self.description,
            "limit": self.limit,
            "is_public": self.is_public,
            "created_at": self.created_at,
            "created_by": self.created_by
        }

    @classmethod
    def from_document(cls, doc: Dict[str, Any]) -> 'LobbyModel':
        """Create from MongoDB document"""
        return cls(
            lobby_id=doc["lobby_id"],
            lobbyname=doc["lobbyname"],
            description=doc.get("description", ""),
            limit=doc["limit"],
            is_public=doc.get("is_public", True),
            created_at=doc.get("created_at", datetime.utcnow()),
            created_by=doc.get("created_by", "unknown"),
            _id=str(doc["_id"]) if "_id" in doc else None
        )
```

#### 3. Mapper (Entity ↔ Model)
**File:** `ari/infrastructure/database/mappers/lobby_mapper.py`
```python
from ari.domain.entities.lobby import Lobby
from ari.infrastructure.database.models.lobby_model import LobbyModel

class LobbyMapper:
    """Converts between Entity (domain) and Model (database)"""

    @staticmethod
    def to_entity(model: LobbyModel) -> Lobby:
        """Model → Entity (database names → domain names)"""
        return Lobby(
            lobby_id=model.lobby_id,
            name=model.lobbyname,  # lobbyname → name
            description=model.description,
            max_connections=model.limit,  # limit → max_connections
            is_public=model.is_public,
            created_at=model.created_at,
            created_by=model.created_by
        )

    @staticmethod
    def to_model(entity: Lobby) -> LobbyModel:
        """Entity → Model (domain names → database names)"""
        return LobbyModel(
            lobby_id=entity.lobby_id,
            lobbyname=entity.name,  # name → lobbyname
            description=entity.description,
            limit=entity.max_connections,  # max_connections → limit
            is_public=entity.is_public,
            created_at=entity.created_at,
            created_by=entity.created_by
        )
```

#### 4. Repository (Data Access)
**File:** `ari/domain/repositories/lobby_repository.py` (Interface)
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from ari.domain.entities.lobby import Lobby

class ILobbyRepository(ABC):
    """Repository interface - works with ENTITIES only"""

    @abstractmethod
    async def find_all(self) -> List[Lobby]:
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Lobby]:
        pass

    @abstractmethod
    async def save(self, lobby: Lobby) -> None:
        pass
```

**File:** `ari/infrastructure/repositories/mongo_lobby_repository.py` (Implementation)
```python
from typing import List, Optional
from ari.domain.entities.lobby import Lobby
from ari.domain.repositories.lobby_repository import ILobbyRepository
from ari.infrastructure.database.models.lobby_model import LobbyModel
from ari.infrastructure.database.mappers.lobby_mapper import LobbyMapper

class MongoLobbyRepository(ILobbyRepository):
    """
    Concrete MongoDB implementation.
    Uses Mapper to convert Entity ↔ Model
    """

    def __init__(self, database):
        self.collection = database.lobby_collection()
        self.mapper = LobbyMapper()

    async def find_by_name(self, name: str) -> Optional[Lobby]:
        # 1. Query database
        doc = await self.collection.find_one({"lobbyname": name})
        if not doc:
            return None

        # 2. Document → Model → Entity
        model = LobbyModel.from_document(doc)
        entity = self.mapper.to_entity(model)
        return entity

    async def save(self, lobby: Lobby) -> None:
        # 1. Entity → Model → Document
        model = self.mapper.to_model(lobby)
        doc = model.to_document()

        # 2. Save to database
        await self.collection.insert_one(doc)

    async def find_all(self) -> List[Lobby]:
        cursor = self.collection.find()
        docs = await cursor.to_list(length=None)

        # Convert each: Document → Model → Entity
        return [
            self.mapper.to_entity(LobbyModel.from_document(doc))
            for doc in docs
        ]
```

#### 5. Service (Business Logic)
**File:** `ari/features/lobbies/services/lobby_service.py`
```python
import logging
from typing import List
from ..models.lobby import Lobby, LobbyNotFoundError, LobbyFullError
from ..repositories.lobby_repository import ILobbyRepository
from ...connections.repositories.connection_repository import IConnectionRepository

log = logging.getLogger("features.lobbies")

class LobbyService:
    """Business logic for lobby operations"""

    def __init__(
        self,
        lobby_repo: ILobbyRepository,
        connection_repo: IConnectionRepository
    ):
        self.lobby_repo = lobby_repo
        self.connection_repo = connection_repo

    async def get_lobby_by_name(self, name: str) -> Lobby:
        """Get lobby by name or raise error"""
        lobby = await self.lobby_repo.find_by_name(name)
        if not lobby:
            raise LobbyNotFoundError(f"Lobby '{name}' not found")
        return lobby

    async def can_join_lobby(self, lobby_name: str) -> tuple[bool, str]:
        """
        Check if a lobby can be joined.
        Returns: (can_join, reason_if_not)
        """
        try:
            lobby = await self.get_lobby_by_name(lobby_name)
        except LobbyNotFoundError as e:
            return False, str(e)

        # Count current connections
        connection_count = await self.connection_repo.count_by_lobby(lobby.lobby_id)

        # Business rule check
        if lobby.is_full(connection_count):
            return False, f"Lobby '{lobby_name}' is full ({connection_count}/{lobby.limit})"

        return True, ""

    async def list_available_lobbies(self) -> List[Lobby]:
        """Get all public lobbies with available space"""
        all_lobbies = await self.lobby_repo.find_all()
        available = []

        for lobby in all_lobbies:
            if not lobby.is_public:
                continue

            connection_count = await self.connection_repo.count_by_lobby(lobby.lobby_id)
            if not lobby.is_full(connection_count):
                available.append(lobby)

        return available

    async def create_lobby(
        self,
        name: str,
        description: str,
        limit: int,
        is_public: bool = True
    ) -> Lobby:
        """Create a new lobby with validation"""

        # Create domain model (validation happens in constructor)
        lobby = Lobby(
            lobby_id=self._generate_id(),
            name=name,
            description=description,
            limit=limit,
            is_public=is_public
        )

        # Validate
        lobby.validate_name()

        # Check if exists
        existing = await self.lobby_repo.find_by_name(name)
        if existing:
            raise ValueError(f"Lobby '{name}' already exists")

        # Persist
        await self.lobby_repo.create(lobby)

        log.info(f"Created lobby: {name} (limit: {limit})")
        return lobby

    def _generate_id(self) -> str:
        import uuid
        return str(uuid.uuid4())
```

#### 6. Commands (Presentation)
**File:** `ari/features/lobbies/commands/lobby_commands.py`
```python
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

from ..services.lobby_service import LobbyService
from ..models.lobby import LobbyNotFoundError

log = logging.getLogger("features.lobbies.commands")

class LobbyCommands(commands.Cog, name="Lobbies"):
    """User commands for lobby management"""

    def __init__(self, bot: commands.Bot, lobby_service: LobbyService):
        self.bot = bot
        self.lobby_service = lobby_service

    @commands.hybrid_command(
        name="lobbies",
        description="List all available lobbies"
    )
    async def list_lobbies(self, ctx: commands.Context):
        """Show all lobbies with connection counts"""

        try:
            lobbies = await self.lobby_service.list_available_lobbies()

            if not lobbies:
                await ctx.send("No lobbies available.")
                return

            # Pure presentation logic
            embed = discord.Embed(
                title="Available Lobbies",
                description="Join a lobby to start chatting!",
                color=discord.Color.blue()
            )

            for lobby in lobbies:
                # Get connection count for display
                # (Service handles the query)
                embed.add_field(
                    name=f"🌐 {lobby.name}",
                    value=f"{lobby.description}\nCapacity: {lobby.limit} connections",
                    inline=False
                )

            await ctx.send(embed=embed)

        except Exception as e:
            log.error(f"Error listing lobbies: {e}", exc_info=True)
            await ctx.send("An error occurred while listing lobbies.")

    @commands.hybrid_command(
        name="lobbyinfo",
        description="Get information about a specific lobby"
    )
    @app_commands.describe(lobby_name="Name of the lobby")
    async def lobby_info(self, ctx: commands.Context, lobby_name: str):
        """Show detailed information about a lobby"""

        try:
            # Service handles business logic
            lobby = await self.lobby_service.get_lobby_by_name(lobby_name)

            # Pure presentation
            embed = discord.Embed(
                title=f"📊 {lobby.name}",
                description=lobby.description,
                color=discord.Color.green()
            )
            embed.add_field(name="Capacity", value=str(lobby.limit))
            embed.add_field(name="Type", value="Public" if lobby.is_public else "Private")

            await ctx.send(embed=embed)

        except LobbyNotFoundError as e:
            await ctx.send(f"❌ {str(e)}")
        except Exception as e:
            log.error(f"Error getting lobby info: {e}", exc_info=True)
            await ctx.send("An error occurred.")
```

#### 7. Feature Bootstrap
**File:** `ari/features/lobbies/__init__.py`
```python
"""Lobby management feature"""

from discord.ext import commands
from ..shared.database import Database
from .repositories.lobby_repository import MongoLobbyRepository
from .services.lobby_service import LobbyService
from .commands.lobby_commands import LobbyCommands

def setup_lobby_feature(bot: commands.Bot, database: Database) -> commands.Cog:
    """
    Bootstrap the lobby feature with dependency injection.

    This is called from the main bot initialization.
    """
    # Create dependencies in correct order
    lobby_repo = MongoLobbyRepository(database)
    connection_repo = ... # from connections feature

    lobby_service = LobbyService(lobby_repo, connection_repo)

    lobby_commands = LobbyCommands(bot, lobby_service)

    return lobby_commands
```

#### 8. Main Bot Integration
**File:** `ari/core/bot.py`
```python
from features.lobbies import setup_lobby_feature

class Ari(commands.Bot):
    async def _pre_connect(self) -> None:
        # Initialize features with dependency injection
        lobby_cog = setup_lobby_feature(self, self.db)
        await self.add_cog(lobby_cog)
```

---

## Comparison: Before vs After

### Code Organization

**Before:**
```
global_chat_commands.py (494 lines)
├── Everything mixed together
├── Database queries scattered
├── Business logic intertwined
└── Hard to test

Responsibilities:
- Presentation (Discord commands)
- Business logic (validation, counting)
- Data access (database queries)
- Error handling
- Logging
```

**After:**
```
domain/
└── entities/lobby.py (80 lines)                    # Pure business logic

infrastructure/
├── database/
│   ├── models/lobby_model.py (50 lines)           # Database representation
│   ├── mappers/lobby_mapper.py (30 lines)         # Entity ↔ Model conversion
│   └── repositories/mongo_lobby_repository.py (60 lines)  # Data access

features/lobbies/
├── services/lobby_service.py (100 lines)          # Use cases
└── commands/lobby_commands.py (80 lines)          # User interface

Each file has ONE responsibility!
Total: 400 lines but MUCH clearer and maintainable
```

### Testing

**Before (Hard to Test):**
```python
# Can't test without:
# - Discord bot instance
# - Database connection
# - Guild data loaded
# - Complex setup

# No tests exist!
```

**After (Easy to Test):**
```python
# tests/features/lobbies/services/test_lobby_service.py
@pytest.mark.asyncio
async def test_can_join_lobby_when_not_full():
    # Arrange
    mock_lobby_repo = Mock(spec=ILobbyRepository)
    mock_connection_repo = Mock(spec=IConnectionRepository)

    mock_lobby = Lobby(
        lobby_id="123",
        name="general",
        description="Test",
        limit=10,
        is_public=True
    )
    mock_lobby_repo.find_by_name.return_value = mock_lobby
    mock_connection_repo.count_by_lobby.return_value = 5  # 5/10 filled

    service = LobbyService(mock_lobby_repo, mock_connection_repo)

    # Act
    can_join, reason = await service.can_join_lobby("general")

    # Assert
    assert can_join is True
    assert reason == ""
    mock_lobby_repo.find_by_name.assert_called_once_with("general")
    mock_connection_repo.count_by_lobby.assert_called_once_with("123")

@pytest.mark.asyncio
async def test_cannot_join_full_lobby():
    # Test the business rule
    mock_lobby_repo = Mock(spec=ILobbyRepository)
    mock_connection_repo = Mock(spec=IConnectionRepository)

    mock_lobby = Lobby(
        lobby_id="123",
        name="general",
        description="Test",
        limit=10,
        is_public=True
    )
    mock_lobby_repo.find_by_name.return_value = mock_lobby
    mock_connection_repo.count_by_lobby.return_value = 10  # Full!

    service = LobbyService(mock_lobby_repo, mock_connection_repo)

    can_join, reason = await service.can_join_lobby("general")

    assert can_join is False
    assert "full" in reason.lower()
```

---

## Benefits Summary

### Before (Current)
- ❌ 494-line files
- ❌ Mixed responsibilities
- ❌ Dictionaries everywhere
- ❌ Hard to test (no tests)
- ❌ Duplicate code
- ❌ Tight coupling to MongoDB
- ❌ No type safety

### After (Proposed)
- ✅ Small, focused files (50-120 lines each)
- ✅ Clear separation of concerns
- ✅ Type-safe domain models
- ✅ Fully testable (90%+ coverage possible)
- ✅ Reusable service logic
- ✅ Database-agnostic (can swap MongoDB)
- ✅ Type hints everywhere

---

## Migration Steps for Lobby Feature

1. **Create domain model** (1 hour)
   - Define `Lobby` dataclass
   - Add validation methods
   - Define custom exceptions

2. **Extract repository** (2 hours)
   - Create `ILobbyRepository` interface
   - Implement `MongoLobbyRepository`
   - Map dictionaries to/from models

3. **Create service** (3 hours)
   - Extract business logic from commands
   - Move to `LobbyService`
   - Add proper error handling

4. **Refactor commands** (2 hours)
   - Remove business logic
   - Inject service dependency
   - Keep only presentation code

5. **Add tests** (4 hours)
   - Unit tests for service
   - Unit tests for repository
   - Integration tests for commands

**Total:** 12 hours for one feature

**ROI:** Much easier to maintain, extend, and test going forward!

---

## Next Steps

Once lobbies are migrated, repeat the pattern for:
1. **Messaging** (message broadcasting, webhooks)
2. **Connections** (join/leave lobby)
3. **Moderation** (muting, blacklists)
4. **Reporting** (user reports)

Each feature follows the same clean architecture pattern!
