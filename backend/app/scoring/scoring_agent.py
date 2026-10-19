"""Scoring + confidence -- Spec sections 33.2 and 33.3."""
import math


def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def _round_half_up(v):
    return int(math.floor(v + 0.5))


def factor_recency(mean_age_days):
    if mean_age_days is None:
        mean_age_days = 0
    if mean_age_days < 0:
        mean_age_days = 0
    lam = math.log(2) / 180.0
    return 100.0 * math.exp(-lam * mean_age_days)


def factor_trend(state, growth_rate=0.0, classification_confidence=0.5):
    base_map = {"EMERGING": 90, "GROWING": 75, "STABLE": 50, "DECLINING": 20}
    base = base_map.get(state, 50)
    gr = max(-1.0, min(1.0, float(growth_rate or 0.0)))
    cc = max(0.0, min(1.0, float(classification_confidence or 0.5)))
    if state in ("EMERGING", "GROWING"):
        return _clamp(base * (0.5 + 0.5 * gr))
    return _clamp(base * cc)


def compute_score(s_problem, s_tech, s_gap, s_trend, s_evidence,
                  s_feasibility, s_recency, weights, trend_window=90):
    for name, v in [
        ("s_problem", s_problem), ("s_tech", s_tech), ("s_gap", s_gap),
        ("s_trend", s_trend), ("s_evidence", s_evidence),
        ("s_feasibility", s_feasibility), ("s_recency", s_recency),
    ]:
        if not (0.0 <= float(v) <= 100.0):
            raise ValueError(name + " must be in [0,100], got " + str(v))
    w_sum = (weights.w_problem + weights.w_tech + weights.w_gap +
             weights.w_trend + weights.w_evidence + weights.w_feasibility +
             weights.w_recency)
    if w_sum <= 0:
        raise ValueError("weights sum must be > 0")
    raw = (weights.w_problem * s_problem +
           weights.w_tech * s_tech +
           weights.w_gap * s_gap +
           weights.w_trend * s_trend +
           weights.w_evidence * s_evidence +
           weights.w_feasibility * s_feasibility +
           weights.w_recency * s_recency)
    score = raw / w_sum
    return _round_half_up(_clamp(score, 0.0, 100.0))


def compute_confidence(evidence_items, conflict_severity, config):
    if not evidence_items:
        return 0
    supporting = [e for e in evidence_items if e.get("polarity") == "SUPPORTS"]
    if not supporting:
        return 0
    N = len(set(e.get("doc_id") for e in supporting if e.get("doc_id")))
    D = len(set(e.get("source_type") for e in supporting if e.get("source_type")))
    D = min(D, config.d_max)
    ws = [float(e.get("credibility_weight") or 0.0) for e in supporting]
    M = (sum(ws) / len(ws)) if ws else 0.0
    total_w = sum(float(e.get("credibility_weight") or 0.0) for e in evidence_items)
    if total_w <= 0:
        A = 0.0
    else:
        sup_w = sum(float(e.get("credibility_weight") or 0.0) for e in supporting)
        con_w = total_w - sup_w
        A = (max(sup_w, con_w)) / total_w
    s_count = 100.0 * min(N / float(config.n_max), 1.0)
    s_diversity = 100.0 * (D / float(config.d_max))
    s_credibility = 100.0 * M
    s_agreement = 100.0 * A
    raw = (config.beta1 * s_count + config.beta2 * s_diversity +
           config.beta3 * s_credibility + config.beta4 * s_agreement)
    sev = max(0.0, min(1.0, float(conflict_severity or 0.0)))
    penalty = config.conflict_penalty * sev
    return _round_half_up(_clamp(raw * (1.0 - penalty), 0.0, 100.0))
