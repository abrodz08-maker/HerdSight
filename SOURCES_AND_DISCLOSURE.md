# Sources, data provenance, AI disclosure and permissions

## External resources used for domain context

1. Merck Veterinary Manual, *Overview of Bovine Respiratory Disease Complex*: https://www.merckvetmanual.com/respiratory-system/bovine-respiratory-disease-complex/overview-of-bovine-respiratory-disease-complex
2. Merck Animal Health, *Frequently Asked Questions: Bovine Respiratory Disease*: https://www.merck-animal-health-usa.com/producers/cattle/faqs/bovine-respiratory-disease-brd/
3. Merck Animal Health, *Advancing your BRD outcomes*: https://www.merck-animal-health-usa.com/producers/cattle/cattle-insights/beef/advance-brd-outcomes/
4. Merck Animal Health, *Best practices to prepare for BRD season*: https://www.merck-animal-health-usa.com/producers/cattle/cattle-insights/beef/best-practices-bovine-respiratory-disease-prevention/

These sources support the *relevance* of transportation, mixing, animal condition, environment, nutrition, early recognition and veterinary-directed treatment. They do **not** establish the numerical risk weights or scenario reduction percentages used in the prototype.

## Data provenance

- `data/BRD_synthetic_10000_cattle.xlsx` was supplied by the project team to the assistant. It contains `Cattle_Records` (10,000 simulated animals; four simulated feedlots), `Data_Dictionary`, and `Dataset_Summary`. Its simulated 45-day BRD label has 1,994 positive outcomes (19.94%).
- The workbook is synthetic. Its original generation algorithm, random seed, permissions provenance, and source citations were not available to independently verify. The original 10,000 rows **cannot be regenerated** from the provided materials. Confirm redistribution rights before submission.
- `scripts/generate_sample.py` creates a **different**, fully reproducible synthetic sample (fixed seed, controllable row count) to demonstrate data generation; it does not reconstruct the source workbook.
- `data/missing_data_test.csv` was generated to exercise incomplete-record handling.
- The workbook's `Data_Dictionary` sheet documents its 37 original columns; the dashboard creates additional derived columns described in the technical brief.

## AI-tool disclosure (draft for team verification)

OpenAI ChatGPT (GPT-6) assisted with **Streamlit application code, scenario calculation logic, testing scripts, preparation of the synthetic missing-data test CSV, technical documentation, report drafting, and project packaging**. Earlier team work also used AI assistance to produce the original synthetic dataset, according to the project's stated provenance. The team must verify and add any other AI systems, tools, dates, or roles actually used. **Do not remove the coding assistance disclosure**: the hackathon explicitly requires disclosure of AI tools used.

## Rights and confidentiality

The included records are synthetic and contain no known real cattle identifiers or personal data. The original workbook was supplied for this task; the assistant cannot establish ownership or redistribution permission. Team members should confirm rights and remove any file they cannot legally share. External sources are linked, not copied into the submission. No paid services or API keys are required.

## Clinical scope

The app does not diagnose BRD, recommend antimicrobial drugs or doses, determine treatment eligibility, or establish causal efficacy. Any clinical or antimicrobial decisions require veterinary judgment and appropriate oversight.
