import os
import sys
import socket
import pandas as pd
import traceback

# Print environment information for debugging
print("=== Railway Debug Information ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")
print(f"PORT environment variable: {os.environ.get('PORT', 'Not set')}")

# Check if data directory exists
if os.path.exists('data'):
    print(f"Data directory exists. Contents: {os.listdir('data')}")
    
    # Try to read each Excel file
    excel_files = [f for f in os.listdir('data') if f.endswith('.xlsx') or f.endswith('.xls')]
    print(f"Found {len(excel_files)} Excel files: {excel_files}")
    
    for excel_file in excel_files:
        file_path = os.path.join('data', excel_file)
        print(f"Attempting to read {file_path}...")
        try:
            # Try to read the Excel file and get sheet names
            excel = pd.ExcelFile(file_path)
            print(f"  Success! Sheets in {excel_file}: {excel.sheet_names}")
            
            # Try to read the first sheet as a test
            first_sheet = excel.sheet_names[0]
            df = pd.read_excel(excel, sheet_name=first_sheet)
            print(f"  Successfully read first sheet '{first_sheet}' with {len(df)} rows and {len(df.columns)} columns")
            print(f"  Column names: {df.columns.tolist()}")
        except Exception as e:
            print(f"  ERROR reading {excel_file}: {str(e)}")
            print(traceback.format_exc())
else:
    print("ERROR: Data directory does not exist!")

# Test port binding
port = int(os.environ.get('PORT', 8501))
print(f"Testing if port {port} is available...")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", port))
    s.listen(1)
    print(f"Successfully bound to port {port}")
    s.close()
except Exception as e:
    print(f"ERROR binding to port {port}: {str(e)}")
    print("This could mean the port is already in use or there's a permission issue")

print("=== End Debug Information ===")

# Continue with normal Streamlit import and execution
import streamlit as st

st.title("Railway Debug Page")
st.write("If you can see this, your Streamlit app is running correctly!")
st.write(f"Current working directory: {os.getcwd()}")

# Display directory structure
st.subheader("Directory Structure")
dir_structure = {}
for root, dirs, files in os.walk('.', topdown=True, followlinks=False):
    if '.git' in root or '__pycache__' in root:
        continue
    if root == '.':
        dir_structure['files'] = files
        for d in dirs:
            if d != '.git' and d != '__pycache__':
                dir_structure[d] = {'files': os.listdir(d) if os.path.exists(d) else []}
    elif root.count(os.sep) == 1 and not root.startswith('./.git'):
        parent = root.split(os.sep)[1]
        dir_structure[parent]['files'] = files

st.json(dir_structure)

# Display Excel file information
st.subheader("Excel Files")
if os.path.exists('data'):
    excel_files = [f for f in os.listdir('data') if f.endswith('.xlsx') or f.endswith('.xls')]
    for excel_file in excel_files:
        file_path = os.path.join('data', excel_file)
        st.write(f"**{excel_file}**")
        try:
            excel = pd.ExcelFile(file_path)
            st.write(f"Sheets: {', '.join(excel.sheet_names)}")
            
            # Show preview of first sheet
            first_sheet = excel.sheet_names[0]
            df = pd.read_excel(excel, sheet_name=first_sheet)
            st.write(f"First sheet '{first_sheet}' preview:")
            st.dataframe(df.head(5))
        except Exception as e:
            st.error(f"Error reading {excel_file}: {str(e)}")
else:
    st.error("Data directory does not exist!")

# Display environment variables (excluding secrets)
st.subheader("Environment Variables")
env_vars = {k: v for k, v in os.environ.items() if not ('key' in k.lower() or 'secret' in k.lower() or 'password' in k.lower() or 'token' in k.lower())}
st.json(env_vars)
