# Persistent LOCAL Owner Review

From PowerShell in `D:\Axyrel_BACKUP_BEFORE_GEMINI`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/Start-OwnerReview.ps1
```

Open http://127.0.0.1:3140/login. Read the local admin/technician credentials in `.owner-review/credentials.txt`; do not publish that file. Keep the launcher terminal open. Ctrl+C stops its servers; relaunch the same command after a server or PC restart. The execution-policy override applies only to this process.

The prepared environment uses PostgreSQL 17 on local port 5432, a separately generated `axyrel_owner_review_<random hex>` database, and persistent private images under `.owner-review/images`. It uses neither the configured application database nor disposable test databases. Customer/Asset records and images are retained on disk. Initialization applies the existing migration ledger only to the new database; no migration history was added or modified. Synthetic seed identities and records are local-review only.

Before startup, the helper checks the local database identity against its PostgreSQL catalog marker before connecting to that application database. Missing/ambiguous identity, incomplete initialization, unknown directory contents, and occupied review ports stop startup; existing databases and processes are left untouched. Subsequent launches never reseed or reset the database. The private directory has Windows ACLs for the workspace owner and initializing account, and is Git-ignored. Back up the identified database and the private configuration/images together; never delete the directory as a reset procedure.

PostgreSQL must already be available on localhost:5432. The installed `postgresql-x64-17` service is configured Automatic; during validation the server was running against `C:/Program Files/PostgreSQL/17/data` outside that service while its status was Stopped. After a PC restart, if PostgreSQL is unavailable, verify that installed service/cluster identity before starting it. The launcher does not start, stop or reconfigure PostgreSQL, and does not connect to remote servers. An actual PC reboot was not performed.

The existing Python virtual environment and built frontend are required. If the production build is missing, build before starting review:

```powershell
Set-Location frontend
npm.cmd run build
Set-Location ..
```

Do not rebuild while the review frontend is running. API: loopback 8140; frontend: loopback 3140. There is no deployment or public anonymous image access. API logs and browser-review artifacts remain inside the private directory.

Read-only browser smoke check while review is running:

```powershell
Set-Location frontend
npx.cmd playwright test --config playwright.owner-review.config.ts
```

Safety unit tests, from root: `.\.venv\Scripts\python.exe -B tests/test_owner_review_safety.py`.
The optional `.\.venv\Scripts\python.exe -B tools/check_owner_review_persistence.py` creates a uniquely tagged synthetic Customer/Asset, uploads private images, verifies them in a separate application process, then removes images and soft-deletes only those synthetic records through the normal APIs. It never resets the environment. Two successful runs demonstrated persistence across independent application processes, not a physical reboot.
