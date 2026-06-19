@echo off
echo Starting Student Record Management System...

echo Installing requirements...
pip install -r requirements.txt

echo Launching Database Microservice (Port 5001)...
start "SRMS Database Server" cmd /k "python db_server.py"

echo Launching Main Application Server (Port 5000)...
start "SRMS App Server" cmd /k "python app.py"

echo Both servers launched successfully!
echo - Admin panel: http://127.0.0.1:5000/admin
echo - Student portal: http://127.0.0.1:5000/
pause
