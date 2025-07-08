import os
import sys

# Print environment information for debugging
print("=== Railway Debug Information ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")
print(f"PORT environment variable: {os.environ.get('PORT', 'Not set')}")
print("=== End Debug Information ===")

# Continue with normal Streamlit import and execution
import streamlit as st

st.title("Railway Debug Page")
st.write("If you can see this, your Streamlit app is running correctly!")
st.write(f"Current working directory: {os.getcwd()}")
st.write(f"Files in directory: {', '.join(os.listdir('.'))}")

# Display environment variables (excluding secrets)
st.subheader("Environment Variables")
env_vars = {k: v for k, v in os.environ.items() if not ('key' in k.lower() or 'secret' in k.lower() or 'password' in k.lower() or 'token' in k.lower())}
st.json(env_vars)
