# Healthy Water Pro
# Refactoring Backlog

Version: 1.0

Status: OFFICIAL

Last Updated: 2026-08-03

---

# Purpose

This document tracks all approved refactoring tasks discovered during project audits.

Nothing is forgotten.

Nothing is removed.

Every item must eventually become DONE.

---

# Priority Levels

HIGH

Must be completed before production.

MEDIUM

Should be completed during refactoring.

LOW

Nice improvement.

---

# Status

Pending

In Progress

Done

Cancelled

---

# Refactoring Items

| ID | File | Description | Priority | Status |
|----|------|-------------|----------|--------|
| R-001 | app.py | Move call_api() to utils/api.py | HIGH | Done |
| R-002 | app.py | Move load_data() to utils/data_service.py | HIGH | Pending |
| R-003 | app.py | Move to_num() to utils/helpers.py | MEDIUM | Pending |
| R-004 | app.py | Move ADMIN_PASSWORD to secrets.toml | HIGH | Pending |
| R-005 | app.py | Remove duplicated WEB_APP_URL constant | LOW | Pending |
| R-006 | app.py | Separate Router logic into a dedicated router module | MEDIUM | Pending |
| R-007 | app.py | Move configuration constants (URLs, Phone, Logo, etc.) to utils/config.py | MEDIUM | Pending |
| R-008 | app.py | Remove direct requests.post() calls from app.py and use a dedicated API service | HIGH | Pending |
| R-009 | app.py | Replace st.write() debug statements with a proper logging system | LOW | Pending |
| R-010 | app.py | Fully separate Presentation Layer from Service/API Layer | HIGH | Pending |
| ID    | File         | Description                                                    | Priority | Status  |
| ----- | ------------ | -------------------------------------------------------------- | -------- | ------- |
| R-011 | customers.py | Split customers.py into reusable UI components                 | HIGH     | Pending |
| R-012 | customers.py | Break app() into smaller rendering functions                   | HIGH     | Pending |
| R-013 | customers.py | Move customer visit/business calculations to CustomerService   | HIGH     | Pending |
| R-014 | customers.py | Move clean_phone() and wa_link() to utils/phone_utils.py       | MEDIUM   | Pending |
| R-015 | customers.py | Remove duplicated phone input fields using loops               | MEDIUM   | Pending |
| R-016 | customers.py | Extract Area selector into reusable component                  | MEDIUM   | Pending |
| R-017 | customers.py | Extract Device Type selector into reusable component           | LOW      | Pending |
| R-018 | customers.py | Move Customer Summary into component                           | LOW      | Pending |
| R-019 | customers.py | Move Maintenance History into component                        | MEDIUM   | Pending |
| R-020 | customers.py | Convert Customer Expander into reusable CustomerCard component | HIGH     | Pending |
| ID    | File         | Description                                           | Priority | Status  |
| ----- | ------------ | ----------------------------------------------------- | -------- | ------- |
| R-021 | inventory.py | Split inventory.py into reusable UI components        | HIGH     | Pending |
| R-022 | inventory.py | Break app() into smaller rendering functions          | HIGH     | Pending |
| R-023 | inventory.py | Move inventory calculations to InventoryService       | HIGH     | Pending |
| R-024 | inventory.py | Move stock status calculation to service              | HIGH     | Pending |
| R-025 | inventory.py | Convert Inventory Card into reusable component        | HIGH     | Pending |
| R-026 | inventory.py | Move inventory history UI into component              | MEDIUM   | Pending |
| R-027 | inventory.py | Move dashboard metrics into component                 | LOW      | Pending |
| R-028 | inventory.py | Extract search and sorting filters into component     | LOW      | Pending |
| R-029 | inventory.py | Convert Add Stock popover into component              | MEDIUM   | Pending |
| R-030 | inventory.py | Implement Remove Stock workflow as separate component | MEDIUM   | Pending |
R-031
maintenance.py
Extract Maintenance Visit Form into reusable component
HIGH
Pending

R-032
maintenance.py
Extract Maintenance History Card component
MEDIUM
Pending

R-033
maintenance.py
Move maintenance business logic to utils/maintenance_service.py
HIGH
Pending

R-034
maintenance.py
Extract maintenance status update service
LOW
Pending
R-035
expenses.py
Move expense business logic to utils/expenses_service.py
HIGH
Pending

R-036
expenses.py
Replace direct dataframe rendering with reusable ExpensesTable component
MEDIUM
Pending

R-037
expenses.py
Implement full CRUD for expenses
HIGH
Pending

R-038
expenses.py
Add expense statistics dashboard and summaries
MEDIUM
Pending
R-039
profits.py
Create profits_service.py and move all profit calculations
HIGH
Pending

R-040
profits.py
Implement Profit Dashboard KPIs
HIGH
Pending

