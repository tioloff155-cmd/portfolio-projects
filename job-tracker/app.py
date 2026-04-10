from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import os

app = Flask(__name__, static_folder='frontend', static_url_path='')
DB_PATH = 'jobs.db'

if not os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            position TEXT,
            status TEXT,
            priority TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()


def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv


@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    rows = query_db('SELECT * FROM jobs ORDER BY id DESC')
    jobs = [dict(row) for row in rows]
    return jsonify(jobs)


@app.route('/api/jobs', methods=['POST'])
def add_job():
    data = request.get_json()
    query_db(
        'INSERT INTO jobs (company, position, status, priority, notes) VALUES (?, ?, ?, ?, ?)',
        (data['company'], data['position'], data['status'], data['priority'], data['notes'])
    )
    return jsonify({'success': True}), 201


@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    query_db('DELETE FROM jobs WHERE id = ?', (job_id,))
    return jsonify({'success': True})


@app.route('/api/jobs/export', methods=['GET'])
def export_jobs():
    rows = query_db('SELECT company, position, status, priority, notes FROM jobs')
    lines = ['company,position,status,priority,notes']
    for row in rows:
        values = [str(row[col]).replace(',', ' ') for col in row.keys()]
        lines.append(','.join(values))
    response = app.response_class('\n'.join(lines), mimetype='text/csv')
    response.headers.set('Content-Disposition', 'attachment', filename='jobs.csv')
    return response


if __name__ == '__main__':
    app.run(debug=True)
