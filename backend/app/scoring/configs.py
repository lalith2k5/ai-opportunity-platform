"""Versioned configuration objects -- Spec section 33.6."""
from dataclasses import dataclass
from app.database import SessionLocal
from app import models


@dataclass
class WeightConfig:
    version: str
    w_problem: float = 0.20
    w_tech: float = 0.15
    w_gap: float = 0.20
    w_trend: float = 0.15
    w_evidence: float = 0.15
    w_feasibility: float = 0.10
    w_recency: float = 0.05


@dataclass
class ConfidenceConfig:
    version: str
    beta1: float = 0.30
    beta2: float = 0.25
    beta3: float = 0.25
    beta4: float = 0.20
    n_max: int = 5
    d_max: int = 6
    conflict_penalty: float = 0.50


@dataclass
class TrendConfig:
    version: str
    window_short: int = 30
    window_mid: int = 90
    window_long: int = 365
    emerging_threshold: float = 0.5
    growing_threshold: float = 0.2
    declining_threshold: float = -0.2
    default_window: int = 90


_DEFAULT_WEIGHT = WeightConfig(version="v1.0.0")
_DEFAULT_CONFIDENCE = ConfidenceConfig(version="v1.0.0")
_DEFAULT_TREND = TrendConfig(version="v1.0.0")


def load_active_weight_config():
    try:
        db = SessionLocal()
        try:
            row = (db.query(models.WeightConfig)
                   .filter(models.WeightConfig.is_active == True)
                   .order_by(models.WeightConfig.id.desc())
                   .first())
            if not row:
                return _DEFAULT_WEIGHT
            return WeightConfig(
                version=row.version,
                w_problem=row.w_problem, w_tech=row.w_tech,
                w_gap=row.w_gap, w_trend=row.w_trend,
                w_evidence=row.w_evidence, w_feasibility=row.w_feasibility,
                w_recency=row.w_recency,
            )
        finally:
            db.close()
    except Exception:
        return _DEFAULT_WEIGHT


def load_active_confidence_config():
    try:
        db = SessionLocal()
        try:
            row = (db.query(models.ConfidenceConfig)
                   .filter(models.ConfidenceConfig.is_active == True)
                   .order_by(models.ConfidenceConfig.id.desc())
                   .first())
            if not row:
                return _DEFAULT_CONFIDENCE
            return ConfidenceConfig(
                version=row.version,
                beta1=row.beta1, beta2=row.beta2,
                beta3=row.beta3, beta4=row.beta4,
                n_max=row.n_max, d_max=row.d_max,
                conflict_penalty=row.conflict_penalty,
            )
        finally:
            db.close()
    except Exception:
        return _DEFAULT_CONFIDENCE


def load_active_trend_config():
    try:
        db = SessionLocal()
        try:
            row = (db.query(models.TrendConfig)
                   .filter(models.TrendConfig.is_active == True)
                   .order_by(models.TrendConfig.id.desc())
                   .first())
            if not row:
                return _DEFAULT_TREND
            return TrendConfig(
                version=row.version,
                window_short=row.window_short,
                window_mid=row.window_mid,
                window_long=row.window_long,
                emerging_threshold=row.emerging_threshold,
                growing_threshold=row.growing_threshold,
                declining_threshold=row.declining_threshold,
                default_window=row.default_window,
            )
        finally:
            db.close()
    except Exception:
        return _DEFAULT_TREND


def seed_defaults_if_empty():
    db = SessionLocal()
    try:
        if db.query(models.WeightConfig).count() == 0:
            db.add(models.WeightConfig(version="v1.0.0", is_active=True))
        if db.query(models.ConfidenceConfig).count() == 0:
            db.add(models.ConfidenceConfig(version="v1.0.0", is_active=True))
        if db.query(models.TrendConfig).count() == 0:
            db.add(models.TrendConfig(version="v1.0.0", is_active=True))
        db.commit()
    finally:
        db.close()
