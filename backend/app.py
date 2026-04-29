from flask import Flask, jsonify
from flask_cors import CORS
from reconcile import run_reconciliation
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Run reconciliation on startup
run_reconciliation()

@app.route('/api/reconciliation')
def get_reconciliation():
    df = pd.read_csv(os.path.join(BASE_DIR, 'reconciled_output.csv'))
    df = df.replace({np.nan: None})
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/worker-summary')
def get_worker_summary():
    df = pd.read_csv(os.path.join(BASE_DIR, 'worker_summary.csv'))
    df = df.replace({np.nan: None})
    return jsonify(df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
