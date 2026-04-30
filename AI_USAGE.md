# AI Usage Log

This document outlines how AI tools were used during the development of this assignment, including where they accelerated progress and where human judgment was required to correct or guide outputs.

---

## Where AI Helped

### 1. Data Processing (Pandas)
AI significantly accelerated the implementation of Pandas operations, especially:
- grouped aggregations (`groupby().agg()`)
- outer joins for reconciliation
- column transformations and cleanup

This reduced time spent on syntax-heavy code and allowed focus on logic design.

---

### 2. UI Scaffolding
AI helped generate:
- initial dashboard layout
- basic styling (including dark mode variables)
- component structure for displaying reconciliation data

This eliminated repetitive frontend setup work.

---

### 3. Environment Debugging
AI helped quickly diagnose a local development issue where port `5000` was occupied by macOS (AirPlay Receiver), and suggested using `127.0.0.1` to avoid resolution issues.

---

## Where AI Required Correction

### 1. Identity Matching Logic
AI initially suggested a straightforward join on normalized phone numbers.  
However, the prompt explicitly notes that:

> “phone/name reflect current registered identity, not historical”

This required rethinking the approach:
- detecting duplicate identities across time
- implementing canonical mapping based on most recent registration
- acknowledging the risk of merging identities based on names

AI did not surface this issue independently; it required manual reasoning about data semantics.

---

### 2. Timezone Handling
AI assumed standard timezone conversion (`tz_convert`) was sufficient.

However, deeper inspection revealed:
- different vendor apps handled timestamps inconsistently
- `vendor_b_v1.0` logged `work_date` incorrectly (based on UTC rather than local time)

This required:
- detecting vendor-specific behavior
- applying a targeted correction for affected rows

AI needed explicit guidance to reach this conclusion.

---

## Takeaway

AI was highly effective for:
- accelerating implementation
- reducing boilerplate
- assisting with debugging

However, it struggled with:
- interpreting ambiguous business rules
- identifying data inconsistencies hidden behind “clean” joins

Human judgment was essential for:
- correctly interpreting identity and timezone edge cases
- validating assumptions against real-world system behavior

The final solution reflects a combination of AI-assisted implementation and manual reasoning over data integrity issues.
