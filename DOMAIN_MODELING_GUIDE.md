# Domain Modeling Guide: Entities vs Models

This guide explains the difference between **Domain Entities** and **Data Models**, and when to use each.

## Quick Answer

**Yes, you should separate them!**

```
Entity  → Business logic, validation, rules (domain layer)
Model   → Database representation, mapping (infrastructure layer)
```

## The Problem with Mixing Them

**Current codebase:**
```python
# Everything is a dictionary - no separation at all!
lobby = {
    "lobby_id": "123",
    "lobbyname": "general",  # Database field name
    "limit": 10,
    "_id": ObjectId("..."),  # MongoDB specific!
}

# Business logic mixed with database structure
if lobby["limit"] <= count:  # What if we rename the DB field?
    raise Exception("Full")
```

**Problems:**
- Business logic coupled to database schema
- Can't change database without breaking business logic
- No validation, no type safety
- Database concerns leak everywhere

## The Solution: Separate Layers

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Presentation Layer                   │
│                    (Discord Commands)                    │
│                 Uses: Domain Entities                    │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                    Service Layer                         │
│                  (Business Logic)                        │
│                 Uses: Domain Entities                    │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   Domain Layer                           │
│              ┌─────────────────────┐                     │
│              │  Domain Entities    │  ← Pure business    │
│              │  - Lobby            │                     │
│              │  - Guild            │                     │
│              │  - Channel          │                     │
│              └─────────────────────┘                     │
└───────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Repository Layer (Interface)                │
│              Uses: Domain Entities (in/out)              │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Infrastructure Layer                        │
│              ┌─────────────────────┐                     │
│              │   Data Models       │  ← DB representation│
│              │  - LobbyModel       │                     │
│              │  - GuildModel       │                     │
│              │  - ChannelModel     │                     │
│              └─────────────────────┘                     │
│              ┌─────────────────────┐                     │
│              │   Mappers           │  ← Converts         │
│              │  Entity ↔ Model     │                     │
│              └─────────────────────┘                     │
└───────────────────────────────────────────────────────────┘
```

## Concrete Example: Lobby Feature

### 1. Domain Entity (Pure Business Logic)

**File:** `ari/domain/entities/lobby.py`

```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Lobby:
    """
    Domain Entity - represents a lobby in the business domain.

    NO DATABASE CONCERNS:
    - No MongoDB ObjectId
    - No database field names
    - No ORM annotations
    - Just pure business logic
    """

    # Identity
    lobby_id: str

    # Business attributes (names that make sense to the domain)
    name: str
    description: str
    max_connections: int  # NOT "limit" - use domain language!
    is_public: bool

    # Metadata
    created_at: datetime
    created_by: str  # User ID who created it

    # --- BUSINESS RULES (This is why we need entities!) ---

    def can_accept_connection(self, current_connections: int) -> bool:
        """Business rule: Can this lobby accept a new connection?"""
        return current_connections < self.max_connections

    def is_full(self, current_connections: int) -> bool:
        """Business rule: Is this lobby at capacity?"""
        return current_connections >= self.max_connections

    def validate(self) -> None:
        """Business rule: Validate lobby properties"""
        if not self.name:
            raise InvalidLobbyError("Name cannot be empty")

        if len(self.name) < 3:
            raise InvalidLobbyError("Name must be at least 3 characters")

        if len(self.name) > 50:
            raise InvalidLobbyError("Name must be less than 50 characters")

        if not self.name.replace("-", "").replace("_", "").isalnum():
            raise InvalidLobbyError("Name must be alphanumeric (-, _ allowed)")

        if self.max_connections < 1:
            raise InvalidLobbyError("Max connections must be at least 1")

        if self.max_connections > 1000:
            raise InvalidLobbyError("Max connections cannot exceed 1000")

    def rename(self, new_name: str) -> None:
        """Business operation: Rename lobby with validation"""
        old_name = self.name
        self.name = new_name

        try:
            self.validate()
        except InvalidLobbyError:
            # Rollback if validation fails
            self.name = old_name
            raise

    def increase_capacity(self, additional: int) -> None:
        """Business operation: Increase lobby capacity"""
        if additional < 0:
            raise ValueError("Cannot increase by negative amount")

        self.max_connections += additional
        self.validate()

    # --- QUERIES (Domain logic, not database queries!) ---

    def connection_percentage(self, current_connections: int) -> float:
        """Calculate what % of capacity is used"""
        return (current_connections / self.max_connections) * 100

    def is_nearly_full(self, current_connections: int, threshold: float = 0.9) -> bool:
        """Business rule: Is lobby nearly full?"""
        return self.connection_percentage(current_connections) >= (threshold * 100)


