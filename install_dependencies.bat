@echo off
echo Installing required packages for Cannae Dashboard...
echo.

:: Set the path to your Python executable - update this if needed
set PYTHON_PATH=python

:: Install required packages
echo Installing streamlit...
%PYTHON_PATH% -m pip install streamlit

echo Installing pandas...
%PYTHON_PATH% -m pip install pandas

echo Installing numpy...
%PYTHON_PATH% -m pip install numpy

echo Installing plotly...
%PYTHON_PATH% -m pip install plotly

echo Installing fpdf...
%PYTHON_PATH% -m pip install fpdf

echo Installing pdfplumber...
%PYTHON_PATH% -m pip install pdfplumber

echo Installing matplotlib...
%PYTHON_PATH% -m pip install matplotlib

echo Installing reportlab...
%PYTHON_PATH% -m pip install reportlab

echo.
echo Installation complete!
echo You can now run the Cannae Dashboard using run_cannae_dashboard.bat
echo.

pause
