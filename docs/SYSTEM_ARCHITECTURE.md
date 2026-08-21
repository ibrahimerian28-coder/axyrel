# Healthy Water Pro
# System Architecture

Version: 2.0

Status: OFFICIAL

Last Updated: 2026-08-03

---

# Purpose

This document defines the complete architecture of the Healthy Water Pro project.

It describes:

- Project structure
- Module responsibilities
- Data flow
- Business logic separation
- Future scalability

---

# Architecture Philosophy

The project follows a modular architecture.

Each module has one responsibility.

Business logic is isolated from UI.

Documentation is treated as part of the architecture.

---

# Root Structure

healthy-water-v2/

│

├── app.py

├── components/

├── modules/

├── utils/

├── assets/

├── docs/

├── .streamlit/

├── requirements.txt

└── README.md

---

# app.py

Responsibilities:

- Entry Point

- Authentication

- Navigation

- Session Initialization

It must not contain business logic.

---

# components/

Responsibilities:

Reusable UI components.

Examples:

- Buttons

- Cards

- Tables

- Dialogs

- Widgets

No database code.

No business rules.

---

# modules/

Responsibilities:

Application pages.

Each page performs one feature.

Examples:

Dashboard

Customers

Inventory

Maintenance

Expenses

Reports

Store

---

# utils/

Responsibilities:

Business Logic

Examples:

Calculations

Validation

Inventory processing

Profit calculations

Maintenance scheduling

UUID generation

Google Sheets communication

Firestore communication

No UI code.

---

# assets/

Responsibilities:

Images

Icons

Fonts

Static resources

---

# docs/

Responsibilities:

Project documentation.

Official project knowledge.

AI references.

Development standards.

---

# Data Flow

User

↓

UI (components)

↓

Module

↓

Business Logic (utils)

↓

Data Storage

↓

Response

↓

UI

Business logic must never bypass utils.

---

# Configuration

Configuration files belong in:

.streamlit/

Future secrets:

secrets.toml

Environment-specific configuration must never be hardcoded.

---

# External Services

Current:

Google Sheets

GitHub

Gemini CLI

Antigravity CLI

Future:

Firestore

Cloud Storage

Payment Gateway

WhatsApp API

SMS Gateway

---

# Business Domains

The project currently contains:

Customer Management

Maintenance Management

Inventory

Expenses

Profits

Store

Reports

Notifications

Each domain should remain isolated.

---

# Scalability

Future modules may be added without changing existing modules.

Preferred architecture:

New module

↓

Own UI

↓

Own Logic

↓

Shared utilities

---

# Dependency Rules

components

↓

modules

↓

utils

↓

External Services

Never reverse this dependency order.

---

# Security

Sensitive information must never be stored in source code.

Examples:

API Keys

Passwords

Secrets

Tokens

Use environment configuration.

---

# Error Handling

Errors originate in utils.

Modules display user-friendly messages.

Components only render the result.

---

# Future Architecture

Planned additions:

Offline Mode

Cloud Synchronization

AI Assistant

Predictive Maintenance

Analytics Dashboard

Multi-user Support

Role Permissions

---

# Architecture Rule

When unsure where code belongs:

If it displays something

→ components

If it performs a feature

→ modules

If it contains business logic

→ utils

If it explains the project

→ docs

---

End of Document