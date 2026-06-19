from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'database.json')

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
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to read database file: {e}")
    return default_data

def save_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Failed to write database file: {e}")
        return False

@app.route('/api/records', methods=['GET'])
def get_records():
    return jsonify(load_db())

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
            
    db = load_db()
    db[usn_clean] = {
        "name": name,
        "marks": clean_marks
    }
    
    if save_db(db):
        return jsonify({"success": True, "message": f"Record for {usn_clean} saved successfully!"})
    else:
        return jsonify({"success": False, "message": "Failed to write database locally."}), 500

@app.route('/api/records/<usn>', methods=['DELETE'])
def delete_record(usn):
    usn_clean = usn.strip().upper()
    db = load_db()
    if usn_clean in db:
        del db[usn_clean]
        if save_db(db):
            return jsonify({"success": True, "message": f"Record {usn_clean} deleted successfully."})
        else:
            return jsonify({"success": False, "message": "Failed to write database locally."}), 500
    return jsonify({"success": False, "message": "Record not found."}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5001)
