# Cannae Dashboard

A Streamlit-based financial dashboard application for business development meetings.

## Project Structure

The project is organized into the following directories:

- **Root Directory**: Contains Python code files and deployment configuration
  - `cannae_dashboard.py` - Main Streamlit application
  - `cannae_report_generator.py` - PDF report generation module
  - `allocation_table.py` - Allocation data processing
  - `attribution_table.py` - Attribution data processing
  - `competitor_table.py` - Competitor data analysis

- **data/**: Contains Excel data files
  - Month-end marks files (`eom_marks_*.xlsx`)
  - Portfolio holdings files (`portfolio_holdings_*.xlsx`)
  - Trading data files (`_cannae_trade_*.xlsx`)
  - Competitor data files
  - Risk report format files

- **reports/**: Contains generated PDF reports

- **assets/**: Contains images and media files

- **scripts/**: Contains batch files for local execution
  - `run_cannae_dashboard.bat` - Script to run the dashboard locally
  - `install_dependencies.bat` - Script to install required Python packages

## Running Locally

To run the dashboard locally:

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the Streamlit application:
   ```
   streamlit run cannae_dashboard.py
   ```

   Or use the provided batch file:
   ```
   scripts\run_cannae_dashboard.bat
   ```

## Deploying to Railway

This project is configured for deployment to Railway. Railway will automatically detect the Streamlit application and deploy it.

### Deployment Steps

1. Create a Railway account at [railway.app](https://railway.app/)

2. Install the Railway CLI (optional):
   ```
   npm i -g @railway/cli
   ```

3. Deploy using one of these methods:

   **Option 1: Deploy via GitHub**
   - Connect your GitHub account to Railway
   - Select this repository to deploy
   - Railway will automatically detect the Streamlit app and deploy it

   **Option 2: Deploy via CLI**
   ```
   railway login
   railway init
   railway up
   ```

   **Option 3: Deploy via Dashboard**
   - Create a new project in the Railway dashboard
   - Connect to your GitHub repo or upload your code directly

### Configuration Files

- `requirements.txt`: Lists all Python dependencies
- `Procfile`: Tells Railway how to run the application

## Data Requirements

The dashboard expects the following data files in the `data/` directory:

1. Month-end marks file (e.g., `eom_marks_May25.xlsx`)
2. Portfolio holdings file (e.g., `portfolio_holdings_2July2025.xlsx`)
3. Trading data file (e.g., `_cannae_trade_OPPF1_2June2025_2July2025.xlsx`)
4. Competitor data file (e.g., `20250207_funds_one-pager.xlsx`)
5. Risk report format file (e.g., `Risk Report Format Master Sheet.xlsx`)

## Features

- Portfolio allocation visualization
- Trading activity monitoring
- Return attribution analysis
- Competitor benchmarking
- PDF report generation
- Interactive data exploration

## Notes for Railway Deployment

When deploying to Railway:

1. Make sure all data files are included in the repository
2. Railway will use the `Procfile` to determine how to run the application
3. The application will be accessible via a public URL provided by Railway
4. Environment variables can be configured in the Railway dashboard if needed
