# BTM Score — AI-Driven Diagnostic Score for Iron Deficiency Anemia vs. Beta-Thalassemia Trait

This repository contains the full analysis pipeline used to develop and validate
**the BTM Score**, a machine learning–derived diagnostic score for differentiating
iron deficiency anemia (IDA) from beta-thalassemia trait (BTM) using routine
complete blood count (CBC) parameters.

Developed at the Department of Hematology and Blood Bank, La Rabta Hospital,
Tunis, Tunisia.

## Contents

- [`BTM_score_analysis.ipynb`](BTM_score_analysis.ipynb) — the complete, reproducible analysis notebook:
  data preprocessing, 13 classical hematological indices, multicollinearity (VIF)
  assessment, XGBoost and Elastic Net models with Monte Carlo cross-validation,
  SHAP explainability analysis, and derivation/validation of the BTM Score.
- `requirements.txt` — Python dependencies.

## Data availability

Patient-level data are **not included** in this repository for confidentiality
reasons. The notebook expects an Excel file at `data/base apres nettoyage.xlsx`
(not tracked in this repo — see `.gitignore`) with one row per patient and the
CBC parameters referenced in the notebook. Researchers interested in the dataset
should contact the corresponding author.

## Running the analysis

```bash
pip install -r requirements.txt
jupyter notebook BTM_score_analysis.ipynb
```

Or open this repository in a GitHub Codespace (configuration provided in
`.devcontainer/`), which sets up the environment automatically.

## Methodology

See the accompanying manuscript for full methodological details, including
inclusion/exclusion criteria, statistical methods, and results.
