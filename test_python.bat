@echo off
echo Testing Python installation...
echo.

python --version

IF %ERRORLEVEL% NEQ 0 (
    echo Python is not found in your PATH.
    echo Please make sure Python is installed and added to your PATH environment variable.
) ELSE (
    echo Python is properly installed and accessible.
    echo.
    echo Testing for Streamlit...
    python -c "import streamlit" 2>nul
    IF %ERRORLEVEL% NEQ 0 (
        echo Streamlit is not installed. Please run install_dependencies.bat
    ) ELSE (
        echo Streamlit is installed.
    )
)

pause
