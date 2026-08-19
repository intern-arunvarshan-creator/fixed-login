from sqlmodel import Field, SQLModel


class PlatformAdmin(SQLModel, table=True):
    __tablename__ = "platform_admins"

    username: str = Field(primary_key=True, max_length=255)
    hashed_password: str
