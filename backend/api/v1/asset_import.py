"""Asset-only CSV preview/commit with bounded authenticated request bodies."""
import json
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authentication import CurrentAuthContext
from backend.core.authorization import Permission, require_permission
from backend.services.asset_import import FIELDS, validate_csv, preview_token, commit_import

router = APIRouter(prefix="/assets/import", tags=["asset import"], dependencies=[Depends(require_permission(Permission.ASSET_MANAGE)), Depends(require_permission(Permission.CUSTOMER_READ))])

async def payload(request):
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 7 * 1024 * 1024: raise HTTPException(413, "Import request is too large.")
    try:
        data = json.loads(body.decode("utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("csv"), str): raise ValueError()
        if len(data["csv"].encode("utf-8")) > 1024 * 1024: raise HTTPException(413, "CSV must be at most 1 MB.")
        return data
    except (ValueError, UnicodeError): raise HTTPException(400, "Expected a UTF-8 JSON request containing CSV text.") from None

@router.get("/template")
def template():
    return {"csv": ",".join(FIELDS) + "\n", "max_bytes":1048576, "max_rows":1000}

@router.post("/validate")
async def validate(request: Request, db: DBSession, company_id: CompanyID, context: CurrentAuthContext):
    data = await payload(request)
    result, _ = validate_csv(db, company_id, data["csv"])
    if result["valid"]: result["token"] = preview_token(data["csv"], company_id, context.user.id)
    return result

@router.post("/commit")
async def commit(request: Request, db: DBSession, company_id: CompanyID, context: CurrentAuthContext):
    data = await payload(request)
    try:
        result = commit_import(db, company_id, context.user.id, data["csv"], data.get("token", ""), data.get("idempotency_key", ""))
        if not result["valid"]:
            db.rollback()
            return result
        db.commit()
        return result
    except (ValueError, jwt.PyJWTError):
        db.rollback()
        raise HTTPException(400, "Invalid or expired preview/retry key. Validate again without changing a pending retry.") from None
    except Exception:
        db.rollback()
        raise
