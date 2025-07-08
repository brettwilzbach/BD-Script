@echo off
echo Starting Cannae Dashboard...
echo.

:: Set the path to your Python executable - update this if needed
set PYTHON_PATH=python

:: Run Streamlit in the foreground to see any errors
echo Running Streamlit (this will show any errors)...
echo If Streamlit starts successfully, you can visit http://localhost:8501 in your browser
echo.

%PYTHON_PATH% -m streamlit run "I:\BW Code\BD Script\cannae_dashboard.py"

:: If we get here, something went wrong
echo.
echo If you see errors above, please fix them and try again.
echo If Streamlit started successfully, you can close this window.

pause
