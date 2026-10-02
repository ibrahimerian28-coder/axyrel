# Task 59 — Production Database Creation and Migration Procedure

Authority: OD-20. Task 59 validates the current MVP schema on an isolated local PostgreSQL database. **No live production database or deployment exists as a result of this task.** An owner-approved hosting target, operational access and deployment decisions are required before applying this procedure to production.

## Verified local readiness

Run from D:\Axyrel_BACKUP_BEFORE_GEMINI:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_task59_database_readiness.py
```

The test requires the existing configured local PostgreSQL server and CREATE DATABASE privilege through its maintenance database. It refuses nonlocal hosts, creates a UUID-named axyrel_task59_test_* database, runs the actual initializer against that generated target and closes connections before dropping only that database. The configured application database is never connected to or changed. No production credentials are requested or stored.

No ORM create_all is used to build the schema. The twelve accepted files run in filename order: 001, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012 and 013. There is no migration 002 in the accepted chain; do not invent one. Migrations 012/013 convert the approved Schedule and Service Visit event columns on the empty tables.

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

   Provision the owner/access policy separately using the approved host's administration mechanism. Task 59 does not choose, create or grant a production role. If a database already exists or contains any tables/data, stop and review its migration state rather than drop, reset or apply the fresh-build procedure.
3. Configure DATABASE_URL securely for exactly the approved new target with the approved connection security. Confirm database identity and schema/search_path independently. The current migration scripts operate in the connection's schema, and timezone migrations inspect current_schema(). The local test uses public. A different production schema needs an explicitly reviewed configuration.
4. From the approved checkpoint, run the actual initializer once against the empty target:

   ```powershell
   .\.venv\Scripts\python.exe -B -m backend.scripts.init_database
   .\.venv\Scripts\python.exe -B -m backend.scripts.verify_database_schema
   ```

   The target is selected by secure DATABASE_URL configuration, not by a database name guessed in the command. Capture migration filenames/results without credentials. Review all twelve successful results including 012/013. A nonzero exit or missing success marker is a failure; do not serve the application or blindly rerun the initializer.
5. Verify the detailed schema checks above, an empty data population and an explicit-offset read of synthetic approved event data before release. Initial identity/setup, existing-data import, operational backup/restore and serving production traffic remain separately authorized roadmap work. Do not seed customer data or reuse disposable credentials as part of this procedure.

## Repeat execution, failure and existing databases

The initializer's old docstring describes idempotence, but the complete current chain is **not a repeatable all-migrations upgrade command**: 012/013 deliberately refuse already-converted columns. No migration ledger or framework is introduced in Task 59. Task 60 owns future migration tooling scope.

The initializer uses an outer SQLAlchemy transaction, while 012/013 contain explicit BEGIN/COMMIT. Do not promise full-chain rollback: a failure may leave an empty target partially initialized or earlier work committed. Stop, inspect exact applied filenames and schema, and obtain approval for recovery. Task 59 does not authorize deleting/recreating an actual production database. The disposable test's cleanup is restricted to its generated database.

Existing populated databases require a separately reviewed upgrade path. For historical event conversions use docs/task52_timezone_migration.md and docs/task53_timezone_migration.md, including backups, Cairo writer/offset review, exclusive locks and rollback considerations. Never run all files blindly against populated production data. Destructive, ambiguous or business-semantic decisions require the owner gate.
