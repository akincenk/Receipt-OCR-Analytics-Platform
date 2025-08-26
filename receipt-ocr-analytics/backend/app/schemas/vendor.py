from pydantic import BaseModel

class VendorOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True
