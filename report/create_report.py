"""Generate an original, evidence-based Unit 1 cybersecurity lab report.

All reported results are loaded from outputs/metrics.json and linked to project-generated
figures. The example report supplied for visual reference is not used as text or data.
There are deliberately no PDF page footers, watermarks or page numbers.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table, TableStyle,
                                Spacer, Image, PageBreak, KeepTogether, HRFlowable)

parser = argparse.ArgumentParser(description="Create the mini-project technical report")
parser.add_argument("--name", default="Aditya Mishra")
parser.add_argument("--roll", default="2301730258")
args = parser.parse_args()

ROOT = Path(__file__).resolve().parents[1]
METRICS = json.loads((ROOT / "outputs" / "metrics.json").read_text(encoding="utf-8"))
DEST = ROOT / "report" / "technical_report.pdf"
A4W, A4H = A4
MARGIN = 48
WIDTH = A4W - 2*MARGIN

INK = colors.HexColor("#1B2C3B")
BLUE = colors.HexColor("#275E81")
ACCENT = colors.HexColor("#2D8390")
DIM = colors.HexColor("#536374")
LIGHT = colors.HexColor("#F2F6F8")
LINE = colors.HexColor("#CBD8E0")
WHITE = colors.white

# Optional Liberation font for Unix. Windows normally does not have this font;
# fall back to ReportLab's built-in Times family, requiring no font downloads.
# Set REPORT_STANDARD_FONTS=1 to test the fallback on any operating system.
font_dir = Path("/usr/share/fonts/truetype/liberation")
font_paths = [font_dir / f"LiberationSerif-{variant}.ttf"
              for variant in ("Regular", "Bold", "Italic")]
if os.environ.get("REPORT_STANDARD_FONTS") != "1" and all(path.is_file() for path in font_paths):
    FONT_NORMAL, FONT_BOLD, FONT_ITALIC = "LibSerif", "LibSerifBold", "LibSerifItalic"
    for name, path in zip((FONT_NORMAL, FONT_BOLD, FONT_ITALIC), font_paths):
        pdfmetrics.registerFont(TTFont(name, str(path)))
else:
    FONT_NORMAL, FONT_BOLD, FONT_ITALIC = "Times-Roman", "Times-Bold", "Times-Italic"
pdfmetrics.registerFontFamily(FONT_NORMAL, normal=FONT_NORMAL, bold=FONT_BOLD, italic=FONT_ITALIC)

STYLE = {
    "eyebrow": ParagraphStyle("eyebrow", fontName=FONT_BOLD, fontSize=9.5, leading=13,
                              textColor=BLUE, alignment=TA_CENTER, spaceAfter=13),
    "title": ParagraphStyle("title", fontName=FONT_BOLD, fontSize=19, leading=24,
                            textColor=INK, alignment=TA_CENTER, spaceAfter=8),
    "subtitle": ParagraphStyle("subtitle", fontName=FONT_ITALIC, fontSize=11.2, leading=15.5,
                               textColor=DIM, alignment=TA_CENTER, spaceAfter=16),
    "h1": ParagraphStyle("h1", fontName=FONT_BOLD, fontSize=14, leading=18.5,
                         textColor=INK, spaceBefore=6, spaceAfter=9, keepWithNext=True),
    "h2": ParagraphStyle("h2", fontName=FONT_BOLD, fontSize=11, leading=15.5,
                         textColor=BLUE, spaceBefore=8, spaceAfter=6, keepWithNext=True),
    "body": ParagraphStyle("body", fontName=FONT_NORMAL, fontSize=10.3, leading=15.0,
                           textColor=INK, spaceAfter=9, allowWidows=0, allowOrphans=0),
    "dense": ParagraphStyle("dense", fontName=FONT_NORMAL, fontSize=9.7, leading=13.8,
                            textColor=INK, spaceAfter=7),
    "caption": ParagraphStyle("caption", fontName=FONT_ITALIC, fontSize=9.1,
                              leading=12.4, textColor=DIM, alignment=TA_CENTER, spaceAfter=10),
    "label": ParagraphStyle("label", fontName=FONT_BOLD, fontSize=9.2,
                            leading=12.4, textColor=INK),
    "cell": ParagraphStyle("cell", fontName=FONT_NORMAL, fontSize=9.2,
                           leading=12.5, textColor=INK),
    "thead": ParagraphStyle("thead", fontName=FONT_BOLD, fontSize=9.2,
                            leading=12.4, textColor=INK),
    "small": ParagraphStyle("small", fontName=FONT_NORMAL, fontSize=9.3,
                            leading=13, textColor=DIM, spaceAfter=6),
    "ref": ParagraphStyle("ref", fontName=FONT_NORMAL, fontSize=9.1,
                          leading=12.5, textColor=INK, spaceAfter=4)
}

def p(s: str, sty="body"):
    return Paragraph(s, STYLE[sty])

def section(s):
    return p(s, "h1")

def sub(s):
    return p(s, "h2")

def table(headers, rows, widths, compact=False):
    data = [[p(escape(str(v)), "thead") for v in headers]]
    data.extend([[p(escape(str(v)), "cell") for v in row] for row in rows])
    tab = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E7EFF3")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LINEBELOW", (0, 0), (-1, -1), 0.7, BLUE),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5 if compact else 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5 if compact else 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    return tab

def fig(filename: str, maxw: float, caption: str):
    path = ROOT / "outputs" / "figures" / filename
    with PILImage.open(path) as im:
        w, h = im.size
    img = Image(str(path), width=maxw, height=maxw * h / w)
    img.hAlign = "CENTER"
    return KeepTogether([img, p(caption, "caption")])

D = METRICS["data_description"]
LR = METRICS["models"]["Logistic Regression"]
DT = METRICS["models"]["Decision Tree"]
MLP = METRICS["models"]["MLP Neural Network"]
TH = {round(x["threshold"], 2): x for x in METRICS["thresholds"]}
FAIR = {(r["training_condition"], r["group"]):r for r in METRICS["fairness"]}

story = []
add = story.append

def new_page():
    add(PageBreak())

# PAGE 1 - paper heading and context, inspired by a conventional student lab layout
add(p("LAB ASSIGNMENT 01 &nbsp; | &nbsp; UNIT I: FOUNDATIONS OF AI IN CYBER SECURITY", "eyebrow"))
add(table(["STUDENT", "ROLL NUMBER", "SUBJECT"], [
    [args.name, args.roll, "AI in Cyber Security Lab (ENSP355)"]],
    [153, 125, WIDTH-278], compact=True))
add(Spacer(1, 22))
add(p("Building an AI-Driven Cyber Threat<br/>Awareness and Detection Prototype", "title"))
add(p("Technical report: synthetic login analytics, detection models and responsible AI", "subtitle"))
add(HRFlowable(width="100%", thickness=0.9, color=ACCENT, spaceAfter=20))
add(section("1. Problem Statement and Project Scope"))
add(p("Login systems receive both ordinary activity and potentially harmful authentication attempts. Fixed security rules can flag repeated failures or unusual locations, but the exact same pattern may appear when a genuine person travels, uses a new device or forgets a password. The challenge is therefore not simply to identify suspicious-looking events; it is to distinguish useful alerts from false alarms."))
add(p("For this Unit I project, I implemented a small classification workflow that studies simulated login records and predicts whether each record should be marked <b>normal</b> or <b>suspicious</b>. The work is educational rather than a live threat-monitoring service: no private logs, accounts or actual network sessions were accessed."))
add(sub("1.1 Objectives"))
add(p("The prototype covers dataset creation, exploratory analysis, preprocessing, Logistic Regression and Decision Tree classifiers, an MLP neural-network model, evaluation on an unseen test partition and two ethical experiments: alert-threshold sensitivity and deliberately biased training labels.", "dense"))
add(sub("1.2 Overall workflow"))
add(table(["INPUT", "PROCESS", "OUTPUT"], [
    ["4,000 simulated login events", "Clean, encode and standardize features", "Comparable model predictions"],
    ["Training / test partition", "Train Logistic Regression, Decision Tree and MLP", "Accuracy, precision, recall, F1, ROC AUC"],
    ["Model scores and clean labels", "Vary threshold and corrupt training labels", "False-alarm and fairness analysis"],
], [156, 166, WIDTH-322], compact=True))
add(Spacer(1, 8))
add(p("All results in this report are generated from the project code with random seed 42. They should not be interpreted as measured effectiveness against real attacks.", "small"))
new_page()

# PAGE 2 - methods and class balance
add(section("2. Data and Experimental Method"))
add(sub("2.1 Repository and development environment"))
add(p("The project contains a README, dependency file, version-control ignore rules, a <b>data/</b> folder, Python modules in <b>src/</b>, a reproducible Jupyter notebook in <b>notebooks/</b>, exported metrics and figures in <b>outputs/</b>, and this report. Python libraries include NumPy, pandas, scikit-learn and Matplotlib. The main entry point is <b>python run_project.py</b>; a separate smoke-test script verifies the basic setup.", "dense"))
add(sub("2.2 Data design"))
add(p(f"I used a reproducible generator rather than downloading personal login information. It created <b>{D['total_events']:,} observations</b>, containing <b>{D['normal_events']:,} normal</b> events and <b>{D['suspicious_events']:,} suspicious</b> events. The {D['positive_rate']*100:.2f}% suspicious share is a choice of the simulation, not a real-world attack rate. The input columns describe access time, failed attempts, login velocity, IP-reputation score, geographic distance, a new-device indicator, MFA usage, weekend usage and login channel.", "dense"))
add(fig("01_class_balance.png", 320,
        "Figure 1. The intentionally imbalanced class distribution used for the lab experiment."))
add(sub("2.3 Preprocessing and validation"))
add(p(f"The generated dataset intentionally contains incomplete records: {D['missing_cells_by_feature']['ip_reputation_score']} missing IP-reputation scores, {D['missing_cells_by_feature']['geo_distance_km']} missing geographic-distance values and {D['missing_cells_by_feature']['login_channel']} missing login-channel entries. Numeric attributes were median-imputed then scaled; the categorical channel was most-frequent-imputed and one-hot encoded.", "dense"))
add(p(f"The events were divided into <b>{D['train_events']:,} training</b> and <b>{D['test_events']:,} test</b> cases (75/25), preserving the class proportions. Preprocessing was fitted only on the training portion through scikit-learn pipelines. Event IDs and the synthetic user-group column were excluded from the primary prediction models.", "dense"))
new_page()

# PAGE 3 - feature study and time of day
add(section("3. Exploring Threat Indicators"))
add(p("Exploratory data analysis examined which observable behaviors separate the two simulated classes. The four distributions below show that suspicious activity tends to produce more failed attempts, faster repeated logins, lower IP-reputation scores and larger travel distances. There is still overlap, so a single indicator is not sufficient for every decision.", "dense"))
add(fig("02_feature_distributions.png", 466,
        "Figure 2. Overlapping feature distributions for normal and suspicious login simulations."))
add(p("Time of access was also included in the generator. As shown in Figure 3, the fraction of suspicious events is higher during certain overnight hours. This is a pattern created for the experiment; applying the same assumption to real employees would be unsafe without local evidence.", "dense"))
add(fig("03_hourly_suspicious_rate.png", 360,
        "Figure 3. Suspicious-event percentage across the 24-hour simulated day."))
new_page()

# PAGE 4 - three-model comparison on exactly the same held-out test set
add(section("4. Supervised ML and Neural-Network Comparison"))
add(p("Three models were trained on the same 3,000 records and evaluated on the same 1,000 unseen records. Logistic Regression is a linear baseline (up to 1,500 iterations), the Decision Tree is depth-limited to six with at least ten samples per leaf, and the MLP uses 32 and 16 hidden neurons with ReLU and early stopping. All share the same training-only preprocessing pipeline and random seed 42.", "dense"))
add(table(["MODEL", "ACCURACY", "PRECISION", "RECALL", "F1", "TRAIN"], [
    ["Logistic Regression", f"{LR['accuracy']:.3f}", f"{LR['precision']:.3f}", f"{LR['recall']:.3f}", f"{LR['f1']:.3f}", f"{LR['training_seconds']:.3f} s"],
    ["Decision Tree", f"{DT['accuracy']:.3f}", f"{DT['precision']:.3f}", f"{DT['recall']:.3f}", f"{DT['f1']:.3f}", f"{DT['training_seconds']:.3f} s"],
    ["Neural Network (MLP)", f"{MLP['accuracy']:.3f}", f"{MLP['precision']:.3f}", f"{MLP['recall']:.3f}", f"{MLP['f1']:.3f}", f"{MLP['training_seconds']:.3f} s"],
], [151, 72, 76, 67, 50, WIDTH-416], compact=True))
add(Spacer(1, 6))
best_name, best_score = max((("Logistic Regression", LR["f1"]), ("Decision Tree", DT["f1"]), ("Neural Network", MLP["f1"])), key=lambda item:item[1])
add(p(f"The highest suspicious-class F1 was obtained by <b>{best_name}</b> ({best_score:.3f}). The three accuracies were {LR['accuracy']*100:.1f}%, {DT['accuracy']*100:.1f}% and {MLP['accuracy']*100:.1f}%, respectively. These results reflect constructed features in synthetic data and should not be treated as operational detection rates.", "dense"))
add(fig("05_confusion_matrices.png", 470,
        "Figure 4. Confusion matrices for Logistic Regression, Decision Tree and MLP."))
add(p(f"False alarms and missed threats were LR: {LR['false_positive']}/{LR['false_negative']}; tree: {DT['false_positive']}/{DT['false_negative']}; MLP: {MLP['false_positive']}/{MLP['false_negative']}. ROC AUC values were {LR['roc_auc']:.3f}, {DT['roc_auc']:.3f} and {MLP['roc_auc']:.3f}. Training times depend on the computer and environment.", "dense"))
add(fig("04_roc_models.png", 210,
        "Figure 5. ROC curves comparing all three classifiers on the held-out set."))
new_page()

# PAGE 5 - decision policy + ethics 1
add(section("5. Ethical Experiment I: Alert Thresholds"))
add(p("A classifier supplies an estimated probability, not a guaranteed verdict. The alert threshold determines when an event is marked suspicious. A lower cutoff catches more problematic events but increases legitimate-user interruptions; a higher cutoff avoids some interruptions but misses more suspicious activity. The experiment changed only the Logistic Regression decision cutoff, keeping its trained model and test data fixed."))
add(table(["THRESHOLD", "WRONGLY FLAGGED (FP)", "MISSED THREATS (FN)", "RECALL"], [
    [f"{t:.2f}", str(TH[t]["false_positive"]), str(TH[t]["false_negative"]), f"{TH[t]['recall']*100:.1f}%"]
    for t in [0.30, 0.50, 0.70]
], [84, 165, 159, WIDTH-408], compact=False))
add(Spacer(1, 16))
add(fig("06_threshold_tradeoff.png", 440,
        "Figure 6. How changing alert sensitivity shifts the two types of classification error."))
add(sub("5.1 What the errors mean"))
add(p(f"At 0.30 the detector would send <b>{TH[0.30]['false_positive']}</b> normal logins for unnecessary review while missing only <b>{TH[0.30]['false_negative']}</b> suspicious logins. At 0.70 it would disturb only <b>{TH[0.70]['false_positive']}</b> legitimate logins, but <b>{TH[0.70]['false_negative']}</b> suspicious events would escape the alert. No single cutoff minimizes both totals at once.", "dense"))
add(p("An alert should therefore not automatically become a hard account lock. A safer response is a step-up authentication request, an analyst review, an explanation to the affected user and a route to reverse an incorrect decision. The correct policy depends on the cost and urgency of each error type, not accuracy alone.", "dense"))
new_page()

# PAGE 6 - bias and privacy
add(section("6. Ethical Experiment II: Label Bias and Oversight"))
add(p(f"To demonstrate data-label bias, I created a separate group-aware Logistic Regression model and deliberately changed <b>{METRICS['biased_training_label_flips']}</b> legitimate training labels belonging to an arbitrary synthetic cohort called Group B. The corresponding test labels were left untouched. Group A and Group B are invented labels, not real demographic categories; this is a controlled stress test, not a claim about any population.", "dense"))
add(table(["TRAINING DATA", "GROUP A FP RATE", "GROUP B FP RATE"], [
    ["Unchanged labels", f"{FAIR[('Original labels','Group A')]['false_positive_rate']*100:.1f}%", f"{FAIR[('Original labels','Group B')]['false_positive_rate']*100:.1f}%"],
    ["Deliberately biased labels", f"{FAIR[('Biased training labels','Group A')]['false_positive_rate']*100:.1f}%", f"{FAIR[('Biased training labels','Group B')]['false_positive_rate']*100:.1f}%"],
], [202, 144, WIDTH-346], compact=True))
add(Spacer(1, 10))
add(fig("07_biased_labels_fpr.png", 408,
        "Figure 7. False-positive rates among benign events, with clean versus corrupted training labels."))
add(p(f"With the corrupted labels, the false-positive rate for Group B rose from <b>{FAIR[('Original labels','Group B')]['false_positive_rate']*100:.1f}%</b> to <b>{FAIR[('Biased training labels','Group B')]['false_positive_rate']*100:.1f}%</b>. This illustrates how biased historical decisions can be learned and reinforced by a model. The fairness experiment intentionally includes the synthetic group identifier; it is separate from the three primary model evaluations above.", "dense"))
add(sub("6.1 Privacy and interpretability"))
add(p("Operational login records could contain location, device information, access times and account identifiers. Responsible systems should minimize collection, control access, limit retention and use logs only for an authorized security purpose. Linear-model coefficients can support investigations, but neither coefficients nor neural-network scores prove the reason for an individual event. Human oversight and a way to contest adverse decisions remain important.", "dense"))
new_page()

# PAGE 7 - end matter
add(section("7. Findings, Constraints and Future Work"))
add(sub("7.1 Main findings"))
add(p("The implemented pipeline demonstrates that basic machine learning can identify artificially generated suspicious-login patterns using a combination of authentication indicators. Comparing Logistic Regression, Decision Tree and MLP on the same test data shows why model complexity should be justified by measurable performance and operational cost rather than assumed superiority."))
add(p("Equally important, the threshold experiment shows a measurable operational conflict between false alarms and missed events, while the corrupted-label experiment shows that a model can absorb discriminatory patterns from its training history. A security system requires safeguards around labels, metrics and actions, not only a high score on a test set."))
add(sub("7.2 Limits of the prototype"))
add(p("The dataset is synthetic, feature patterns were created using knowledge of the simulated label and the test data come from the same generator as the training data. These conditions can produce optimistic performance. The experiment includes only one seeded train/test division and does not assess new attack families, changing real-world behavior, adversarial inputs, concept drift or live detection delays. The MLP is a small educational neural network, not a large deployment-grade deep-learning system.", "dense"))
add(sub("7.3 Next steps"))
add(p("A stronger follow-up study would validate on an appropriately authorized external security dataset, report confidence intervals across repeated splits, check calibration, compare class-weighted alternatives, test temporal drift and measure fairness across justified subgroups. A prototype should first operate in analyst-review mode rather than automatically blocking accounts.", "dense"))
add(sub("7.4 Reproducibility and supplied outputs"))
add(p("Create a Python virtual environment, install dependencies using <b>python -m pip install -r requirements.txt</b>, then run <b>python run_project.py</b>. The project writes seven figures, three analysis CSV files and <b>outputs/metrics.json</b>. The <b>notebooks/Threat_Detection_Exploration.ipynb</b> notebook provides a separate step-by-step exploratory walkthrough. Use <b>python report/create_report.py</b> to regenerate this PDF from the saved outputs. The repository is supplied for private GitHub upload; a live repository URL is not claimed here.", "dense"))
add(sub("References"))
add(p("[1] AI in Cyber Security Lab, ENSP355, <i>Lab Assignment 01 - Unit 1</i>, course handout provided for this assessment.", "ref"))
add(p("[2] scikit-learn documentation, <i>LogisticRegression</i>, <i>DecisionTreeClassifier</i>, <i>MLPClassifier</i>, and <i>Pipeline</i>. https://scikit-learn.org/stable/", "ref"))
add(p("[3] National Institute of Standards and Technology, <i>AI Risk Management Framework (AI RMF 1.0)</i>, 2023. https://www.nist.gov/itl/ai-risk-management-framework", "ref"))
add(p("[4] Dataset provenance: synthetic login-event generator in <b>src/generate_data.py</b> (seed 42); no third-party or personal event records were used.", "ref"))

DEST.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(
    str(DEST), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=47, bottomMargin=52, title="AI Cyber Security Lab - Assignment 01 - Aditya Mishra",
    author=args.name, subject="Original Unit I mini-project technical report"
)
# No onPage canvas decorations: no footer, no page number and no watermark.
doc.build(story)
print(f"Created {DEST} ({DEST.stat().st_size:,} bytes)")
