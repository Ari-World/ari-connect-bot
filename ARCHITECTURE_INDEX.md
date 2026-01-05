# Architecture Documentation Index

This index helps you navigate all the architecture documentation for the Ari Connect bot.

## 📚 Documentation Overview

### For Understanding the Current Codebase

1. **[CLAUDE.md](CLAUDE.md)** - Start here!
   - How to run the bot
   - Current architecture overview
   - Database structure
   - Environment configuration
   - **Read this first** if you're new to the project

### For Learning Clean Architecture

2. **[LAYERS_GUIDE.md](LAYERS_GUIDE.md)** - Architectural layers explained
   - What are the different layers? (Domain, Application, Infrastructure, Presentation)
   - What goes in each layer?
   - How do layers interact?
   - The dependency rule
   - **Read this** to understand clean architecture principles

3. **[DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md)** - Entity vs Model separation
   - Difference between Domain Entities and Data Models
   - Why separate them?
   - How to map between them?
   - When to use each approach?
   - **Read this** to understand the Entity/Model pattern

### For Improving the Codebase

4. **[REFACTORING_GUIDE.md](REFACTORING_GUIDE.md)** - Code smells & refactoring roadmap
   - Critical issues in current code
   - Code smells identified
   - Refactoring priorities
   - Phase-by-phase migration plan
   - Quick wins you can do today
   - **Read this** to understand what needs improvement

5. **[ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md)** - Concrete before/after example
   - Real code example showing current vs proposed architecture
   - Complete lobby feature migration
   - Line-by-line code examples
   - Testing examples
   - **Read this** to see exactly how to refactor

---

## 🎯 Quick Navigation by Topic

### "I want to understand..."

| Topic | Document | Section |
|-------|----------|---------|
| How the bot works currently | [CLAUDE.md](CLAUDE.md) | Architecture Overview |
| What clean architecture is | [LAYERS_GUIDE.md](LAYERS_GUIDE.md) | The Layer Pyramid |
| Entity vs Model | [DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md) | Quick Answer |
| What's wrong with current code | [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) | Critical Issues |
| How to refactor properly | [ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md) | Proposed Architecture |

### "I want to do..."

| Task | Document | Section |
|------|----------|---------|
| Set up the development environment | [CLAUDE.md](CLAUDE.md) | Environment Configuration |
| Fix naming issues | [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) | Quick Wins |
| Create a domain entity | [DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md) | Domain Entity Example |
| Implement a repository | [LAYERS_GUIDE.md](LAYERS_GUIDE.md) | Infrastructure Layer |
| Write a Discord command | [LAYERS_GUIDE.md](LAYERS_GUIDE.md) | Presentation Layer |
| Understand testing strategy | [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) | Testing Strategy |

### "I'm working on..."

| Feature | Start With | Then Read |
|---------|-----------|-----------|
| Lobby management | [ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md) | [DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md) |
| Message broadcasting | [LAYERS_GUIDE.md](LAYERS_GUIDE.md) | [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) |
| Database changes | [DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md) | [CLAUDE.md](CLAUDE.md) - Database Layer |
| New Discord commands | [LAYERS_GUIDE.md](LAYERS_GUIDE.md) - Presentation | [ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md) |

---

## 📖 Reading Order by Role

### New Developer (Just Joined the Project)

1. **[CLAUDE.md](CLAUDE.md)** - Understand current setup
2. **[LAYERS_GUIDE.md](LAYERS_GUIDE.md)** - Learn architecture concepts
3. **[ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md)** - See concrete examples
4. **[REFACTORING_GUIDE.md](REFACTORING_GUIDE.md)** - Know what to improve

### Experienced Developer (Refactoring)

1. **[REFACTORING_GUIDE.md](REFACTORING_GUIDE.md)** - Identify problems
2. **[DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md)** - Understand Entity/Model
3. **[ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md)** - See how to refactor
4. **[LAYERS_GUIDE.md](LAYERS_GUIDE.md)** - Reference for layer responsibilities

### Architect / Tech Lead

1. **[REFACTORING_GUIDE.md](REFACTORING_GUIDE.md)** - Review roadmap
2. **[LAYERS_GUIDE.md](LAYERS_GUIDE.md)** - Validate architecture
3. **[DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md)** - Review domain design
4. **[ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md)** - Verify implementation

