# HerdSight — end-to-end demonstration case

**Purpose:** Illustrate a feedlot manager's decision for cattle during the first 45 days after arrival. This is a **hypothetical scenario**, not a validated prediction or clinical recommendation.

## 1. Starting conditions

1. Run `python -m streamlit run app.py` and retain the default synthetic workbook.
2. Select **TX_Panhandle_1** in the sidebar. The dataset contains 2,828 cattle from this yard (historical 2025 arrivals).
3. Keep **All selected arrivals (45-day outcome per arrival)**. Do **not** select “Currently within days 0–45”: these historical cattle are not currently in that calendar window.
4. Use the default illustrative assumptions: 20% 45-day BRD incidence, $110 treatment cost/case, $90 performance loss/case, 5% case fatality, $1,600 loss/death, and 90% of cases receiving a clinical antimicrobial course.
5. Set four staff × 40 daily checks = 160 monitoring checks/day, 35 veterinary evaluations/day, 60 observation spaces, and five planning days. Current operations already use 40 checks/day, eight vet evaluations/day, and 15 observation spaces.

## 2. Risk and uncertainty review

Open **Risk & Missing Data**. Inspect at least one animal with incomplete vaccination status. Its unknown risk contribution is reflected in the **upper** score bound. The review queue includes incomplete records and never assumes missing values mean low risk. The model is uncalibrated and cannot give clinical probabilities.

## 3. Compare alternatives

Go to **Strategy Comparison**. Use three approaches:

| Alternative | Assumed BRD reduction | Incremental cost | Additional checks per priority animal | Additional veterinary reviews | Additional observation-space demand |
|---|---:|---:|---:|---:|---:|
| Current operations | 0% | $0/head | 0 | 0% | 0% |
| Targeted monitoring | 10% | $5/head | 1 | 25% of high-priority + data-review animals | 10% of high-priority + data-review animals |
| Enhanced husbandry | 18% | $12/head | 2 | 40% of high-priority + data-review animals | 20% of high-priority + data-review animals |

The dashboard recalculates cases, deaths, costs, antimicrobial courses and demand against the actual number of selected high-priority/data-review animals. It flags alternatives exceeding **any** entered capacity. No strategy is automatically declared medically optimal.

## 4. Worked baseline projection (2,828 animals)

Under the explicitly assumed 20% 45-day BRD incidence:

- Baseline BRD cases = 2,828 × 0.20 = **565.6 expected cases**.
- Baseline deaths = 565.6 × 0.05 = **28.28 expected deaths**.
- Baseline clinical antimicrobial courses = 565.6 × 0.90 = **509.04 expected courses**.
- Baseline disease costs = 565.6 × ($110 + $90) + 28.28 × $1,600 = **$158,368**.

These are **expectation values**, so fractional cases/deaths/courses are acceptable for scenario planning. No real-world outcome is asserted.

## 5. Decision and recommendation

The manager should **not** choose solely on the lowest projected cost. First verify which alternatives are feasible under current staff, veterinary and pen-space limits. Then compare assumed BRD cases, deaths, incremental program expense, total cost and antimicrobial courses. If a strategy is infeasible, either adjust staffing/capacity, revise the proposed scope, or retain the feasible baseline while arranging necessary clinical care. **Never delay or deny evaluation of symptomatic cattle to satisfy a modeled capacity.** Any antimicrobial treatment or prevention plan requires veterinary review.

## 6. Export

Open **Decision Summary**, select the alternative under consideration, add a rationale and download both JSON and printable TXT. The report captures assumptions, constraints, projected consequences and feasibility. It is an audit trail of an **assumption-driven decision**, not a clinical order.

## 7. Demonstration of incomplete information

Upload `data/missing_data_test.csv`. The 36-animal, four-feedlot file contains intentional missing values and missing arrival dates. Confirm that incomplete animals show score bounds, missing-field lists, and “Data review” priority when core completeness is insufficient. Some animals will have unknown current 45-day status. No automatic “low risk” should be inferred from missing inputs.
