"""Pydantic models for the external Auburn and Opelika responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class MmcDataValidationError(ValueError):
    """Raised when an external rainfall response cannot be safely used."""


class AuburnDatum(BaseModel):
    """Validated Auburn value container used by the project."""

    model_config = ConfigDict(extra="ignore")

    valid: list[tuple[int, float]] = Field(default_factory=list)


class AuburnRecord(BaseModel):
    """Validated Auburn record containing one datum block."""

    model_config = ConfigDict(extra="ignore")

    datum: AuburnDatum


class AuburnValue(BaseModel):
    """Validated Auburn response value containing provider records."""

    model_config = ConfigDict(extra="ignore")

    records: list[AuburnRecord] = Field(default_factory=list)


class AuburnPayload(BaseModel):
    """Validated top-level Auburn response fields consumed by MMC."""

    model_config = ConfigDict(extra="ignore")

    value: AuburnValue


class OpelikaRecord(BaseModel):
    """Validated Opelika timestamp and cumulative rainfall fields."""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    created_dt: datetime = Field(alias="CreatedDT")
    rain_today: float = Field(alias="RainToday")


def validate_auburn_payload(payload: Any) -> AuburnPayload:
    """Validate the Auburn response fields consumed by the project."""

    try:
        return AuburnPayload.model_validate(payload)
    except ValidationError as exc:
        raise _as_domain_error("Auburn", exc) from exc


def validate_opelika_records(records: Any) -> list[OpelikaRecord]:
    """Validate the Opelika response records used for rainfall conversion."""

    try:
        if not isinstance(records, list):
            raise TypeError("response must be a JSON list")
        return [OpelikaRecord.model_validate(record) for record in records]
    except (TypeError, ValidationError) as exc:
        if isinstance(exc, ValidationError):
            raise _as_domain_error("Opelika", exc) from exc
        raise MmcDataValidationError(f"Opelika data could not be used: {exc}") from exc


def _as_domain_error(source: str, exc: ValidationError) -> MmcDataValidationError:
    """Convert a Pydantic error into a concise source-specific exception."""

    first_problem = exc.errors(include_url=False)[0]
    location = ".".join(str(part) for part in first_problem["loc"])
    message = first_problem["msg"]
    return MmcDataValidationError(
        f"{source} data could not be used at {location}: {message}"
    )
