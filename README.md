# Bharat Intelligence - Payout Reconciliation System

A full-stack system to detect and explain wage miscalculations across field workers by reconciling:

* Supervisor shift logs
* Wage rate tables (effective-dated)
* Bank transfer records
* Worker identity registry

---

##  What This System Does

This tool reconstructs **expected wages** and compares them against **actual payouts**, then surfaces discrepancies for Ops teams.

### Core capabilities:

* Computes **expected pay per shift**
* Applies **effective-dated wage rates**
* Handles **timezone inconsistencies across vendor apps**
* Resolves **identity issues (phone number churn)**
* Aggregates payouts and performs reconciliation
* Flags discrepancies with:

  * `delta_paise` (difference)
  * `needs_manual_review`
  * `review_reason`
  * `confidence` level

---

##  Project Structure

```
bharat_intelligence/
├── backend/
│   ├── app.py
│   ├── reconcile.py
│   └── data/
│       ├── workers.csv
│       ├── supervisor_logs.csv
│       ├── bank_transfers.csv
│       └── wage_rates.csv
├── frontend/
├── docs/
│   ├── FORENSICS.md
│   ├── DECISIONS.md
│   ├── ASSUMPTIONS.md
│   └── AI_USAGE.md
├── README.md
```

---

##  How to Run Locally

### 1. Start Backend (Flask API)

Setup
python3 -m venv .venv
source .venv/bin/activate
pip install pandas flask flask-cors

```bash
cd backend
source ../.venv/bin/activate
python app.py
```

Backend will run at:

```
http://127.0.0.1:5000
```

### API Endpoints:

* `/api/summary` → key metrics
* `/api/reconciliation` → full reconciled dataset

---

### 2. Start Frontend (Dashboard)

Open a new terminal:

```bash
python -m http.server 8080
```

Then open in browser:

```
http://localhost:8080/frontend/
```

---

##  Outputs Generated

Running the backend generates:

### `reconciled_output.csv`

* Expected vs actual payouts (per worker/month)
* Includes:

  * discrepancy (`delta_paise`)
  * review flags
  * confidence score

### `worker_summary.csv`

* Total expected vs actual per worker
* Highlights:

  * who is underpaid
  * who is overpaid

---

##  Key Design Highlights

* Handles **messy real-world identity (phone changes)**
* Fixes **timezone inconsistencies across vendors**
* Applies **effective-dated wage rates (with overlaps)**
* Surfaces **data anomalies and edge cases**
* Separates **high-confidence vs low-confidence discrepancies**

---

##  Known Limitations (Intentional)

* Uses **monthly aggregation** instead of exact transfer matching
* Name-based identity fallback may merge similar workers
* Static anomaly thresholds (not statistical)
* CSV-based processing (no database layer)

All trade-offs are documented in:

* `docs/ASSUMPTIONS.md`
* `docs/DECISIONS.md`

---

##  Key Deliverables

* `FORENSICS.md` → Findings & root cause analysis (**most important**)
* `DECISIONS.md` → Design trade-offs
* `ASSUMPTIONS.md` → Risk-based assumptions
* `AI_USAGE.md` → How AI was used

---

##  Quick Test

After starting backend, open:

```
http://127.0.0.1:5000/api/summary
```

This returns:

* total workers
* underpaid / overpaid counts
* total discrepancy
* review count

---

##  macOS Note

If Flask fails with:

```
Address already in use
```

Disable **AirPlay Receiver** in System Settings
(or run Flask on a different port)

---

##  Design Philosophy

This system is intentionally designed to:

> **Surface discrepancies with clear confidence levels, rather than attempt perfect matching.**

Real-world financial pipelines are messy — the goal is to:

* identify issues reliably
* explain uncertainty
* enable efficient Ops triage
