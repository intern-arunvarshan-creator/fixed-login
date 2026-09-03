from sqlmodel import Field, SQLModel


class Zone(SQLModel, table=True):
    __tablename__ = "zone"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(max_length=20, nullable=False)
    name: str = Field(max_length=100, nullable=False)