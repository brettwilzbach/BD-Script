@echo off
echo Starting Cannae Dashboard...
cd /d "I:\BW Code\BD Script"
start "" http://localhost:8501
streamlit run cannae_dashboard.py
pause
