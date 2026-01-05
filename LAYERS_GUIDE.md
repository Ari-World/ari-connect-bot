# Architectural Layers Guide

This guide explains the different layers in clean architecture and how they work together.

## The Layer Pyramid

```
┌─────────────────────────────────────────────────────────┐
│                  Presentation Layer                      │
│              (User Interface / Discord)                  │
│   - Commands, Views, Embeds, Message Formatting         │
│   - Depends on: Application, Domain                     │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  Application Layer                       │
│                   (Use Cases / Services)                 │
│   - Business workflows, orchestration                    │
│   - Depends on: Domain                                   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    Domain Layer                          │
│              (Business Logic & Rules)                    │
│   - Entities, Value Objects, Domain Services            │
│   - Repository Interfaces                                │
│   - Domain Exceptions                                    │
│   - Depends on: NOTHING (pure business logic)           │
└───────────────────────────────────────────────────────────┘
                      ▲
                      │
┌─────────────────────┴───────────────────────────────────┐
│                Infrastructure Layer                      │
│              (External Concerns)                         │
│   - Database, Discord API, File System                  │
│   - Repository Implementations                           │
│   - External Services                                    │
│   - Depends on: Domain (implements interfaces)          │
└───────────────────────────────────────────────────────────┘
```

## The Dependency Rule

**Core Principle:** Dependencies point INWARD only!

- ✅ Infrastructure → Domain (OK)
- ✅ Application → Domain (OK)
- ✅ Presentation → Application → Domain (OK)
- ❌ Domain → Infrastructure (NEVER!)
- ❌ Domain → Application (NEVER!)

**Why?** Business logic should be independent of frameworks, databases, and UI.

---

## Layer 1: Domain Layer (Core)

**Location:** `ari/domain/`

**Purpose:** Pure business logic - the heart of your application

**Contains:**
- **Entities**: Business objects with identity and behavior
- **Value Objects**: Immutable objects defined by their values
- **Domain Services**: Business logic that doesn't belong to a single entity
- **Repository Interfaces**: Abstract definitions (implementations elsewhere)
- **Domain Events**: Things that happen in the business
- **Exceptions**: Domain-specific errors

**Dependencies:** NONE (completely independent)

**Rules:**
- No framework imports (no discord.py, no motor/pymongo)
- No database code
- No external API calls
- Pure Python only

### Example: Domain Layer

```python
# ari/domain/entities/lobby.py
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Lobby:
    """
    Business entity representing a chat lobby.
    Contains business rules and validation.
    """
    lobby_id: str
    name: str
    max_connections: int
    created_at: datetime

    def can_accept_connection(self, current_count: int) -> bool:
        """Business rule: can lobby accept new connection?"""
        return current_count < self.max_connections

    def validate(self) -> None:
        """Business rule: lobby must be valid"""
        if len(self.name) < 3:
            raise InvalidLobbyNameError("Name too short")
        if self.max_connections < 1:
            raise InvalidLobbyCapacityError("Invalid capacity")


# ari/domain/repositories/lobby_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.lobby import Lobby

class ILobbyRepository(ABC):
    """
    Repository interface (abstract).
    Domain defines WHAT it needs, not HOW it's implemented.
    """

    @abstractmethod
    async def find_by_id(self, lobby_id: str) -> Optional[Lobby]:
        """Find lobby by ID"""
        pass

    @abstractmethod
    async def save(self, lobby: Lobby) -> None:
        """Save lobby"""
        pass


# ari/domain/services/lobby_domain_service.py
class LobbyDomainService:
    """
    Domain service - business logic that involves multiple entities
    or doesn't naturally belong to one entity.
    """

    @staticmethod
    def calculate_lobby_score(
        lobby: Lobby,
        message_count: int,
        user_count: int
    ) -> float:
        """Business logic: calculate lobby popularity score"""
        # Complex business calculation
        utilization = user_count / lobby.max_connections
        activity = message_count / user_count if user_count > 0 else 0
        return (utilization * 0.6) + (activity * 0.4)


# ari/domain/exceptions/lobby_exceptions.py
class LobbyDomainError(Exception):
    """Base exception for lobby domain"""
    pass

class InvalidLobbyNameError(LobbyDomainError):
    pass

class LobbyFullError(LobbyDomainError):
    pass
```

