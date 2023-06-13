from fastapi import APIRouter, Depends, HTTPException
from service.license_service_manager.license_service_manager import LicenseServiceManager
from starlette import status
from starlette.responses import RedirectResponse
from models.license_model.license_model import AddLicenseModel, CheckLicenseModel


license_router = APIRouter(tags=["LICENSE API"], prefix="/license")


@license_router.get('/ping')
async def license_ping():
    return {"status": "LICENSE PINGING"}


@license_router.post("/add-license")
async def add_license(add_license_info: AddLicenseModel):
    _license_info = await LicenseServiceManager.add_license(add_license_info)
    if _license_info:
        return _license_info
    return HTTPException(404)


@license_router.post("/check-license")
async def check_license(check_license_info: CheckLicenseModel):
    _port_ip_state = await LicenseServiceManager.check_license(check_license_info)
    if not _port_ip_state:
        HTTPException(404)
    return _port_ip_state
