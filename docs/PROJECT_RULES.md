# Healthy Water Pro
# Project Rules

Version: 1.0

Status: OFFICIAL

Last Updated: 2026-08-02

---

# Purpose

This document defines the official development rules for the Healthy Water Pro project.

These rules are mandatory for:

- Project Owner
- ChatGPT
- Gemini CLI
- Antigravity CLI
- Future Developers
- Any AI Coding Assistant

No rule may be violated without explicit approval from the Project Owner.

---

# Rule 1
One Task Only

Only one development task may be executed at a time.

Never implement multiple unrelated tasks together.

---

# Rule 2
Approval Gate

Every task must follow:

Analysis

↓

Execution Plan

↓

Owner Approval

↓

Implementation

↓

Testing

↓

Owner Acceptance

↓

Commit

↓

Next Task

---

# Rule 3
No Breaking Existing Features

No new feature may remove, modify or silently break an existing feature.

Backward compatibility is mandatory.

---

# Rule 4
No Hidden Changes

Never modify files that are unrelated to the current task.

Every change must have a clear reason.

---

# Rule 5
Single Source of Truth

Every document, configuration and business logic must exist in only one location.

No duplicated files.

No duplicated business logic.

---

# Rule 6
Refactoring Before Features

Major new features are forbidden until:

Audit completed.

Refactoring completed.

Project Stabilization completed.

---

# Rule 7
Git Policy

Development happens only on:

development

Main branch remains production-ready.

---

# Rule 8
Commit Policy

Every Commit must represent one completed task.

Commit messages must be meaningful.

No temporary commits.

---

# Rule 9
Documentation First

Major architectural changes require documentation updates before implementation.

---

# Rule 10
No Hardcoded Values

Never hardcode:

Business values

API Keys

Passwords

Sheet IDs

Configuration

Use configuration files instead.

---

# Rule 11
Code Quality

Readable code.

Small functions.

Single Responsibility Principle.

No duplicated code.

No dead code.

No magic numbers.

---

# Rule 12
Error Handling

Never ignore exceptions.

Never hide errors.

Display user-friendly messages.

Log technical details.

---

# Rule 13
Testing

Every completed task must be tested before Commit.

---

# Rule 14
Performance

Prefer optimization only after correctness.

Correct code comes before fast code.

---

# Rule 15
Security

Sensitive information must remain inside:

.streamlit/secrets.toml

Never commit secrets.

---

# Rule 16
Project Architecture

Business logic belongs only inside:

utils/

UI belongs inside:

components/

Pages belong inside:

modules/

---

# Rule 17
Roadmap Freeze

The official roadmap cannot be modified without owner approval.

New versions:

Roadmap v1.1

Roadmap v1.2

...

---

# Rule 18
Checkpoint Policy

Every completed milestone creates:

Commit

Checkpoint

Optional Git Tag

---

# Rule 19
Zero Silent Errors

Warnings and errors must never be ignored.

---

# Rule 20
Production Safety

No change may risk customer data.

No change may risk production stability.

---

---

# Healthy Water Pro Specific Rules

The following rules apply specifically to the Healthy Water Pro project.

These rules override any generic behavior when necessary.

---

## Data Rules

1. UUID is the only primary identifier.

2. Google Sheets row numbers must never be used as identifiers.

3. Column order must never be changed without updating documentation.

4. Sheet names are considered part of the system contract.

5. Data deletion is prohibited unless explicitly approved.

---

## Streamlit Rules

1. Business logic belongs only inside:

utils/

2. User Interface belongs only inside:

components/

3. Application pages belong only inside:

modules/

4. Pages should never contain duplicated business logic.

---

## Customer Rules

1. Customer UUID never changes.

2. Phone number is not a primary key.

3. Duplicate customers are forbidden.

---

## Maintenance Rules

1. Every maintenance visit must have its own UUID.

2. Closed maintenance records must never be modified silently.

3. Every modification must be traceable.

---

## Inventory Rules

1. Inventory cannot become negative.

2. Every inventory movement must be recorded.

3. Inventory history must never be deleted.

Reverse transactions should be used instead.

---

## Documentation Rules

1. Documentation is part of the source code.

2. Every architectural change requires documentation update.

3. Roadmap must be updated before implementing major features.

---

## AI Development Rules

Any AI agent working on this project must:

- Respect the official roadmap.
- Respect project architecture.
- Modify only the requested files.
- Never introduce duplicated code.
- Never remove existing functionality.
- Explain architectural changes before implementing them.
- Wait for owner approval before executing major changes.

---

## Architecture Lock

Public interfaces inside utils must not be modified without reviewing every dependent module.

Breaking shared interfaces is prohibited.

---

## Migration Rules

Future database migrations must preserve business logic.

Only the data access layer may change.

Application behavior must remain unchanged.
# Final Rule

When two rules conflict:

Protecting customer data and project stability always has highest priority.

---

End of Document