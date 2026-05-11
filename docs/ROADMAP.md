# Roadmap – ECM_002_StatefulClaude

**Future directions and planned features**

---

## Current Status – v0.1.0

**Release Date:** 2026-05-11  
**Status:** ✅ Production Ready  
**License:** MIT  

### What v0.1.0 Includes
- 5-phase action capture system (bash, SSH, Fossil, files, system)
- SQLite3 FTS5 searchable database (RAM disk + SSD backup)
- 9 automated cron jobs (zero manual intervention)
- Comprehensive documentation (6 markdown files)
- Prompt-based installer for Claude Code CLI
- Health monitoring and troubleshooting guides
- Full source code and architecture documentation

### Supported Systems
- **Claude Code CLI** (primary target)
- Linux/Ubuntu (tested)
- Bash 4.0+
- Python 3.7+
- SQLite 3.9.0+ (FTS5 support)

---

## Planned – v0.2.0

**Target:** 2026-Q3 2026  
**Goal:** Multi-AI Support

### Features
- **ChatGPT API call logging**
  - Capture all API requests and responses
  - Track model versions, temperature, token usage
  - Store in same FTS5 database as Claude activity
  - Query: "What prompts did I send to GPT-4? When? How much did it cost?"

- **API Activity Phase (Phase 6)**
  - New capture: `/var/www/html/PQ/0510/ecm-ingest-api-calls.py`
  - Log format: timestamp | model | token_input | token_output | cost | response_time | status
  - Searchable metadata: model name, temperature, tokens, cost

- **Unified Search**
  - Search across Claude activity + ChatGPT activity simultaneously
  - "Show me all times I asked both Claude and ChatGPT the same question"
  - Correlation queries: "Which model was faster? More accurate? Cost-effective?"

- **Cost Tracking**
  - Dashboard showing ChatGPT spending over time
  - Alerts for high-cost sessions
  - ROI analysis: "Time saved vs cost"

### Implementation
- New Python module: `ecm-api-activity.py` (GPT-specific)
- Generic API abstraction layer for future expansion
- Integration tests with mock API responses
- Documentation: new section in PHASES.md

---

## Planned – v0.3.0

**Target:** 2026-Q4 2026  
**Goal:** Semantic Search with Vector Embeddings

### Features
- **Vector Embeddings**
  - Convert all captured activity into semantic vectors
  - Models supported:
    - **MiniLM-L6-v2** (384-dim) – fast, lightweight
    - **all-mpnet-base-v2** (768-dim) – balance
    - **all-mpnet-large-v2** (1024-dim) – high quality
  - Concatenate to 2,176-dim vectors for maximum expressiveness

- **Semantic Search**
  - Query by meaning, not keywords
  - Example: "Show me times I was debugging authentication"
    - Captures: failed login attempts, auth.log parsing, code changes to auth module, SSH failures
    - Not just keyword matches – understands intent
  
- **Activity Clustering**
  - Group related activities by semantic similarity
  - Example: "Find all sessions where I worked on database optimization"
  - Automatic project/topic detection without explicit tags

- **Context Retrieval for AI**
  - When you ask Claude Code "What was I working on?", automatically retrieve semantically similar previous sessions
  - Semantic ranking: most relevant context first
  - No need to remember keywords or dates

- **Anomaly Detection**
  - Find unusual activity patterns
  - Example: "Show me times I accessed unusual directories"
  - Security: "Detect SSH attempts from unfamiliar hosts"

### Implementation
- New table: `ecm_embeddings` (FTS5 vectors table)
- Batch processing: embed 100 records at a time
- Caching: store vectors to avoid re-computation
- Integration with existing FTS5 search (hybrid: keyword + semantic)
- Documentation: new section SEMANTIC_SEARCH.md

### Trade-offs
- **Storage:** 2,176-dim vectors × 100K records = ~800 MB additional storage
- **Processing:** One-time cost to embed 100K records (~2 hours)
- **Speed:** Vector search slightly slower than FTS5 (still <100ms)
- **Value:** Enables "find by meaning" which keyword search can't do

---

## Planned – v1.0.0

