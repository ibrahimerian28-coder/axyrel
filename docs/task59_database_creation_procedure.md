# Task 59 — Production Database Creation and Migration Procedure

Authority: OD-20 and OD-21. Task 59 validates the current MVP schema on an isolated local PostgreSQL database; Task 60 adds checksum-verified migration tracking. **No live production database or deployment exists as a result of these tasks.** An owner-approved hosting target, operational access and deployment decisions are required before applying this procedure to production.

## Verified local readiness

Run from D:\Axyrel_BACKUP_BEFORE_GEMINI:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_task59_database_readiness.py
```

The test requires the existing configured local PostgreSQL server and CREATE DATABASE privilege through its maintenance database. It refuses nonlocal hosts, creates a UUID-named axyrel_task59_test_* database, runs the actual initializer against that generated target and closes connections before dropping only that database. The configured application database is never connected to or changed. No production credentials are requested or stored.

No ORM create_all is used to build the schema. The twelve accepted files run in deterministic numeric order: 001, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012 and 013. There is no migration 002 in the accepted chain; do not invent one. Migrations 012/013 convert the approved Schedule and Service Visit event columns on the empty tables. Task 60 adds the separate infrastructure table axyrel_schema_migrations; it is not a business model or customer-data table.

Verification checks all seventeen ORM tables and exact column names, model foreign keys, NUMERIC(12,2) money columns, approved event TIMESTAMPTZ types/nullability, unchanged naive created_at columns, existing identity/inventory uniqueness and check constraints, ORM reads, the existing schema verifier, and zero seeded rows. This is schema-build readiness evidence; it does not certify hosting, performance, backups, production permissions, deployment security or real historical data migration.

## Later fresh production creation

1. Obtain explicit owner approval for the target PostgreSQL server/provider, database name, schema, database owner, access and operational security. Do not infer these from local development settings. Confirm the target is a new empty database and coordinate the accepted application version. Secure credentials outside Git and command history; do not print connection strings.
2. On that approved server, an authorized database administrator creates the database. Substitute only reviewed identifiers in this SQL template; do not paste untrusted names into SQL:

   ```sql
   CREATE DATABASE "APPROVED_DATABASE_NAME"
       OWNER "APPROVED_DATABASE_OWNER"
       TEMPLATE template0
       ENCODING 'UTF8';
   ```

   Provision the owner/access policy separately using the approved host's administration mechanism. Task 59 does not choose, create or grant a production role. If the target already contains schema objects, review its trustworthy migration history first. An untracked target requires an explicit owner-approved baseline/reconciliation procedure; never drop, reset or stamp it automatically.
3. Configure DATABASE_URL securely for exactly the approved new target with the approved connection security. Confirm database identity and schema/search_path independently. The current migration scripts operate in the connection's schema, and timezone migrations inspect current_schema(). The local test uses public. A different production schema needs an explicitly reviewed configuration.
4. From the approved checkpoint, run the tracked initializer against the approved target:

   ```powershell
   .\.venv\Scripts\python.exe -B -m backend.scripts.init_database
   .\.venv\Scripts\python.exe -B -m backend.scripts.verify_database_schema
   ```

   The target is selected by secure DATABASE_URL configuration, not by a database name guessed in the command. The runner never prints the connection URL. Review OK results for pending migrations and SKIP (verified) for recorded migrations. On a fresh target there must be twelve OK results including 012/013; a verified rerun must skip all twelve. A nonzero exit or missing success marker is a failure; do not serve the application until the migration state is reviewed.
5. Verify the detailed schema checks above, an empty data population and an explicit-offset read of synthetic approved event data before release. Initial identity/setup, existing-data import, operational backup/restore and serving production traffic remain separately authorized roadmap work. Do not seed customer data or reuse disposable credentials as part of this procedure.

## Repeat execution, failure and existing databases

Under OD-21, the runner creates axyrel_schema_migrations only in an empty target schema. Each success record stores numeric version, exact filename, SHA-256 checksum of raw file bytes and TIMESTAMPTZ applied_at. Applied history must match an ordered prefix of current files. Missing/renamed files, checksum changes, duplicate numeric versions and inserted earlier versions fail safely. Preserve migration file bytes, including line endings, across deployment; do not silently normalize checksums or rewrite history.

All recorded identities/checksums are verified before pending migrations run. Only verified applied files are skipped, so 012/013 retain their one-time SQL guards without being re-executed on reruns. A schema containing objects without a ledger, or an empty ledger alongside existing objects, is refused. There is no automatic baseline or ledger-rewrite option. Ledger trust assumes controlled administrative access; it is not protection against manual database/history tampering.

Each pending migration and its success record share one PostgreSQL transaction. The historical outer BEGIN/COMMIT wrappers in 012/013 are removed only in memory, leaving the accepted source files and their raw checksums unchanged. Unsupported transaction control or ambiguous escaped-string/nested-comment syntax requires review rather than uncontrolled execution. A session advisory lock serializes cooperative runners for the selected database/schema.

A failed migration or ledger insertion rolls back that migration's effects and creates no success record. Earlier successful migrations remain committed; the whole chain is not one atomic transaction. After diagnosing a failure, rerun only a reviewed pending migration plan: verified earlier entries will skip. Never edit already-applied SQL or delete ledger rows to force reapplication. Existing untracked databases need separately owner-approved reconciliation. No actual production deletion/recreation is authorized. Disposable test cleanup is restricted to generated databases.

Run the mechanism acceptance suite locally with `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_task60_tracked_migrations.py`. It uses only generated local PostgreSQL databases, including rollback, checksum, untracked-schema and cooperative concurrency cases.

Existing populated databases require a separately reviewed upgrade path. For historical event conversions use docs/task52_timezone_migration.md and docs/task53_timezone_migration.md, including backups, Cairo writer/offset review, exclusive locks and rollback considerations. Never run all files blindly against populated production data. Destructive, ambiguous or business-semantic decisions require the owner gate.
