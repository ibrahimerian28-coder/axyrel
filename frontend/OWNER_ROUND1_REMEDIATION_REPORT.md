# AXYREL FRONTEND v1 - OWNER ACCEPTANCE REMEDIATION ROUND 1 REPORT

Baseline: bb0968670cfa1c4311f1b96738804d82e21446e9, branch frontend/v1. The exact delivered commit SHA and remote verification are supplied in the final delivery message. Owner Acceptance remains stopped at test 18; tests 19-60 were not started.

## 1. Customer image failure

The persistent environment's actual log showed PermissionError at NamedTemporaryFile in the Customer image directory. Python's Windows handling of mkdir(mode=0o700) creates a creator-only DACL; directories created under the sandbox account excluded the manual-review account. This was an OS permissions failure, not invalid content, size validation or an API permission rejection.

New Windows image subdirectories inherit the secured private parent ACL; POSIX retains 0700. Existing private image directories/files were granted access only to the verified workspace/review and initializing accounts, without deleting or altering image bytes or granting Everyone/public access. The repair command verifies the review database marker and rejects symlinks/out-of-root paths. The existing image-storage abstraction, authorized tenant lookups, 5 MiB JPEG/PNG/WebP content validation, metadata stripping and private WebP delivery remain unchanged.

Python behavior reference: https://docs.python.org/3/library/os.html#os.mkdir .

## 2. Asset image failure

The same PermissionError occurred in the Asset image directory, through the shared storage implementation. The same ACL inheritance and existing-directory repair fixes it. Both resources passed actual persistent-review browser upload -> display -> refresh -> replace -> refresh -> remove. Separate application-process checks also verified persisted images and record fields. No exception was hidden and no validation was weakened.

## 3. Exact schema/API changes

Added only `migrations/015_owner_customer_phones_asset_location.sql` using the existing checksum-verified numbered migration runner, not Alembic (this repository has no Alembic migration history).

- Customer: nullable JSONB `phones`, holding one optional bounded collection of country, original number, label and server-normalized E.164 metadata.
- Asset: nullable `country` VARCHAR(2), `state` VARCHAR(150), `area` VARCHAR(150), `address` VARCHAR(500), `location_url` VARCHAR(1000), `maintenance_cycle` INTEGER and `warranty_years` INTEGER. Cycle constraint 1-1200 months; warranty constraint 0-100 whole years.

The migration is additive: no DROP, UPDATE, guessed location transfer, legacy-column rename or image-storage reference change. All pre-existing Asset/Customer values remain intact. It was rehearsed against a generated PostgreSQL database containing old rows and ledger records, and applied only to the catalog-marker-verified existing Owner Review database. Thirteen prior migration identities/checksums verified; the new ledger contains fourteen records. Rerunning verifies/skips the chain. Existing migration files were not modified.

Existing Customer/Asset CRUD endpoints accept/read the new fields with the same tenant and role checks; no new general CRM endpoint or model. Customer search includes canonical phone metadata. Asset service validates ISO country/state relationships and HTTP(S) location links. Imported fields use the same Asset service rules. No Streamlit files were changed.

## 4. Preservation of Phone 1-4

Legacy `phone`, `phone_1`, `phone_2`, `phone_3`, `phone_4` columns are retained byte-for-value, including invalid/unresolved legacy strings and duplicates. NULL `phones` means API reads expose a lossless legacy collection; explicit valid international numbers can be recognized, while local/ambiguous numbers are retained without guessing a country. Selecting a country explicitly adopts normalization; editing the canonical collection does not overwrite the original legacy columns. Legacy fields remain API-compatible; they are not automatically synchronized to the new collection for legacy clients/Streamlit.

The normal editor has one empty row initially (including an empty existing contact collection), Add Phone Number, remove, country/calling-code selection defaulting to Egypt +20, national/international number and a Primary/Work/Home/Other or custom description. Limit 100 records is a bounded reasonable safety limit, replacing the four-number UX. Numbers are validated with pinned phonenumberslite and normalized server-side. Call/WhatsApp/Copy use E.164, including Asset-related Customer contact controls. WhatsApp remains an explicit click and no longer requires manually entering +20 for a national Egyptian number. Unresolved legacy numbers remain visible and require a country before international actions.

## 5. Legacy Customer location preservation

Customer address, area, location_url, install_date, cycle and device_type columns and values remain intact and API-accessible, but are removed from the normal Customer edit/contact UI. No automated copying to Assets was performed because a Customer may own multiple Assets. Existing Asset installation_date remains the sole canonical installation input. New Asset location fields are independently editable and tenant-scoped.

## 6. Geographic reference strategy

Pinned pycountry 26.2.16 supplies ISO countries/subdivision codes; phonenumberslite 9.0.40 supplies calling-code/phone metadata. A generated local snapshot includes 27 Egyptian governorates and 11,473 GeoNames locality suggestions grouped through a reviewed ISO/admin-code mapping. Source hashes, versions, date, generation script and license/attribution are committed. No runtime third-party geographic request is required.

Country changes clear dependent state/locality; governorate changes clear locality. Egypt has governorate-dependent suggestions plus actual free-text locality fallback. Other countries use ISO subdivisions where available and free-text locality; optional subdivision may be omitted where unavailable. Suggestions are not an exhaustive official postal/district validation system, and no universal locality hierarchy is fabricated. See design-references/GEOGRAPHIC_REFERENCE.md.