R-041
profits.py
Implement Charts (Revenue / Expenses / Profit)
MEDIUM
Pending

R-042
profits.py
Implement Date Filters
MEDIUM
Pending

R-043
profits.py
Implement Export Reports (PDF / Excel / CSV)
LOW
Pending

R-044
profits.py
Separate UI from Business Logic
HIGH
Pending
R-045
store.py
Create store_service.py for business logic
HIGH
Pending

R-046
store.py
Implement Product CRUD
HIGH
Pending

R-047
store.py
Replace dataframe with StoreCard components
MEDIUM
Pending

R-048
store.py
Implement Search & Filters
MEDIUM
Pending

R-049
store.py
Integrate Store with Inventory quantities
HIGH
Pending

R-050
store.py
Separate UI from Business Logic
HIGH
Pending
R-051
utils/data_service.py
Move configuration constants to config.py
MEDIUM
Pending

R-052
utils/data_service.py
Remove Streamlit dependency from Data Layer
HIGH
Pending

R-053
utils/data_service.py
Replace print() with Logging
MEDIUM
Pending

R-054
utils/data_service.py
Add Type Hints to all functions
LOW
Pending

R-055
utils/data_service.py
Add Docstrings
LOW
Pending

R-056
utils/data_service.py
Implement Retry Logic for API calls
MEDIUM
Pending

R-057
utils/data_service.py
Centralize timeout configuration
LOW
Pending
R-058
utils/inventory_service.py
Remove unused Streamlit import
LOW
Pending

R-059
utils/inventory_service.py
Load inventory once and reuse DataFrame
MEDIUM
Pending

R-060
utils/inventory_service.py
Extract inventory search into helper function
MEDIUM
Pending

R-061
utils/inventory_service.py
Pass technician/reference to inventory history
HIGH
Pending

R-062
utils/inventory_service.py
Add Type Hints and Docstrings
LOW
Pending

R-063
utils/inventory_service.py
Protect inventory updates with transaction/rollback strategy
HIGH
Pending

R-064
utils/inventory_service.py
Validate negative stock inside deduct_inventory()
MEDIUM
Pending
R-065
utils/inventory_history_service.py
Remove Streamlit dependency from service layer
HIGH
Pending

R-066
utils/inventory_history_service.py
Remove debug code after testing
LOW
Pending

R-067
utils/inventory_history_service.py
Move import statements to top of file
LOW
Pending

R-068
utils/inventory_history_service.py
Add Type Hints and Docstrings
LOW
Pending

R-069
utils/inventory_history_service.py
Validate movement values (IN/OUT/ADJUST)
MEDIUM
Pending

R-070
utils/inventory_history_service.py
Replace positional list with structured payload
MEDIUM
Pending
R-071
requirements.txt
Pin dependency versions
LOW
Pending
R-072
README.md
Update architecture description to match current implementation
MEDIUM
Pending

R-073
README.md
Document official project documentation files
LOW
Pending

R-074
README.md
Mark placeholder modules as future implementation
LOW
Pending
R-075
.gitignore
Add virtual environment and OS generated files
LOW
Pending
R-076
components/parts_manager.py
Move standard filter list to utils/constants.py
LOW
Pending

R-077
components/parts_manager.py
Remove Session State dependency from component
HIGH
Pending

R-078
components/parts_manager.py
Extract Other Parts selector into reusable component
MEDIUM
Pending

R-079
components/parts_manager.py
Convert component to fully stateless reusable UI
HIGH
Pending
R-080
app.py
Move remaining helper functions to utils package
HIGH
Pending

R-081
app.py
Move configuration constants to config.py
HIGH
Pending

R-082
app.py
Extract Login UI into reusable Login component
MEDIUM
Pending

R-083
app.py
Replace if/elif router with centralized PAGE_MAP router
MEDIUM
Pending

R-084
app.py
Use lazy loading for modules
LOW
Pending

R-085
app.py
Move CSS into assets/css
LOW
Pending

R-086
app.py
Extract session initialization into dedicated initializer
LOW
Pending
R-087
.devcontainer/devcontainer.json
Move updateContentCommand into setup.sh script
MEDIUM
Pending

R-088
.devcontainer/devcontainer.json
Remove duplicated Streamlit installation
LOW
Pending

R-089
.devcontainer/devcontainer.json
Remove unnecessary apt upgrade from DevContainer
LOW
Pending

R-090
.devcontainer/devcontainer.json
Add VS Code workspace settings for formatting and linting
LOW
Pending                                                                                        
| **R-91** | **app.py** | Replace remaining direct `load_data()` usage with `utils.data_service.load_sheet()` and remove obsolete helper references | **HIGH** | **Pending** |

---

# Refactoring Statistics

Total Pending: 80

High Priority: 27

Medium Priority: 30

Low Priority: 24

Completed: 11
End of Document
---

End of Document