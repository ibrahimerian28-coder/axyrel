"""Read-only checks for already identified Owner Review data and private files.
Capture before synthetic tests; verify all pre-existing rows/files are unchanged.
"""
import hashlib
import json
from pathlib import Path
import sys
from sqlalchemy import text
sys.path.insert(0,str(Path(__file__).resolve().parent))
import owner_review
SNAPSHOT=owner_review.STATE/"round1-preservation.json"
def current():
    config=json.loads(owner_review.CONFIG.read_text());engine=owner_review.verify(config)
    try:
        with engine.connect() as db:
            result={table:[dict(row) for row in db.execute(text("SELECT * FROM "+table)).mappings()] for table in ["customers","assets"]}
            result["ledger"]=list(db.execute(text("SELECT version,filename,checksum FROM axyrel_schema_migrations ORDER BY version")).tuples())
    finally:engine.dispose()
    result["files"]={str(p.relative_to(owner_review.STATE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (owner_review.STATE/"images").rglob("*") if p.is_file()}
    result["credentials_hash"]=hashlib.sha256((owner_review.STATE/"credentials.txt").read_bytes()).hexdigest()
    result["configuration_hash"]=hashlib.sha256(owner_review.CONFIG.read_bytes()).hexdigest()
    return json.loads(json.dumps(result,default=str))
def main():
    after=current()
    if len(sys.argv)>1 and sys.argv[1]=="capture":
        if SNAPSHOT.exists():raise RuntimeError("Existing preservation snapshot retained; refusing overwrite.")
        SNAPSHOT.write_text(json.dumps(after),encoding="utf-8");print("Captured private Owner Review preservation snapshot.");return
    before=json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    for table in ["customers","assets"]:
        rows={row["id"]:row for row in after[table]}
        for row in before[table]:
            if rows.get(row["id"])!=row:raise RuntimeError("A pre-existing Owner Review record changed; inspect privately.")
    for path,digest in before["files"].items():
        if after["files"].get(path)!=digest:raise RuntimeError("A pre-existing private image changed; inspect privately.")
    for field in ["ledger","credentials_hash","configuration_hash"]:
        if before[field]!=after[field]:raise RuntimeError("Owner Review ledger/configuration/credentials changed; inspect privately.")
    print("PASS: all pre-existing Customer/Asset rows, private images, migration ledger, configuration and credentials unchanged.")
if __name__=="__main__":main()
