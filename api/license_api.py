from fastapi import APIRouter, Depends, HTTPException
from service.license_service_manager.license_service_manager import LicenseServiceManager
from starlette import status
from starlette.responses import RedirectResponse
from models.license_model.license_model import AddLicenseModel, CheckLicenseModel


license_router = APIRouter(tags=["LICENSE API"], prefix="/license")


@license_router.get('/ping')
async def license_ping():
    return {"status": "LICENSE PINGING"}


@license_router.post("/addlicense")
async def add_license(add_license_info: AddLicenseModel):
    _license_info = await LicenseServiceManager.add_license(add_license_info)
    if _license_info:
        return _license_info
    return HTTPException(404)


@license_router.post("/checklicense")
async def check_license(check_license_info: CheckLicenseModel):
    ...
