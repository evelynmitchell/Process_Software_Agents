# Observability Platform Evaluation for ASP System

**Date:** November 11, 2025
**Purpose:** Evaluate observability platforms for Phase 1 (ASP0 - Measurement Foundation)
**Decision Required:** Select platform for Agent Cost Vector and Defect Log telemetry

---

## Requirements Summary

Based on PRD Section 4.2 (FR-9, FR-10) and Section 6, the observability platform must:

1. **Capture Agent Cost Vector** (FR-9):
   - Computational cost: Processing latency (ms), memory usage
   - Financial cost: API call costs, token usage (input/output)
   - Task cost: Tool calls, self-correction loops

2. **Log Defect Data** (FR-10):
   - Defect ID, Task ID, Defect Type (from taxonomy)
   - Phase Injected, Phase Removed (agent roles)
   - Effort to Fix Vector, Description

3. **Support Bootstrap Learning** (Section 14):
   - Track accuracy metrics for 5 bootstrap capabilities
   - Support dashboard visualization (FR-23, FR-24)
   - Monthly recalibration queries

4. **Performance Requirements** (Section 5):
   - NFR-3: Telemetry write latency <100ms (async)
   - NFR-6: Support 100,000+ execution records with <1s query time

---

## Option 1: Langfuse

### Overview
Open-source LLM engineering platform with deep observability for AI agents. MIT license with enterprise features available.

### Pros

** Purpose-Built for AI Agents:**
- Native support for multi-agent workflows (LangGraph, CrewAI, AutoGen)
- Traces entire agent sessions with hierarchical spans (API calls, tool usage, reasoning steps)
- Built-in cost tracking per model/generation with dashboard breakdowns

** Rich Feature Set:**
- Prompt management and versioning (matches our FR-12 Process Scripts requirement)
- Evaluation framework (useful for bootstrap learning validation)
- Session replay for debugging (matches FR-22 execution traceability)

** Flexible Deployment:**
- Self-hosted option (full data control, no vendor lock-in)
- Cloud-hosted option (fast setup, managed infrastructure)
- SDK-based integration (Python, TypeScript) - typically 2-4 hours setup

** Cost-Effective:**
- Open-source core (MIT license)
- Free tier: 50k units/month, 2 users
- Startup tier: $25-500/month (suitable for Phase 1-2)
- Enterprise: $2,000-10,000+/month (Phase 4-5)

** Strong Ecosystem:**
- Active development and community
- Integrations with major frameworks
- Good documentation

### Cons

** Learning Curve:**
- Requires understanding of Langfuse's trace/span model
- May need custom instrumentation for ASP-specific metrics (Semantic Complexity, Defect Type)

** Schema Flexibility:**
- Optimized for LLM traces, may require workarounds for defect logging
- Custom metadata fields limited compared to raw database

** Query Capabilities:**
- Dashboard-focused, complex analytics may require exporting data
- Limited support for custom aggregations (e.g., defect density by component)

### Effort Estimate

| Task | Estimated Hours |
|------|----------------|
| Setup (cloud or self-hosted) | 4-8 hours |
| SDK integration (7 agents) | 16-24 hours |
| Custom instrumentation (Semantic Complexity, Defect Types) | 16-32 hours |
| Dashboard configuration | 8-16 hours |
| **Total** | **44-80 hours (1-2 weeks)** |

### Recommendation Fit
**Best for:** Teams prioritizing fast time-to-value, rich out-of-box features, and strong agent framework integration.

---

## Option 2: AgentOps

### Overview
Python SDK for AI agent monitoring with focus on session replays and multi-agent visualization. Free to start with cloud-only deployment.

### Pros

** Agent-Centric Design:**
- Time-travel debugging and session replay (excellent for understanding agent behavior)
- Multi-agent workflow visualization (useful for TSP Orchestrator debugging)
- Real-time monitoring of cost, token usage, latency

** Easy Integration:**
- Extremely fast setup (minutes via LiteLLM)
- Native integration with CrewAI, Langchain, AutoGen, OpenAI Agents SDK
- Python SDK aligns with our Python-only decision (Q1)

** Cost-Effective:**
- Free to get started
- "Flexibility at scale" pricing (unclear exact tiers, but competitive)

** Session-Based Model:**
- Natural fit for tracking agent "tasks" as sessions
- Good for tracking failure patterns and multi-agent interactions

### Cons

