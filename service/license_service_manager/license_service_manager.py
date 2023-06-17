from uuid import UUID
from repository.license_db_manager.license_db_manager import LicenseDbManager
from typing import Union
from service.license_service_manager.license_service_interface import LicenseServiceInterface
from asyncpg import Record
from models.license_model.license_model import AddLicenseModel, CheckLicenseModel


class LicenseServiceManager(LicenseServiceInterface):

    @staticmethod
    async def add_license(add_license_info: AddLicenseModel):
        try:
            _license_state = await LicenseDbManager.check_license_state(
                unique_code=add_license_info.unique_code,
                product_id=add_license_info.product_id
            )
            _license_date = _license_state['license_date']
            if not _license_date:
                return
            _license_state = _license_state['state_of_license']
            if add_license_info.product_id == 3:
                _web_license = await LicenseDbManager.web_manager_license(
                    _license_state,
                    add_license_info.unique_code,
                    add_license_info.device_code,
                    add_license_info.product_id
                )
                return _web_license
            else:
                _other_license = await LicenseDbManager.other_platform_license(
                        _license_state,
                        add_license_info.unique_code,
                        add_license_info.device_code,
                        add_license_info.product_id
                    )
                return _other_license

        except Exception as e:
            print(e)
            return

    @staticmethod
    async def check_license(check_license_info: CheckLicenseModel):
        try:
            _port_ip_state = await LicenseDbManager.check_license(
                license_key=check_license_info.license_key,
                device_code=check_license_info.device_code,
                product_id=check_license_info.product_id
            )
            return _port_ip_state
        except Exception as e:
            print(e)
            return

    @staticmethod
    async def version(product_id, device_type):
        try:
            _version = await LicenseDbManager.version(product_id, device_type)
            return _version
        except Exception as e:
            print(e)
            return

    @staticmethod
    async def get_port_for_suro(u_id, lc_key):
        try:
            _port = await LicenseDbManager.get_port_for_suro(u_id, lc_key)
            return _port
        except Exception as e:
            print(e)
            return