## 7. Warranty behavior

User supplies one Installation Date, maintenance cycle in months and optional warranty period in whole calendar years. The frontend shows a preview; the backend always calculates and persists the authoritative end for year-based warranties, overriding conflicting manually supplied legacy end dates. February 29 anniversaries clamp to February 28 in non-leap years; zero years means the installation date. Missing installation date or explicitly cleared warranty years produces NULL end. Invalid/overflowing calendar ranges are rejected.

Untouched legacy manual start/end dates with no warranty_years remain preserved; no duration is guessed. Editing a legacy Asset without choosing years does not clear its old end date. Once years are supplied, the canonical calculation applies, including subsequent edits. Legacy warranty_start/warranty_end API/CSV fields remain accepted for compatibility; the new editor/template does not ask for manual dates.

## 8. Asset Import changes

CSV template now includes country/state/area/address/location URL, maintenance_cycle and warranty_years, with one installation_date. Country is ISO alpha-2; state is ISO subdivision code. Whole-number durations, field bounds, country/state consistency and URLs are validated server-side. Preview includes supported location/service fields and calculated warranty end; errors retain structured row/column information. Old supported headers remain compatible.

Preview/checksum binding, revalidation at commit, transactional all-or-nothing commit, durable idempotent retry, tenant-local Customer resolution, optional blank serials, same-file/same-tenant nonblank duplicate rejection, case-sensitive whitespace-only comparison and shared-lock display-ID allocation are unchanged. No overwrite/upsert or other entity imports.

## 9. Validation

| Suite/check | Final result |
| --- | --- |
| Focused Round 1 API/migration: dynamic phones, normalization/default, unresolved legacy retention, tenant/role restrictions, location/service fields, calendar limits/legacy dates, import and additive preservation | 6 passed, 38.201s |
| Asset Import safety/concurrency/rollback/retry regression | 12 passed, 10.213s |
| Existing Customer/Asset integration | 19 passed, 13.441s |
| Existing migration rehearsal | 8 passed, 15.677s |
| Existing MVP backend regressions, ten isolated modules | 97 passed; summed suite time 556.217s |
| Existing Service Flow backend regressions, five isolated modules | 94 passed; summed suite time 145.799s |
| Regression target safety (no retained DB access) | 4 passed, 0.333s |
| Owner Review identity safety | 5 passed, 0.156s |
| Focused Round 1 browser, desktop/390px/RTL, phone removal/empty editor, geography/dependencies, warranty and import | 4 passed, 28.6s |
| Phase 2 browser, including images/contact actions | 7 passed, 1.1m |
| Phase 3 browser, full stored service flow and inventory reversal | 4 passed, 47.6s |
| MVP browser, inventory/financial truth/import retry/tenant isolation/errors | 5 passed, 38.5s |
| Foundation browser/session/origin/navigation | 5 passed, 30.9s |
| Actual persistent-review browser images and login/navigation | 2 passed, 13.2s |
| Separate application-process persistence of phones, Asset fields and private images | Passed; unique synthetic case removed through existing APIs |
| Preservation snapshot of all pre-existing review Customer/Asset rows, image hashes, credential/configuration hashes and ledger | Passed |
| Final typecheck/lint/production build; whitespace check | Passed |

Suite counts overlap and are not a unique-test total. Assertions were retained; existing route expectations were updated for approved Dashboard landing and Egyptian WhatsApp normalization, and ledger-count assertions include the additive migration. Initial failures exposed real mobile overflow (fixed), selector labels (made explicit), hardcoded test-port origins (corrected), and Windows artifact/teardown interference (isolated port/artifact paths and permission for the framework to clean its own test servers). None were hidden or accepted as final passes. No Stop-Process command was executed; foreground review sessions were restarted through Ctrl+C.

The earlier shared-process regression runner cached PostgreSQL configuration and redirected its intended SQLite image fixture to the configured local `axyrel` database. Both runners now use separate processes and fail-closed connection/admin guards. Subsequent validation rejects `axyrel`, Owner Review, remote and uncreated test targets before driver access. `axyrel` was not audited or changed during continuation; its historical contents/effects remain unverified and any audit/recovery is a separate owner decision. See OWNER_ROUND1_VALIDATION_BLOCKER.md for the incident and containment. The actual marker-verified Owner Review data preservation check passed.

## 10. Checkpoint/governance

Dedicated validated checkpoint is on frontend/v1 only; final message gives exact SHA and remote verification. Main remains e8accb377e6f0c32cc919463466ae9ba97995c06. Streamlit and existing migration history remain untouched. No force push, destructive Git, review database reset/recreation or unrelated business-rule refactoring. Explicit staging excludes the pre-existing generated next-env.d.ts change. Official Axyrel logo SHA256 remains CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3.

## 11. Restart for retesting

See OWNER_REVIEW.md for two foreground terminals requiring no Stop-Process. The existing review database, private images and credentials are preserved. No initialization/reset or reseeding is needed. Verify/migrate only through the marker-checked helper (migration rerun skips applied revisions), then serve on 8140 and production Next on 3140. Open http://127.0.0.1:3140/login with the unchanged .owner-review/credentials.txt. Stop with Ctrl+C, confirming batch termination if prompted. Actual PC reboot was not tested; separate application lifetimes demonstrated persistence. Retest Round 1 and earlier pending cases only; do not begin Owner Acceptance test 19 or later.
