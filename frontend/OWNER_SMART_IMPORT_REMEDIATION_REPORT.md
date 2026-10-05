# Owner-approved Customer / Asset UX and Smart Import checkpoint

Branch: `frontend/v1`. Owner Acceptance remains after Tests 5–18; Test 19 was not started. Dedicated scope begins at `a34c5baca9c9c92952a81d8cdb5b8ce6227adad0`. The pushed commit SHA is supplied in the delivery message and verified against the remote.

## Result and design decisions

- Phone labels now use Primary, Mobile, Work, Home, Office, Emergency and Other. Other opens a custom text editor. Unknown/legacy labels retain their exact stored value until the user changes it. Dynamic phone collections, countries and backend E.164 normalization remain intact.
- Customer detail prominently labels the existing human reference as `Customer No. #…`; system UUIDs are not displayed.
- Customers and Assets now offer **Import Data**, defaulting to **Customers + Assets** when permitted. Customers-only and Assets-only are also supported. Four steps: Upload, Match Columns, Review, Import. Excel is the prominent template, CSV the secondary option.
- Deterministic Arabic/English heading aliases preselect columns. Unrecognized columns can be mapped or ignored; duplicate destination mappings are prevented by UI and backend. No external AI is involved.
- Review separates Ready, Existing matched and Needs attention, with field-specific Errors inside each affected row. Corrections support country, governorate, phone country, status, predefined/custom phone labels, customer selection and all mapped text/service fields. Every correction requires a fresh review before confirmation.
- Confirmation lists new Customers, matched existing Customers, new Assets and zero overwritten Assets. Import requires an explicit checkbox and button. Receipt appears after record refresh, with customer/asset numbers and durable replay information.

## Matching and geography

- Uploaded phones use the same country-aware `normalized_phone` as Customer CRUD. Only visible current-tenant customers participate. Existing canonical phone records and safely recognizable international legacy numbers participate; unresolved legacy national phones never receive a guessed country.
- Zero phone matches prepares a new Customer for Customers/combined import. One match shows Existing Customer Found without duplicating or editing the Customer. Multiple matches require explicit customer selection; an ambiguous phone can only select one of its current-tenant candidates.
- Repeated new-customer rows group by normalized phone only when names, labels and customer statuses agree (case-insensitive comparison). Conflicts flag every affected row. Names alone never silently match or group customers. Assets-only requires an existing match or explicit tenant-scoped selection by human customer number.
- Country/subdivision resolution uses the existing Round 1 `geography.json`, including reviewed GeoNames Egypt governorate names, plus authoritative pycountry names/codes. Surrounding whitespace and case differences are tolerated; ambiguous or unknown values require correction. Egypt/Cairo resolves to EG/EG-C internally. The template never requires codes. Blank country/phone country defaults to Egypt, explicitly explained in Upload.
- Locality stays free text, consistent with the existing locality-suggestion infrastructure and its fallback. Names such as Nasr City are retained rather than fabricated into codes.

## Import guarantees and security

- Legacy `asset_import.py`, its endpoints and CSV format remain unchanged, accessible through **Advanced / legacy Asset CSV import**. Existing compatible imports still use the tested engine.
- The new engine creates only; it never updates existing Customers or Assets. Serial comparisons reuse the legacy trim-only, case-sensitive function, preserve stored serial text and include deleted Assets in tenant serial reservations.
- Confirmation uses the existing PostgreSQL tenant Asset advisory transaction lock. Customer create/update/delete now share that lock to prevent phone-match and customer-number allocation races with import. Referenced visible Customer rows are locked through revalidation and creation.
- Signed 15-minute review tokens bind company, actor, exact reviewed rows/mapping/corrections, resolved match/group plan and existing customer detail snapshots. Changed matches, identity details or source require review again. Commit revalidates geography, phones, service fields and tenant serials under the lock. All Customer/Asset writes and the audit receipt commit atomically; failures roll back the whole batch.
- UUID retry keys identify tenant/actor-scoped `SMART_IMPORT_COMMITTED` audit receipts in the existing audit table. Completed retries retrieve the original result, including after token expiry; a changed input cannot reuse a key. UI freezes uncertain confirmations and retries with the same token, data and key. No new table or migration is required.
- Maintenance is 1–1200 whole months; warranty is 0–100 whole calendar years. Existing `prepare_asset_details` remains authoritative for warranty end calculation, including leap-day behavior. Installation dates accept YYYY-MM-DD text or typed Excel date cells; ambiguous slash dates and time-bearing cells are rejected. No manual warranty end column exists in normal templates.
- Imports require authentication, Customer read, and mode-specific Customer/Asset manage permissions. The frontend proxy narrowly allowlists the four import endpoints and retains same-origin mutation, HttpOnly session and no-store protections. Service entry points require an explicit company scope.
- Upload content is decoded and parsed on the backend; extensions/MIME are not trusted. Limits: 1 MB file, 1000 data rows, 40 columns, 1000 characters per cell, 7 MB bounded JSON request, 100 ZIP entries and 16 MB expanded workbook. Sparse row/column coordinates are bounded before workbook loading; archive entries are never extracted.
- Only one plain-value XLSX worksheet or UTF-8 CSV is accepted. Macro-enabled content, formulas, defined names, error cells, external relationships/workbook links, embedded objects, active content, duplicate ZIP entries, XML entities and malformed archives are rejected. No macros/formulas execute and external links are never followed.
- Downloaded CSV/XLSX templates contain fixed trusted headings and formats, not uploaded values. User-provided errors/receipts are displayed as escaped React text; no user-data CSV/XLSX report export is produced, avoiding formula injection through generated reports.