# Domain Exceptions
class InvalidLobbyError(Exception):
    """Raised when lobby entity validation fails"""
    pass

class LobbyFullError(Exception):
    """Raised when attempting to join a full lobby"""
    pass
```

### 2. Data Model (Database Representation)

**File:** `ari/infrastructure/database/models/lobby_model.py`

```python
from typing import Optional, Dict, Any
from datetime import datetime

class LobbyModel:
    """
    Data Model - represents how a lobby is stored in MongoDB.

    DATABASE CONCERNS ONLY:
    - Maps to MongoDB document structure
    - Uses database field names
    - Handles MongoDB ObjectId
    - No business logic!
    """

    def __init__(
        self,
        lobby_id: str,
        lobbyname: str,  # MongoDB uses this field name
        description: str,
        limit: int,  # MongoDB uses "limit", domain uses "max_connections"
        is_public: bool,
        created_at: datetime,
        created_by: str,
        _id: Optional[str] = None  # MongoDB ObjectId
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
        """Convert to MongoDB document format"""
        doc = {
            "lobby_id": self.lobby_id,
            "lobbyname": self.lobbyname,
            "description": self.description,
            "limit": self.limit,
            "is_public": self.is_public,
            "created_at": self.created_at,
            "created_by": self.created_by
        }

        if self._id:
            doc["_id"] = self._id

        return doc

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
            _id=str(doc.get("_id")) if doc.get("_id") else None
        )
```

### 3. Mapper (Converts Between Entity and Model)

**File:** `ari/infrastructure/database/mappers/lobby_mapper.py`

```python
from datetime import datetime
from ari.domain.entities.lobby import Lobby
from ari.infrastructure.database.models.lobby_model import LobbyModel

class LobbyMapper:
    """
    Mapper - converts between domain entities and data models.

    This is the ONLY place that knows about both!
    """

    @staticmethod
    def to_entity(model: LobbyModel) -> Lobby:
        """
        Convert Data Model → Domain Entity

        Maps database field names to domain names:
        - lobbyname → name
        - limit → max_connections
        """
        return Lobby(
            lobby_id=model.lobby_id,
            name=model.lobbyname,  # Database: "lobbyname" → Domain: "name"
            description=model.description,
            max_connections=model.limit,  # Database: "limit" → Domain: "max_connections"
            is_public=model.is_public,
            created_at=model.created_at,
            created_by=model.created_by
        )

    @staticmethod
    def to_model(entity: Lobby) -> LobbyModel:
        """
        Convert Domain Entity → Data Model

        Maps domain names to database field names:
        - name → lobbyname
        - max_connections → limit
        """
        return LobbyModel(
            lobby_id=entity.lobby_id,
            lobbyname=entity.name,  # Domain: "name" → Database: "lobbyname"
            description=entity.description,
            limit=entity.max_connections,  # Domain: "max_connections" → Database: "limit"
            is_public=entity.is_public,
            created_at=entity.created_at,
            created_by=entity.created_by
        )

    @staticmethod
    def to_entity_from_dict(data: dict) -> Lobby:
        """Convenience: Convert dict directly to entity"""
        model = LobbyModel.from_document(data)
        return LobbyMapper.to_entity(model)
```

### 4. Repository (Uses Mapper)

**File:** `ari/infrastructure/repositories/mongo_lobby_repository.py`

```python
from typing import List, Optional
from ari.domain.entities.lobby import Lobby
from ari.domain.repositories.lobby_repository import ILobbyRepository
from ari.infrastructure.database.models.lobby_model import LobbyModel
from ari.infrastructure.database.mappers.lobby_mapper import LobbyMapper

