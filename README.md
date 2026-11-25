# AI Cyber Threat Detection

A Python mini-project that detects **suspicious login activity** using machine learning. It uses **4,000 simulated events**, not real customer data.

## Features

- Explore login patterns with charts
- Train and compare Logistic Regression, Decision Tree, and MLP Neural Network
- Check accuracy, precision, recall, F1-score, and ROC AUC
- Investigate false alerts and simulated label bias
- Explore a step-by-step Jupyter notebook
- Export graphs, model results, and a PDF report

## Results (synthetic test data)

| Model | Accuracy | F1-score |
|---|---:|---:|
| Logistic Regression | 97.0% | 94.4% |
| Decision Tree | 94.0% | 88.9% |
| MLP Neural Network | 96.4% | 93.3% |

These scores are from artificially generated data and **do not measure performance on real attacks**.

## Tools

Python, Pandas, NumPy, Scikit-learn, Matplotlib, Jupyter, ReportLab.

## How to run

1. Open this repository folder in VS Code.
2. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Run all experiments:

   ```bash
   python run_project.py
   ```

4. Create the PDF report:

   ```bash
   python report/create_report.py --name "Aditya Mishra" --roll "2301730258"
   ```

5. Optional: explore the notebook:

   ```bash
   jupyter notebook notebooks/Threat_Detection_Exploration.ipynb
   ```

Results and charts appear in `outputs/`. The PDF is at `report/technical_report.pdf`.

## Project folders

- `src/` — Python modules for dataset generation and analysis
- `data/` — synthetic dataset
- `notebooks/` — interactive EDA and model comparison
- `outputs/` — exported charts and results
- `report/` — technical report and report generator
- `run_project.py` — run the full analysis

