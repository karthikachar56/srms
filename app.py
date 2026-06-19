from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import json
import os

app = Flask(__name__)

# Serverless path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'database.json')
INDEX_FILE = os.path.join(BASE_DIR, 'index.html')
ADMIN_LOGIN_FILE = os.path.join(BASE_DIR, 'admin login.html')
ADMIN_PANEL_FILE = os.path.join(BASE_DIR, 'admin panel.html')
RESULT_SHEET_FILE = os.path.join(BASE_DIR, 'result sheet.html')

# Helper function to load database
def load_db():
    if not os.path.exists(DB_FILE):
        # Initialize default record matching your original HTML
        default_data = {
            "1SP25CS001": {
                "name": "Karthik D",
                "marks": {
                    "Mathematics": 88,
                    "Data Structures": 92,
                    "OOPs (Java)": 85,
                    "Computer Arch.": 79,
                    "Basic Electrical": 90
                }
            }
        }
        try:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=4)
        except Exception as e:
            # Fallback to returning default data if write fails (e.g. read-only filesystem on Vercel)
            return default_data
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        # Emergency fallback database if reading fails or file is corrupted
        return {
            "1SP25CS001": {
                "name": "Karthik D",
                "marks": {
                    "Mathematics": 88,
                    "Data Structures": 92,
                    "OOPs (Java)": 85,
                    "Computer Arch.": 79,
                    "Basic Electrical": 90
                }
            }
        }

# Helper function to save database
def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# 1. Routes to serve Main Pages
@app.route('/')
@app.route('/login')
def student_login():
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/admin-login')
def admin_login_page():
    with open(ADMIN_LOGIN_FILE, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/admin')
def admin_panel():
    with open(ADMIN_PANEL_FILE, 'r', encoding='utf-8') as f:
        return f.read()

# 2. API Route to get all active records (for loading table on startup)
@app.route('/api/records', methods=['GET'])
def get_records():
    return jsonify(load_db())

# 3. API Route to check if a specific USN exists in the database
@app.route('/api/records/<usn>/exists', methods=['GET'])
def check_student_exists(usn):
    db = load_db()
    usn_clean = usn.strip().upper()
    if usn_clean in db:
        return jsonify({"exists": True, "name": db[usn_clean]["name"]})
    return jsonify({"exists": False}), 404

# 4. API Route to save or update student records
@app.route('/api/records', methods=['POST'])
def save_record():
    data = request.json or {}
    usn = data.get('usn')
    name = data.get('name')
    marks = data.get('marks')
    
    if not usn or not name:
        return jsonify({"success": False, "message": "USN and Name are required fields."}), 400
        
    db = load_db()
    db[usn] = {
        "name": name,
        "marks": marks
    }
    
    try:
        save_db(db)
        return jsonify({"success": True, "message": f"Record for {usn} updated successfully!"})
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"Database is read-only (Vercel Serverless environment). Local updates are not persistent. Error: {str(e)}"
        }), 500

# 5. API Route to delete student records
@app.route('/api/records/<usn>', methods=['DELETE'])
def delete_record(usn):
    db = load_db()
    if usn in db:
        del db[usn]
        try:
            save_db(db)
            return jsonify({"success": True, "message": f"Record {usn} deleted."})
        except Exception as e:
            return jsonify({
                "success": False, 
                "message": f"Database is read-only (Vercel Serverless environment). Deletion failed. Error: {str(e)}"
            }), 500
    return jsonify({"success": False, "message": "Record not found."}), 404

# 6. API Route for Secure Admin Login
@app.route('/api/admin/login', methods=['POST'])
def admin_login_api():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    if username == "SRMS" and password == "1234567":
        return jsonify({"success": True, "message": "Authentication successful!"})
    return jsonify({"success": False, "message": "Invalid Username or Password."}), 401

# 7. Route to dynamically generate and display the Result Sheet
@app.route('/result')
def result_sheet():
    usn = request.args.get('usn', '').strip().upper()
    db = load_db()
    
    if usn not in db:
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Record Not Found</title>
            <style>
                body {{
                    background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
                    height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                }}
                .error-card {{
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
                    text-align: center;
                    max-width: 400px;
                    width: 90%;
                }}
                .icon {{
                    font-size: 48px;
                    color: #ef4444;
                    margin-bottom: 20px;
                }}
                h2 {{
                    color: #1f2937;
                    margin-top: 0;
                    margin-bottom: 10px;
                }}
                p {{
                    color: #6b7280;
                    font-size: 15px;
                    line-height: 1.5;
                    margin-bottom: 25px;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    transition: background-color 0.2s;
                }}
                .btn:hover {{
                    background-color: #5a67d8;
                }}
            </style>
        </head>
        <body>
            <div class="error-card">
                <div class="icon">🔍❌</div>
                <h2>Record Not Found</h2>
                <p>Student record for USN <strong>{usn}</strong> could not be found. Please check the USN and try again.</p>
                <a href="/" class="btn">Go Back to Login</a>
            </div>
        </body>
        </html>
        """, 404
    
    student = db[usn]
    marks = student['marks']
    
    # Calculate performance metrics
    total_marks = sum(int(m) for m in marks.values())
    max_possible = len(marks) * 100
    percentage = (total_marks / max_possible) * 100 if max_possible > 0 else 0
    status = "PASS" if all(int(m) >= 35 for m in marks.values()) else "FAIL" # standard 35 pass mark
    
    # Generate table rows dynamically
    # Assigning dummy subject codes derived loosely from names
    codes = ["22CSE11", "22CSE12", "22CSE13", "22CSE14", "22CSE15"]
    table_rows = ""
    for idx, (sub_name, sub_mark) in enumerate(marks.items()):
        code = codes[idx] if idx < len(codes) else f"22CSE{11+idx}"
        table_rows += f"""
        <tr>
            <td>{code}</td>
            <td>{sub_name}</td>
            <td>100</td>
            <td>{sub_mark}</td>
        </tr>
        """

    # Read original result sheet markup and inject values natively using Python template processing
    with open(RESULT_SHEET_FILE, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Modify the HTML script block handling so it displays the fetched data seamlessly
    html_content = html_content.replace('<strong id="displayName">Loading...</strong>', f'<strong id="displayName">{student["name"]}</strong>')
    html_content = html_content.replace('<strong id="displayUsn">Loading...</strong>', f'<strong id="displayUsn">{usn}</strong>')
    
    # Replace hardcoded table body content
    start_tbody = html_content.find('<tbody>') + 7
    end_tbody = html_content.find('</tbody>')
    html_content = html_content[:start_tbody] + table_rows + html_content[end_tbody:]
    
    # Update metrics values dynamically 
    html_content = html_content.replace('<div class="metric-value">434 / 500</div>', f'<div class="metric-value">{total_marks} / {max_possible}</div>')
    html_content = html_content.replace('<div class="metric-value">86.8%</div>', f'<div class="metric-value">{percentage:.1f}%</div>')
    
    if status == "FAIL":
        html_content = html_content.replace('class="status-pass">PASS', 'style="background:#fed7d7; color:#c53030;" class="status-pass">FAIL')

    return html_content

if __name__ == '__main__':
    app.run(debug=True, port=5000)