** Python-Only, Cloud-Only:**
- No self-hosting option (vendor lock-in, data privacy concerns)
- Forces cloud dependency (may not meet enterprise security requirements)

** Smaller Ecosystem:**
- Less mature than Langfuse (fewer integrations, smaller community)
- Limited documentation compared to Langfuse

** Limited Customization:**
- Unclear if defect taxonomy and custom metrics are supported
- May not support complex bootstrap learning queries

** Pricing Uncertainty:**
- "Flexibility at scale" is vague - unclear costs for 100k+ records
- Risk of unexpected cost scaling

** Query Capabilities:**
- Focus on session replay/debugging, not analytics
- May require data export for bootstrap learning analysis

### Effort Estimate

| Task | Estimated Hours |
|------|----------------|
| Setup (cloud only) | 1-2 hours |
| SDK integration (7 agents) | 8-16 hours |
| Custom instrumentation (if supported) | 16-40 hours (high uncertainty) |
| Dashboard configuration | 4-8 hours |
| **Total** | **29-66 hours (1-1.5 weeks)** |

### Recommendation Fit
**Best for:** Teams prioritizing fast prototyping and debugging, willing to accept cloud-only dependency.

---

## Option 3: Custom PostgreSQL + TimescaleDB

### Overview
Build custom telemetry system using PostgreSQL (relational) + TimescaleDB (time-series extension). Full control over schema and queries.

### Pros

** Complete Control:**
- Design schema exactly to ASP requirements (Agent Cost Vector, Defect Log)
- No vendor lock-in, no API limits
- Can extend indefinitely (e.g., add Bootstrap Metrics tables)

** Optimal for Analytics:**
- SQL enables any query/aggregation for bootstrap learning
- Native support for time-series analysis (TimescaleDB)
- Easy integration with data science tools (Jupyter, pandas, scikit-learn for PROBE-AI)

** Cost-Effective at Scale:**
- No per-event pricing
- Cloud hosting: $25-200/month (AWS RDS, DigitalOcean Managed PostgreSQL)
- Self-hosted: Free (except infrastructure)

** Familiar Technology:**
- SQL is widely known (lower learning curve for queries)
- Mature ecosystem (ORMs like SQLAlchemy, visualization tools like Grafana)

** Production-Ready:**
- PostgreSQL is battle-tested for high-volume transactional systems
- TimescaleDB optimized for time-series (perfect for Cost Vector logs)

### Cons

** High Initial Effort:**
- Must design and implement all schemas from scratch
- Must build instrumentation layer (Python decorator/context manager for telemetry)
- Must build dashboards (Grafana or custom React app)

** No Agent-Specific Features:**
- No trace visualization like Langfuse/AgentOps
- No prompt management, session replay, or built-in agent debugging
- Requires building everything from first principles

** Maintenance Burden:**
- Responsible for schema migrations, backup/restore, performance tuning
- Must handle TimescaleDB-specific operations (compression, retention policies)

** Slower Time-to-Value:**
- Weeks to reach feature parity with Langfuse/AgentOps
- Risk of scope creep (building dashboards, alert systems, etc.)

### Effort Estimate

| Task | Estimated Hours |
|------|----------------|
| Schema design (Agent Cost Vector + Defect Log) | 8-16 hours |
| Database setup (TimescaleDB, indexing, partitioning) | 8-16 hours |
| Instrumentation library (Python decorators, async logging) | 24-40 hours |
| Agent integration (7 agents) | 16-24 hours |
| Basic dashboard (Grafana or custom) | 24-40 hours |
| Testing and optimization | 16-24 hours |
| **Total** | **96-160 hours (3-5 weeks)** |

### Recommendation Fit
**Best for:** Teams with strong database expertise, requiring full control and custom analytics, willing to invest upfront.

---

## Comparison Matrix

