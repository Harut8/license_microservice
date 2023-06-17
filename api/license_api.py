from fastapi import APIRouter, Depends, HTTPException
from service.license_service_manager.license_service_manager import LicenseServiceManager
from models.license_model.license_model import AddLicenseModel, CheckLicenseModel, Version, DeviceType, GetPortForSuro

license_router = APIRouter(tags=["LICENSE API"], prefix="/license")


@license_router.get('/ping')
async def license_ping():
    return {"status": "LICENSE PINGING"}


@license_router.post("/add-device")
async def add_license(add_license_info: AddLicenseModel):
    _license_info = await LicenseServiceManager.add_license(add_license_info)
    if _license_info:
        return _license_info
    raise HTTPException(status_code=400, detail='ERROR', headers={'status': 'ADD LICENSE ERROR'})


@license_router.post("/check-license")
async def check_license(check_license_info: CheckLicenseModel):
    _port_ip_state = await LicenseServiceManager.check_license(check_license_info)
    if not _port_ip_state:
        raise HTTPException(status_code=404, detail='ERROR', headers={'status': 'LICENSE TIME ERROR'})
    return _port_ip_state


@license_router.post('/version/{device_type}')
async def version(version_info: Version, device_type: DeviceType):
    _version = await LicenseServiceManager.version(version_info.product_id, device_type.value)
    if not _version:
        raise HTTPException(status_code=404, detail='ERROR', headers={'status': 'VERSION ERROR'})
    _version = _version['versions']
    return {'current_version': _version[0], 'forced_version': _version[1]}


@license_router.post('/port_for_suro')
async def get_port_for_suro(u_lc_info: GetPortForSuro):
    _port = await LicenseServiceManager.get_port_for_suro(u_lc_info.u_id, u_lc_info.lc_key)
    if _port is not None:
        return _port
    raise HTTPException(status_code=400, detail='ERROR', headers={'status': 'LICENSE ERROR'})
