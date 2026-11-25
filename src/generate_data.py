"""Create a documented, fully synthetic login security dataset (no personal data)."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def generate_synthetic_events(n: int = 4000, seed: int = 42) -> pd.DataFrame:
    """Simulate benign and suspicious authentication events with overlapping signals.

    Labels are simulated first; conditional feature distributions describe a hypothetical
    organization. Do NOT interpret this data or the results as real-world threat rates.
    """
    if n < 200:
        raise ValueError("n must be at least 200 for a meaningful demonstration")
    rng = np.random.default_rng(seed)
    suspicious = rng.binomial(1, 0.27, size=n).astype(int)
    group = rng.choice(["Group A", "Group B"], size=n, p=[0.5, 0.5])
    failed = rng.poisson(np.where(suspicious == 1, 3.1, 1.0)).clip(0, 12)
    velocity = rng.poisson(np.where(suspicious == 1, 3.8, 1.65)).clip(0, 14)
    reputation = np.clip(rng.normal(np.where(suspicious == 1, 43, 75), 19), 0, 100)
    geo_distance = np.clip(rng.gamma(
        shape=np.where(suspicious == 1, 2.1, 1.5),
        scale=np.where(suspicious == 1, 430.0, 130.0)), 0, 6500)
    device_new_probability = np.where(suspicious == 1, 0.66, 0.23)
    device_new = rng.binomial(1, device_new_probability)
    mfa_used = rng.binomial(1, np.where(suspicious == 1, 0.39, 0.83))
    is_weekend = rng.binomial(1, np.where(suspicious == 1, 0.35, 0.26))
    night = rng.binomial(1, np.where(suspicious == 1, 0.55, 0.24)).astype(bool)
    hour = np.where(night, rng.choice([0, 1, 2, 3, 4, 5], size=n), rng.integers(6, 24, size=n))
    channels = np.array(["web", "mobile", "vpn"], dtype=object)
    channel = np.array([
        rng.choice(channels, p=[0.45, 0.33, 0.22] if t else [0.53, 0.40, 0.07])
        for t in suspicious
    ], dtype=object)

    # Intentionally add realistic missing values to exercise preprocessing.
    reputation[rng.random(n) < 0.035] = np.nan
    geo_distance[rng.random(n) < 0.025] = np.nan
    channel[rng.random(n) < 0.02] = None

    return pd.DataFrame({
        "event_id": [f"EVT-{i:06d}" for i in range(1, n + 1)],
        "hour": hour,
        "failed_attempts": failed,
        "login_velocity_10m": velocity,
        "ip_reputation_score": np.round(reputation, 2),
        "geo_distance_km": np.round(geo_distance, 1),
        "new_device": device_new,
        "mfa_used": mfa_used,
        "is_weekend": is_weekend,
        "login_channel": channel,
        "user_group": group,
        "is_suspicious": suspicious,
    })


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate simulated cyber login events")
    parser.add_argument("--rows", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="data/synthetic_login_events.csv")
    args = parser.parse_args()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_synthetic_events(args.rows, args.seed)
    df.to_csv(path, index=False)
    print(f"Saved {len(df):,} synthetic events to {path} | suspicious: {df.is_suspicious.mean():.1%}")


if __name__ == "__main__":
    main()
