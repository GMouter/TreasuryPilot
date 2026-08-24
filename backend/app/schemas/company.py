from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    country: str
    base_currency: str


class CompanyUpdate(BaseModel):
    name: str
    country: str
    base_currency: str


class CompanyResponse(BaseModel):
    id: int
    name: str
    country: str
    base_currency: str

    class Config:
        from_attributes = True