"""Persistent LOCAL owner review only; never reuse an unknown database."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
STATE = ROOT / ".owner-review"
CONFIG = STATE / "configuration.json"
os.environ["AXYREL_ENV"]="development"
from backend.core.config import Settings, get_settings


def check_url(raw):
    url=make_url(raw)
    if url.get_backend_name()!="postgresql" or url.host not in {"localhost","127.0.0.1","::1"}:
        raise RuntimeError("Owner review requires a known local PostgreSQL server.")
    return url


def verify(config):
    url=check_url(config["database_url"])
    if not re.fullmatch(r"axyrel_owner_review_[0-9a-f]{32}",url.database or ""):
        raise RuntimeError("Owner review database identity is unexpected; refusing access.")
    if not re.fullmatch(r"[0-9a-f]{32}", config["identity"]):
        raise RuntimeError("Owner review identity is malformed; refusing access.")
    # Inspect the catalog through postgres before connecting to the application
    # database. An unknown database must never be reused, even for initialization.
    admin=create_engine(url.set(database="postgres"))
    try:
        with admin.connect() as db:
            marker=db.execute(text("SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname=:name"), {"name":url.database}).scalar()
            if marker!="axyrel-owner-review:"+config["identity"]:
                raise RuntimeError("Database marker does not match private local configuration; refusing access.")
    finally:
        admin.dispose()
    return create_engine(url)


def initialize():
    if CONFIG.exists():
        config=json.loads(CONFIG.read_text()); engine=verify(config); engine.dispose()
        if not config.get("ready"): raise RuntimeError("Initialization is incomplete. Review the local state before continuing.")
        print("Existing identified owner review environment preserved; no seed or reset performed."); return
    if STATE.exists() and any(STATE.iterdir()): raise RuntimeError("Unknown owner-review directory contents; refusing initialization.")
    STATE.mkdir(exist_ok=True)
    if os.name=="nt":
        identity=subprocess.check_output(["whoami"],text=True).strip()
        # The sandbox service account and actual workspace owner can differ.
        owner=subprocess.check_output(["powershell.exe","-NoProfile","-Command","(Get-Acl -LiteralPath '"+str(ROOT).replace("'","''")+"').Owner"],text=True).strip()
        subprocess.run(["icacls",str(STATE),"/inheritance:r","/grant:r",identity+":(OI)(CI)F",owner+":(OI)(CI)F"],check=True,capture_output=True)
    else: STATE.chmod(0o700)
    url=check_url(Settings(_env_file=ROOT/".env").database_url)
    name="axyrel_owner_review_"+uuid4().hex; identity=uuid4().hex
    admin=create_engine(url.set(database="postgres"),isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as db:
            if db.execute(text("SELECT 1 FROM pg_database WHERE datname=:name"),{"name":name}).scalar():
                raise RuntimeError("Generated database already exists; refusing to reuse it.")
            db.exec_driver_sql(f'CREATE DATABASE "{name}"')
            db.exec_driver_sql(f"COMMENT ON DATABASE \"{name}\" IS 'axyrel-owner-review:{identity}'")
    finally: admin.dispose()
    config={"identity":identity,"database_url":url.set(database=name).render_as_string(hide_password=False),"secret":secrets.token_urlsafe(48),"ready":False}
    CONFIG.write_text(json.dumps(config,indent=2)); CONFIG.chmod(0o600)
    engine=verify(config)
    try:
        from backend.scripts.init_database import apply_migrations
        apply_migrations(engine,ROOT/"migrations")
        from sqlalchemy.orm import Session
        from backend.models.company import Company
        from backend.models.user import User
        from backend.models.customer import Customer
        from backend.models.asset import Asset
        from backend.core.security import hash_password
        password=secrets.token_urlsafe(18)
        with Session(engine) as db, db.begin():
            company=Company(id=uuid4(),name="Axyrel Local Owner Review",status="active"); db.add(company);db.flush()
            for email,role,name in [("owner@axyrel.local","admin","Owner Review"),("technician@axyrel.local","technician","Review Technician")]:
                db.add(User(company_id=company.id,email=email,full_name=name,role=role,password_hash=hash_password(password)))
            customer=Customer(company_id=company.id,display_id=1001,name="Synthetic Review Customer",phone="+201000000001",status="Active");db.add(customer);db.flush()
            db.add(Asset(company_id=company.id,customer_id=customer.id,display_id=1,asset_type="Synthetic Review Device",serial_number="REVIEW-001",status="Active"))
        (STATE/"credentials.txt").write_text("LOCAL REVIEW ONLY\nAdmin: owner@axyrel.local\nTechnician: technician@axyrel.local\nPassword: "+password+"\n")
        (STATE/"credentials.txt").chmod(0o600)
        (STATE/"images").mkdir(exist_ok=True)
        config["ready"]=True;CONFIG.write_text(json.dumps(config,indent=2))
        print("Persistent local review initialized. Credentials: .owner-review/credentials.txt")
    finally:engine.dispose()


def migrate():
    """Apply only owner-approved additive migrations to the identified review DB."""
    config=json.loads(CONFIG.read_text()); engine=verify(config)
    try:
        if not config.get("ready"): raise RuntimeError("Review initialization is incomplete.")
        from backend.scripts.init_database import apply_migrations
        apply_migrations(engine, ROOT/"migrations")
    finally: engine.dispose()


def repair_image_permissions():
    """Repair Python 3.13 creator-only Windows directories, preserving files."""
    config=json.loads(CONFIG.read_text()); engine=verify(config); engine.dispose()
    root=STATE/"images"
    if os.name!="nt": return
    if root.is_symlink(): raise RuntimeError("Unexpected image-root link; refusing ACL repair.")
    owner=subprocess.check_output(["powershell.exe","-NoProfile","-Command","(Get-Acl -LiteralPath '"+str(ROOT).replace("'","''")+"').Owner"],text=True).strip()
    identity=subprocess.check_output(["whoami"],text=True).strip()
    # Touch only directories/files physically beneath the verified private image root.
    for path in [root,*root.rglob("*")]:
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise RuntimeError("Unexpected private image link; refusing ACL repair.")
        grant=[identity+":(OI)(CI)F",owner+":(OI)(CI)F"] if path.is_dir() else [identity+":F",owner+":F"]
        subprocess.run(["icacls",str(path),"/grant:r",*grant],check=True,capture_output=True)
    print("Private image permissions repaired for the review account; files retained.")


def serve():
    config=json.loads(CONFIG.read_text());engine=verify(config);engine.dispose()
    if not config.get("ready"):raise RuntimeError("Owner review initialization is incomplete.")
    os.environ.update(DATABASE_URL=config["database_url"],SECRET_KEY=config["secret"],AXYREL_PRIVATE_IMAGE_ROOT=str(STATE/"images"),AXYREL_ENV="development")
    get_settings.cache_clear()
    import backend.core.config as configuration
    configuration.settings=get_settings()
    os.chdir(STATE) # No workspace dotenv or transient image directory fallback.
    from backend.main import app
    import uvicorn
    uvicorn.run(app,host="127.0.0.1",port=8140,log_level="warning",access_log=False)


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("action",choices=["init","verify","serve","migrate","repair-images"]);args=parser.parse_args()
    if args.action=="init":initialize()
    elif args.action=="verify":
        engine=verify(json.loads(CONFIG.read_text()));engine.dispose();print("Owner review database identity verified.")
    elif args.action=="migrate":migrate()
    elif args.action=="repair-images":repair_image_permissions()
    else:serve()