---

## 🔍 Key Concepts Cross-Reference

### Concept: Domain Entity

- **Definition:** [DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md) - "Domain Entity (Pure Business Logic)"
- **Layer:** [LAYERS_GUIDE.md](LAYERS_GUIDE.md) - "Domain Layer"
- **Example:** [ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md) - "Domain Entity"
- **Problem:** [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - "Missing Domain Models"

### Concept: Repository Pattern

- **Interface:** [LAYERS_GUIDE.md](LAYERS_GUIDE.md) - "Domain Layer" → Repository Interfaces
- **Implementation:** [LAYERS_GUIDE.md](LAYERS_GUIDE.md) - "Infrastructure Layer"
- **Example:** [ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md) - "Repository (Data Access)"
- **Current Issues:** [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - "Missing Abstraction Layer"

### Concept: Service Layer

- **Definition:** [LAYERS_GUIDE.md](LAYERS_GUIDE.md) - "Application Layer"
- **Example:** [ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md) - "Service (Business Logic)"
- **Problem:** [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - "God Object Anti-Pattern"

### Concept: Dependency Injection

- **Explanation:** [LAYERS_GUIDE.md](LAYERS_GUIDE.md) - "The Dependency Rule"
- **Problem:** [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - "No Dependency Injection"
- **Example:** [ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md) - "Feature Bootstrap"

### Concept: Data Mapping

- **Why:** [DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md) - "Benefits of Entity + Model Separation"
- **How:** [DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md) - "Mapper (Converts Between Entity and Model)"
- **Example:** [ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md) - "Mapper (Entity ↔ Model)"

---

## 🚀 Implementation Checklist

Use this when implementing a new feature following clean architecture:

### ✅ Phase 1: Domain Design
- [ ] Read: [DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md)
- [ ] Create domain entity with business rules
- [ ] Define repository interface
- [ ] Add domain exceptions

### ✅ Phase 2: Infrastructure
- [ ] Read: [LAYERS_GUIDE.md](LAYERS_GUIDE.md) - Infrastructure Layer
- [ ] Create data model (MongoDB representation)
- [ ] Create mapper (Entity ↔ Model)
- [ ] Implement repository

### ✅ Phase 3: Application
- [ ] Read: [LAYERS_GUIDE.md](LAYERS_GUIDE.md) - Application Layer
- [ ] Create service with use cases
- [ ] Add dependency injection
- [ ] Handle orchestration logic

### ✅ Phase 4: Presentation
- [ ] Read: [LAYERS_GUIDE.md](LAYERS_GUIDE.md) - Presentation Layer
- [ ] Create Discord commands
- [ ] Add input validation
- [ ] Format output (embeds)

### ✅ Phase 5: Testing
- [ ] Read: [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - Testing Strategy
- [ ] Write domain entity tests
- [ ] Write service tests (with mocks)
- [ ] Write integration tests

---

## 🎓 Learning Path

### Beginner → Intermediate

**Week 1: Understand Current System**
- Day 1-2: Read [CLAUDE.md](CLAUDE.md) thoroughly
- Day 3-4: Explore codebase, identify patterns
- Day 5-7: Read [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - Critical Issues

**Week 2: Learn Clean Architecture**
- Day 1-3: Study [LAYERS_GUIDE.md](LAYERS_GUIDE.md)
- Day 4-5: Study [DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md)
- Day 6-7: Analyze [ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md)

**Week 3: Practice**
- Implement one small feature using clean architecture
- Follow the Implementation Checklist above
- Get code review from senior dev

### Intermediate → Advanced

**Month 1: Refactor Existing Code**
- Week 1: Fix Quick Wins from [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md)
- Week 2-3: Migrate one feature (e.g., Lobbies)
- Week 4: Write comprehensive tests

**Month 2-3: Full Migration**
- Follow Phase-by-Phase Roadmap in [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md)
- Migrate all features to clean architecture
- Achieve 75%+ test coverage

---

## 📝 Document Summaries

### CLAUDE.md (Current State)
**Purpose:** Onboarding and current architecture reference
**Audience:** All developers
**Length:** ~200 lines
**Topics:**
- How to run the bot
- Environment variables
- Current file structure
- Database collections
- Known issues

### LAYERS_GUIDE.md (Concepts)
**Purpose:** Teach clean architecture layers
**Audience:** Developers learning architecture
**Length:** ~800 lines
**Topics:**
- 4 layers explained in detail
- Dependency rule
- Responsibilities per layer
- Code examples for each layer
- Common mistakes

### DOMAIN_MODELING_GUIDE.md (Pattern)
**Purpose:** Explain Entity vs Model separation
**Audience:** Developers implementing features
**Length:** ~600 lines
**Topics:**
- Domain entities vs data models
- Why separate them
- Mapper pattern
- Complete working examples
- When to use which approach

### REFACTORING_GUIDE.md (Action Plan)
**Purpose:** Identify problems and provide roadmap
**Audience:** Developers refactoring code
**Length:** ~800 lines
**Topics:**
- 10 critical code smells
- Feature-based architecture proposal
- 5-phase refactoring roadmap
- Quick wins
- Architecture principles

### ARCHITECTURE_EXAMPLE.md (Practice)
**Purpose:** Show before/after refactoring
**Audience:** Developers wanting concrete examples
**Length:** ~600 lines
**Topics:**
- Current code problems
- Proposed solution with full code
- Step-by-step migration
- Testing examples
- 12-hour migration estimate

---

## 🔗 External Resources

### Clean Architecture
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)

### Python Best Practices
- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

### Discord.py
- [discord.py Documentation](https://discordpy.readthedocs.io/)
- [discord.py Examples](https://github.com/Rapptz/discord.py/tree/master/examples)

### Testing
- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

---

## 💡 Quick Tips

### When Starting a New Feature
1. Design domain entity first (business rules)
2. Define repository interface
3. Implement service (use cases)
4. Create command (presentation)
5. Write tests

### When Fixing a Bug
1. Identify which layer the bug is in
2. Write a failing test
3. Fix in appropriate layer
4. Ensure test passes

### When Refactoring
1. Write tests for existing behavior
2. Refactor one layer at a time
3. Ensure tests still pass
4. Commit frequently

---

## 📊 Documentation Status

| Document | Status | Last Updated | Completeness |
|----------|--------|--------------|--------------|
| CLAUDE.md | ✅ Complete | Current | 100% |
| LAYERS_GUIDE.md | ✅ Complete | Current | 100% |
| DOMAIN_MODELING_GUIDE.md | ✅ Complete | Current | 100% |
| REFACTORING_GUIDE.md | ✅ Complete | Current | 100% |
| ARCHITECTURE_EXAMPLE.md | ✅ Complete | Current | 100% |
| ARCHITECTURE_INDEX.md | ✅ Complete | Current | 100% |

---

## 🤝 Contributing to Documentation

When adding new documentation:
1. Add it to this index
2. Update cross-references in other documents
3. Add to appropriate reading order sections
4. Update the Quick Navigation table

When you update existing documentation:
1. Update "Last Updated" in status table
2. Review cross-references
3. Ensure examples are still accurate

---

## ❓ FAQ

**Q: I'm new. Where do I start?**
A: Read [CLAUDE.md](CLAUDE.md) first, then [LAYERS_GUIDE.md](LAYERS_GUIDE.md)

**Q: How do I implement a new feature?**
A: Follow the Implementation Checklist above, using [ARCHITECTURE_EXAMPLE.md](ARCHITECTURE_EXAMPLE.md) as reference

**Q: What's wrong with the current code?**
A: See [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - Critical Issues

**Q: Entity vs Model - what's the difference?**
A: See [DOMAIN_MODELING_GUIDE.md](DOMAIN_MODELING_GUIDE.md) - Quick Answer

**Q: How long will refactoring take?**
A: See [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - Refactoring Roadmap (estimate: 9-10 weeks)

**Q: Can I mix old and new architecture during migration?**
A: Yes! See [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - Migration Strategy (Strangler Fig Pattern)

---

**Need help?** Join the [support server](https://discord.gg/HnjyK33cJp) or open an issue on GitHub.
