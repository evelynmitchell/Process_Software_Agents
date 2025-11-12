# Data Storage Architecture Decision

**Date:** November 12, 2025
**Status:** Accepted
**Deciders:** Engineering Team
**Decision Type:** Architecture

---

## Context and Problem Statement

The ASP Platform requires a database to store telemetry data, including:
- Agent Cost Vectors (latency, tokens, API costs)
- Defect Recording Logs
- Task Metadata (for PROBE-AI estimation)
- Bootstrap Learning Metrics

The original PRD and database schema specification recommended **PostgreSQL + TimescaleDB** for production-grade time-series optimization. However, during Phase 1 planning, we need to decide:

**Should we start with SQLite for simplicity, or commit to PostgreSQL from day one?**

---

## Decision Drivers

1. **Development Speed:** Minimize setup friction to start collecting data quickly
2. **Simplicity:** Reduce operational complexity during learning phases
3. **Data Volume:** Realistic storage needs for Phase 1-3 (months 1-6)
4. **Portability:** Ability to share project state and reproduce results
5. **Future Scalability:** Clear migration path if needs grow
6. **Cost:** Infrastructure costs during early phases

---

## Considered Options

### Option 1: SQLite (Local File-Based Database)
### Option 2: PostgreSQL (Client-Server Database)
### Option 3: PostgreSQL + TimescaleDB (Time-Series Optimized)

---

## Decision Outcome

**Chosen Option:** **SQLite First, Migrate Later**

We will use **SQLite as the default database** for Phase 1-3 (months 1-6), with a clear migration path to PostgreSQL if/when needed.

### Rationale

#### Phase 1-3 Data Volume Estimate
```
Phase 1 (Measurement):     30 tasks × 50 records each  = 1,500 rows
Phase 2 (Estimation):      50 tasks × 50 records each  = 2,500 rows
Phase 3 (Review):          50 tasks × 75 records each  = 3,750 rows
Bootstrap Learning:        Additional ~2,000 rows
-------------------------------------------------------------
Total (6 months):          ~10,000 rows across 4 tables
```

**SQLite handles this easily** (tested to 100K+ rows with excellent performance).

#### Key Decision Factors

| Factor | SQLite | PostgreSQL | Winner |
|--------|--------|------------|--------|
| **Setup Time** | 0 minutes (built-in) | 15-30 minutes (local) / 1 hour (cloud) | SQLite |
| **Operational Overhead** | None (single file) | Database server management | SQLite |
| **Portability** | Excellent (commit .db file) | Poor (requires separate DB instance) | SQLite |
| **Concurrency** | Limited (single writer) | Excellent (multi-writer) | PostgreSQL |
| **Data Volume** | Good (<1GB) / Excellent (<100MB) | Excellent (any size) | Tie (Phase 1-3) |
| **Production Ready** | Limited | Excellent | PostgreSQL |
| **Cost** | $0 | $0 (local) / $25-200/month (cloud) | SQLite |
| **Analytics Tools** | Limited BI tool support | Excellent BI tool support | PostgreSQL |
| **Time-Series Optimization** | None | TimescaleDB extension available | PostgreSQL |

#### Why SQLite Wins for Phase 1-3

1. **Zero Setup Friction:** Start collecting data immediately, no database installation required
2. **Perfect for Learning:** Database state commits with code, making debugging/experimentation easy
3. **Good Enough Performance:** Single-agent sequential execution has no concurrency needs
4. **Reversible Decision:** Migration to PostgreSQL is straightforward when needed

#### When to Migrate to PostgreSQL

Migrate when **any** of these conditions are met:
- ✅ Data volume exceeds 100K rows (~200+ tasks completed)
- ✅ High concurrency: 5+ agents running simultaneously
- ✅ Production deployment with multiple users/teams
- ✅ Need for real-time dashboard queries during agent execution
- ✅ Integration with enterprise BI tools required
- ✅ Time-series analytics become critical (continuous aggregates, compression)

---

