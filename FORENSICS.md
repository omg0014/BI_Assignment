# Forensics & Findings

## Executive Summary
The payout pipeline has been miscalculating wages due to a combination of identity fragmentation, timezone inconsistencies, and rate application errors. 

Across the dataset:
- X workers are underpaid (positive delta)
- Y workers are overpaid (negative delta)
- Total net underpayment: ₹Z
- ~N% of records require manual review due to data inconsistencies

(Values derived from `worker_summary.csv` and reconciliation output.)

---

## 1. Who is owed money?

The reconciliation tool computes expected vs actual payouts per worker and surfaces discrepancies with confidence levels:

- **High Confidence:** Clean identity match, valid rate, no anomalies → reliable payout discrepancy  
- **Medium Confidence:** Minor inconsistencies (e.g., amount mismatch only) → likely true discrepancy  
- **Low Confidence:** Data issues present (identity mismatch, timezone issues, missing rates) → requires manual review  

Workers with **positive `delta_paise`** are owed money.  
Workers with **negative `delta_paise`** may have been overpaid.

The attached dashboard and `worker_summary.csv` provide a ranked list of workers by total discrepancy.

---

## 2. Root Causes (Multiple Bugs Detected)

The payout errors are not due to a single bug, but a combination of systemic issues:

### 2.1 Identity Fragmentation (Phone Number Churn)
Workers update their phone numbers over time.  
The pipeline relied on phone numbers as a primary key.

**Impact:**
- Same worker appears as multiple identities
- Historical shifts are not linked to current bank records
- Results in:
  - “Unpaid ghost workers” (logs exist, no transfers)
  - “Overpaid active workers” (transfers without matching logs)

---

### 2.2 Vendor Timezone Mismatch
Different vendor apps log timestamps differently:
- `vendor_a`: local IST timestamps (correct)
- `vendor_b_v1.0`: UTC timestamps stored as local dates (incorrect)

**Impact:**
- Shifts near midnight are assigned to the wrong calendar date
- Wage rate selection becomes incorrect near effective-date boundaries
- Leads to systematic under/over calculation depending on rate changes

---

### 2.3 Wage Rate Ambiguity & Overlaps
Wage rates are defined using effective date windows, with some overlaps.

**Impact:**
- Multiple rates may apply to a single shift
- Without deterministic precedence rules, incorrect rates may be selected
- Even with “latest effective rate” logic, ambiguity remains

---

### 2.4 Lack of Data Validation & Outlier Detection
The pipeline lacks safeguards against anomalous values.

**Impact:**
- Incorrect rates or hours propagate unchecked
- INR/paise inconsistencies can inflate values by 100x
- Observed extreme cases (e.g., ₹2L+ expected monthly payout) indicate missing validation

---

## 3. Confidence in Findings

- **High confidence:** identity + rate + timezone consistent  
- **Medium confidence:** minor discrepancies (likely real financial mismatch)  
- **Low confidence:** data inconsistencies (identity/timezone/rate ambiguity)

Overall confidence:
- High/Medium records reliably indicate payout issues
- Low-confidence records require manual Ops validation

---

## 4. Recommended Pipeline Changes

To prevent recurrence, changes are required at ingestion and validation layers:

### 4.1 Enforce Stable Worker Identity (UUID)
- Do not rely on mutable fields like phone numbers
- All logs and payouts must reference a canonical `worker_id`

---

### 4.2 Standardize Time Handling
- Require ISO-8601 timestamps with timezone offsets
- Convert all timestamps to UTC at ingestion
- Apply business logic (e.g., work_date) only after normalization

---

### 4.3 Resolve Rate Ambiguity
- Enforce non-overlapping effective date windows
- Define explicit precedence rules for overlapping rates
- Add validation checks for missing or duplicate rate windows

---

### 4.4 Add Anomaly Detection Layer
- Reject or flag:
  - payouts outside expected range
  - abnormal hours or rates
- Example: trigger review if payout exceeds statistical threshold for role/state

---

### 4.5 Improve Reconciliation Logic
- Support non-monthly payout matching (handle batching / partial payments)
- Track payout lineage across periods

---

## 5. Final Takeaway

The issue is not a single calculation bug but a **system design problem**:
- identity is unstable
- time is inconsistent
- rates are ambiguous
- validation is missing

Fixing these requires **data modeling + ingestion discipline**, not just code changes.
