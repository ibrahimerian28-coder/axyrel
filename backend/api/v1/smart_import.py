"""Authenticated Smart Import; mode-specific authorization and bounded JSON bodies."""
import json
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from backend.api.dependencies import DBSession, CompanyID
from backend.core.authentication import CurrentAuthContext
from backend.core.authorization import Permission, require_permission, has_permission
from backend.services import smart_import as service
from backend.services.smart_import_files import parse_file, template, MODES

router = APIRouter(prefix='/imports', tags=['smart import'], dependencies=[Depends(require_permission(Permission.CUSTOMER_READ))])


def authorize(context, mode):
    if not isinstance(mode, str) or mode not in MODES: raise HTTPException(400, 'Choose Customers only, Assets only, or Customers + Assets.')
    required = ([Permission.CUSTOMER_MANAGE] if mode != 'assets' else []) + ([Permission.ASSET_MANAGE] if mode != 'customers' else [])
    if any(not has_permission(context.user.role, permission) for permission in required): raise HTTPException(403, 'Insufficient permissions for this import type.')


async def payload(request):
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > 7 * 1048576: raise HTTPException(413, 'Import request is too large.')
        body.extend(chunk)
    try:
        data = json.loads(body.decode('utf-8'))
        if not isinstance(data, dict): raise ValueError()
        return data
    except (ValueError, UnicodeError): raise HTTPException(400, 'Expected a valid import request.') from None


@router.get('/template')
def get_template(context: CurrentAuthContext, mode: str = 'combined', format: str = 'xlsx'):
    authorize(context, mode)
    try: return template(mode, format)
    except ValueError as exc: raise HTTPException(400, str(exc)) from None


@router.post('/upload')
async def upload(request: Request, context: CurrentAuthContext):
    data = await payload(request); authorize(context, data.get('mode'))
    try: return parse_file(data.get('content'), data.get('format'))
    except ValueError as exc: raise HTTPException(400, str(exc)) from None


@router.post('/preview')
async def preview(request: Request, db: DBSession, company_id: CompanyID, context: CurrentAuthContext):
    data = await payload(request); authorize(context, data.get('mode'))
    try:
        result, plan = service.validate(db, company_id, data)
        if result['valid']: result['token'] = service.preview_token(data, company_id, context.user.id, plan)
        return result
    except ValueError as exc: raise HTTPException(400, str(exc)) from None


@router.post('/commit')
async def commit(request: Request, db: DBSession, company_id: CompanyID, context: CurrentAuthContext):
    payload_data = await payload(request)
    data = payload_data.get('data')
    if not isinstance(data, dict): raise HTTPException(400, 'Review the import first.')
    authorize(context, data.get('mode'))
    try:
        result = service.commit(db, company_id, context.user.id, data, payload_data.get('token', ''), payload_data.get('idempotency_key', ''))
        if result['valid']: db.commit()
        else: db.rollback()
        return result
    except (ValueError, jwt.PyJWTError):
        db.rollback()
        raise HTTPException(400, 'Review expired or rows/customer matches changed. Review again; keep an uncertain retry unchanged.') from None
    except Exception:
        db.rollback()
        raise
