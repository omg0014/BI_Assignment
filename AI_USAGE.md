# AI Usage Log

This document tracks how AI was utilized to accelerate the development of this take-home assignment, highlighting where it excelled and where it stumbled.

## Where AI Helped
* **Data Munging (Pandas):** Writing complex grouped aggregations and outer joins in Pandas is syntax-heavy. AI was excellent at instantly scaffolding the `groupby().agg()` logic for the expected/actual pay aggregations.
* **Rapid UI Styling:** Generating the initial layout, dark-mode CSS variables, and flexbox structural code for the dashboard was heavily accelerated by AI. It saved hours of boilerplate styling.
* **Debugging macOS Collisions:** When the Flask server refused to run on port 5000, AI quickly identified that the macOS "AirPlay Receiver" silently occupies port 5000 and suggested fetching against `127.0.0.1` instead of `localhost` to force IPv4 resolution.

## Where AI Didn't Help (And Stumbled)
* **Contextual Nuance in Data:** The AI struggled initially with the prompt instruction: *"phone/name reflect current registered identity, not historical"*. Because the raw Pandas join returned 0 errors (historical phones technically existed as duplicate rows in `workers.csv`), the AI assumed the code was perfectly fine. It lacked the business logic context to realize that "0 errors" actually meant a single human was being tracked as two separate financial entities. 
* **Spotting Timezone Subtleties:** When instructed to look for timezone bugs, the AI initially assumed the standard `tz_convert('Asia/Kolkata')` function was sufficient. I had to manually guide it to realize that `vendor_b_v1.0` was logging `work_date` incorrectly based on raw UTC strings, requiring a hardcoded manual override inside the script.

## The Takeaway
AI was an incredible co-pilot for syntax generation and boilerplate UI, but it required constant human "steering" to navigate the intentional business-logic traps hidden in the assignment's data architecture.
