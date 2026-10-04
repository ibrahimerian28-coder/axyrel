"""Separate application lifetimes verify tagged synthetic review records/images."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import owner_review

def run(action):
    config = json.loads(owner_review.CONFIG.read_text())
    engine = owner_review.verify(config); engine.dispose()
    os.environ.update(DATABASE_URL=config["database_url"], SECRET_KEY=config["secret"], AXYREL_PRIVATE_IMAGE_ROOT=str(owner_review.STATE / "images"), AXYREL_ENV="development")
    from backend.core.config import get_settings
    get_settings.cache_clear()
    import backend.core.config as configuration
    configuration.settings = get_settings()
    from backend.main import app
    from backend.core.database import engine as application_engine
    from fastapi.testclient import TestClient
    state_file = owner_review.STATE / "persistence-check.json"
    password = (owner_review.STATE / "credentials.txt").read_text().split("Password: ")[1].strip()
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/login", data={"username":"owner@axyrel.local", "password":password})
        assert response.status_code == 200
        headers = {"Authorization":"Bearer " + response.json()["access_token"]}
        if action == "write":
            if state_file.exists(): raise RuntimeError("A previous synthetic persistence case needs review before another run.")
            tag = "Synthetic Persistence " + uuid4().hex
            customer = client.post("/api/v1/customers", headers=headers, json={"name":tag}).json()
            asset = client.post("/api/v1/assets", headers=headers, json={"customer_id":customer["id"], "asset_type":tag, "serial_number":tag}).json()
            saved = {"tag":tag,"customers":customer["id"],"assets":asset["id"],"hashes":{}}
            state_file.write_text(json.dumps(saved))
            for kind in ["customers", "assets"]:
                path=f'/api/v1/{kind}/{saved[kind]}/image'
                response=client.put(path, headers={**headers,"Content-Type":"image/png"},content=(ROOT/"frontend/tests/fixtures/profile.png").read_bytes())
                assert response.status_code==204, response.text
                saved["hashes"][kind]=hashlib.sha256(client.get(path,headers=headers).content).hexdigest()
            state_file.write_text(json.dumps(saved))
        else:
            saved=json.loads(state_file.read_text())
            for kind in ["customers", "assets"]:
                path=f'/api/v1/{kind}/{saved[kind]}'
                response=client.get(path,headers=headers);assert response.status_code==200
                assert response.json()["name" if kind=="customers" else "asset_type"]==saved["tag"]
                if action=="read":
                    image=client.get(path+"/image",headers=headers);assert image.status_code==200
                    assert hashlib.sha256(image.content).hexdigest()==saved["hashes"][kind]
                else:
                    assert client.delete(path+"/image",headers=headers).status_code==204
                    assert client.delete(path,headers=headers).status_code==204
            if action=="cleanup":state_file.unlink()
    application_engine.dispose()

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--step",choices=["write","read","cleanup"]);args=parser.parse_args()
    if args.step:run(args.step)
    else:
        for step in ["write","read","cleanup"]:
            subprocess.run([sys.executable,"-B",str(Path(__file__).resolve()),"--step",step],check=True,cwd=ROOT)
        print("PASS: Customer and Asset records/images persisted across separate application processes; tagged synthetic case cleaned up.")
