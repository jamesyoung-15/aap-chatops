from pydantic import BaseModel


class AAPUser(BaseModel):
    """AAP user information returned from the /me/ endpoint."""

    id: int
    username: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
