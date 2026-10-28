"""Schémas d'entrée et de sortie de l'API, validés par Pydantic."""
from pydantic import BaseModel, ConfigDict, Field


class SensorReading(BaseModel):
    """Un relevé de capteurs pour une machine."""

    model_config = ConfigDict(
        extra="forbid",  # refuse les champs inconnus
        json_schema_extra={
            "examples": [
                {"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85.0, "runtime_hours": 15000}
            ]
        },
    )

    temperature_c: float = Field(
        ge=-40.0, le=150.0, description="Température du moteur (°C)"
    )
    vibration_mm_s: float = Field(
        ge=0.0, le=50.0, description="Vitesse de vibration (mm/s)"
    )
    load_pct: float = Field(
        ge=0.0, le=120.0, description="Charge du moteur en %"
    )
    runtime_hours: float = Field(
        ge=0.0, le=100000.0, description="Heures de fonctionnement cumulées"
    )


class PredictionOut(BaseModel):
    failure_probability: float = Field(description="Probabilité estimée de panne, entre 0 et 1")
    alert: bool = Field(description="Vrai si la probabilité atteint le seuil")
    threshold: float
    model_version: str


class HealthOut(BaseModel):
    status: str
    model_loaded: bool
