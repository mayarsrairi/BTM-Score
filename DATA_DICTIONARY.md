# Data dictionary

The patient-level file is **not** distributed (confidentiality). The notebook expects an Excel
file at `data/cohort_after_cleaning.xlsx` with **one row per patient** and the 24 columns below
(names must match exactly; leading/trailing spaces in column names are stripped).
All values are the raw values exported from the Sysmex XN-1000 analyser; unit conversions used
for the tables and for the score formula are done inside the notebook.

| Column | Meaning | Unit of the raw value |
|---|---|---|
| `Age` | Age at diagnosis | years |
| `Sex` | Sex | `f` / `m` (case-insensitive) |
| `Diagnosis` | Final diagnosis (used to build the outcome) | text: `iron deficiency anemia` (outcome 0) or `beta-thalassemia minor` (outcome 1); any other value is excluded |
| `WBC` | White blood cell count (descriptive only, not a model input) | cells/uL |
| `RBC` | Red blood cell count | x10^6/uL (= x10^12/L) |
| `Hb` | Hemoglobin | g/dL |
| `HCT` | Hematocrit | % |
| `MCV` | Mean corpuscular volume | fL |
| `MCH` | Mean corpuscular hemoglobin | pg |
| `MCHC` | Mean corpuscular hemoglobin concentration | g/dL |
| `PLT` | Platelet count | cells/uL |
| `RDW-SD` | Red cell distribution width, standard deviation (analyser-specific definition) | fL |
| `RDW-CV` | Red cell distribution width, coefficient of variation | % |
| `NEUT`, `LYMPH`, `MONO`, `EO`, `BASO` | Absolute differential leukocyte counts | cells/uL |
| `RET %` | Reticulocyte percentage | % |
| `RET absolute` | Absolute reticulocyte count | cells/uL (e.g. 45300; **not** x10^6/uL) |
| `IRF` | Immature reticulocyte fraction | % |
| `LFR`, `MFR`, `HFR` | Low / medium / high fluorescence reticulocyte fractions | % |

The 20 model inputs (`HEMATO_VARS` in the notebook) are: RBC, Hb, HCT, MCV, MCH, MCHC, PLT, RDW-SD,
RDW-CV, NEUT, LYMPH, MONO, EO, BASO, RET %, RET absolute, IRF, LFR, MFR, HFR.
Ferritin, HbA2 and hemoglobin electrophoresis (which define the classes) are **not** model inputs.

Missing values are median-imputed **inside each training fold** (the test fold uses the training
medians), for the models and for the 13 conventional indices. A sensitivity analysis without any
imputation, on the complete cases, is in Section 14.4 of the notebook.

## Units of the BTM score variables

The formulas are written, and must be applied, with these units:

| Score | Variable | Unit to enter |
|---|---|---|
| Main score | `MCHC` | **g/dL** |
| Main score | `RDW-SD` | **fL** |
| Main score | `RET absolute` | **x10^9/L** (= x10^3/uL; the usual reticulocyte reporting unit). The raw cells/uL count stored in the data file must be **divided by 1,000** before it enters the formula |
| Universal version | `MCHC` | **g/dL** |
| Universal version | `MCV` | **fL** |
| Universal version | `RBC` | **x10^12/L** (= x10^6/uL, the unit stored in the data file) |

Entering values in other units gives a wrong probability. The notebook prints the units next to each
formula (Sections 10 and 12), and the Excel calculator it generates (`results/BTM_score_calculator.xlsx`)
states them next to every input cell.