**What belongs here:**
- ✅ Business rules: "Lobby name must be 3-50 characters"
- ✅ Validation: "Max connections must be positive"
- ✅ Calculations: "Calculate lobby utilization percentage"
- ❌ Database queries
- ❌ Discord API calls
- ❌ File operations

---

## Layer 2: Application Layer (Use Cases)

**Location:** `ari/features/*/services/`

**Purpose:** Orchestrate business workflows (use cases)

**Contains:**
- **Application Services**: Implement specific use cases
- **DTOs**: Data Transfer Objects (if needed)
- **Commands/Queries**: CQRS pattern (optional)

**Dependencies:** Domain layer only

**Rules:**
- Orchestrates entities and domain services
- Calls repositories (via interfaces)
- Handles transactions
- No UI concerns
- No database implementation details

### Example: Application Layer

```python
# ari/features/lobbies/services/lobby_service.py
from typing import Optional
import logging
from uuid import uuid4
from datetime import datetime

from ari.domain.entities.lobby import Lobby
from ari.domain.repositories.lobby_repository import ILobbyRepository
from ari.domain.exceptions.lobby_exceptions import InvalidLobbyNameError

log = logging.getLogger(__name__)

class LobbyService:
    """
    Application Service - implements use cases.
    Orchestrates domain objects to accomplish business workflows.
    """

    def __init__(
        self,
        lobby_repo: ILobbyRepository,  # Depends on interface!
        connection_service: 'ConnectionService'
    ):
        self.lobby_repo = lobby_repo
        self.connection_service = connection_service

    async def create_lobby(
        self,
        name: str,
        max_connections: int,
        created_by_user_id: str
    ) -> Lobby:
        """
        Use Case: Create a new lobby

        Steps:
        1. Create domain entity
        2. Validate business rules
        3. Check for duplicates
        4. Save to repository
        5. Log the action
        """

        # 1. Create entity
        lobby = Lobby(
            lobby_id=str(uuid4()),
            name=name,
            max_connections=max_connections,
            created_at=datetime.utcnow()
        )

        # 2. Validate (business rules in entity)
        lobby.validate()

        # 3. Business constraint: no duplicate names
        existing = await self.lobby_repo.find_by_name(name)
        if existing:
            raise InvalidLobbyNameError(f"Lobby '{name}' already exists")

        # 4. Persist
        await self.lobby_repo.save(lobby)

        # 5. Side effects / logging
        log.info(f"Lobby created: {name} by user {created_by_user_id}")

        return lobby

    async def join_lobby(
        self,
        lobby_id: str,
        guild_id: int,
        channel_id: int
    ) -> None:
        """
        Use Case: Join a lobby

        Orchestrates multiple operations across different services.
        """

        # 1. Get lobby
        lobby = await self.lobby_repo.find_by_id(lobby_id)
        if not lobby:
            raise LobbyNotFoundError(f"Lobby {lobby_id} not found")

        # 2. Check capacity (business rule in entity)
        current_count = await self.connection_service.count_connections(lobby_id)
        if not lobby.can_accept_connection(current_count):
            raise LobbyFullError(f"Lobby {lobby.name} is full")

        # 3. Create connection (orchestration)
        await self.connection_service.create_connection(
            lobby_id=lobby_id,
            guild_id=guild_id,
            channel_id=channel_id
        )

        # 4. Side effects
        log.info(f"Guild {guild_id} joined lobby {lobby.name}")

    async def get_available_lobbies(self) -> List[Lobby]:
        """
        Use Case: List all lobbies with available space

        This is a query use case (read-only).
        """
        all_lobbies = await self.lobby_repo.find_all()

        # Filter using business logic
        available = []
        for lobby in all_lobbies:
            count = await self.connection_service.count_connections(lobby.lobby_id)
            if lobby.can_accept_connection(count):
                available.append(lobby)

        return available
```

**What belongs here:**
- ✅ Use case orchestration: "Create lobby and notify admins"
- ✅ Transaction boundaries
- ✅ Calling multiple repositories
- ✅ Logging business events
- ❌ Business rules (those go in domain!)
- ❌ UI formatting
- ❌ Database queries

---

## Layer 3: Infrastructure Layer (External)

**Location:** `ari/infrastructure/`

**Purpose:** Implement interfaces, handle external concerns

**Contains:**
- **Repository Implementations**: Concrete database access
- **Data Models**: Database schema representations
- **Mappers**: Convert entities ↔ models
- **External Services**: APIs, file systems, etc.
- **Framework Integration**: Discord.py setup, etc.

