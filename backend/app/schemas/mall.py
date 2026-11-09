from pydantic import BaseModel, ConfigDict


class MallOut(BaseModel):
    """Shape of a Mall as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
