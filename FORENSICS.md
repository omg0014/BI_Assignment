# Forensics & Findings

## 1. Who is owed money?
The system calculates exact deltas for the ~12,000 workers dynamically on every run, surfacing the discrepancies in the provided dashboard tool. The dashboard automatically sorts workers by confidence level (`High`, `Medium`, `Low`). 

Workers with a `Medium` confidence score (Delta != 0, but no data anomalies) are guaranteed to be owed (or owe) money due to the silent miscalculations. Workers with a `Low` confidence score must be manually triaged by Ops, as their calculations involve corrupted/missing source data.

## 2. Root Causes (Multiple Bugs Detected)
The payout pipeline was failing silently due to **three distinct bugs** acting simultaneously:

1. **Identity & Phone Number Churn:** Workers periodically update their registered phone numbers. Because the pipeline relied on a strict phone-number join, shifts logged by supervisors using a historical phone number failed to match the current bank transfer records. This caused the system to split a single worker into two identities: an "unpaid ghost" and an "overpaid active worker."
2. **Vendor Timezone Mismatches:** Two different vendor apps were recording timestamps differently. `vendor_a` correctly used local IST time, while `vendor_b` recorded raw UTC timestamps. Because shifts near midnight (00:00 - 05:30 IST) were stamped with the previous day's UTC date, the system miscalculated their `work_date`. This caused the old, incorrect wage rate to be applied during rate-change boundaries.
3. **Implicit Paise/INR Conversions:** The pipeline lacked sanity checks. If an unexpectedly large amount was logged or a decimal was misplaced, the `rate_multiplier` compounded the error by 100x. We found massive outliers (e.g., ₹2.4 Lakh expected pay for a single month) that passed silently through the old pipeline.

## 3. Recommended Pipeline Changes
To prevent this category of bug going forward, we must change the architecture at the ingestion layer:
1. **Enforce Canonical UUIDs:** Do not rely on mutable PII (phone numbers) as primary keys. The supervisor mobile app must inject a stable `worker_id` (UUID) into the payload when logging shifts.
2. **Standardize Timezone Payloads:** Mandate ISO-8601 strict formats with explicit timezone offsets for all vendor APIs. The backend should convert all incoming logs to UTC immediately upon ingestion, and only convert to local IST immediately before querying rate-boundary dates.
3. **Implement Anomaly Gates:** Add an automated bounds-check layer before triggering bank transfers. Any payout exceeding 2 standard deviations from a role's median expected pay should be automatically quarantined and flagged for human review.
