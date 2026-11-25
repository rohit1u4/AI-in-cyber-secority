"""One-command end-to-end project execution from the repository root."""
from pathlib import Path
from src.generate_data import generate_synthetic_events
from src.analyze import run

if __name__ == "__main__":
    data_path = Path("data/synthetic_login_events.csv")
    data_path.parent.mkdir(parents=True, exist_ok=True)
    if not data_path.exists():
        generate_synthetic_events(n=4000, seed=42).to_csv(data_path, index=False)
        print("Generated synthetic dataset:", data_path)
    run(data_path, Path("outputs"), seed=42)
