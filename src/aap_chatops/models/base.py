"""Shared base models common to AAP API responses."""

from pydantic import BaseModel


class AapListResponse[T](BaseModel):
    """Generic paginated envelope returned by AAP list endpoints."""

    count: int
    next: str | None = None
    previous: str | None = None
    results: list[T]
