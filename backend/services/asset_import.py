"""Bounded, create-only Asset CSV import; no other entity bulk operations."""
import csv
import hashlib
import io
import re
import time
from uuid import UUID, uuid5, NAMESPACE_URL

import jwt
from pydantic import ValidationError
from sqlalchemy import select
from backend.core.config import get_settings
from backend.models.asset import Asset
from backend.models.customer import Customer
from backend.models.audit_log import AuditLog
from backend.schemas.asset import AssetCreate
from backend.services.asset import AssetService
from backend.core.asset_lock import lock_assets

MAX_BYTES = 1024 * 1024
MAX_ROWS = 1000
FIELDS = ["customer_reference", "asset_type", "serial_number", "model", "manufacturer",
          "installation_date", "warranty_start", "warranty_end", "status", "notes"]


def serial_key(value):
    # Comparison only: remove surrounding Unicode whitespace; case-sensitive.
    # No case folding, Unicode normalization or alteration of stored values.
    return (value or "").strip()


def validate_csv(db, company_id, source):
    errors, preview, prepared = [], [], []
    def error(row, column, code, message):
        errors.append(dict(row=row, column=column, code=code, message=message))
    if not isinstance(source, str) or len(source.encode("utf-8")) > MAX_BYTES:
        error(0, "file", "size", "CSV must be UTF-8 and at most 1 MB.")
        return dict(valid=False, rows=0, preview=[], errors=errors), []
    if "\x00" in source:
        error(0, "file", "content", "NUL bytes are not allowed.")
        return dict(valid=False, rows=0, preview=[], errors=errors), []
    customers = list(db.scalars(select(Customer).where(Customer.company_id == company_id, Customer.status != "Deleted")))
    existing = {serial_key(s) for s in db.scalars(select(Asset.serial_number).where(Asset.company_id == company_id)) if serial_key(s)}
    seen = set()
    count = 0
    try:
        reader = csv.reader(io.StringIO(source.lstrip("\ufeff"), newline=""), strict=True)
        headers = next(reader, [])
        if len(headers) != len(set(headers)) or any(h not in FIELDS for h in headers) or not {"customer_reference", "asset_type"}.issubset(headers):
            error(1, "headers", "headers", "Use unique supported headers including customer_reference and asset_type.")
            return dict(valid=False, rows=0, preview=[], errors=errors), []
        for count, values in enumerate(reader, 1):
            row_number = reader.line_num
            if count > MAX_ROWS:
                error(row_number, "file", "rows", "CSV must contain at most 1000 data rows.")
                break
            if len(values) != len(headers):
                error(row_number, "row", "columns", "Row has a different number of columns than the header.")
                continue
            data = dict(zip(headers, values))
            reference = data.pop("customer_reference").strip()
            matches = [c for c in customers if c.display_id is not None and str(c.display_id) == reference and reference.isdecimal()]
            if len(matches) != 1:
                error(row_number, "customer_reference", "customer", "Customer reference must identify one visible customer in your company.")
            data = {k: v if v != "" else None for k, v in data.items()}
            if not data.get("status"): data["status"] = "Active"
            if not str(data.get("asset_type") or "").strip(): error(row_number, "asset_type", "required", "Asset type is required.")
            if data["status"] == "Deleted": error(row_number, "status", "status", "Import cannot create deleted Assets.")
            for field, limit in {"asset_type":150, "serial_number":150, "model":150, "manufacturer":150, "status":30, "notes":1000}.items():
                if data.get(field) and len(data[field]) > limit: error(row_number, field, "length", f"Maximum {limit} characters.")
            serial = serial_key(data.get("serial_number"))
            if serial:
                if serial in seen: error(row_number, "serial_number", "duplicate_file", "Serial number repeats in this file.")
                if serial in existing: error(row_number, "serial_number", "duplicate_tenant", "Serial number already belongs to an Asset in your company.")
                seen.add(serial)
            for field in ["installation_date", "warranty_start", "warranty_end"]:
                if data.get(field) and not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", data[field]): error(row_number, field, "date", "Use an ISO date (YYYY-MM-DD).")
            if matches:
                data["customer_id"] = matches[0].id
                try:
                    validated = AssetCreate.model_validate(data).model_dump()
                    prepared.append(validated)
                except ValidationError as exc:
                    for problem in exc.errors(include_input=False):
                        error(row_number, str(problem["loc"][0]), "field_type", "Invalid field value; dates must use YYYY-MM-DD.")
                preview.append({"row":row_number, "customer":matches[0].name, **{k:str(v) if v is not None else "" for k,v in data.items() if k != "customer_id"}})
    except (csv.Error, UnicodeError):
        error(0, "file", "csv", "Malformed UTF-8 CSV; use comma-separated columns and valid quoting.")
    if not count: error(0, "file", "empty", "CSV needs at least one data row.")
    return dict(valid=not errors, rows=count, preview=preview, errors=errors), prepared


def checksum(source):
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def preview_token(source, company_id, user_id):
    return jwt.encode(dict(purpose="asset-import", company=str(company_id), user=str(user_id), sha=checksum(source), exp=int(time.time()) + 900), get_settings().secret_key, algorithm="HS256")


def commit_import(db, company_id, user_id, source, token, retry_key):
    claims = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"], options={"verify_exp":False, "require":["exp"]})
    if claims.get("purpose") != "asset-import" or claims.get("company") != str(company_id) or claims.get("user") != str(user_id) or claims.get("sha") != checksum(source):
        raise ValueError("Preview does not match this file or account. Validate again.")
    retry_key = str(UUID(retry_key))
    lock_assets(db, company_id)
    receipt_id = uuid5(NAMESPACE_URL, f"axyrel:asset-import:{company_id}:{user_id}:{retry_key}")
    receipt = db.scalar(select(AuditLog).where(AuditLog.id == receipt_id,
        AuditLog.company_id == company_id, AuditLog.actor_user_id == user_id,
        AuditLog.action == "ASSET_IMPORT_COMMITTED"))
    if receipt:
        if receipt.event_metadata.get("checksum") != checksum(source): raise ValueError("Retry key was already used for a different file.")
        return {**receipt.event_metadata["result"], "replayed":True}
    if claims["exp"] < time.time(): raise ValueError("Preview expired. Validate again.")
    result, rows = validate_csv(db, company_id, source)
    if not result["valid"]: return result
    # Lock referenced customers through creation so soft deletion cannot race validation.
    db.execute(select(Customer).where(Customer.id.in_([r["customer_id"] for r in rows]), Customer.company_id == company_id).order_by(Customer.id).with_for_update()).all()
    result, rows = validate_csv(db, company_id, source)
    if not result["valid"]: return result
    service = AssetService()
    created = [service.create_asset(db, company_id, dict(row)) for row in rows]
    response = dict(valid=True, created=len(created), display_ids=[a.display_id for a in created], replayed=False)
    db.add(AuditLog(id=receipt_id, company_id=company_id, actor_user_id=user_id, action="ASSET_IMPORT_COMMITTED", entity_type="asset_import", event_metadata={"checksum":checksum(source), "result":response}))
    db.flush()
    return response
