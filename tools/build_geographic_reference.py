"""Rebuild pinned ISO/phone reference and Egypt GeoNames locality suggestions.
Usage: python tools/build_geographic_reference.py admin1CodesASCII.txt EG.zip
Download inputs from https://download.geonames.org/export/dump/ .
GeoNames CC BY 4.0; pycountry ISO data and libphonenumber regional metadata.
"""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import pycountry
import phonenumbers
ROOT = Path(__file__).resolve().parents[1]
# Reviewed mapping between two published code systems, not fabricated hierarchy.
EG_CODES = {"01":"DK","02":"BA","03":"BH","04":"FYM","05":"GH","06":"ALX","07":"IS","08":"GZ","09":"MNF","10":"MN","11":"C","12":"KB","13":"WAD","14":"SHR","15":"SUZ","16":"ASN","17":"AST","18":"BNS","19":"PTS","20":"DT","21":"KFS","22":"MT","23":"KN","24":"SHG","26":"JS","27":"SIN","28":"LX"}
def build(admin_file, egypt_file):
    egypt_names = {}
    for line in admin_file.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if parts[0].startswith("EG.") and parts[0][3:] in EG_CODES:
            egypt_names["EG-"+EG_CODES[parts[0][3:]]] = parts[1]
    areas = {}
    with zipfile.ZipFile(egypt_file) as archive:
        for line in archive.read("EG.txt").decode("utf-8").splitlines():
            row = line.split("\t")
            if row[6]=="P" and row[10] in EG_CODES:
                state = "EG-"+EG_CODES[row[10]]
                areas.setdefault(state,set()).add(row[2] or row[1])
    countries = [dict(code=c.alpha_2,name=c.name,callingCode=phonenumbers.country_code_for_region(c.alpha_2)) for c in pycountry.countries]
    states = {}
    for s in pycountry.subdivisions:
        states.setdefault(s.country_code,[]).append(dict(code=s.code,name=egypt_names.get(s.code,s.name)))
    data = dict(countries=sorted(countries,key=lambda c:c["name"]),states={k:sorted(v,key=lambda s:s["name"]) for k,v in states.items()},areas={k:sorted(v) for k,v in areas.items()},source=dict(pycountry=pycountry.__version__,phonenumbers=phonenumbers.__version__,geonames="https://www.geonames.org/",license="GeoNames CC BY 4.0",downloaded="2026-10-05",admin_sha256=hashlib.sha256(admin_file.read_bytes()).hexdigest(),egypt_sha256=hashlib.sha256(egypt_file.read_bytes()).hexdigest()))
    (ROOT/"frontend/src/features/phase2/geography.json").write_text(json.dumps(data,ensure_ascii=True,separators=(",",":")),encoding="utf-8")
    print("Generated countries:",len(countries),"Egypt governorates:",len(egypt_names),"Egypt locality suggestions:",sum(len(v) for v in areas.values()))
if __name__=="__main__":build(Path(sys.argv[1]),Path(sys.argv[2]))
