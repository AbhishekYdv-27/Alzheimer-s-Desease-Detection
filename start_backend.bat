@echo off
cd /d "C:\Users\abhis\OneDrive\Desktop\CODING\COLLEGE PROJECT\Alzheimer's Desease Detection"
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