**Target:** 2027-Q1 2027  
**Goal:** Stable Release, Multi-AI API

### Features
- **Stable Public API**
  - REST endpoints for querying ECM data
  - Authentication token support
  - Rate limiting
  - Version pinning (v1, v2, etc.)
  - OpenAPI/Swagger documentation

- **Support for All AI Systems**
  - Claude (Claude Code CLI, claude.ai web, API)
  - ChatGPT (web + API)
  - Google Gemini (web + API)
  - Ollama (local LLMs)
  - LLaMA 2 (local)
  - Anthropic Workbench (when available)

- **Unified Activity Database**
  - Single searchable repository for ALL your AI interactions
  - "Show me every time I asked ANY AI system about OAuth"
  - Compare which AI performed best for different task types
  - Track learning: "How has my prompting improved over 6 months?"

- **Long-Term Context Window**
  - Infinite external context for any AI system
  - Upload conversation history to Claude: "Remember this, I'll reference it later"
  - No more "I don't have context from previous sessions"
  - Persistent, searchable, private (on-device)

- **Self-Hosted Deployment**
  - Docker container with pre-built database
  - Datasette UI for web-based search
  - Optional S3 backup to cloud storage
  - Grafana dashboards for usage analytics

- **Community Plugins**
  - Language support (capture code changes in specific languages)
  - Tool integration (capture Slack messages, emails, calendar events)
  - Framework-specific (Django, React, etc. project structure awareness)
  - Custom capture phases written by users

### Release Quality
- ✅ Full test suite (unit + integration + end-to-end)
- ✅ Security audit (third-party penetration test)
- ✅ Performance benchmarks (query latency SLAs)
- ✅ Documentation (API guide, deployment guide, examples)
- ✅ Stable versioning (semantic versioning)
- ✅ Backward compatibility guarantees

---

## Extension Pathways for Community

### 1. New Capture Phases

**Template:** Create a new ingest script following this pattern:

```bash
# Phase N: [YourFeature]Capture

# 1. Create capture script
/var/www/html/PQ/0510/ecm-capture-yourfeature.py
  → Read from source (API, file, system)
  → Write to /tmp/ecm-yourfeature.log
  → Format: timestamp|actor|target|details_json

# 2. Create ingest script
/var/www/html/PQ/0510/ecm-ingest-yourfeature.py
  → Read /tmp/ecm-yourfeature.log
  → Compute content hash
  → Check for duplicates
  → INSERT into ecm_actions + ecm_actions_details
  → Update /tmp/ecm-yourfeature-ingest-state.json

# 3. Add cron job
# */5 * * * * /usr/bin/python3 /var/www/html/PQ/0510/ecm-ingest-yourfeature.py

# 4. Document in docs/PHASES.md
```

**Examples of community-built phases:**
- Phase 6: IDE activity (VS Code, JetBrains editors)
- Phase 7: Git commits (GitHub, GitLab, Gitea)
- Phase 8: Slack messages (personal workspace)
- Phase 9: Email activity (subject, sender, timestamp)
- Phase 10: Calendar events (meetings, blocked time)
- Phase 11: Document edits (Google Docs, Notion)
- Phase 12: Code review (pull request comments, reviews)

### 2. Custom Search Interfaces

**Template:** Create a web UI querying the ECM database

```bash
# Static HTML file
/var/www/html/PQ/0510/ecm-search-yourinterface.html

# Features you can build:
- Timeline visualization (activity over time)
- Heat map (when are you most productive?)
- Word cloud (what topics do you work on?)
- Dependency graph (which files are you modifying together?)
- Network graph (which hosts do you SSH to? frequency?)
```

**Examples:**
- GitHub-style contribution calendar (bash commands per day)
- Gantt chart (project timelines inferred from commits)
- Sankey diagram (command flow: where you run commands → where files change)
- 3D activity visualization (time × action_type × system_load)

### 3. Analysis Tools

**Template:** Create Python scripts that query ECM and produce insights