**Dependencies:** Domain (implements interfaces)

**Rules:**
- Implements repository interfaces from domain
- Contains all database-specific code
- Handles all external I/O
- Maps between domain entities and data models

### Example: Infrastructure Layer

```python
# ari/infrastructure/database/models/lobby_model.py
from typing import Dict, Any
from datetime import datetime

class LobbyModel:
    """
    Data Model - represents database structure.
    Uses MongoDB field names and structure.
    """

    def __init__(
        self,
        lobby_id: str,
        lobbyname: str,  # Database field name!
        limit: int,  # Database field name!
        created_at: datetime,
        _id: str = None
    ):
        self.lobby_id = lobby_id
        self.lobbyname = lobbyname
        self.limit = limit
        self.created_at = created_at
        self._id = _id

    def to_document(self) -> Dict[str, Any]:
        """Convert to MongoDB document"""
        return {
            "lobby_id": self.lobby_id,
            "lobbyname": self.lobbyname,
            "limit": self.limit,
            "created_at": self.created_at
        }

    @classmethod
    def from_document(cls, doc: Dict[str, Any]) -> 'LobbyModel':
        """Create from MongoDB document"""
        return cls(
            lobby_id=doc["lobby_id"],
            lobbyname=doc["lobbyname"],
            limit=doc["limit"],
            created_at=doc["created_at"],
            _id=str(doc.get("_id"))
        )


# ari/infrastructure/database/mappers/lobby_mapper.py
from ari.domain.entities.lobby import Lobby
from ..models.lobby_model import LobbyModel

class LobbyMapper:
    """Maps between domain entity and data model"""

    @staticmethod
    def to_entity(model: LobbyModel) -> Lobby:
        """Data Model → Domain Entity"""
        return Lobby(
            lobby_id=model.lobby_id,
            name=model.lobbyname,  # Map field names!
            max_connections=model.limit,  # Map field names!
            created_at=model.created_at
        )

    @staticmethod
    def to_model(entity: Lobby) -> LobbyModel:
        """Domain Entity → Data Model"""
        return LobbyModel(
            lobby_id=entity.lobby_id,
            lobbyname=entity.name,  # Map field names!
            limit=entity.max_connections,  # Map field names!
            created_at=entity.created_at
        )


# ari/infrastructure/repositories/mongo_lobby_repository.py
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection

from ari.domain.entities.lobby import Lobby
from ari.domain.repositories.lobby_repository import ILobbyRepository
from ..database.models.lobby_model import LobbyModel
from ..database.mappers.lobby_mapper import LobbyMapper

class MongoLobbyRepository(ILobbyRepository):
    """
    Concrete implementation of ILobbyRepository for MongoDB.

    This is infrastructure - domain doesn't know about it!
    """

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
        self.mapper = LobbyMapper()

    async def find_by_id(self, lobby_id: str) -> Optional[Lobby]:
        """Implements interface method"""
        # 1. MongoDB query
        doc = await self.collection.find_one({"lobby_id": lobby_id})
        if not doc:
            return None

        # 2. Document → Model → Entity
        model = LobbyModel.from_document(doc)
        entity = self.mapper.to_entity(model)

        return entity

    async def save(self, lobby: Lobby) -> None:
        """Implements interface method"""
        # 1. Entity → Model → Document
        model = self.mapper.to_model(lobby)
        doc = model.to_document()

        # 2. MongoDB operation
        await self.collection.insert_one(doc)

    async def find_all(self) -> List[Lobby]:
        """Implements interface method"""
        cursor = self.collection.find()
        docs = await cursor.to_list(length=None)

        # Convert all documents to entities
        return [
            self.mapper.to_entity(LobbyModel.from_document(doc))
            for doc in docs
        ]
```

**What belongs here:**
- ✅ Database queries and connections
- ✅ File I/O operations
- ✅ External API calls
- ✅ Framework-specific code
- ❌ Business logic
- ❌ Use case orchestration

---

## Layer 4: Presentation Layer (UI)

**Location:** `ari/features/*/commands/`

**Purpose:** Handle user interaction (Discord commands, views)

**Contains:**
- **Commands**: Discord slash commands, text commands
- **Views**: Discord UI components (buttons, selects)
- **Formatters**: Convert entities to embeds/messages
- **Input Validation**: User input parsing

**Dependencies:** Application, Domain

