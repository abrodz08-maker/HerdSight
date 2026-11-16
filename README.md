# HerdSight — Livestock Health Intelligence

AISFS × Merck Animal Health Interdisciplinary Hackathon 2026 — independent student research prototype.

## Quick start (no paid services)

Requires Python 3.10+.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The application loads `data/BRD_synthetic_10000_cattle.xlsx` by default. Use the sidebar to upload a CSV/XLSX instead. A deliberately incomplete test CSV is included at `data/missing_data_test.csv`.

## Decision workflow

1. Choose feedlots and the 45-day cohort definition.
2. Review risk **intervals** and the data-review queue; missing values never automatically imply low risk.
3. Set baseline incidence, case costs, mortality and antimicrobial-course assumptions.
4. Set staffing, veterinary and observation-space capacities, including existing baseline utilization.
5. Compare current operations, targeted monitoring and enhanced husbandry. Adjust assumed effects and resource use.
6. Check feasible strategies and health/cost/antimicrobial trade-offs; download JSON/TXT decision summaries.

## Data and model cautions

- Dataset is synthetic and outcome labels are simulated. Not real animals, not a clinical validation study.
- Risk score is an uncalibrated additive prioritization index, **not** an estimated probability.
- Lower/upper score bounds reflect unobserved additive inputs, not confidence intervals.
- Baseline 45-day BRD incidence and all intervention effects are adjustable assumptions; they are **not** inferred from risk scores.
- Historical arrivals in the workbook are from 2025. The default analysis considers each arrival's subsequent 45-day outcome period, not whether the animal is within 45 days **today**. The optional current-cohort filter will therefore usually be empty.
- The source workbook's original data-generation code was not available. `scripts/generate_sample.py` creates a separate fully reproducible example; it **does not** reproduce the 10,000-row workbook.
- Clinical care and antimicrobial decisions require veterinary oversight; no medication selection or dose is provided.

## Included submission materials

- `app.py`, `requirements.txt`, `README.md`: dashboard and launch instructions.
- `data/BRD_synthetic_10000_cattle.xlsx`: shareable synthetic demonstration workbook (records, data dictionary, summary).
- `data/missing_data_test.csv`: incomplete-data robustness test.
- `scripts/generate_sample.py`: reproducible *new* demonstration data generator.
- `scripts/evaluate.py`: deterministic synthetic-data evaluation and completeness summary.
- `tests/test_logic.py`: basic calculation and missing-data regression checks.
- `docs/TECHNICAL_BRIEF.pdf`: three-page-or-less technical brief.
- `docs/DEMONSTRATION_CASE.md`: end-to-end decision workflow.
- `docs/SOURCES_AND_DISCLOSURE.md`: source links, AI disclosure, licensing and limitations.

## Test

```bash
python -m unittest discover -s tests -v
python scripts/evaluate.py
python scripts/generate_sample.py --output data/reproducible_sample.csv --rows 120 --seed 2026
```

**Before submitting:** Team members should verify all assumptions, references, calculations, data sharing rights and AI disclosure; run the live Streamlit interface on their own computers. This is a research prototype, not a clinically validated decision tool.