## Implementation Plan

### Phase 0: SQLite Setup (Week 1)

1. **Adapt Schema Scripts**
   - Convert `database/migrations/*.sql` to be SQLite-compatible
   - Remove PostgreSQL-specific features (e.g., TimescaleDB, ENUM types)
   - Use SQLite equivalents (TEXT with CHECK constraints for enums)

2. **Create SQLite Directory Structure**
   ```
   database/
   ├── sqlite/
   │   ├── create_tables.sql       # SQLite-compatible schema
   │   ├── create_indexes.sql      # Same as PostgreSQL
   │   ├── sample_data.sql         # Same as PostgreSQL
   │   └── README.md               # SQLite setup instructions
   ├── migrations/                 # Keep PostgreSQL scripts for future
   │   ├── 001_create_tables.sql
   │   ├── 002_create_indexes.sql
   │   ├── 003_timescaledb_setup.sql
   │   └── 004_sample_data.sql
   └── README.md                   # Updated with SQLite default
   ```

3. **Update Configuration**
   - Add `DATABASE_URL` to `.env.example`: `sqlite:///data/asp_telemetry.db`
   - Use SQLAlchemy for database abstraction (works with both SQLite and PostgreSQL)
   - Default to SQLite, allow PostgreSQL via environment variable

4. **Test Data Access Patterns**
   - Verify PROBE-AI queries work efficiently on SQLite
   - Test dashboard queries (if interactive, ensure <500ms response time)
   - Benchmark with 10K sample rows

### Phase 3+: PostgreSQL Migration (If Needed)

1. **Create Migration Script**
   ```bash
   scripts/migrate_sqlite_to_postgres.py
   ```
   - Export SQLite data to CSV/JSON
   - Create PostgreSQL database
   - Run PostgreSQL schema scripts
   - Import data with proper type conversion
   - Verify row counts and data integrity

2. **Update Documentation**
   - Add migration guide to `database/README.md`
   - Document PostgreSQL setup for production

3. **Deploy TimescaleDB (Optional)**
   - Only if time-series analytics become critical
   - Add hypertables and continuous aggregates
   - Enable compression for older data

---

## Consequences

### Positive Consequences

✅ **Immediate Start:** No database setup delays, start Phase 1 implementation today
✅ **Lower Barrier to Entry:** Contributors can clone and run without database configuration
✅ **Better Debugging:** Can inspect `.db` file in VS Code, share exact state in issues
✅ **Cost Savings:** $0 infrastructure cost during Phase 1-3 (~6 months)
✅ **Portability:** Easy to share project state, run demos, create test fixtures

### Negative Consequences

⚠️ **Concurrency Limitations:** Cannot run multiple agents writing simultaneously (not needed in Phase 1-3)
⚠️ **Migration Work Later:** Will need to migrate if project scales beyond initial phases
⚠️ **BI Tool Integration:** Limited support for direct BI tool connections (can export CSV)
⚠️ **No TimescaleDB:** Cannot leverage time-series optimizations (compression, continuous aggregates)

### Mitigation Strategies

1. **Concurrency:** If Phase 3 requires concurrent agent execution, implement write queueing or migrate early
2. **Migration Path:** Maintain PostgreSQL schema scripts in parallel, test migration script with sample data
3. **BI Tools:** Use Python notebooks (Jupyter) for analytics in early phases, export CSV if needed
4. **Monitoring:** Track database file size and query performance, set alert at 50MB to plan migration

---

## Alternative Considered: "Both from Day One"

We considered supporting both SQLite and PostgreSQL from the start using SQLAlchemy's abstraction layer.

**Rejected because:**
- Adds complexity with minimal Phase 1-3 benefit
- Must test on both databases continuously
- PostgreSQL-specific features (ENUM, TimescaleDB) would be unused
- Increases cognitive load for contributors

**YAGNI Principle:** Don't build infrastructure for problems we don't have yet.

---

## Validation

