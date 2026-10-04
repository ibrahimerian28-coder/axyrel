"""Authorized image access uses exactly the existing record permissions/scope."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool
from anyio import CapacityLimiter, to_thread
from backend.api.dependencies import CompanyID, DBSession
from backend.core.authorization import Permission, require_permission
from backend.services.customer import CustomerService
from backend.services.asset import AssetService
from backend.services.profile_images import (
    ImageStorage, MAX_UPLOAD, get_image_storage, image_key, process_image,
)

image_processing_limit = CapacityLimiter(2)


def image_router(resource: str, read: Permission, manage: Permission):
    router = APIRouter(prefix=f"/{resource}", tags=[resource])
    lookup = CustomerService().get_customer if resource == "customers" else AssetService().get_asset

    def key_for(db, company_id, record_id):
        if lookup(db, company_id, record_id) is None:
            raise HTTPException(404, "Record not found.")
        return image_key(company_id, resource, record_id)

    @router.get("/{record_id}/image", dependencies=[Depends(require_permission(read))])
    def get_image(record_id: UUID, db: DBSession, company_id: CompanyID,
                  storage: ImageStorage = Depends(get_image_storage)):
        data = storage.read(key_for(db, company_id, record_id))
        if data is None:
            raise HTTPException(404, "No profile image.")
        return Response(data, media_type="image/webp", headers={
            "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
            "Content-Disposition": 'inline; filename="profile.webp"',
        })

    @router.put("/{record_id}/image", status_code=204, dependencies=[Depends(require_permission(manage))])
    async def put_image(record_id: UUID, request: Request, db: DBSession, company_id: CompanyID,
                        storage: ImageStorage = Depends(get_image_storage)):
        key = key_for(db, company_id, record_id)
        data = bytearray()
        async for chunk in request.stream():
            if len(data) + len(chunk) > MAX_UPLOAD:
                raise HTTPException(413, "Image must be 5 MB or smaller.")
            data.extend(chunk)
        mime = request.headers.get("content-type", "").split(";", 1)[0].lower()
        processed = await to_thread.run_sync(process_image, bytes(data), mime, limiter=image_processing_limit)
        await run_in_threadpool(storage.replace, key, processed)
        return Response(status_code=204)

    @router.delete("/{record_id}/image", status_code=204, dependencies=[Depends(require_permission(manage))])
    def delete_image(record_id: UUID, db: DBSession, company_id: CompanyID,
                     storage: ImageStorage = Depends(get_image_storage)):
        storage.remove(key_for(db, company_id, record_id))
        return Response(status_code=204)

    return router


router = APIRouter()
router.include_router(image_router("customers", Permission.CUSTOMER_READ, Permission.CUSTOMER_MANAGE))
router.include_router(image_router("assets", Permission.ASSET_READ, Permission.ASSET_MANAGE))
