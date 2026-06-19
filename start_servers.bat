@echo off
echo Starting Student Record Management System...

echo Installing requirements...
pip install -r requirements.txt

echo Launching Main Application Server (Port 5000)...
python app.py

pause
