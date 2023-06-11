from pydantic import BaseModel, Field


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