```bash
# Example: Productivity analyzer
/var/www/html/PQ/0510/ecm-analyze-productivity.py
  → Query: commands per hour, success rate, peak times
  → Output: JSON report
  → Use case: "When am I most productive?"

# Example: Security auditor
/var/www/html/PQ/0510/ecm-audit-security.py
  → Query: SSH failures, unusual file access patterns
  → Output: risk report with recommendations
  → Use case: "Am I accessing unusual resources?"

# Example: Learning tracker
/var/www/html/PQ/0510/ecm-track-learning.py
  → Query: new commands over time, error rates
  → Output: skill development graph
  → Use case: "How much have I learned about Docker?"
```

### 4. Integration Bridges

**Template:** Connect ECM with external systems

```bash
# Export to external tools:

# To Grafana
/var/www/html/PQ/0510/ecm-export-grafana.py
  → Query ECM
  → Push to Grafana API
  → Create dashboards

# To Slack
/var/www/html/PQ/0510/ecm-export-slack.py
  → Query ECM
  → Post daily summary to channel
  → "You ran 150 commands today, 92% success rate"

# To GitHub Wiki
/var/www/html/PQ/0510/ecm-export-wiki.py
  → Query ECM
  → Auto-generate documentation from commits + file changes
  → "Here's what I shipped this week"
```

---

## How to Contribute

### Report a Bug
1. Search: Has this been reported?
2. Create issue with: reproduction steps, expected behavior, actual behavior
3. Include: ECM version, OS, log files from `/tmp/ecm-*.log`

### Request a Feature
1. Describe: What would it enable you to do?
2. Explain: How would you use it?
3. Estimate: Is it v0.2, v0.3, v1.0 material?

### Contribute Code
1. Fork repository
2. Create feature branch: `feature/your-feature-name`
3. Write code + tests
4. Submit PR with description
5. PR requirements:
   - Passes tests (`pytest tests/`)
   - Follows PEP 8 (Python) or Bash style guide
   - Includes documentation
   - One feature per PR (keep scope focused)

### Contribute Documentation
1. Identify: What's unclear or missing?
2. Write: Clear examples with queries
3. Test: Verify examples actually work
4. Submit: PR to docs/ directory

### Contribute a Phase
1. Design: What will you capture?
2. Build: Capture + ingest scripts
3. Test: Run for 24 hours, verify data quality
4. Document: Add to docs/PHASES.md
5. Submit: PR with all scripts + documentation

---

## Design Principles (Won't Change)

### Privacy First
- All data stays on your machine
- No external APIs (except optional cloud backup)
- You own your memory
- No ads, no tracking, no monetization

### Simplicity
- Single SQLite database (no postgres, no elasticsearch)
- Bash + Python (no external dependencies)
- Readable code (easy to fork and modify)
- Clear architecture (easy to extend)

### Reliability
- Cron automation (no manual intervention)
- State tracking (resume capability)
- Content-hash deduplication (no duplicates)
- Health monitoring (know when something breaks)

### Transparency
- Open source (MIT license)
- All code visible
- All design documented
- Built by humans (Claude Haiku 4.5), for humans

---

## Timeline (Estimated)

| Version | Target | Status | Description |
|---------|--------|--------|-------------|
| v0.1.0 | 2026-05-11 | ✅ Released | 5-phase capture, FTS5 search, CLI installer |
| v0.2.0 | 2026-Q3 | 🔄 Planned | ChatGPT API logging, multi-AI support |
| v0.3.0 | 2026-Q4 | 📋 Planned | Vector embeddings, semantic search |
| v1.0.0 | 2027-Q1 | 📋 Planned | Stable API, all AI systems, deployment |

**Note:** Dates are estimates based on community interest and feedback. Real-world timeline may shift based on:
- Community contributions
- User feature requests
- Bug reports and fixes
- Performance optimizations needed

---

## Questions?

- **How do I get started?** → Read: `INSTALL_PROMPT.md`
- **How do I use it?** → Read: `docs/USAGE.md`
- **How does it work?** → Read: `docs/ARCHITECTURE.md`
- **Something broke?** → Read: `docs/TROUBLESHOOTING.md`
- **Want to contribute?** → Read: `CONTRIBUTING.md`

---

**ECM_002_StatefulClaude: Infinite external persistence of memory for Claude Code CLI**

*Created by Claude Haiku 4.5*