class MongoLobbyRepository(ILobbyRepository):
    """
    Repository - handles database operations.

    Works with ENTITIES in its interface,
    but uses MODELS internally for database operations.
    """

    def __init__(self, database):
        self.collection = database.lobby_collection()
        self.mapper = LobbyMapper()

    async def find_by_name(self, name: str) -> Optional[Lobby]:
        """
        Interface works with domain entities.
        Internally converts: Document → Model → Entity
        """
        # 1. Query database (returns dict/document)
        doc = await self.collection.find_one({"lobbyname": name})

        if not doc:
            return None

        # 2. Convert to Model (database representation)
        model = LobbyModel.from_document(doc)

        # 3. Convert to Entity (domain representation)
        entity = self.mapper.to_entity(model)

        return entity

    async def save(self, lobby: Lobby) -> None:
        """
        Accepts domain entity.
        Internally converts: Entity → Model → Document
        """
        # 1. Convert Entity to Model
        model = self.mapper.to_model(lobby)

        # 2. Convert Model to Document
        doc = model.to_document()

        # 3. Save to database
        await self.collection.insert_one(doc)

    async def update(self, lobby: Lobby) -> None:
        """Update existing lobby"""
        model = self.mapper.to_model(lobby)
        doc = model.to_document()

        await self.collection.update_one(
            {"lobby_id": lobby.lobby_id},
            {"$set": doc}
        )

    async def find_all(self) -> List[Lobby]:
        """Get all lobbies as entities"""
        cursor = self.collection.find()
        docs = await cursor.to_list(length=None)

        # Convert each document to entity
        entities = [
            self.mapper.to_entity(LobbyModel.from_document(doc))
            for doc in docs
        ]

        return entities
```

### 5. Service (Works with Entities Only)

**File:** `ari/features/lobbies/services/lobby_service.py`

```python
from ari.domain.entities.lobby import Lobby, LobbyFullError, InvalidLobbyError
from ari.domain.repositories.lobby_repository import ILobbyRepository

class LobbyService:
    """
    Service - implements business use cases.

    ONLY knows about domain entities!
    Has NO idea about database models.
    """

    def __init__(self, lobby_repo: ILobbyRepository):
        self.lobby_repo = lobby_repo

    async def create_lobby(
        self,
        name: str,
        description: str,
        max_connections: int,
        created_by: str
    ) -> Lobby:
        """
        Business use case: Create a new lobby.

        Works entirely with domain entities!
        """
        from datetime import datetime
        import uuid

        # 1. Create domain entity
        lobby = Lobby(
            lobby_id=str(uuid.uuid4()),
            name=name,
            description=description,
            max_connections=max_connections,
            is_public=True,
            created_at=datetime.utcnow(),
            created_by=created_by
        )

        # 2. Validate using business rules
        lobby.validate()

        # 3. Check business constraint: no duplicate names
        existing = await self.lobby_repo.find_by_name(name)
        if existing:
            raise InvalidLobbyError(f"Lobby '{name}' already exists")

        # 4. Save (repository handles Entity → Model conversion)
        await self.lobby_repo.save(lobby)

        return lobby

    async def can_join_lobby(
        self,
        lobby_name: str,
        current_connections: int
    ) -> tuple[bool, str]:
        """
        Business use case: Check if lobby can be joined.

        Uses business logic from entity!
        """
        lobby = await self.lobby_repo.find_by_name(lobby_name)

        if not lobby:
            return False, f"Lobby '{lobby_name}' not found"

        # Business logic is in the entity!
        if not lobby.can_accept_connection(current_connections):
            percentage = lobby.connection_percentage(current_connections)
            return False, f"Lobby is full ({percentage:.0f}% capacity)"

        return True, ""
```

## Benefits of Entity + Model Separation

### 1. **Independence**
```python
# Can change database schema WITHOUT touching business logic!

# Old database field name
{"lobbyname": "general", "limit": 10}

# New database field name (maybe you standardize to camelCase)
{"lobby_name": "general", "max_limit": 10}

# Only change: LobbyModel and LobbyMapper
# Domain Entity: UNCHANGED ✅
# Service Layer: UNCHANGED ✅
# Commands: UNCHANGED ✅
```

### 2. **Testability**
```python
# Test business logic WITHOUT database!

def test_lobby_is_full():
    # Create entity directly - no database needed!
    lobby = Lobby(
        lobby_id="123",
        name="test",
        description="Test lobby",
        max_connections=10,
        is_public=True,
        created_at=datetime.utcnow(),
        created_by="user123"
    )

    # Test business rule
    assert lobby.is_full(10) == True
    assert lobby.is_full(9) == False
    assert lobby.can_accept_connection(5) == True
