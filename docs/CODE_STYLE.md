# Healthy Water Pro
# Code Style Guide

Version: 1.0

Status: OFFICIAL

Last Updated: 2026-08-02

---

# Purpose

This document defines the official coding style for the Healthy Water Pro project.

All contributors and AI agents must follow these rules.

---

# General Principles

Code must be:

- Readable
- Predictable
- Maintainable
- Consistent

Readable code is preferred over clever code.

---
The project follows the principle:

Make it work.

Make it correct.

Make it clean.

Make it maintainable.
# File Organization

Each file should have a single responsibility.

Avoid mixing:

- UI
- Business Logic
- Data Access

---

# Folder Responsibilities

components/

UI Components only

modules/

Application Pages

utils/

Business Logic

helpers/

Utility Functions

assets/

Static Files

docs/

Project Documentation

---

# Naming Rules

Variables

Use:

snake_case

Example:

customer_name

filter_price

inventory_count

---

Functions

Use:

snake_case

Example:

calculate_total()

load_customer()

update_inventory()

---

Classes

Use:

PascalCase

Example:

CustomerService

InventoryManager

---

Constants

Use:

UPPER_CASE

Example:

MAX_FILTERS

DEFAULT_STATUS

---

# Function Rules

A function should:

- Do one thing only
- Be short
- Be easy to understand

Preferred length:

Less than 40 lines

---

# Comments

Explain WHY.

Avoid explaining obvious code.

Good:

# Calculate monthly maintenance cost

Bad:

# Add two numbers

---

# Imports

Standard Library

↓

Third-party Packages

↓

Local Modules

---

# Error Handling

Never ignore exceptions.

Always:

- Catch expected errors
- Show meaningful messages
- Preserve debugging information

---
Errors must never be ignored.

Never use:

pass

except:

without logging or explanation.

Every handled exception must have a reason.
# Formatting

Indentation:

4 Spaces

Maximum line length:

100 Characters

Blank lines between logical sections.

---

# Duplication

Never duplicate code.

Extract reusable logic into utils.

---

# Magic Numbers

Avoid:

if x > 17

Prefer:

MAX_ALLOWED_FILTERS = 17

---

# Logging

Errors should be logged.

Do not print debug messages in production.

---

# Security

Never hardcode:

- Passwords
- Tokens
- API Keys
- Secrets

Use configuration files.

---

# Performance

Optimize only after correctness.

Correct code comes first.

---

# Refactoring

Refactoring must never change behavior.

Only improve:

- Readability
- Maintainability
- Structure

---

# Git Rules

One logical change per commit.

Commit messages must describe:

What changed.

Not how.

---
Never commit:

Temporary debugging code.

Commented dead code.

Unused imports.

Unused variables.

# AI Rules

AI-generated code must:

Follow PROJECT_RULES.md

Follow AI_RULES.md

Follow DEVELOPMENT_WORKFLOW.md

Follow this document.

---
---

# Final Principle

Every new line of code must leave the project in a better state than before.

Small continuous improvements are preferred over large risky changes.
End of Document