"""Small smoke test for reproducibility and expected output files."""
from pathlib import Path
import json
import tempfile
import pandas as pd
from generate_data import generate_synthetic_events
from analyze import run


def main():
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        data = base / "events.csv"
        generated = generate_synthetic_events(500, seed=42)
        assert generated.shape == (500, 12)
        assert set(generated.is_suspicious.unique()) == {0, 1}
        generated.to_csv(data, index=False)
        result = run(data, base / "outputs", seed=42)
        assert len(result["models"]) == 3
        assert "Decision Tree" in result["models"]
        assert (base / "outputs" / "figures" / "07_biased_labels_fpr.png").exists()
        assert len(pd.read_csv(base / "outputs" / "threshold_analysis.csv")) == 3
        assert json.loads((base / "outputs" / "metrics.json").read_text())["data_description"]["total_events"] == 500
    print("PASS: generation, model training, figures, ethics checks, and exports")


if __name__ == "__main__":
    main()
