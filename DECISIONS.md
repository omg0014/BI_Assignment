# Technical Decisions

## Why this Stack, Dedup, and UI?

### The Stack
I chose Python + Pandas for the backend because the core problem is data reconciliation:
- joining heterogeneous sources,
- applying effective-dated logic,
- handling timezones,
- and performing vectorized calculations.

Pandas allowed rapid iteration on these transformations without schema overhead.

Flask was used as a minimal API layer to expose results for inspection.  
For the frontend, I chose Vanilla JS + CSS to avoid build complexity and prioritize speed of execution and portability for a take-home assignment.

---

### The Reconciliation Strategy (Key Decision)
This problem is explicitly *not* solvable via a single JOIN.

I implemented a multi-step pipeline:
1. Normalize identity (phones, names)
2. Map historical logs → canonical worker identity
3. Resolve effective-dated wage rates per shift
4. Compute expected pay at shift level
5. Aggregate expected and actual payouts at a monthly level
6. Reconcile differences and propagate uncertainty flags

I chose **monthly aggregation (`year_month`)** as a practical compromise:
- aligns reasonably with payroll cycles
- simplifies matching expected vs actual transfers
- avoids complex many-to-many matching between shifts and bank transfers

Trade-off:
- does not handle cross-month batching or partial payouts perfectly (documented in ASSUMPTIONS.md)

---

### The Deduplication Strategy
`workers.csv` reflects *current identity*, while `supervisor_logs.csv` contains *historical identity*.

To unify identities:
- I normalized names and phones
- sorted workers by `registered_on` (latest first)
- mapped each normalized name → latest known phone
- rewrote historical logs to use this canonical identity

This allows aggregation of lifetime earnings for a worker despite phone number changes.

Trade-off:
- assumes normalized names uniquely identify a worker
- risks merging distinct individuals with similar names (documented in ASSUMPTIONS.md)

---

### The UI
The UI is designed for **Ops triage, not exploration**.

It focuses on:
- grouping workers by confidence (`High`, `Medium`, `Low`)
- surfacing discrepancies (`delta`)
- displaying explicit `review_reason` flags inline

This enables:
- quick identification of clean discrepancies (actionable payouts)
- separation of cases requiring manual investigation

---

## 3 Things I Got Wrong on Purpose

These were deliberate trade-offs to meet the time constraint:

### 1. Using CSVs as a Database
The pipeline reads CSVs into memory on each run.

In production:
- data should live in a relational database (e.g., PostgreSQL)
- indexed joins and historical tracking would improve correctness and performance
- reconciliation should run incrementally, not from scratch

---

### 2. Monthly Aggregation Instead of True Matching
I aggregated payouts by `year_month` rather than performing exact matching between shifts and bank transfers.

Why:
- significantly reduces complexity
- avoids ambiguous many-to-many matching

Trade-off:
- fails when:
  - payments are batched across months
  - payouts are split or delayed

This is the largest correctness compromise in the system.

---

### 3. Hardcoded Anomaly Thresholds
I used a fixed threshold (₹1,00,000) to detect extreme payout anomalies.

In production:
- thresholds should be dynamic (e.g., percentile-based per role/state)
- anomaly detection should be statistical, not rule-based

---

## Final Thought

The system is intentionally designed to be:
- **correct enough to surface real discrepancies**
- **transparent about uncertainty**
- **fast to iterate on**

Rather than attempting perfect matching, the design prioritizes:
> surfacing issues + enabling human triage

which is more realistic for messy real-world financial pipelines.