| Criteria | Langfuse | AgentOps | Custom PostgreSQL + TimescaleDB |
|----------|----------|----------|----------------------------------|
| **Setup Time** | 1-2 weeks | 1-1.5 weeks | 3-5 weeks |
| **Time-to-Value** | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐ Fast | ⭐⭐ Slow |
| **Agent Framework Integration** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐ Good | ⭐⭐ Manual |
| **Custom Metrics Support** | ⭐⭐⭐ Good (via metadata) | ⭐⭐ Limited | ⭐⭐⭐⭐⭐ Full control |
| **Analytics/Query Power** | ⭐⭐⭐ Dashboard-focused | ⭐⭐ Limited | ⭐⭐⭐⭐⭐ SQL unlimited |
| **Self-Hosting Option** | ⭐⭐⭐⭐⭐ Yes (MIT) | ⭐ No (cloud-only) | ⭐⭐⭐⭐⭐ Full control |
| **Cost (Phase 1-2)** | $0-500/month | $0-?/month | $25-200/month |
| **Cost at Scale (100k+ events)** | $500-2000/month | Unknown | $100-500/month |
| **Maintenance Burden** | ⭐⭐⭐⭐⭐ Low | ⭐⭐⭐⭐⭐ Low (cloud) | ⭐⭐ High (self-managed) |
| **Vendor Lock-In Risk** | ⭐⭐⭐⭐ Low (self-host option) | ⭐⭐ High (cloud-only) | ⭐⭐⭐⭐⭐ None |
| **Data Privacy/Control** | ⭐⭐⭐⭐⭐ Full (self-host) | ⭐⭐ Cloud-only | ⭐⭐⭐⭐⭐ Full |
| **Bootstrap Learning Support** | ⭐⭐⭐ Export + analysis | ⭐⭐ Limited | ⭐⭐⭐⭐⭐ Native SQL |
| **Debugging Features** | ⭐⭐⭐⭐⭐ Trace visualization | ⭐⭐⭐⭐⭐ Session replay | ⭐⭐ Requires custom tooling |
| **Ecosystem Maturity** | ⭐⭐⭐⭐ Strong | ⭐⭐⭐ Growing | ⭐⭐⭐⭐⭐ PostgreSQL mature |

---

## Decision Framework

### If You Prioritize:

**Fast MVP and Agent Debugging → Choose Langfuse**
- Rich out-of-box features for agent observability
- Self-hosting option provides data control
- Balance of speed and flexibility

**Fastest Setup with Minimal Effort → Choose AgentOps**
- Minutes to integrate
- Good for prototyping and Phase 0.5 bootstrap
- Accept cloud-only limitation

**Long-Term Control and Custom Analytics → Choose PostgreSQL + TimescaleDB**
- Perfect fit for bootstrap learning queries
- No vendor constraints
- Higher upfront investment pays off in Phase 3+

### Hybrid Approach (Recommended for ASP)

**Phase 0.5 - 1 (Months 1-3): Start with Langfuse**
- Get fast telemetry for bootstrap learning
- Use Langfuse free tier or self-hosted
- Instrument all 7 agents quickly
- Validate ASP framework basics

**Phase 2-3 (Months 4-6): Evaluate Migration to Custom DB**
- Once requirements are stable, assess if Langfuse limitations are blocking
- If complex bootstrap queries are needed, migrate to TimescaleDB
- Use Langfuse data export to seed TimescaleDB

**Phase 4+ (Months 7+): Maintain or Hybrid**
- Option A: Keep Langfuse for trace visualization + Add PostgreSQL for analytics
- Option B: Full migration to custom DB + Build custom dashboards

---

## Recommendation

**Primary Recommendation: Langfuse (Self-Hosted)**

**Rationale:**
1. **Fastest time-to-value** for Phase 1 (1-2 weeks vs. 3-5 weeks for custom)
2. **Self-hosting option** addresses data privacy and vendor lock-in concerns
3. **Native agent framework support** reduces integration effort
4. **Prompt versioning** aligns with FR-12 (Process Scripts)
5. **Migration path exists** if we outgrow it (export to PostgreSQL later)

**Implementation Plan:**
1. Start with Langfuse Cloud (free tier) for rapid prototyping (Week 1)
2. Migrate to self-hosted Langfuse once validated (Week 2-3)
3. Instrument Planning Agent first, validate telemetry (Week 3-4)
4. Roll out to remaining 6 agents (Week 4-6)
5. Re-evaluate after 30 tasks (Month 3) - migrate to custom DB if needed

**Backup Plan:**
If Langfuse proves insufficient for bootstrap learning analytics (e.g., complex defect density queries), we can export data to PostgreSQL/TimescaleDB for analysis while keeping Langfuse for trace visualization (hybrid approach).

---

## Next Steps

- [ ] Get stakeholder approval for Langfuse recommendation
- [ ] Set up Langfuse Cloud account (free tier)
- [ ] Run proof-of-concept with Planning Agent (1 week)
- [ ] Document instrumentation patterns
- [ ] Evaluate self-hosted deployment if PoC succeeds

---

**Document Prepared By:** Claude Code
**Review Status:** Draft - Awaiting Approval
**Version:** 1.0
