"""EDA, Logistic Regression / Decision Tree / MLP models, and ethics experiments."""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score,
                             ConfusionMatrixDisplay, RocCurveDisplay)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "is_suspicious"
NUMERIC = ["hour", "failed_attempts", "login_velocity_10m", "ip_reputation_score",
           "geo_distance_km", "new_device", "mfa_used", "is_weekend"]
CATEGORICAL = ["login_channel"]
PALETTE = {"normal": "#187C91", "suspicious": "#DB6947", "ink": "#243447", "muted": "#738395"}


def preprocessing(include_group: bool = False) -> ColumnTransformer:
    categorical = CATEGORICAL + (["user_group"] if include_group else [])
    return ColumnTransformer([
        ("numeric", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), NUMERIC),
        ("categorical", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical),
    ])


def metrics(y_true, probability, elapsed: float, threshold: float = 0.5) -> dict:
    pred = (np.asarray(probability) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, probability)),
        "true_negative": int(tn), "false_positive": int(fp),
        "false_negative": int(fn), "true_positive": int(tp),
        "training_seconds": float(elapsed), "threshold": threshold,
    }


def save_figure(path: Path) -> None:
    plt.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close()


def plot_eda(df: pd.DataFrame, figures: Path) -> None:
    counts = df[TARGET].value_counts().reindex([0, 1], fill_value=0)
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    bars = ax.bar(["Normal", "Suspicious"], counts.values,
                  color=[PALETTE["normal"], PALETTE["suspicious"]], width=0.5)
    for bar in bars:
        ax.annotate(f"{bar.get_height():,}", (bar.get_x()+bar.get_width()/2, bar.get_height()),
                    xytext=(0, 5), textcoords="offset points", ha="center", fontweight="bold")
    ax.set_title("Simulated login events by class", weight="bold")
    ax.set_ylabel("Number of events")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save_figure(figures / "01_class_balance.png")

    cols = ["failed_attempts", "login_velocity_10m", "ip_reputation_score", "geo_distance_km"]
    names = ["Failed attempts", "Logins in 10 minutes", "IP reputation (higher = safer)", "Geo distance (km)"]
    fig, axs = plt.subplots(2, 2, figsize=(11, 7.1))
    for ax, col, title in zip(axs.ravel(), cols, names):
        vals = df[col].dropna()
        bins = np.linspace(vals.min(), vals.quantile(.99), 22)
        for label, name, color in [(0,"Normal",PALETTE["normal"]), (1,"Suspicious",PALETTE["suspicious"])]:
            ax.hist(df.loc[df[TARGET] == label, col].dropna(), bins=bins, alpha=0.60,
                    color=color, density=True, label=name)
        ax.set_title(title)
        ax.set_ylabel("Density")
        ax.spines[["top", "right"]].set_visible(False)
    axs[0,0].legend()
    fig.suptitle("Attack-related feature distributions (synthetic)", weight="bold", fontsize=14)
    fig.tight_layout()
    save_figure(figures / "02_feature_distributions.png")

    risk_by_hour = df.groupby("hour")[TARGET].mean().reindex(range(24), fill_value=0)
    fig, ax = plt.subplots(figsize=(9,4.5))
    ax.bar(risk_by_hour.index, risk_by_hour.values * 100, color=PALETTE["normal"])
    ax.set_title("Share of simulated suspicious logins by hour", weight="bold")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Suspicious share (%)")
    ax.set_xticks(range(0,24,2))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save_figure(figures / "03_hourly_suspicious_rate.png")


def subgroup_fpr(y_true, probability, group, threshold: float = 0.5) -> dict:
    pred = (np.asarray(probability) >= threshold).astype(int)
    values = {}
    for name in ["Group A", "Group B"]:
        mask = np.asarray(group) == name
        good = mask & (np.asarray(y_true) == 0)
        total_benign = int(good.sum())
        blocked_benign = int((pred[good] == 1).sum())
        values[name] = {"benign_events": total_benign,
                        "false_positives": blocked_benign,
                        "false_positive_rate": float(blocked_benign / total_benign) if total_benign else 0.0}
    return values


