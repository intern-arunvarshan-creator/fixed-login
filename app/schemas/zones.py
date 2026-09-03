from pydantic import BaseModel, Field


class ZoneCreate(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)


class ZoneUpdate(BaseModel):
    code: str | None = Field(default=None, max_length=20)
    name: str | None = Field(default=None, max_length=100)


class ZoneResponse(BaseModel):
    id: int
    code: str
    name: str