**Rules:**
- Handles Discord-specific code
- Converts user input to application calls
- Formats output for users
- NO business logic!
- NO database access!

### Example: Presentation Layer

```python
# ari/features/lobbies/commands/lobby_commands.py
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

from ..services.lobby_service import LobbyService
from ari.domain.exceptions.lobby_exceptions import (
    InvalidLobbyNameError,
    LobbyFullError,
    LobbyNotFoundError
)

log = logging.getLogger(__name__)

class LobbyCommands(commands.Cog, name="Lobbies"):
    """
    Presentation Layer - handles Discord interaction.

    Responsibilities:
    - Parse user input
    - Call application services
    - Format output for Discord
    - Handle Discord-specific errors
    """

    def __init__(self, bot: commands.Bot, lobby_service: LobbyService):
        self.bot = bot
        self.service = lobby_service  # Application service

    @commands.hybrid_command(
        name="create-lobby",
        description="Create a new chat lobby"
    )
    @app_commands.describe(
        name="Name of the lobby",
        max_connections="Maximum number of server connections"
    )
    async def create_lobby(
        self,
        ctx: commands.Context,
        name: str,
        max_connections: int = 10
    ):
        """
        Command handler - pure presentation logic.

        1. Validate input (UI validation, not business validation!)
        2. Call application service
        3. Format response
        4. Handle errors gracefully
        """

        try:
            # 1. UI validation (quick checks before service call)
            if max_connections < 1 or max_connections > 100:
                await ctx.send("❌ Max connections must be between 1 and 100")
                return

            # 2. Call application service (business logic happens here)
            lobby = await self.service.create_lobby(
                name=name,
                max_connections=max_connections,
                created_by_user_id=str(ctx.author.id)
            )

            # 3. Format response (presentation logic)
            embed = discord.Embed(
                title="✅ Lobby Created",
                description=f"Successfully created lobby **{lobby.name}**",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Capacity",
                value=f"{lobby.max_connections} connections"
            )
            embed.add_field(
                name="ID",
                value=f"`{lobby.lobby_id}`"
            )

            await ctx.send(embed=embed)

        # 4. Handle domain exceptions (convert to user-friendly messages)
        except InvalidLobbyNameError as e:
            await ctx.send(f"❌ Invalid lobby name: {str(e)}")
        except Exception as e:
            log.error(f"Error creating lobby: {e}", exc_info=True)
            await ctx.send("❌ An error occurred while creating the lobby.")

    @commands.hybrid_command(
        name="join-lobby",
        description="Connect this channel to a lobby"
    )
    @app_commands.describe(lobby_name="Name of the lobby to join")
    async def join_lobby(self, ctx: commands.Context, lobby_name: str):
        """Join a lobby - presentation logic only"""

        # Ensure command is run in a guild
        if not ctx.guild:
            await ctx.send("❌ This command must be used in a server.")
            return

        try:
            # Call service
            await self.service.join_lobby(
                lobby_id=lobby_name,  # Service will handle lookup
                guild_id=ctx.guild.id,
                channel_id=ctx.channel.id
            )

            # Format success message
            embed = discord.Embed(
                title="✅ Joined Lobby",
                description=f"This channel is now connected to **{lobby_name}**",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)

        except LobbyNotFoundError:
            await ctx.send(f"❌ Lobby '{lobby_name}' not found.")
        except LobbyFullError:
            await ctx.send(f"❌ Lobby '{lobby_name}' is full.")
        except Exception as e:
            log.error(f"Error joining lobby: {e}", exc_info=True)
            await ctx.send("❌ An error occurred.")

    @commands.hybrid_command(
        name="lobbies",
        description="List all available lobbies"
    )
    async def list_lobbies(self, ctx: commands.Context):
        """List lobbies - presentation logic"""

        try:
            # Get data from service
            lobbies = await self.service.get_available_lobbies()

            if not lobbies:
                await ctx.send("No lobbies available.")
                return

            # Format for Discord (presentation logic!)
            embed = discord.Embed(
                title="🌐 Available Lobbies",
                description="Lobbies with available space",
                color=discord.Color.blue()
            )

            for lobby in lobbies:
                # Format each lobby nicely
                embed.add_field(
                    name=f"📍 {lobby.name}",
                    value=f"Capacity: {lobby.max_connections} connections",
                    inline=False
                )

            await ctx.send(embed=embed)

        except Exception as e:
            log.error(f"Error listing lobbies: {e}", exc_info=True)
            await ctx.send("❌ An error occurred.")


# ari/features/lobbies/formatters/lobby_formatter.py
class LobbyFormatter:
    """
    Formatter - converts domain entities to Discord embeds.
    This is presentation logic.
    """

    @staticmethod
    def to_embed(lobby: Lobby, connection_count: int) -> discord.Embed:
        """Convert lobby entity to Discord embed"""
        utilization = (connection_count / lobby.max_connections) * 100

        embed = discord.Embed(
            title=f"🌐 {lobby.name}",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Connections",
            value=f"{connection_count}/{lobby.max_connections} ({utilization:.0f}%)"
        )
        embed.add_field(
            name="Created",
            value=discord.utils.format_dt(lobby.created_at, "R")
        )

        return embed
```

