# Assumptions & Questions

While building the reconciliation pipeline, I made several assumptions to proceed. Below are the key questions I would clarify with stakeholders, ranked by risk (impact if the assumption is wrong).

---

## 1. High Risk: Bank Transfer Batching & Timing
**Question:** *Are bank transfers strictly aligned 1:1 with a single month’s work, or can a UTR include multiple months (back-pay), or partial payouts within a month?*

**Why it’s dangerous:**  
The current approach aggregates both expected and actual amounts by `year_month`. If payouts are:
- batched across months, or
- split across multiple transfers within a month,

then the reconciliation will show false underpayments and overpayments (e.g., January appears underpaid while February appears overpaid).

---

## 2. High Risk: Identity & Payout Liability (Phone Changes)
**Question:** *When a worker changes their phone/bank details, should historical payouts be tied to the original identity at time of work, or to the latest registered identity?*

**Why it’s dangerous:**  
The pipeline consolidates worker identity by mapping to the most recent canonical phone. This simplifies aggregation but may:
- misattribute payouts across identities, or
- violate business/legal rules if liability is tied to the original account used at shift time.

---

## 3. High Risk: Timezone & Vendor Semantics
**Question:** *Do all vendor apps log timestamps and work dates consistently (IST vs UTC), and which field is authoritative for wage calculation?*

**Why it’s dangerous:**  
`vendor_b_v1.0` appears to log `work_date` incorrectly relative to UTC timestamps. The pipeline adjusts this by deriving `work_date` from `entered_at` converted to IST.  
If this assumption is incorrect:
- shifts may be assigned to the wrong day,
- incorrect wage rates may be applied due to effective-date boundaries.

---

## 4. Medium Risk: Wage Rate Overlaps & Effective Dates
**Question:** *Are overlapping wage rate windows intentional (e.g., corrections), and if so, which rate takes precedence?*

**Why it’s dangerous:**  
When multiple wage rates match a shift date, the pipeline selects the most recent `effective_from` value.  
If overlaps represent data errors or require a different precedence rule, expected pay may be systematically incorrect.

---

## 5. Medium Risk: Open-Ended Wage Rates
**Question:** *Does a missing `effective_to` date always indicate that the wage rate is currently active with no defined end?*

**Why it’s dangerous:**  
The pipeline treats missing `effective_to` values as open-ended by assigning a far-future date (`2099-12-31`).  
If missing end dates instead indicate incomplete or erroneous data, this assumption could incorrectly apply outdated rates to current shifts.

---

## 6. Medium Risk: Backdated Log Policy
**Question:** *For backdated entries, should wage rates be applied based on `work_date` or `entered_at` (submission time)?*

**Why it’s dangerous:**  
The pipeline uses `work_date` to determine the applicable wage rate. If policy dictates that the rate should be based on submission time, some entries will be evaluated against incorrect rate windows.

---

## 7. Medium Risk: Identity Matching Fallback
**Question:** *Is it acceptable to match workers by normalized name when phone numbers are missing or inconsistent?*

**Why it’s dangerous:**  
Name-based matching can:
- merge distinct individuals with similar names, or
- incorrectly link historical records.

The current approach prioritizes phone-based matching and flags unmatched rows for manual review.

---

## 8. Low Risk: Rate Unit Consistency (INR vs Paise)
**Question:** *Are all wage rates consistently stored in INR, or are some already in paise?*

**Why it’s dangerous:**  
A heuristic is used to infer units based on magnitude. If incorrect, expected pay could be off by 100x.

---

## 9. Low Risk: Outlier Thresholds
**Question:** *What constitutes a “reasonable” upper bound for shift earnings?*

**Why it’s dangerous:**  
Outlier detection uses a fixed threshold to flag anomalies. If this threshold is poorly calibrated, legitimate cases may be flagged (false positives) or true anomalies missed.
