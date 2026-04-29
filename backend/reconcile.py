def run_reconciliation():
    import pandas as pd
    import re
    import os


    # 1. LOAD DATA
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')

    transfers = pd.read_csv(os.path.join(DATA_DIR, 'bank_transfers.csv'))
    logs = pd.read_csv(os.path.join(DATA_DIR, 'supervisor_logs.csv'))
    wage_rates = pd.read_csv(os.path.join(DATA_DIR, 'wage_rates.csv'))
    workers = pd.read_csv(os.path.join(DATA_DIR, 'workers.csv'))


    # 2. NORMALIZATION FUNCTIONS

    def normalize_phone(phone):
        phone = str(phone).strip()
        digits = re.sub(r'\D', '', phone) 
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        if digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]
        return digits if len(digits) == 10 else None

    def normalize_name(name):
        if pd.isna(name):
            return ''
        name = name.lower().strip()
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', ' ', name)
        return name


    # 3. CLEAN DATA

    workers['phone_norm'] = workers['phone'].apply(normalize_phone)
    logs['phone_norm'] = logs['worker_phone'].apply(normalize_phone)
    transfers['phone_norm'] = transfers['worker_phone'].apply(normalize_phone)

    workers['name_norm'] = workers['name'].apply(normalize_name)
    logs['name_norm'] = logs['worker_name'].apply(normalize_name)

    # Fill missing phones
    logs['phone_norm'] = logs['phone_norm'].fillna('UNKNOWN')
    transfers['phone_norm'] = transfers['phone_norm'].fillna('UNKNOWN')

    # Deduplicate workers by keeping the newest registered phone per canonical name
    workers['registered_on'] = pd.to_datetime(workers['registered_on'])
    workers = workers.sort_values('registered_on', ascending=False)
    
    canonical_phones = workers.groupby('name_norm')['phone_norm'].first().to_dict()
    phone_to_canonical = workers.set_index('phone_norm')['name_norm'].map(canonical_phones).to_dict()
    
    # Map all logs and transfers to their current canonical phone
    logs['phone_norm'] = logs['phone_norm'].map(phone_to_canonical).fillna(logs['phone_norm'])
    transfers['phone_norm'] = transfers['phone_norm'].map(phone_to_canonical).fillna(transfers['phone_norm'])
    
    # Keep only the newest worker record per canonical phone
    workers = workers.drop_duplicates(subset=['phone_norm'], keep='first')

    # =========================
    # 4. MATCH LOGS TO WORKERS
    # =========================
    logs_with_worker = logs.merge(
        workers[['worker_id', 'phone_norm', 'name_norm', 'state', 'role', 'seniority']],
        on='phone_norm',
        how='left',
        suffixes=('', '_worker')
    )

    logs_with_worker['review_reason'] = ''
    logs_with_worker['needs_manual_review'] = False

    # Flag unmatched workers
    mask_no_worker = logs_with_worker['worker_id'].isna()
    logs_with_worker.loc[mask_no_worker, 'review_reason'] += '|no_worker_match'
    logs_with_worker.loc[mask_no_worker, 'needs_manual_review'] = True


    # 5. TIMEZONE HANDLING

    logs_with_worker['entered_at_ist'] = pd.to_datetime(
        logs_with_worker['entered_at'], utc=True
    ).dt.tz_convert('Asia/Kolkata')

    logs_with_worker['entered_at_date'] = logs_with_worker['entered_at_ist'].dt.strftime('%Y-%m-%d')
    logs_with_worker['work_date_parsed'] = pd.to_datetime(logs_with_worker['work_date']).dt.strftime('%Y-%m-%d')

    # Overwrite work_date for vendor_b_v1.0 (they record UTC date instead of local date)
    is_vendor_b = logs_with_worker['vendor_app'] == 'vendor_b_v1.0'
    logs_with_worker.loc[is_vendor_b, 'work_date'] = logs_with_worker.loc[is_vendor_b, 'entered_at_date']
    logs_with_worker.loc[is_vendor_b, 'work_date_parsed'] = logs_with_worker.loc[is_vendor_b, 'entered_at_date']

    logs_with_worker['date_mismatch'] = (
        logs_with_worker['entered_at_date'] != logs_with_worker['work_date_parsed']
    )

    logs_with_worker.loc[logs_with_worker['date_mismatch'], 'review_reason'] += '|date_mismatch'
    logs_with_worker.loc[logs_with_worker['date_mismatch'], 'needs_manual_review'] = True


    # 6. PREPARE WAGE RATES

    wage_rates['effective_from'] = pd.to_datetime(wage_rates['effective_from'])
    wage_rates['effective_to'] = pd.to_datetime(
        wage_rates['effective_to'].fillna('2099-12-31')
    )

    # Detect if rates already in paise
    if wage_rates['hourly_rate_inr'].max() > 1000:
        rate_multiplier = 1  # already paise
    else:
        rate_multiplier = 100  # INR → paise


    # 7. RATE MATCHING FUNCTION for overlapping rates

    def get_rate_info(row):
        matches = wage_rates[
            (wage_rates['role'] == row['role']) &
            (wage_rates['state'] == row['state']) &
            (wage_rates['seniority'] == row['seniority']) &
            (wage_rates['effective_from'] <= pd.to_datetime(row['work_date'])) &
            (wage_rates['effective_to'] >= pd.to_datetime(row['work_date']))
        ]

        if len(matches) == 0:
            return pd.Series([None, 'no_rate_found'])

        if len(matches) > 1:
            rate = matches.sort_values('effective_from').iloc[-1]['hourly_rate_inr']
            return pd.Series([rate, 'overlapping_rate'])

        return pd.Series([matches.iloc[0]['hourly_rate_inr'], ''])

    logs_with_worker[['rate_inr', 'rate_issue']] = logs_with_worker.apply(get_rate_info, axis=1)

    # Flag rate issues
    logs_with_worker.loc[logs_with_worker['rate_issue'] != '', 'review_reason'] += '|' + logs_with_worker['rate_issue']
    logs_with_worker.loc[logs_with_worker['rate_issue'] != '', 'needs_manual_review'] = True


    # 8. COMPUTE EXPECTED PAY

    logs_with_worker['expected_paise'] = (
        logs_with_worker['rate_inr'] * logs_with_worker['hours'] * rate_multiplier
    ).round(0).astype('Int64')


    # 9. AGGREGATE BY MONTH

    logs_with_worker['year_month'] = pd.to_datetime(logs_with_worker['work_date']).dt.to_period('M')

    expected_by_period = logs_with_worker.groupby(['phone_norm', 'year_month']).agg(
        expected_paise=('expected_paise', 'sum'),
        shift_count=('log_id', 'count')
    ).reset_index()


    # 10. BANK AGGREGATION

    transfers['year_month'] = pd.to_datetime(transfers['transfer_timestamp']).dt.to_period('M')

    actual_by_period = transfers.groupby(['phone_norm', 'year_month']).agg(
        actual_paise=('amount_paise', 'sum')
    ).reset_index()


    # 11. RECONCILIATION

    reconciled = expected_by_period.merge(
        actual_by_period,
        on=['phone_norm', 'year_month'],
        how='outer'
    )

    reconciled['delta_paise'] = reconciled['expected_paise'] - reconciled['actual_paise']
    reconciled['delta_inr'] = reconciled['delta_paise'] / 100

    # =========================
    # 12. PROPAGATE REVIEW FLAGS
    # =========================
    review_flags = logs_with_worker.groupby(['phone_norm', 'year_month']).agg(
        review_reasons=('review_reason', lambda x: '|'.join(set(filter(None, x)))),
        needs_review=('needs_manual_review', 'max')
    ).reset_index()

    reconciled = reconciled.merge(review_flags, on=['phone_norm', 'year_month'], how='left')


    # 13. FINAL REVIEW FLAGS

    def flag_review(row):
        reasons = str(row.get('review_reasons', '')).split('|') if pd.notna(row.get('review_reasons')) else []

        if pd.isna(row['actual_paise']):
            reasons.append('no_transfer_found')
        if pd.isna(row['expected_paise']):
            reasons.append('no_expected_computed')
        if pd.notna(row['delta_paise']) and abs(row['delta_paise']) > 0:
            reasons.append('amount_mismatch')
            
        expected_p = 0 if pd.isna(row.get('expected_paise')) else float(row['expected_paise'])
        actual_p = 0 if pd.isna(row.get('actual_paise')) else float(row['actual_paise'])
        
        if expected_p > 10000000 or actual_p > 10000000:
            reasons.append('massive_amount_anomaly')

        reasons = list(set(filter(None, reasons)))

        return pd.Series([bool(reasons), '|'.join(reasons)])

    reconciled[['needs_manual_review', 'review_reason']] = reconciled.apply(flag_review, axis=1)


    # 14. CONFIDENCE SCORING

    def compute_confidence(row):
        if row['needs_manual_review']:
            return 'low'
        if pd.notna(row['delta_paise']) and abs(row['delta_paise']) > 0:
            return 'medium'
        return 'high'

    reconciled['confidence'] = reconciled.apply(compute_confidence, axis=1)

    # =========================
    # 15. WORKER SUMMARY
    # =========================
    worker_summary = reconciled.groupby('phone_norm').agg(
        total_expected=('expected_paise', 'sum'),
        total_actual=('actual_paise', 'sum'),
        total_delta=('delta_paise', 'sum'),
        periods=('year_month', 'count')
    ).reset_index()

    worker_summary['owed_inr'] = worker_summary['total_delta'] / 100

    # =========================
    # 16. SAVE OUTPUT
    # =========================
    reconciled.to_csv('reconciled_output.csv', index=False)
    worker_summary.to_csv('worker_summary.csv', index=False)

    print("Reconciliation complete")
    print("Outputs saved:")
    print("- reconciled_output.csv")
    print("- worker_summary.csv")