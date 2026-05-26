from typing import Optional

from app.schemas.base import AuditMixin, TransfermarktBaseModel


class PlayerSearchClub(TransfermarktBaseModel):
    id: str
    name: str


class PlayerSearchResult(TransfermarktBaseModel):
    id: str
    name: str
    thumbnail: str
    position: str
    club: PlayerSearchClub
    age: Optional[int] = None
    nationalities: list[str]
    market_value: Optional[int] = None


class PlayerSearch(TransfermarktBaseModel, AuditMixin):
    query: str
    pageNumber: int
    lastPageNumber: int
    results: list[PlayerSearchResult]