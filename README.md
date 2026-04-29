# Bharat Intelligence - Payout Reconciliation System

A full-stack tool designed to ingest worker logs, wage rates, and bank transfers to identify miscalculated wages and surface actionable discrepancies for operations teams.

## Tech Stack
* **Backend:** Python, Pandas (Data processing), Flask (API Server)
* **Frontend:** Vanilla HTML, CSS, JavaScript (Zero-build-step, fast rendering)

## How to Run Locally

### 1. Start the Backend
The backend runs on Python and Flask. It will automatically process the CSV files and start the API server on `http://127.0.0.1:5000`.

```bash
# Navigate to the backend directory
cd backend

# Activate the virtual environment
source ../.venv/bin/activate

# Run the Flask server
python app.py
```

### 2. Start the Frontend
The frontend is a static HTML page. You can serve it using Python's built-in HTTP server. Open a *new* terminal window:

```bash
# From the project root directory
python -m http.server 8080
```

Then, open your web browser and navigate to:
`http://localhost:8080/frontend/`

---
*Note: If you are on macOS and the backend fails to start with "Address already in use", you may need to disable the "AirPlay Receiver" in System Settings, as it secretly occupies port 5000.*
