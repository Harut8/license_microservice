from typing import Union

from pydantic import BaseModel, Field, validator
from enum import Enum


class DeviceType(Enum):
    android = 'android'
    ios = 'ios'
    windows = 'windows'
    linux = 'linux'


class AddLicenseModel(BaseModel):
    unique_code: int
    device_code: str
    product_id: int = Field(gt=0, le=4)


class CheckLicenseModel(BaseModel):
    license_key: str
    device_code: str
    product_id: int = Field(gt=0, le=4)


class GetLicenseType(BaseModel):
    license_key: str


class GetPortForSuro(BaseModel):
    u_id: str
    lc_key: str


class Version(BaseModel):
    product_id: int = Field(gt=0, le=4)


