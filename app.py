import os
import sqlite3
from flask import Flask, render_template, jsonify, request

app = Flask(__name__, template_folder='templates', static_folder='static')

BASE_DIR = os.path.dirname(__file__)

DATABASES = {
    'mb': {
        'id': 'mb',
        'name': 'Mid-Block Traffic Counts (MB)',
        'file': 'MB_traffic_counts_database.db',
        'path': os.path.join(BASE_DIR, 'MB_traffic_counts_database.db'),
        'description': 'Mid-Block road section counting stations'
    },
    'utc': {
        'id': 'utc',
        'name': 'U-Turn Traffic Counts (UTC)',
        'file': 'UTC_traffic_counts_database.db',
        'path': os.path.join(BASE_DIR, 'UTC_traffic_counts_database.db'),
        'description': 'U-turn intersection counting stations'
    }
}

def get_db_path(db_key):
    db_key = (db_key or 'mb').lower().strip()
    if db_key not in DATABASES:
        db_key = 'mb'
    return db_key, DATABASES[db_key]['path']

def get_db_connection(db_key='mb'):
    _, db_path = get_db_path(db_key)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/databases')
def list_databases():
    return jsonify({
        'status': 'success',
        'databases': [
            {
                'id': k,
                'name': v['name'],
                'file': v['file'],
                'description': v['description'],
                'exists': os.path.exists(v['path'])
            }
            for k, v in DATABASES.items()
        ]
    })

@app.route('/api/health')
def health():
    db_key = request.args.get('db', 'mb')
    key, path = get_db_path(db_key)
    return jsonify({
        'status': 'ok',
        'active_db': key,
        'database_file': os.path.basename(path),
        'database_exists': os.path.exists(path)
    })

@app.route('/api/summary')
def get_summary():
    try:
        db_key = request.args.get('db', 'mb').strip().lower()
        key, db_path = get_db_path(db_key)
        
        period_filter = request.args.get('period', 'all').strip().upper()
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Build SQL condition based on period parameter
        if period_filter in ['WD', 'WE']:
            p_where = " WHERE i.period = ? "
            p_params = [period_filter]
        else:
            p_where = ""
            p_params = []
            period_filter = 'ALL'

        # 1. Total counts, total records, min/max dates
        sql_summary = f"""
            SELECT 
                SUM(c.count) as total_vehicles,
                COUNT(c.id) as total_records,
                MIN(c.interval_start) as min_date,
                MAX(c.interval_end) as max_date
            FROM counts c
            JOIN imports i ON c.import_id = i.id
            {p_where}
        """
        cur.execute(sql_summary, p_params)
        summary_row = cur.fetchone()
        
        total_vehicles = summary_row['total_vehicles'] or 0
        total_records = summary_row['total_records'] or 0
        min_date = summary_row['min_date'] or ''
        max_date = summary_row['max_date'] or ''

        # 2. Distinct active stations count
        sql_stations = f"""
            SELECT COUNT(DISTINCT station_id) as total_stations 
            FROM imports i 
            {p_where}
        """
        cur.execute(sql_stations, p_params)
        total_stations = cur.fetchone()['total_stations'] or 0

        # 3. Imports count & latest import timestamp
        sql_imports = f"""
            SELECT COUNT(id) as total_imports, MAX(imported_at) as latest_import 
            FROM imports i 
            {p_where}
        """
        cur.execute(sql_imports, p_params)
        import_row = cur.fetchone()
        total_imports = import_row['total_imports'] or 0
        latest_import = import_row['latest_import'] or ''

        # 4. Counts by vehicle type
        sql_vehicles = f"""
            SELECT c.vehicle_type, SUM(c.count) as vehicle_count
            FROM counts c
            JOIN imports i ON c.import_id = i.id
            {p_where}
            GROUP BY c.vehicle_type
            ORDER BY vehicle_count DESC
        """
        cur.execute(sql_vehicles, p_params)
        vehicle_rows = cur.fetchall()
        
        by_vehicle_type = []
        top_vehicle_type = vehicle_rows[0]['vehicle_type'] if vehicle_rows else "N/A"
        
        for r in vehicle_rows:
            v_cnt = r['vehicle_count'] or 0
            pct = round((v_cnt / total_vehicles * 100), 2) if total_vehicles > 0 else 0
            by_vehicle_type.append({
                'vehicle_type': r['vehicle_type'],
                'count': v_cnt,
                'percentage': pct
            })

        # 5. Station breakdown summary
        sql_top_stations = f"""
            SELECT 
                s.station_code,
                COUNT(DISTINCT i.id) as import_count,
                SUM(c.count) as total_traffic
            FROM stations s
            JOIN imports i ON s.id = i.station_id
            JOIN counts c ON i.id = c.import_id
            {p_where}
            GROUP BY s.id
            ORDER BY total_traffic DESC
            LIMIT 10
        """
        cur.execute(sql_top_stations, p_params)
        top_stations = [
            {
                'station_code': r['station_code'],
                'import_count': r['import_count'],
                'total_traffic': r['total_traffic'] or 0
            }
            for r in cur.fetchall()
        ]

        conn.close()

        return jsonify({
            'status': 'success',
            'data': {
                'active_db': key,
                'db_name': DATABASES[key]['name'],
                'db_description': DATABASES[key]['description'],
                'active_period': period_filter,
                'total_vehicles': total_vehicles,
                'total_stations': total_stations,
                'total_records': total_records,
                'total_imports': total_imports,
                'latest_import': latest_import,
                'min_date': min_date,
                'max_date': max_date,
                'top_vehicle_type': top_vehicle_type,
                'by_vehicle_type': by_vehicle_type,
                'top_stations': top_stations
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
