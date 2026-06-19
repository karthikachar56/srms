from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import json
import os
from pymongo import MongoClient

app = Flask(__name__)

# Serverless path resolution for static assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_DIR, 'index.html')
ADMIN_LOGIN_FILE = os.path.join(BASE_DIR, 'admin login.html')
ADMIN_PANEL_FILE = os.path.join(BASE_DIR, 'admin panel.html')
RESULT_SHEET_FILE = os.path.join(BASE_DIR, 'result sheet.html')

def get_local_db_path():
    # If running on Vercel or in a read-only environment, write local fallback to /tmp
    if os.environ.get("VERCEL") or not os.access(BASE_DIR, os.W_OK):
        path = '/tmp/database.json'
        
        # If the file doesn't exist in /tmp, copy the default database.json from BASE_DIR if it exists
        if not os.path.exists(path):
            orig_path = os.path.join(BASE_DIR, 'database.json')
            if os.path.exists(orig_path):
                try:
                    import shutil
                    shutil.copyfile(orig_path, path)
                except Exception:
                    pass
        return path
    return os.path.join(BASE_DIR, 'database.json')

# MongoDB Connection Initialization
# Read from environment MONGO_URI (e.g. for Vercel) or fall back to connection string
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://achark659_db:achark659_db@cluster0.qqxk8gr.mongodb.net/")
try:
    # Set tlsAllowInvalidCertificates=True to bypass local SSL/TLS certificate scanning errors
    mongo_client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
    db_mongo = mongo_client["srms_db"]
    records_collection = db_mongo["student_records"]
except Exception as e:
    print(f"MongoDB connection failed to initialize: {e}")
    records_collection = None

# Helper function to load database
def load_db():
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
    
    # 1. Try loading from MongoDB Collection
    if records_collection is not None:
        try:
            cursor = records_collection.find({})
            db_data = {}
            for doc in cursor:
                usn = doc["_id"]
                db_data[usn] = {
                    "name": doc["name"],
                    "marks": doc["marks"]
                }
            
            # Seed collection if first successful connect
            if not db_data:
                records_collection.insert_one({
                    "_id": "1SP25CS001",
                    "name": "Karthik D",
                    "marks": default_data["1SP25CS001"]["marks"]
                })
                return default_data
                
            return db_data
        except Exception as e:
            print(f"MongoDB Load failed, falling back to local file: {e}")

    # 2. Fallback to local database.json file
    LOCAL_DB = get_local_db_path()
    if os.path.exists(LOCAL_DB):
        try:
            with open(LOCAL_DB, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as file_err:
            print(f"Failed to read local fallback database: {file_err}")
            
    return default_data

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
        
    usn_clean = usn.strip().upper()
    clean_marks = {}
    if marks:
        for sub, val in marks.items():
            clean_marks[sub] = int(val)
            
    # 1. Try saving to MongoDB Collection
    if records_collection is not None:
        try:
            records_collection.update_one(
                {"_id": usn_clean},
                {"$set": {"name": name, "marks": clean_marks}},
                upsert=True
            )
            return jsonify({"success": True, "message": f"Record for {usn_clean} updated successfully in MongoDB!"})
        except Exception as e:
            print(f"MongoDB save failed, falling back to local file: {e}")
            
    # 2. Fallback to local database.json file
    try:
        LOCAL_DB = get_local_db_path()
        local_db_data = {}
        if os.path.exists(LOCAL_DB):
            with open(LOCAL_DB, 'r', encoding='utf-8') as f:
                local_db_data = json.load(f)
        
        local_db_data[usn_clean] = {
            "name": name,
            "marks": clean_marks
        }
        
        with open(LOCAL_DB, 'w', encoding='utf-8') as f:
            json.dump(local_db_data, f, indent=4)
            
        return jsonify({
            "success": True,
            "message": f"Record for {usn_clean} saved successfully locally (Fallback: MongoDB is offline/unreachable)."
        })
    except Exception as file_err:
        return jsonify({
            "success": False,
            "message": f"Failed to save record: MongoDB is unreachable AND local file save failed. Details: {str(file_err)}"
        }), 500

# 5. API Route to delete student records
@app.route('/api/records/<usn>', methods=['DELETE'])
def delete_record(usn):
    usn_clean = usn.strip().upper()
    
    # 1. Try deleting from MongoDB Collection
    if records_collection is not None:
        try:
            result = records_collection.delete_one({"_id": usn_clean})
            if result.deleted_count > 0:
                return jsonify({"success": True, "message": f"Record {usn_clean} deleted from MongoDB."})
            # If not found in MongoDB, we check if it is in the local fallback file before returning 404
        except Exception as e:
            print(f"MongoDB delete failed, falling back to local file: {e}")
            
    # 2. Fallback to local database.json file
    try:
        LOCAL_DB = get_local_db_path()
        if os.path.exists(LOCAL_DB):
            with open(LOCAL_DB, 'r', encoding='utf-8') as f:
                local_db_data = json.load(f)
                
            if usn_clean in local_db_data:
                del local_db_data[usn_clean]
                with open(LOCAL_DB, 'w', encoding='utf-8') as f:
                    json.dump(local_db_data, f, indent=4)
                return jsonify({"success": True, "message": f"Record {usn_clean} deleted locally."})
        return jsonify({"success": False, "message": "Record not found locally or on MongoDB."}), 404
    except Exception as file_err:
        return jsonify({
            "success": False,
            "message": f"Failed to delete record: MongoDB failed AND local file delete failed. Details: {str(file_err)}"
        }), 500

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