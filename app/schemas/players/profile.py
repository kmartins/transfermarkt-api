from datetime import date
from enum import Enum
from typing import Optional

from pydantic import Field, HttpUrl

from app.schemas.base import AuditMixin, TransfermarktBaseModel


class PlayerPlaceOfBirth(TransfermarktBaseModel):
    city: Optional[str] = None
    country: Optional[str] = None


class PlayerPosition(TransfermarktBaseModel):
    main: Optional[str] = None
    other: Optional[list[str]] = None


class PlayerClub(TransfermarktBaseModel):
    id: Optional[str] = None
    name: str
    joined: Optional[date] = None
    contract_expires: Optional[date] = None
    contract_option: Optional[str] = None
    # Retired player
    last_club_id: Optional[str] = None
    last_club_name: Optional[str] = None
    most_games_for: Optional[str] = None


class PlayerParentClub(TransfermarktBaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    contract_expires: Optional[date] = None


class PlayerAgent(TransfermarktBaseModel):
    name: Optional[str] = None
    url: Optional[str] = None


class TrainerProfile(TransfermarktBaseModel):
    id: Optional[str] = None
    url: Optional[str] = None
    position: Optional[str] = None


class RelativeProfileTypeEnum(str, Enum):
    PLAYER = "player"
    TRAINER = "trainer"


class Relatives(TransfermarktBaseModel):
    id: str
    url: str
    name: str
    profile_type: RelativeProfileTypeEnum


class PlayerProfile(TransfermarktBaseModel, AuditMixin):
    id: str
    url: HttpUrl
    name: str
    description: str
    full_name: Optional[str] = None
    name_in_home_country: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    date_of_birth: Optional[date] = None
    place_of_birth: PlayerPlaceOfBirth
    age: Optional[int] = None
    height: Optional[int] = None
    citizenship: list[str]
    is_retired: bool
    retired_since: Optional[date] = None
    position: PlayerPosition
    foot: Optional[str] = None
    shirt_number: Optional[str] = None
    club: PlayerClub
    parent_club: Optional[PlayerParentClub] = Field(None, description="Only present when the player is currently on loan")
    market_value: Optional[int] = None
    agent: Optional[PlayerAgent] = None
    outfitter: Optional[str] = None
    socialMedia: Optional[list[str]] = None
    trainer_profile: Optional[TrainerProfile] = None
    relatives: Optional[list[Relatives]] = None