**What belongs here:**
- ✅ Discord command definitions
- ✅ User input parsing
- ✅ Embed/message formatting
- ✅ Error message display
- ❌ Business logic
- ❌ Database queries
- ❌ Complex calculations

---

## How Layers Work Together

### Example Flow: Creating a Lobby

```
User types: /create-lobby general 50

1. PRESENTATION LAYER (Commands)
   ↓ Parses input: name="general", max=50
   ↓ Validates UI constraints
   ↓ Calls application service

2. APPLICATION LAYER (Service)
   ↓ Creates domain entity
   ↓ Validates business rules
   ↓ Checks for duplicates (via repository)
   ↓ Saves entity (via repository)
   ↓ Returns entity

3. DOMAIN LAYER (Entity)
   ↓ Validates business rules
   ↓ Ensures name length, capacity, etc.

4. INFRASTRUCTURE LAYER (Repository)
   ↓ Converts entity → model → document
   ↓ Saves to MongoDB
   ↓ Converts document → model → entity
   ↓ Returns entity

5. APPLICATION LAYER (Service)
   ↓ Returns entity to presentation

6. PRESENTATION LAYER (Commands)
   ↓ Formats entity as Discord embed
   ↓ Sends to user
```

### Data Flow

```
User Input (Discord)
    ↓
[PRESENTATION] Command parses input
    ↓
[APPLICATION] Service orchestrates workflow
    ↓
[DOMAIN] Entity validates business rules
    ↓
[INFRASTRUCTURE] Repository saves to database
    ↑
[DOMAIN] Entity returned
    ↑
[APPLICATION] Service returns result
    ↑
[PRESENTATION] Command formats as embed
    ↑
User sees result (Discord)
```

---

## Layer Responsibilities Summary

| Layer | What It Does | What It Knows About | What It Doesn't Know About |
|-------|--------------|---------------------|---------------------------|
| **Domain** | Business logic & rules | Business concepts only | Database, Discord, Files |
| **Application** | Use case orchestration | Domain entities, workflows | Database implementation, Discord |
| **Infrastructure** | External I/O | Database, APIs, Files | Business rules |
| **Presentation** | User interaction | Discord API, formatting | Business rules, Database |

---

## Directory Structure

```
ari/
├── domain/                          # DOMAIN LAYER
│   ├── entities/
│   │   ├── lobby.py
│   │   ├── guild.py
│   │   └── channel.py
│   ├── repositories/                # Interfaces only!
│   │   ├── lobby_repository.py
│   │   └── guild_repository.py
│   ├── services/
│   │   └── lobby_domain_service.py
│   └── exceptions/
│       └── lobby_exceptions.py
│
├── application/                     # APPLICATION LAYER
│   └── features/
│       ├── lobbies/
│       │   └── services/
│       │       └── lobby_service.py
│       └── messaging/
│           └── services/
│               └── message_broadcaster.py
│
├── infrastructure/                  # INFRASTRUCTURE LAYER
│   ├── database/
│   │   ├── models/
│   │   │   ├── lobby_model.py
│   │   │   └── guild_model.py
│   │   ├── mappers/
│   │   │   ├── lobby_mapper.py
│   │   │   └── guild_mapper.py
│   │   └── repositories/
│   │       ├── mongo_lobby_repository.py
│   │       └── mongo_guild_repository.py
│   └── discord/
│       └── webhook_service.py
│
└── presentation/                    # PRESENTATION LAYER
    └── features/
        ├── lobbies/
        │   ├── commands/
        │   │   └── lobby_commands.py
        │   └── formatters/
        │       └── lobby_formatter.py
        └── messaging/
            └── views/
                └── message_view.py
```

