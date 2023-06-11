from uuid import UUID
from repository.license_db_manager.license_db_manager import LicenseDbManager
from typing import Union
from service.license_service_manager.license_service_interface import LicenseServiceInterface
from asyncpg import Record
from models.license_model.license_model import AddLicenseModel, CheckLicenseModel


class LicenseServiceManager(LicenseServiceInterface):

    @staticmethod
    async def add_license(add_license_info: AddLicenseModel):
        x = await LicenseDbManager.add_new_license(
            add_license_info.device_code,
            add_license_info.product_id,
            'ewfnkewjfneknfjk',
            add_license_info.unique_code
        )
        return x

    @staticmethod
    async def check_license(check_license_info: CheckLicenseModel):
        ...