## Dependencies and migrations

Pinned `openpyxl==3.1.5` supplies native XLSX parsing/generation and typed spreadsheet dates without a browser spreadsheet dependency. Pinned `defusedxml==0.7.1` protects XML parsing; it was already installed locally but is now explicit in requirements. XML preflight uses it directly. The [openpyxl security documentation](https://openpyxl.readthedocs.io/en/stable/#security) recommends defusedxml for XML expansion protection. No frontend dependency was added.

No schema migration was required or applied. Current Customer/Asset models and the existing audit table suffice. Existing migration files and Owner Review's migration ledger remain unchanged.

## Changed files

- Backend: `api/v1/smart_import.py`, router registration in `api/v1/__init__.py`, `services/smart_import.py`, `services/smart_import_files.py`, and shared serialization in `services/customer.py`.
- Frontend: `features/phase4/smart-import.tsx`; Customer phone selector and detail/entry-point wiring in `features/phase2/customer-phones.tsx` and `screens.tsx`; bounded endpoint forwarding in `app/api/backend/[...path]/route.ts`; scoped wizard CSS in `styles/globals.css`.
- Tests: `tests/test_smart_import.py`; `playwright.smart-import.config.ts`; `tests/smart-import/journeys.spec.ts` and `retry.spec.ts`. Existing Round 1/MVP browser tests now open the advanced compatibility section; Round 1 uses the new label selector/custom input. MVP waits for Expense save completion before navigating to Reports, resolving an observed test race without application changes.
- `requirements.txt` and this report. Only these intended files are explicitly staged; generated `next-env.d.ts` is excluded.

## Validation and preservation

| Check | Result |
| --- | --- |
| Smart Import file/API/PostgreSQL tests | 25 passed |
| Existing Asset CSV Import tests | 12 passed |
| Round 1 backend/migration regression on disposable DBs | 6 passed |
| Customer/Asset integration | 19 passed |
| Profile image backend regression | 8 passed |
| Owner Review identity/preservation safety unit tests | 5 passed |
| Smart Import browser | 4 passed |
| Phase 2 browser, including images | 7 passed |
| Round 1 browser | 4 passed |
| Phase 3 browser | 4 passed |
| MVP browser | 5 passed |
| Typecheck / lint / production build | Passed |

New tests cover XLSX/CSV templates and upload; bilingual aliases/manual mapping/ignored columns; all three import modes; repeated grouping; unique/ambiguous/foreign phone matches; geography resolution/ambiguity/corrections; warranty/month validation; upload/existing/deleted serial collisions; rollback; changed review input/customer identity; expiry and replay; concurrent confirmation; malformed/oversized/active/external content; authorization and missing tenant scope. Browser journeys cover desktop, 390px LTR/RTL, label persistence, Customer No., no visible UUIDs, inline corrections, explicit confirmation, refreshed counts and lost-response retry with a blank serial.

Desktop mapping/review and 390px mapping/review/receipt screenshots were captured and inspected. No horizontal overflow. Artifacts remain under ignored `frontend/test-results/smart-import/`.

The private, verified Owner Review snapshot was captured before tests and compared read-only afterward: every Customer/Asset row, private image, credential/configuration hash and migration-ledger entry matches exactly. Customer #1010 and Asset `IMPORT-TEST-001` are present and unchanged. Regression runners used generated PostgreSQL or temporary SQLite databases, never Owner Review. No initialization, reset, reseed or private-data rewrite occurred.

Main baseline remains `e8accb377e6f0c32cc919463466ae9ba97995c06`. Streamlit and the official logo have no diff from the scope baseline. Official logo SHA256 remains `CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3`; no logo or derivative bytes were written.

## Limits and Owner handoff

- Normal import represents one phone per customer; repeated rows represent multiple assets. Additional phone countries/labels are supported. Multiple distinct phone columns per customer are not combined automatically; use the existing dynamic Customer editor for additional contact numbers.
- Combined imports require an asset on each data row; Customers-only is available for customer rows without assets. Asset-specific notes/address/location stay with Assets; Customers-only template includes only supported customer/contact fields.
- Phone-free rows cannot automatically create/group new customers. Assets-only rows may explicitly select an existing Customer. Unknown/ambiguous geography and conflicting customer grouping require correction; no fuzzy matching is used.
- Workbook formulas/defined names/external hyperlinks, multiple worksheets and ambiguous textual dates are intentionally unsupported. Paste values into one clean worksheet. Uploaded files are kept only in wizard memory; navigating away loses an uncommitted draft. Keep an uncertain confirmation open and use its same-key retry.
- Backend geography resolution reads the existing checked-in frontend reference file; keep that shared file with the backend deployment. No deployment is part of this checkpoint.

Restart both existing Owner Review foreground terminals with Ctrl+C, then use the existing **serve** and **frontend start** commands in `OWNER_REVIEW.md` to load the new backend routes and production build. Do not run init/reset/migrate: no migration is needed. The running Owner Review servers were left untouched. Manually retest only this remediation; Owner Acceptance Test 19 remains unstarted.