---

## Testing by Layer

### Domain Layer Testing
```python
# Test business logic in isolation - no mocks needed!

def test_lobby_rejects_short_name():
    lobby = Lobby(
        lobby_id="123",
        name="ab",  # Too short!
        max_connections=10,
        created_at=datetime.now()
    )

    with pytest.raises(InvalidLobbyNameError):
        lobby.validate()
```

### Application Layer Testing
```python
# Test use cases with mocked repositories

@pytest.mark.asyncio
async def test_create_lobby_checks_for_duplicates():
    # Mock repository
    mock_repo = Mock(spec=ILobbyRepository)
    mock_repo.find_by_name.return_value = Lobby(...)  # Existing lobby

    service = LobbyService(mock_repo)

    # Should raise error when duplicate exists
    with pytest.raises(InvalidLobbyNameError):
        await service.create_lobby("general", 10, "user123")
```

### Infrastructure Layer Testing
```python
# Test database operations (integration tests)

@pytest.mark.asyncio
async def test_mongo_repository_saves_lobby(mongo_db):
    repo = MongoLobbyRepository(mongo_db.lobbies)

    lobby = Lobby(...)
    await repo.save(lobby)

    # Verify it was saved
    found = await repo.find_by_id(lobby.lobby_id)
    assert found.name == lobby.name
```

### Presentation Layer Testing
```python
# Test Discord commands (integration/E2E tests)

@pytest.mark.asyncio
async def test_create_lobby_command(bot, test_guild):
    cog = LobbyCommands(bot, lobby_service)

    # Simulate command
    ctx = create_mock_context(...)
    await cog.create_lobby(ctx, "test-lobby", 10)

    # Verify response
    assert "✅ Lobby Created" in ctx.sent_messages[0].embeds[0].title
```

---

## Common Mistakes

### ❌ Mistake 1: Business Logic in Commands
```python
# BAD - Business logic in presentation layer
@commands.command()
async def join(self, ctx, lobby_name: str):
    lobby = await get_lobby(lobby_name)
    if len(lobby["channels"]) >= lobby["limit"]:  # Business rule!
        await ctx.send("Full")
```

✅ **Fix:** Move to domain entity
```python
# GOOD - Business logic in domain
if lobby.is_full(current_connections):
    raise LobbyFullError()
```

### ❌ Mistake 2: Database Code in Service
```python
# BAD - MongoDB code in application layer
async def create_lobby(self, name: str):
    doc = {"lobbyname": name}
    await self.db.lobbies.insert_one(doc)  # Infrastructure concern!
```

✅ **Fix:** Use repository
```python
# GOOD - Use repository abstraction
async def create_lobby(self, name: str):
    lobby = Lobby(...)
    await self.lobby_repo.save(lobby)  # Repository handles database!
```

### ❌ Mistake 3: Domain Depending on Infrastructure
```python
# BAD - Domain entity importing database
from motor import AsyncIOMotorClient  # Infrastructure import!

class Lobby:
    async def save(self):
        client = AsyncIOMotorClient()  # NO!
```

✅ **Fix:** Inversion of control
```python
# GOOD - Domain defines interface, infrastructure implements
class ILobbyRepository(ABC):
    @abstractmethod
    async def save(self, lobby: Lobby): pass
```

---

## Benefits of Layered Architecture

1. **Testability**: Test each layer in isolation
2. **Maintainability**: Changes in one layer don't affect others
3. **Flexibility**: Swap MongoDB for PostgreSQL? Only change infrastructure!
4. **Clarity**: Each layer has clear responsibility
5. **Reusability**: Domain logic can be reused across different UIs
6. **Team Productivity**: Different devs can work on different layers

---

## Summary

| Question | Answer |
|----------|--------|
| Where do business rules go? | **Domain Layer** (entities, domain services) |
| Where do use cases go? | **Application Layer** (services) |
| Where do database queries go? | **Infrastructure Layer** (repositories) |
| Where do Discord commands go? | **Presentation Layer** (commands, views) |
| What can domain depend on? | **Nothing!** (pure business logic) |
| What can application depend on? | **Domain only** |
| What can infrastructure depend on? | **Domain** (implements interfaces) |
| What can presentation depend on? | **Application & Domain** |

**Golden Rule:** Dependencies flow inward toward the domain!
