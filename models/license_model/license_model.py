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
    device_code: str = Field(regex=r'^[a-zA-Z0-9\/-_]+$')
    product_id: int = Field(gt=0, le=4)


class CheckLicenseModel(BaseModel):
    license_key: str = Field(regex=r'^[a-zA-Z0-9\/-_]+$')
    device_code: str = Field(regex=r'^[a-zA-Z0-9\/-_]+$')
    product_id: int = Field(gt=0, le=4)


class GetLicenseType(BaseModel):
    license_key: str = Field(regex=r'^[a-zA-Z0-9\/-_]+$')


class GetPortForSuro(BaseModel):
    u_id: str
    lc_key: str


class Version(BaseModel):
    product_id: int = Field(gt=0, le=4)