def run(data_path: Path, output_path: Path, seed: int = 42) -> dict:
    figures = output_path / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(data_path)
    expected = set(NUMERIC + CATEGORICAL + [TARGET,"user_group"])
    if not expected.issubset(df.columns):
        raise ValueError(f"Dataset is missing: {sorted(expected - set(df.columns))}")
    if not df[TARGET].isin([0, 1]).all():
        raise ValueError("Target must have binary 0/1 values")

    plot_eda(df, figures)
    base_features = NUMERIC + CATEGORICAL
    # Both methods use exactly the same held-out split (25%), with stratification.
    train_idx, test_idx = train_test_split(np.arange(len(df)), test_size=.25,
                                           random_state=seed, stratify=df[TARGET])
    train = df.iloc[train_idx].copy()
    test = df.iloc[test_idx].copy()
    y_train = train[TARGET].to_numpy()
    y_test = test[TARGET].to_numpy()
    model_specs = {
        "Logistic Regression": LogisticRegression(max_iter=1500, random_state=seed),
        "Decision Tree": DecisionTreeClassifier(max_depth=6, min_samples_leaf=10,
                                                random_state=seed),
        "MLP Neural Network": MLPClassifier(hidden_layer_sizes=(32, 16), activation="relu",
                                            early_stopping=True, n_iter_no_change=15,
                                            max_iter=400, random_state=seed),
    }
    models = {}
    outputs = {}
    for name, estimator in model_specs.items():
        model = Pipeline([("prepare", preprocessing()), ("classifier", estimator)])
        start = time.perf_counter()
        model.fit(train[base_features], y_train)
        elapsed = time.perf_counter() - start
        probabilities = model.predict_proba(test[base_features])[:,1]
        models[name] = model
        outputs[name] = {"probabilities": probabilities,
                         "metrics": metrics(y_test, probabilities, elapsed)}

    # ROC curves (same holdout examples). No peeking at test data during fitting.
    fig, ax = plt.subplots(figsize=(7.7, 5.0))
    for name in model_specs:
        RocCurveDisplay.from_predictions(y_test, outputs[name]["probabilities"],
                                         name=name, ax=ax)
    ax.set_title("Test-set ROC comparison", weight="bold")
    fig.tight_layout()
    save_figure(figures / "04_roc_models.png")

    fig, axs = plt.subplots(1, len(model_specs), figsize=(15, 4.6))
    for ax, name in zip(axs, model_specs):
        pred = (outputs[name]["probabilities"] >= .5).astype(int)
        ConfusionMatrixDisplay.from_predictions(y_test, pred, labels=[0, 1],
                                                 display_labels=["Normal", "Suspicious"],
                                                 cmap="Blues", colorbar=False, ax=ax)
        ax.set_title(name)
    fig.suptitle("Held-out confusion matrices: three models (threshold 0.50)", weight="bold")
    fig.tight_layout()
    save_figure(figures / "05_confusion_matrices.png")

    comparison = pd.DataFrame([{"model": name, **outputs[name]["metrics"]} for name in model_specs])
    comparison.to_csv(output_path / "model_comparison.csv", index=False)

    # Human-review / blocked login tradeoff on the clean logistic baseline.
    baseline = outputs["Logistic Regression"]["probabilities"]
    threshold_rows = []
    for t in [0.30, 0.50, 0.70]:
        row = metrics(y_test, baseline, outputs["Logistic Regression"]["metrics"]["training_seconds"], t)
        row["false_positive_rate"] = row["false_positive"] / (row["false_positive"] + row["true_negative"])
        threshold_rows.append(row)
    thresholds = pd.DataFrame(threshold_rows)
    thresholds.to_csv(output_path / "threshold_analysis.csv", index=False)
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.plot(thresholds.threshold, thresholds.false_positive, "o-", label="Legitimate events wrongly flagged")
    ax.plot(thresholds.threshold, thresholds.false_negative, "s-", label="Suspicious events missed")
    ax.set_xlabel("Alert / block decision threshold")
    ax.set_ylabel("Count in held-out test set")
    ax.set_title("Threshold policy tradeoff", weight="bold")
    ax.set_xticks([.3,.5,.7])
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save_figure(figures / "06_threshold_tradeoff.png")

    # Fairness illustration: introduce deliberately biased training labels for one
    # *synthetic* cohort. Both models see the cohort feature, but labels differ.
    all_features = base_features + ["user_group"]
    clean = Pipeline([("prepare", preprocessing(include_group=True)),
                      ("classifier", LogisticRegression(max_iter=1500, random_state=seed))])
    clean.fit(train[all_features], y_train)
    clean_prob = clean.predict_proba(test[all_features])[:, 1]
    y_corrupted = y_train.copy()
    candidates = np.flatnonzero((train["user_group"].to_numpy() == "Group B") & (y_train == 0))
    rng = np.random.default_rng(seed + 100)
    flipped_indices = rng.choice(candidates, size=int(len(candidates) * .45), replace=False)
    y_corrupted[flipped_indices] = 1
    biased = Pipeline([("prepare", preprocessing(include_group=True)),
                       ("classifier", LogisticRegression(max_iter=1500, random_state=seed))])
    biased.fit(train[all_features], y_corrupted)
    biased_prob = biased.predict_proba(test[all_features])[:, 1]

    fairness_rows = []
    for name, prob in [("Original labels", clean_prob), ("Biased training labels", biased_prob)]:
        groups = subgroup_fpr(y_test, prob, test["user_group"].to_numpy())
        for group, values in groups.items():
            fairness_rows.append({"training_condition":name, "group":group, **values})
    fair = pd.DataFrame(fairness_rows)
    fair.to_csv(output_path / "fairness_analysis.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    x = np.arange(2)
    width = .34
    for i, condition in enumerate(["Original labels", "Biased training labels"]):
        rows = fair[fair.training_condition == condition].set_index("group")
        vals = [rows.loc[g,"false_positive_rate"] * 100 for g in ["Group A","Group B"]]
        ax.bar(x + (i - .5)*width, vals, width=width, label=condition,
               color=[PALETTE["normal"],PALETTE["suspicious"]][i])
    ax.set_xticks(x, ["Group A", "Group B"])
    ax.set_ylabel("False positive rate among benign events (%)")
    ax.set_title("Effect of simulated label bias on benign users", weight="bold")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    save_figure(figures / "07_biased_labels_fpr.png")

    # Final export deliberately saves aggregated metrics, not person-level data.
    missing = df.isna().sum().to_dict()
    result = {
        "data_description": {
            "type": "fully simulated, not a real incident dataset",
            "total_events": int(len(df)), "train_events": int(len(train)),
            "test_events": int(len(test)),
            "normal_events": int((df[TARGET] == 0).sum()),
            "suspicious_events": int((df[TARGET] == 1).sum()),
            "positive_rate": float(df[TARGET].mean()),
            "missing_cells_by_feature": {key:int(val) for key,val in missing.items()},
        },
        "models": {name: data["metrics"] for name,data in outputs.items()},
        "thresholds": threshold_rows,
        "fairness": fairness_rows,
        "biased_training_label_flips": int(len(flipped_indices)),
        "classification_reports": {
            name: classification_report(y_test, (data["probabilities"] >= .5).astype(int),
                                        target_names=["Normal","Suspicious"], output_dict=True)
            for name,data in outputs.items()
        },
        "seed": seed,
    }
    (output_path / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Data: {len(df)} simulated events | train={len(train)} test={len(test)}")
    print(comparison[["model","accuracy","precision","recall","f1","roc_auc","training_seconds"]].round(3).to_string(index=False))
    print("\nThreshold analysis:\n" + thresholds[["threshold","false_positive","false_negative","recall"]].round(3).to_string(index=False))
    print("\nFairness analysis:\n" + fair.to_string(index=False))
    print(f"\nGenerated outputs in {output_path.resolve()}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze simulated authentication threats")
    parser.add_argument("--data", default="data/synthetic_login_events.csv")
    parser.add_argument("--output", default="outputs")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(Path(args.data), Path(args.output), args.seed)


if __name__ == "__main__":
    main()
