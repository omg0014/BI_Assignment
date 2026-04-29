# Technical Decisions

## Why this Stack, Dedup, and UI?

**The Stack:**
I chose Python/Pandas for the backend because it excels at rapid, complex data munging, timezone manipulation, and vectorized math over thousands of rows. I chose Flask to serve the JSON API due to its lightweight setup. For the frontend, I chose Vanilla JS and CSS—avoiding React or complex build tools to ensure maximum execution speed, rapid iteration, and guaranteed portability for a take-home assignment.

**The Deduplication Strategy:**
Because `workers.csv` acts as the source of truth for *current* identity but `supervisor_logs.csv` contains *historical* data, I deduplicated identities based on their normalized Name + State. I sorted the registry by `registered_on` to find their newest active phone number, and mapped all historical shift logs to that canonical phone number *before* aggregation. This unifies their lifetime expected pay.

**The UI:**
I built a triage-focused dashboard. Operations teams don't need raw data; they need actionable alerts. The UI groups workers by Confidence Score (`High`, `Medium`, `Low`) and explicitly lists the `review_reason` flags (e.g., `date_mismatch`, `amount_anomaly`) directly inline.

---

## 3 Things I Got Wrong on Purpose

To meet the 16-hour deadline, I made deliberate trade-offs that would be unacceptable in production:

1. **Using CSVs as a Database:**
   The backend processes the raw CSV files into pandas DataFrames in-memory on every startup. In production, this data should be migrated to a relational database (like PostgreSQL) to support efficient indexing, concurrent reads, and ACID compliance for payouts.
2. **Client-Side Heavy Rendering:**
   The frontend fetches the entire reconciled JSON payload at once and handles all filtering and sorting client-side. While perfectly fast for 12,000 workers, this will crash the browser tab if the company scales to 1,000,000 workers. Server-side pagination is required long-term.
3. **Hardcoded Anomaly Thresholds:**
   To catch the massive paise/INR bugs, I hardcoded a safeguard threshold of ₹1,00,000 (10M paise). In a real financial pipeline, this should be a dynamic statistical threshold (e.g., > 99th percentile for that specific role/state) to account for natural wage inflation or high-tier workers.
