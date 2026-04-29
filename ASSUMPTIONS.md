# Assumptions & Questions

When building this pipeline, I had to make several assumptions to proceed. If I were on the job, I would ask the stakeholders the following questions, ranked by how dangerous my assumption could be:

### 1. High Risk: Bank Transfer Batching
**Question:** *"Are bank transfers strictly 1-to-1 with a specific month's expected pay, or do UTRs sometimes batch multiple months of back-pay together?"*
**Why it's dangerous:** My code aggregates expected pay and actual pay using a strict `year_month` outer join. If a worker worked in January, but was paid for both January and February in a single February UTR transfer, my code will flag January as massively underpaid and February as massively overpaid.

### 2. High Risk: Phone Ownership Liability
**Question:** *"When a worker registers a new phone number, are we legally required to direct back-pay to the new phone/bank account, or to the account associated with the phone they originally logged the shift under?"*
**Why it's dangerous:** My deduplication logic intentionally merges historical logs to their *newest* canonical phone number to unify the worker's lifetime summary. If payout liability is strictly tied to the phone used *at the time of the shift*, my grouping strategy is legally incorrect.

### 3. Medium Risk: Backdated Log Rates
**Question:** *"If a supervisor backdates a shift log by 3 days, should we apply the wage rate that was active on the `work_date` or the rate active on the `entered_at` date?"*
**Why it's dangerous:** I assumed the wage rate corresponds to the physical `work_date`. If company policy dictates that the rate applied is based on the submission date, some `date_mismatch` flags are actually calculating the incorrect expected pay.

### 4. Low Risk: Paise Conversions
**Question:** *"Are there any roles that legitimately earn > ₹1,000 per hour?"*
**Why it's dangerous:** I used a heuristic that assumes any base rate > 1,000 in `wage_rates.csv` is already formatted in paise. If a highly specialized role earns ₹1,500/hr, the system will incorrectly assume it means 1,500 paise (₹15) and underpay them severely.
