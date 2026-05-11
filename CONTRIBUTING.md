# Contributing to ECM_002_StatefulClaude

*ECM_002_StatefulClaude was created and produced by Claude Haiku 4.5*

Thank you for your interest in contributing to StatefulClaude! This document explains how to contribute code, documentation, bug reports, and ideas.

## A Note About This Project

ECM_002_StatefulClaude is an open-source system that was designed, architected, built, tested, and documented entirely by Claude Haiku 4.5. This is a production-ready system created by an AI to solve a real problem: making Claude Code CLI stateful through external memory persistence.

By contributing to this project, you're building on work created by an advanced AI system. Your contributions will improve a system that was born from conversational prompts and iterative feedback.

---

## Code of Conduct

ECM 002 is an open and welcoming community. We are committed to providing a safe and inclusive environment for all contributors.

**Our Values:**
- **Respect** — Treat everyone with kindness and respect
- **Inclusivity** — Welcome contributions from people of all backgrounds
- **Transparency** — Communicate clearly and honestly
- **Collaboration** — Help each other build better software

**Expected Behavior:**
- Be respectful in all discussions
- Assume good intentions
- Accept constructive criticism
- Focus on the idea, not the person
- Help others learn and grow

**Unacceptable Behavior:**
- Harassment or discrimination
- Personal attacks
- Unwelcome advances or attention
- Publishing private information without consent
- Intentional disruption

**Reporting Issues:**
If you experience or witness unacceptable behavior, please report it to [maintainer email]. All reports will be handled confidentially.

---

## How to Contribute

### 1. Report a Bug

**Found a bug?** Open an issue with:

- **Title:** Brief description of the bug
- **Environment:** OS, Python version, SQLite version
- **Steps to reproduce:** Exact steps to trigger the bug
- **Expected behavior:** What should happen
- **Actual behavior:** What actually happened
- **Error messages:** Full error output (if applicable)
- **Logs:** Relevant log excerpts from `/tmp/ecm-*.log`

**Example:**
```
Title: File operations not captured in /home/user/work

Environment:
- Ubuntu 20.04
- Python 3.9
- SQLite 3.31.1

Steps:
1. Modify ~/.ecm-watched-dirs to include /home/user/work
2. Run: touch /home/user/work/test.txt
3. Wait 2 minutes for cron ingest
4. Query: SELECT * FROM ecm_actions_details WHERE action_type='file' AND target LIKE '%test.txt%'

Expected: Record appears
Actual: No record found

Log excerpt from /tmp/ecm-monitor.log:
[error message here]
```

### 2. Suggest a Feature

**Have an idea?** Open an issue with:

- **Title:** Feature name
- **Problem:** What problem does this solve?
- **Proposed solution:** How should it work?
- **Alternatives considered:** Other approaches you thought of
- **Additional context:** Why is this important?

**Example:**
```
Title: Add email activity logging (Phase 6)

Problem: My workflow includes email, but ECM 002 doesn't capture it.

Proposed Solution:
- Phase 6: Email Logging
- Parse ~/.local/share/evolution/mail/ (Evolution email client)
- Or integrate with IMAP to capture inbox changes
- Log: timestamp | operation (new/read/deleted) | sender | subject | size

Why: Modern workflows often involve email communication alongside coding.
```

### 3. Ask Questions

**Unsure about something?** Open a discussion instead of an issue:

- Go to [Discussions](https://github.com/your-username/ecm-002/discussions)
- Choose a category (Ideas, Q&A, Show & Tell)
- Describe your question or use case
- Community members will help

---

## Contributing Code

### Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/ecm-002.git
   cd ecm-002
   ```

2. **Create a branch for your work**
   ```bash
   git checkout -b feature/my-feature-name
   # or: git checkout -b bugfix/my-bug-fix
   ```

3. **Make your changes**
   - Follow the coding style (see below)
   - Test your changes (see Testing)
   - Update documentation if needed

4. **Commit your changes**
   ```bash
   git add [files]
   git commit -m "Clear description of what changed and why"
   ```

5. **Push and create a pull request**
   ```bash
   git push origin feature/my-feature-name
   ```
   Then open a PR on GitHub with a description of your changes.

### Coding Style

**Python**
- Follow PEP 8
- Use meaningful variable names (not `x`, `y`, `z`)
- Comment the "why", not the "what"
- Max line length: 100 characters
- Use type hints where helpful

**Bash**
- Use `#!/bin/bash` shebang
- Quote variables: `"$VAR"` not `$VAR`
- Use `set -e` to exit on errors
- Comment complex logic
- Test on Bash 4.0+

**SQL**
- Use uppercase for keywords (SELECT, FROM, WHERE)
- Use lowercase for identifiers
- Indent subqueries
- Comment non-obvious logic

**Example Python:**
```python
def ingest_system_state(log_file_path):
    """
    Parse system state log and insert into database.
    
    Deduplicates based on rounded metrics to filter minor fluctuations.
    """
    metrics = parse_log(log_file_path)
    
    # Round metrics to avoid noise (2.251 and 2.249 are the same state)
    rounded = {
        'cpu': round(metrics['cpu'], 1),
        'memory': round(metrics['memory']),
    }
    
    # Skip if this state was recently logged
    if state_exists(rounded):
        return False
    
    insert_into_database(metrics)
    return True
```

### Branch Naming

- Feature: `feature/short-description`
- Bug fix: `bugfix/short-description`
- Documentation: `docs/short-description`
- Refactor: `refactor/short-description`
- Test: `test/short-description`

**Example:** `feature/add-email-logging`, `bugfix/timestamps-corrupted`, `docs/improve-architecture-guide`

### Commit Messages

- **First line:** 50 characters max, describe what changed
- **Blank line:** Separate from body
- **Body:** Explain why the change was needed (can be multiple lines)
- **Footer:** Reference issues: `Fixes #123` or `Related to #456`

**Example:**
```
Phase 6: Add email activity logging

Implement email capture for Evolution email client. Users can now see
all inbox changes (new, read, deleted) in their external memory.

Reads ~/.local/share/evolution/mail/ directory structure and parses
metadata. Logs to /tmp/ecm-email-events.log with timestamp, operation,
sender, subject, and size.

Deduplicates by message ID to avoid duplicate entries.

Fixes #42
Related to #18
```

### Testing Your Changes

**Before submitting a PR:**

1. **Test on your system**
   ```bash
   # Run the affected phase manually
   python3 ecm-ingest-bash-commands.py
   
   # Query the database
   sqlite3 /mnt/ecm-ram/ecm-hot.db "SELECT COUNT(*) FROM ecm_actions_details"
   ```

2. **Test with different scenarios**
   - Empty logs (no data yet)
   - Large logs (1000+ entries)
   - Corrupted data (invalid JSON, malformed lines)
   - Missing files (log file doesn't exist)

3. **Verify cron still works**
   ```bash
   crontab -l | grep ecm
   tail -f /tmp/ecm-*.log
   ```

4. **Check health report**
   ```bash
   python3 ecm-health-report.py
   ```

### Pull Request Process

1. **Describe your changes clearly**
   - What problem does this solve?
   - How does it work?
   - What was tested?
   - Any breaking changes?

2. **Link related issues**
   - Use `Fixes #123` to auto-close issues
   - Use `Related to #456` for context

3. **Include a checklist**
   ```markdown
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] No breaking changes
   - [ ] Tested on Linux [distro]
   - [ ] Code follows style guide
   ```

4. **Wait for review**
   - Maintainers will review your code
   - Address feedback and push updates
   - Once approved, PR will be merged

---

## Contributing Documentation

Documentation is just as important as code.

### Improving Existing Docs

1. Find the file in `/docs/`
2. Create a branch: `docs/improve-[topic]`
3. Make your changes (Markdown)
4. Submit a PR

**Types of documentation improvements:**
- Clarifying confusing sections
- Adding examples
- Fixing typos
- Adding missing information
- Creating quick reference guides

### Writing New Docs

Want to write a new guide? Discuss it first:

1. Open an issue or discussion
2. Propose the topic and outline
3. Get feedback from maintainers
4. Write the documentation
5. Submit as a PR

**Documentation should:**
- Be clear and concise
- Include examples where helpful
- Assume reader has basic Linux/Python knowledge
- Link to related documentation
- Use code blocks for commands and examples

---

## Contributing to Different Areas

### Phase Improvements (1-5)

Each phase has opportunities for improvement:

**Phase 1 (Bash):**
- Support zsh, fish, other shells
- Capture shell aliases and functions
- Better error handling for non-bash shells

**Phase 2 (SSH):**
- Extend to other SSH clients (not just /var/log/auth.log)
- Capture SSH config changes
- Support scp/sftp operations

**Phase 3 (Fossil):**
- Support Git repositories
- Support Mercurial
- Capture branch changes

**Phase 4 (Files):**
- More efficient monitoring (inotify alternative)
- Support symlinks
- Capture file permissions changes separately

**Phase 5 (System):**
- Network interface details
- GPU metrics
- Container/VM detection
- Custom metrics

### Adding New Phases

Want to capture something not in the 5 phases?

1. Open a discussion: "Phase X: [Activity Type]"
2. Explain what would be captured
3. Propose where data comes from
4. Describe deduplication approach
5. If approved, implement following existing phase pattern

**Recent phase ideas:**
- Phase 6: Email activity
- Phase 7: Browser history / research activity
- Phase 8: Network connections (netstat/ss)
- Phase 9: Package installations
- Phase 10: Database queries (PostgreSQL logs)

### Extending to Other AI Systems

ECM 002 is currently Claude Code CLI only, but designed to extend to other AIs.

**To add support for a new AI:**

1. Create a new capture phase: `ecm-ingest-[ai-name]-calls.py`
2. Log format should match existing: `timestamp|json_metrics`
3. Deduplication strategy (how to avoid duplicate captures?)
4. Add to cron: Run every 1 or 5 minutes?
5. Document in `docs/EXTENDING.md`
6. Add to health report: `action_type='[ai-name]'`

**Examples to implement:**
- ChatGPT API calls (from ~/.config/chatgpt-cli/)
- Claude API calls (from inference logs)
- LLaMA local invocations
- Ollama API calls
- Anthropic API calls (general)

**Requirements for new AI support:**
- Data source must be local and accessible
- Clear API for extracting activity
- Deduplication strategy
- No privacy violations (handle tokens/credentials safely)
- Documentation for other contributors

---

## Development Workflow

### Local Testing Setup

```bash
# Clone the repo
git clone https://github.com/your-username/ecm-002.git
cd ecm-002

# Create your branch
git checkout -b feature/my-feature

# Test installation (if changing installer)
bash install-test.sh

# Run manual tests
python3 ecm-capture-system-state.py
python3 ecm-ingest-bash-commands.py

# Check cron jobs
crontab -l | grep ecm

# Query database
sqlite3 /mnt/ecm-ram/ecm-hot.db "SELECT COUNT(*) FROM ecm_actions_details"

# Health check
python3 ecm-health-report.py
```

### Debugging Tips

**Check logs:**
```bash
tail -f /tmp/ecm-*.log
```

**Query database directly:**
```bash
sqlite3 /mnt/ecm-ram/ecm-hot.db
sqlite> SELECT COUNT(*) FROM ecm_actions_details;
sqlite> SELECT * FROM ecm_actions_details LIMIT 5;
```

**Enable debug mode in scripts:**
```python
import sys
logging.basicConfig(level=logging.DEBUG)
```

**Test ingest state tracking:**
```bash
cat /tmp/ecm-bash-ingest-state.json
```

**Verify cron job ran:**
```bash
ls -lh /tmp/ecm-bash-commands.log
# Check timestamp matches last cron time
```

---

## Testing Checklist

Before submitting a PR:

- [ ] Code follows style guide
- [ ] All changes documented
- [ ] No new warnings or errors
- [ ] Tested on your system
- [ ] Tested edge cases (empty logs, corrupted data, missing files)
- [ ] Cron jobs still run
- [ ] Health report shows correct status
- [ ] Database queries return expected results
- [ ] No breaking changes to existing phases
- [ ] Log format unchanged (or migration documented)

---

## Release Process

Maintainers follow this process for releases:

1. Create a release branch: `release/v0.2.0`
2. Update version numbers and CHANGELOG
3. Review all changes
4. Tag release: `git tag -a v0.2.0 -m "Release v0.2.0"`
5. Push tag: `git push origin v0.2.0`
6. Create GitHub Release with notes

**You can help:**
- Keep changelog updated
- Suggest release timing
- Test pre-release versions

---

## Recognition

Contributors will be recognized in:

- **CONTRIBUTORS.md** — Full list of all contributors
- **Release notes** — Notable contributions highlighted
- **GitHub** — Automatically shows in repo contributors page

Thank you for your contributions!

---

## Questions?

- **How do I...?** → Open a Discussion
- **I found a bug** → Open an Issue
- **I have an idea** → Open an Issue or Discussion
- **How do I set up?** → See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **I need help** → Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## Additional Resources

- **GitHub Issues:** [github.com/your-username/ECM_002_StatefulClaude/issues](https://github.com/your-username/ECM_002_StatefulClaude/issues)
- **Discussions:** [github.com/your-username/ECM_002_StatefulClaude/discussions](https://github.com/your-username/ECM_002_StatefulClaude/discussions)
- **Main Docs:** [docs/](docs/)
- **License:** [MIT](LICENSE)

---

## Final Words

ECM_002_StatefulClaude is a community project. Every contribution — whether code, documentation, bug reports, or ideas — helps build something special.

We're not just building a tool. We're building toward a future where AI assistants remember, learn, and grow alongside their users.

Thank you for being part of that journey.

---

**Happy contributing! 🚀**