```

### 3. **Database Flexibility**
```python
# Want to switch from MongoDB to PostgreSQL?

# Change ONLY the infrastructure layer:
# - LobbyModel (use SQLAlchemy model instead)
# - LobbyMapper (map differently)
# - Repository implementation (use SQLAlchemy queries)

# Domain Entity: UNCHANGED ✅
# Service Layer: UNCHANGED ✅
# Commands: UNCHANGED ✅
```

### 4. **Clear Responsibilities**
```python
# Entity:       "What are the business rules?"
# Model:        "How is this stored in the database?"
# Mapper:       "How do I convert between them?"
# Repository:   "How do I fetch/save to the database?"
# Service:      "What are the use cases?"
# Commands:     "How does the user interact with this?"
```

## When to Use Entity vs Model

### Use Single Class When:
- ✅ Simple CRUD app with no business logic
- ✅ Database schema perfectly matches business domain
- ✅ Small project (< 5 entities)
- ✅ Prototyping / MVP

### Use Entity + Model When:
- ✅ Complex business rules and validation
- ✅ Database schema differs from business domain
- ✅ Need to support multiple databases
- ✅ Large project with multiple features
- ✅ Long-term maintainability matters
- ✅ High testability requirements

## For Ari Connect Bot

**Recommendation: Use Entity + Model**

Why?
1. **Complex business rules**: Lobby capacity, user permissions, content filtering
2. **Database doesn't match domain**: `lobbyname` vs `name`, `limit` vs `max_connections`
3. **Testability**: Need to test business logic without database
4. **Future-proofing**: Might want to change database later
5. **Clarity**: Separate business concerns from database concerns

## Directory Structure

```
ari/
├── domain/                      # Pure business logic
│   ├── entities/                # Domain entities
│   │   ├── lobby.py
│   │   ├── guild.py
│   │   ├── channel.py
│   │   └── user.py
│   │
│   ├── repositories/            # Repository interfaces (abstractions)
│   │   ├── lobby_repository.py       # ILobbyRepository (ABC)
│   │   └── guild_repository.py       # IGuildRepository (ABC)
│   │
│   └── exceptions/              # Domain exceptions
│       └── lobby_exceptions.py
│
├── infrastructure/              # Database implementation
│   └── database/
│       ├── models/              # Data models (MongoDB specific)
│       │   ├── lobby_model.py
│       │   └── guild_model.py
│       │
│       ├── mappers/             # Entity ↔ Model converters
│       │   ├── lobby_mapper.py
│       │   └── guild_mapper.py
│       │
│       └── repositories/        # Repository implementations
│           ├── mongo_lobby_repository.py    # Concrete implementation
│           └── mongo_guild_repository.py
│
└── features/                    # Application features
    └── lobbies/
        ├── services/            # Uses entities only
        │   └── lobby_service.py
        └── commands/            # Uses entities only
            └── lobby_commands.py
```

## Migration Strategy

### Phase 1: Create Entities
```bash
# Create domain entities for existing dictionaries
ari/domain/entities/lobby.py
ari/domain/entities/guild.py
ari/domain/entities/channel.py
```

### Phase 2: Create Models
```bash
# Wrap existing database documents in models
ari/infrastructure/database/models/lobby_model.py
```

### Phase 3: Create Mappers
```bash
# Convert between entities and models
ari/infrastructure/database/mappers/lobby_mapper.py
```

### Phase 4: Update Repositories
```bash
# Make repositories return entities instead of dicts
# Use mappers internally
```

### Phase 5: Update Services
```bash
# Use entities instead of dicts
# Add business logic to entities
```

## Summary

| Aspect | Entity | Model |
|--------|--------|-------|
| **Purpose** | Business logic | Database storage |
| **Location** | `domain/entities/` | `infrastructure/database/models/` |
| **Knows About** | Business rules only | Database structure only |
| **Field Names** | Domain language | Database field names |
| **Dependencies** | None (pure Python) | Database library (motor, pymongo) |
| **Used By** | Services, Commands | Repositories only |
| **Example** | `max_connections`, `is_full()` | `limit`, `to_document()` |

**Golden Rule:** Your business logic should never know about your database!
