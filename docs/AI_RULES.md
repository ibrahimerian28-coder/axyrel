# Healthy Water Pro
# AI Rules

Version: 1.0

Status: OFFICIAL

Last Updated: 2026-08-02

---

# Purpose

This document defines how any AI agent must interact with the Healthy Water Pro project.

It is mandatory for:

- ChatGPT
- Gemini CLI
- Antigravity CLI
- Codex
- Future AI Agents

---

# Core Principle

The AI is a development assistant.

The Project Owner always has the final decision.

---

# Rule 1
Read Before Acting

Before making any modification the AI must read:

1. PROJECT_RULES.md

2. SYSTEM_ARCHITECTURE.md

3. ROADMAP_UPDATED.md

4. DEVELOPMENT_WORKFLOW.md

Only then may implementation begin.

---

# Rule 2
One Task Only

The AI must work on only one approved task.

No additional features.

No hidden improvements.

No unrelated refactoring.

---

# Rule 3
Approval Required

Major architectural changes require owner approval before implementation.

---

# Rule 4
No Silent Changes

Every modified file must be reported.

Nothing may be changed silently.

---

# Rule 5
Protect Existing Features

The AI must never break existing functionality.

Backward compatibility is mandatory.

---

# Rule 6
Minimal Changes

Modify the minimum number of files required.

Avoid touching unrelated code.

---

# Rule 7
No Duplicate Code

Reuse existing utilities whenever possible.

Never create duplicated business logic.

---

# Rule 8
Business Logic Separation

Business logic belongs only inside:

utils/

UI belongs only inside:

components/

Pages belong only inside:

modules/

---

# Rule 9
Documentation First

Architecture changes require documentation updates before implementation.

---

# Rule 10
Git Workflow

The AI must never create commits automatically.

Workflow:

Analysis

↓

Implementation

↓

Testing

↓

Owner Approval

↓

Commit

---

# Rule 11
Commit Scope

Each commit represents exactly one completed task.

---

# Rule 12
Testing

Every completed task must be tested before requesting approval.

---

# Rule 13
No Secrets

The AI must never expose:

API Keys

Passwords

Secrets

Tokens

Sensitive customer data

---

# Rule 14
Roadmap Protection

The AI must not modify the official roadmap without approval.

---

# Rule 15
Refactoring Rules

Refactoring must preserve behavior.

Only internal code quality may change.

---

# Rule 16
Error Handling

Never suppress exceptions.

Never hide failures.

Explain problems clearly.

---

# Rule 17
Code Style

Follow CODE_STYLE.md.

Readable code is preferred over clever code.

---

# Rule 18
Healthy Water Pro Priority

When uncertain:

Protect customer data.

Protect project stability.

Protect business logic.

These priorities override all other considerations.

---

# Rule 19
Session Continuity

The AI must preserve project context between tasks.

Never restart architecture decisions without owner approval.

---
---

# Rule 20
Project Stability

When multiple valid solutions exist, the AI must always choose:

1. Stability over speed.

2. Readability over complexity.

3. Maintainability over cleverness.

4. Consistency over personal preference.

The project must remain understandable after every task.
# Final Rule

The AI exists to assist the Project Owner.

It never makes business decisions independently.

---

End of Document