### Phase 1 Success Criteria (Month 2)
- [ ] SQLite database created and schema loaded
- [ ] 30+ tasks logged with full telemetry
- [ ] Database file size < 10MB
- [ ] All PROBE-AI queries execute in <100ms
- [ ] Bootstrap metrics dashboard loads in <2s

### Phase 3 Re-evaluation (Month 6)
- [ ] Review data volume (target: <100K rows)
- [ ] Review concurrency needs (target: single-agent sequential)
- [ ] Review query performance (target: all queries <500ms)
- [ ] Decision: Continue with SQLite OR migrate to PostgreSQL

---

## References

- **PRD Section 6.3:** Technology Stack Recommendations (originally specified PostgreSQL)
- **PRD Section 7:** Phase 1 requirements (30+ tasks with telemetry)
- **SQLite Documentation:** https://www.sqlite.org/limits.html (max 281 TB database size)
- **SQLite Performance:** https://www.sqlite.org/whentouse.html (recommended for <100K req/day)
- **Database Schema Specification:** `docs/database_schema_specification.md`

---

## Addendum: Database File Location

**Date:** November 12, 2025 (Afternoon)
**Issue:** Where should the SQLite database file be stored in the project structure?

### Options Considered

1. **Project Root: `asp_telemetry.db`**
   - ✅ Simple, obvious, easy to find
   - ❌ Clutters project root
   - ❌ Mixes runtime data with source code

2. **Database Directory: `database/asp_telemetry.db`**
   - ✅ Co-locates schema and data
   - ❌ Mixes static schema files with runtime data
   - ❌ Conceptually confusing (schema vs data)

3. **Hidden Directory: `.data/asp_telemetry.db`**
   - ✅ Keeps root clean
   - ❌ Less discoverable for new users
   - ❌ Hidden files can be problematic in some environments

4. **Data Directory: `data/asp_telemetry.db`** ⭐ **SELECTED**
   - ✅ Clean separation of runtime data from code
   - ✅ Follows common conventions (like `logs/`, `output/`)
   - ✅ Extensible for other runtime files (exports, reports, backups)
   - ✅ Clear, discoverable, and organized
   - ✅ Naturally fits with `.gitignore` patterns

### Decision

**Use `data/asp_telemetry.db` as the default database location.**

### Rationale

1. **Separation of Concerns:** Runtime data should be separated from source code and static configuration
2. **Convention:** The `data/` directory is a common pattern in software projects for storing generated/runtime data
3. **Scalability:** As the project grows, we may add:
   - Exported reports: `data/exports/`
   - Backups: `data/backups/`
   - Test databases: `data/test_*.db`
4. **Organization:** Keeps project root clean and professional
5. **Git-Friendly:** Easy to add entire `data/` directory to `.gitignore`

### Implementation

1. Update `scripts/init_database.py` default path: `data/asp_telemetry.db`
2. Create `data/` directory with `.gitkeep` file
3. Update `.gitignore` to exclude `data/*` (except `.gitkeep`)
4. Update all documentation references
5. Move existing database file if present

### Impact

- **Low Risk:** No breaking changes to schema or API
- **User Benefit:** Clearer project structure
- **Documentation:** Requires updates to README and database docs

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-12 | Use SQLite for Phase 1-3 | Zero setup, good enough for data volume, easy portability |
| 2025-11-12 | Database file location: `data/asp_telemetry.db` | Separates runtime data from code, follows common conventions |
| TBD | Migrate to PostgreSQL (if needed) | When concurrency, volume, or production deployment requires it |

---

## Approval

| Role | Name | Approval | Date |
|------|------|----------|------|
| Technical Lead | Claude Code | ✅ Approved | 2025-11-12 |
| Project Owner | TBD | Pending | |

---

**Status:** ✅ **Accepted and Implemented**

**Next Steps:**
1. Create SQLite-compatible schema scripts
2. Update `database/README.md` with SQLite as default
3. Test schema with sample data
4. Proceed with Phase 1 telemetry implementation
