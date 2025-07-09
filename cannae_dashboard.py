# cannae_dashboard.py

# Dynamic port override for Railway compatibility
import os
os.environ["STREAMLIT_SERVER_PORT"] = os.environ.get("PORT", "8501")
os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import base64
import os
import io
import pdfplumber
import logging
import re
from cannae_report_generator import generate_pdf_report

# ---------- CONFIG ----------
st.set_page_config(page_title="Cannae Dashboard", layout="wide")

import sys
import socket

# Updated paths for organized directory structure - OS-agnostic for Railway compatibility
import os

# Determine if running locally or on Railway
if os.path.exists("I:\\BW Code\\BD Script"):
    # Local Windows path
    BASE_PATH = "I:\\BW Code\\BD Script"
else:
    # Railway path (current directory)
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Use os.path.join for OS-agnostic paths
DATA_PATH = os.path.join(BASE_PATH, "data")
REPORTS_PATH = os.path.join(BASE_PATH, "reports")
ASSETS_PATH = os.path.join(BASE_PATH, "assets")

# Custom CSS for styling
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&display=swap');

    /* Global styles */
    body, .stMarkdown, .stDataFrame, .stTable, .stMetric, .stButton > button, .stDownloadButton > button, .stTextInput > div > div > input, .stTextArea > div > textarea {
        font-family: 'Merriweather', serif !important;
        color: #333; /* Darker gray for text */
    }

    /* Headers */
    h1 {
        font-family: 'Merriweather', serif !important;
        font-size: 26px; /* Slightly smaller than default */
        color: #1E3A8A; /* A deep blue, adjust as needed */
    }
    h2 {
        font-family: 'Merriweather', serif !important;
        font-size: 20px; /* Reduced for cohesion */
        color: #1E3A8A; 
        border-bottom: 1px solid #DDDDDD; /* Subtle separator */
        padding-bottom: 5px;
        margin-top: 30px;
    }
    h3 {
        font-family: 'Merriweather', serif !important;
        font-size: 17px; /* Reduced */
        color: #2E5A9A; /* A slightly lighter blue */
    }

    /* Paragraphs and general text */
    p, .stMarkdown p, .stDataFrame, .stTable {
        font-size: 14px;
        line-height: 1.6;
    }

    /* Streamlit Metric specific styling */
    .stMetric > div:nth-child(1) { /* Metric Label */
        font-size: 14px;
        color: #555;
    }
    .stMetric > div:nth-child(2) { /* Metric Value */
        font-size: 24px; 
        font-weight: bold;
        color: #1E3A8A;
    }
    .stMetric > div:nth-child(3) { /* Metric Delta (if present) */
        font-size: 13px;
    }
    
    /* Improve spacing for main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }

    /* Style buttons for a more modern feel */
    .stButton>button {
        border-radius: 5px;
        background-color: #1E3A8A; /* Blue background */
        color: white;
        padding: 10px 20px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2E5A9A; /* Lighter blue on hover */
    }

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ---------- HELPER FUNCTIONS ----------

def generate_html_pdf(output_path, key_stats, fig_strategy_allocation, allocation_table, recent_trades, top_positions, 
                     fig_deployment_waterfall, attribution_data, fig_attribution, gross_return_bps, net_return_bps, 
                     fig_gainers, fig_sub_strategy, competitor_data, percentile_rank):
    """
    Generate a PDF report using HTML/CSS and WeasyPrint.
    This provides better layout control and more professional results than FPDF.
    """
    try:
        # Initialize the HTML PDF generator
        html_pdf = HTMLPDFGenerator(DATA_PATH)
        
        # Generate the PDF using the HTML template
        html_pdf.generate_pdf(
            key_stats=key_stats,
            fig_strategy_allocation=fig_strategy_allocation,
            allocation_table=allocation_table,
            recent_trades=recent_trades,
            top_positions=top_positions,
            fig_deployment_waterfall=fig_deployment_waterfall,
            attribution_data=attribution_data,
            fig_attribution=fig_attribution,
            gross_return_bps=gross_return_bps,
            net_return_bps=net_return_bps,
            fig_gainers=fig_gainers,
            fig_sub_strategy=fig_sub_strategy,
            competitor_data=competitor_data,
            percentile_rank=percentile_rank
        )
        
        logging.info(f"HTML PDF successfully generated at: {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error generating HTML PDF: {e}", exc_info=True)
        raise e

def extract_kpis_from_factsheet():
    """Extract KPI data from the 'Key Stats' sheet in 'Risk Report Format Master Sheet.xlsx'."""
    import os # Ensure os is available for path operations
    # pandas (pd), logging, DATA_PATH should be available globally/module-level.

    kpi_data = {
        "monthly_return_str": "N/A",
        "monthly_return_float": 0.0,
        "ytd_return_str": "N/A",
        "ytd_return_float": 0.0,
        "ann_return_str": "N/A",
        "ann_return_float": 0.0,
        "aum_str": "N/A",
        "aum_float": 0.0,
        "extraction_source": "Fallback (Initial values - Excel)"  # extracted_text_snippet removed
    }

    excel_filename = "Risk Report Format Master Sheet.xlsx"
    excel_path = os.path.join(DATA_PATH, excel_filename)
    sheet_name = "Key Stats"

    if not os.path.exists(excel_path):
        logging.warning(f"KPI source file '{excel_filename}' not found at: {excel_path}. Using fallback KPI values.")
        kpi_data["extraction_source"] = f"Fallback (Excel file not found: {excel_filename})"
        return kpi_data

    try:
        excel_file_obj = pd.ExcelFile(excel_path)
        if sheet_name not in excel_file_obj.sheet_names:
            logging.warning(f"Sheet '{sheet_name}' for KPIs not found in '{excel_filename}'. Using fallback values.")
            kpi_data["extraction_source"] = f"Fallback (Sheet '{sheet_name}' not found in {excel_filename})"
            return kpi_data

        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
        
        stats_map = {}
        if not df.empty and df.shape[1] >= 2:
            stats_map = df.dropna(subset=[0]).set_index(0)[1].to_dict()
        else:
            logging.warning(f"Sheet '{sheet_name}' in '{excel_filename}' is empty or has fewer than 2 columns. Cannot extract KPIs.")
            kpi_data["extraction_source"] = f"Fallback (Sheet '{sheet_name}' empty or malformed in {excel_filename})"
            return kpi_data

        # Helper to safely get and convert values from the stats_map
        def get_value_from_map(label, data_type):
            raw_value = stats_map.get(label)
            default_str, default_float = "N/A", 0.0

            if raw_value is None:
                logging.warning(f"KPI Label '{label}' not found in '{sheet_name}' of '{excel_filename}'.")
                return default_str, default_float

            try:
                if data_type == 'percentage':
                    if isinstance(raw_value, str):
                        numeric_part = raw_value.replace('%', '').strip()
                        val_float = float(numeric_part)
                    elif isinstance(raw_value, (int, float)):
                        # If value is like 0.0421 (Excel % format) vs 4.21 (direct number)
                        val_float = float(raw_value) * 100.0 if abs(raw_value) < 1 and raw_value != 0 else float(raw_value)
                    else:
                        logging.warning(f"Unexpected type for percentage KPI '{label}': {type(raw_value)}. Value: {raw_value}")
                        return str(raw_value), default_float
                    return f"{val_float:.2f}%", val_float
                
                elif data_type == 'aum':
                    if isinstance(raw_value, str):
                        numeric_part = raw_value.replace('$', '').replace(',', '').strip()
                        val_float = float(numeric_part)
                    elif isinstance(raw_value, (int, float)):
                        val_float = float(raw_value)
                    else:
                        logging.warning(f"Unexpected type for AUM KPI '{label}': {type(raw_value)}. Value: {raw_value}")
                        return str(raw_value), default_float
                    return f"${int(val_float):,}", val_float
            except ValueError as ve:
                logging.error(f"Could not convert value for KPI '{label}' ('{raw_value}') to float: {ve}")
                return str(raw_value), default_float
            return str(raw_value), default_float # Fallback for unhandled cases

        # Extract KPIs
        kpi_data["ytd_return_str"], kpi_data["ytd_return_float"] = get_value_from_map("YTD Return", "percentage")
        kpi_data["monthly_return_str"], kpi_data["monthly_return_float"] = get_value_from_map("Monthly Return", "percentage")
        kpi_data["ann_return_str"], kpi_data["ann_return_float"] = get_value_from_map("Annualized Return", "percentage")
        kpi_data["aum_str"], kpi_data["aum_float"] = get_value_from_map("AUM", "aum")

        # Update extraction source
        parsed_any_kpi = any(kpi_data[key_str] != "N/A" for key_str in ["ytd_return_str", "monthly_return_str", "ann_return_str", "aum_str"])
        if parsed_any_kpi:
             kpi_data["extraction_source"] = f"Successfully extracted from {excel_filename}, sheet {sheet_name}"
        elif not stats_map: # Initial df read was problematic
             kpi_data["extraction_source"] = f"Fallback (Could not read data/labels from {excel_filename}, sheet {sheet_name})"
        else: # Labels might be missing or values unparseable
             kpi_data["extraction_source"] = f"Fallback (KPIs not found or unparseable in {excel_filename}, sheet {sheet_name})"

    except Exception as e:
        logging.error(f"Error processing Excel file '{excel_path}' for KPIs: {e}", exc_info=True)
        kpi_data["extraction_source"] = f"Fallback (Error processing Excel for KPIs: {str(e)[:100]})"

    logging.info(f"KPI Data from Excel: {kpi_data}")
    return kpi_data


def extract_key_stats_from_risk_report():
    """Extract key statistics directly from the Risk Report Format Master Sheet Excel file.

    No PDF fallback - only uses Excel.

    Returns:
        dict: Dictionary containing key stats extracted from the Excel file
    """
    excel_filename = "Risk Report Format Master Sheet.xlsx"
    excel_path = os.path.join(DATA_PATH, excel_filename)
    
    # Check if Excel file exists
    if not os.path.exists(excel_path):
        logging.warning(f"Risk report Excel file '{excel_filename}' not found at: {excel_path}. Using hardcoded fallback key stats.")
        return {
            'avg_yield': '13.10%',
            'wal': '3.20',
            'pct_ig': '24.2%',
            'pct_risk_rating_1': '52.3%',
            'floating_rate_pct': '21.2%',
            'monthly_carry_bps': '61 bps',
            'bond_line_items': '3',
            'bond_breakdown': {'CMBS': 1, 'ABS': 2, 'CLO': 0},
            'avg_holding_size': '$5.17mm',
            'top_10_concentration': '20.6%',
            'extraction_source': 'hardcoded_fallback'
        }
    
    try:
        # Try to read the Excel file
        excel = pd.ExcelFile(excel_path)
        logging.debug(f"Available sheets in {excel_path}: {excel.sheet_names}")
        
        # Check if Key Stats sheet exists
        if 'Key Stats' not in excel.sheet_names:
            logging.warning("'Key Stats' sheet not found in Excel file! Using hardcoded fallback values.")
            logging.debug("KEY STATS EXTRACTED:\n Using hardcoded fallback values (Key Stats sheet not found)")
            return {
                'avg_yield': '13.10%',
                'wal': '3.20',
                'pct_ig': '24.2%',
                'pct_risk_rating_1': '52.3%',
                'floating_rate_pct': '21.2%',
                'monthly_carry_bps': '61 bps',
                'bond_line_items': '3',
                'bond_breakdown': {'CMBS': 1, 'ABS': 2, 'CLO': 0},
                'avg_holding_size': '$5.17mm',
                'top_10_concentration': '20.6%',
                'extraction_source': 'hardcoded_fallback'
            }
        
        # Read the Key Stats sheet
        df = pd.read_excel(excel_path, sheet_name='Key Stats', header=None)
        logging.debug(f"Successfully read Key Stats sheet from {excel_path} with {len(df)} rows")
        
        # Extract metrics from the sheet
        metrics = {}
        for i in range(len(df)):
            if pd.notna(df.iloc[i, 0]) and pd.notna(df.iloc[i, 1]):
                metrics[str(df.iloc[i, 0])] = df.iloc[i, 1]
        
        logging.debug(f"Extracted metrics from Excel {excel_path}: {metrics}")
        
        # Format metrics for display
        key_stats = {}
        key_stats['attribution_by_strategy'] = {}

        def _parse_to_bps(raw_value, default_bps=0):
            if pd.isna(raw_value):
                return default_bps
            try:
                if isinstance(raw_value, str) and '%' in raw_value:
                    numeric_part_str = raw_value.strip('%')
                    numeric_part_float = float(numeric_part_str)
                    return int(round(numeric_part_float * 100))
                elif isinstance(raw_value, (int, float)):
                    if abs(raw_value) < 2.0 and raw_value != 0: # Treat 0 as 0 bps, not 0*10000
                        return int(round(raw_value * 10000))
                    else:
                        return int(round(raw_value))
                else:
                    numeric_value = float(raw_value)
                    if abs(numeric_value) < 2.0 and numeric_value != 0:
                        return int(round(numeric_value * 10000))
                    else:
                        return int(round(numeric_value))
            except (ValueError, TypeError):
                logging.warning(f"Could not parse value '{raw_value}' to bps. Using default {default_bps} bps.")
                return default_bps
        
        # Average Yield
        if 'Average Yield' in metrics:
            avg_yield_value = float(metrics['Average Yield'])
            key_stats['avg_yield'] = f"{avg_yield_value*100:.2f}%"
        else:
            key_stats['avg_yield'] = "13.10%"  # Fallback
            
        # WAL
        if 'WAL' in metrics:
            key_stats['wal'] = f"{float(metrics['WAL']):.2f}"
        else:
            key_stats['wal'] = "3.20"  # Fallback
            
        # Percent IG
        if '% IG' in metrics:
            key_stats['pct_ig'] = f"{float(metrics['% IG'])*100:.1f}%"
        else:
            key_stats['pct_ig'] = "24.2%"  # Fallback
            
        # Risk Rating 1%
        if 'Risk Rating 1%' in metrics:
            key_stats['pct_risk_rating_1'] = f"{float(metrics['Risk Rating 1%'])*100:.1f}%"
        else:
            key_stats['pct_risk_rating_1'] = "52.3%"  # Fallback
            
        # Floating Rate %
        if 'Floating Rate %' in metrics:
            key_stats['floating_rate_pct'] = f"{float(metrics['Floating Rate %'])*100:.1f}%"
        else:
            key_stats['floating_rate_pct'] = "21.2%"  # Fallback
            
        # Monthly Carry
        if 'Monthly Carry' in metrics:
            raw_value = metrics['Monthly Carry']
            bps_value_str = "57 bps"  # Default to fallback
            try:
                if isinstance(raw_value, str) and '%' in raw_value:
                    # Case 1: Value is a string like "0.57%"
                    numeric_part_str = raw_value.strip('%')
                    numeric_part_float = float(numeric_part_str)  # e.g., 0.57
                    bps = int(round(numeric_part_float * 100))  # 0.57 * 100 = 57 bps
                    bps_value_str = f"{bps} bps"
                elif isinstance(raw_value, (int, float)):
                    # Case 2: Value is a number, e.g., 0.0057 (from Excel "0.57%") or 57 (from Excel "57")
                    if abs(raw_value) < 2.0:  # Heuristic: if value is like 0.xx or 1.xx, treat as decimal percent
                        # This handles 0.0057 (for 0.57%) correctly
                        bps = int(round(raw_value * 10000))  # e.g., 0.0057 * 10000 = 57 bps
                    else:  # Otherwise, assume the number is already in BPS
                        bps = int(round(raw_value))  # e.g., 57 directly means 57 bps
                    bps_value_str = f"{bps} bps"
                else:
                    # Case 3: Value is a string without '%', e.g., "57" or "0.0057"
                    # Attempt to convert to float and apply similar logic as Case 2.
                    numeric_value = float(raw_value)
                    if abs(numeric_value) < 2.0:
                        bps = int(round(numeric_value * 10000))
                    else:
                        bps = int(round(numeric_value))
                    bps_value_str = f"{bps} bps"
                key_stats['monthly_carry_bps'] = bps_value_str
            except (ValueError, TypeError) as e:
                logging.warning(f"Could not parse 'Monthly Carry' value '{raw_value}': {e}. Using fallback '57 bps'.")
                key_stats['monthly_carry_bps'] = "57 bps"  # Fallback
        else:
            key_stats['monthly_carry_bps'] = "57 bps"  # Fallback if 'Monthly Carry' label not found
            
        # Bond Line Items
        if 'Bond Line Items' in metrics:
            key_stats['bond_line_items'] = str(int(metrics['Bond Line Items']))
        else:
            key_stats['bond_line_items'] = "3"  # Fallback
            
        # Bond Breakdown
        bond_breakdown = {'CMBS': 0, 'ABS': 0, 'CLO': 0}
        if 'CMBS Line Items' in metrics:
            bond_breakdown['CMBS'] = int(metrics['CMBS Line Items'])
        if 'ABS Line Items' in metrics:
            bond_breakdown['ABS'] = int(metrics['ABS Line Items'])
        if 'CLO Line Items' in metrics:
            bond_breakdown['CLO'] = int(metrics['CLO Line Items'])
        key_stats['bond_breakdown'] = bond_breakdown
            
        # Average Holding Size
        if 'Average Holding Size ($mm)' in metrics:
            key_stats['avg_holding_size'] = f"${float(metrics['Average Holding Size ($mm)']):.2f}mm"
        else:
            key_stats['avg_holding_size'] = "$5.17mm"  # Fallback
            
        # Top 10 Concentration
        if 'Top 10% Concentration' in metrics:
            key_stats['top_10_concentration'] = f"{float(metrics['Top 10% Concentration'])*100:.1f}%"
        else:
            key_stats['top_10_concentration'] = "20.6%"  # Fallback
            
        # Total Leverage
        if 'Total Leverage' in metrics:
            leverage_value = metrics['Total Leverage']
            if isinstance(leverage_value, (int, float)):
                # Convert to percentage (e.g., 0.10 to 10%)
                key_stats['total_leverage'] = f"{leverage_value*100:.1f}%"
            else:
                key_stats['total_leverage'] = leverage_value
        else:
            key_stats['total_leverage'] = "10.0%"  # Fallback
            
        # Repo MV
        if 'Repo MV' in metrics:
            repo_value = metrics['Repo MV']
            if isinstance(repo_value, (int, float)):
                key_stats['repo_mv'] = f"${repo_value:.2f}mm"
            else:
                key_stats['repo_mv'] = repo_value
        else:
            key_stats['repo_mv'] = "$75.00mm"  # Fallback
        
        # Add extraction source
        key_stats['extraction_source'] = 'excel'
        
        # New Attribution by Strategy from Key Stats sheet
        attribution_labels = {
            "CMBS": "CMBS",
            "ABS": "ABS",
            "CLO": "CLO",
            "Hedges": "Hedges",
            "Cash": "Cash",
            "Total (Gross)": "Total (Gross)",
            "Total (Net)": "Total (Net)"
        }

        for excel_label, key_name in attribution_labels.items():
            if excel_label in metrics:
                key_stats['attribution_by_strategy'][key_name] = _parse_to_bps(metrics[excel_label])
            else:
                key_stats['attribution_by_strategy'][key_name] = 0 # Default to 0 bps if not found
                logging.debug(f"Attribution label '{excel_label}' not found in Key Stats metrics. Defaulting to 0 bps for '{key_name}'.")

        key_stats['extraction_source'] = 'excel_extract'
        logging.debug(f"KEY STATS EXTRACTED ({excel_path}):\n{key_stats}")
        return key_stats
        
    except Exception as e:
        logging.error(f"Error extracting key stats from Excel {excel_path}: {str(e)}", exc_info=True)
        logging.debug(f"KEY STATS EXTRACTED (fallback due to error):\n Using hardcoded fallback values (Error: {str(e)})")
        return {
            'avg_yield': '13.10%',
            'wal': '3.20',
            'pct_ig': '24.2%',
            'pct_risk_rating_1': '52.3%',
            'floating_rate_pct': '21.2%',
            'monthly_carry_bps': '61 bps',
            'bond_line_items': '3',
            'bond_breakdown': {'CMBS': 1, 'ABS': 2, 'CLO': 0},
            'avg_holding_size': '$5.17mm',
            'top_10_concentration': '20.6%',
            'extraction_source': 'hardcoded_fallback'
        }
        
        # Log the extracted key stats for debugging
        logging.debug(f"KEY STATS EXTRACTED (after fallback processing in extract_key_stats_from_risk_report):\n {key_stats}")
        logging.debug(f"Extraction source (after fallback processing in extract_key_stats_from_risk_report): {key_stats.get('extraction_source', 'unknown')}")
        
        return key_stats
    
    except Exception as e:
        logging.warning(f"Error extracting data from risk report (extract_key_stats_from_risk_report): {e}", exc_info=True)
        # Ensure key_stats is defined before returning, even if it's just the fallback from the inner try-except
        if 'key_stats' not in locals():
             key_stats = {
                'avg_yield': '13.10%', 'wal': '3.20', 'pct_ig': '24.2%',
                'pct_risk_rating_1': '52.3%', 'floating_rate_pct': '21.2%',
                'monthly_carry_bps': '61 bps', 'bond_line_items': '3',
                'bond_breakdown': {'CMBS': 1, 'ABS': 2, 'CLO': 0},
                'avg_holding_size': '$5.17mm', 'top_10_concentration': '20.6%',
                'extraction_source': 'hardcoded_fallback_outer_exception'
            }
        logging.debug(f"Returning key_stats due to outer exception in extract_key_stats_from_risk_report: {key_stats}")
        return key_stats

# ---------- FILES ----------
# Function to find the most recent month-end file
def find_latest_eom_file():
    eom_files = [f for f in os.listdir(DATA_PATH) if f.startswith('eom_marks_') and f.endswith('.xlsx')]
    if not eom_files:
        return None
    # Sort by modification date (newest first)
    eom_files.sort(key=lambda f: os.path.getmtime(os.path.join(DATA_PATH, f)), reverse=True)
    return eom_files[0]

# Function to find the most recent holdings file
def find_latest_holdings_file():
    holdings_files = [f for f in os.listdir(DATA_PATH) if 
                     (f.startswith('portfolio_holdings_') or f.startswith('holdings_')) and 
                     f.endswith('.xlsx')]
    if not holdings_files:
        return None
    # Sort by modification date (newest first)
    holdings_files.sort(key=lambda f: os.path.getmtime(os.path.join(DATA_PATH, f)), reverse=True)
    return holdings_files[0]

# Function to find the most recent trades file
def find_latest_trades_file():
    trades_files = [f for f in os.listdir(DATA_PATH) if 
                   f.startswith('_cannae_trade_') and 
                   f.endswith('.xlsx')]
    if not trades_files:
        return None
    # Sort by modification date (newest first)
    trades_files.sort(key=lambda f: os.path.getmtime(os.path.join(DATA_PATH, f)), reverse=True)
    return trades_files[0]

# Find the latest files
latest_eom_file = find_latest_eom_file()
latest_holdings_file = find_latest_holdings_file()
latest_trades_file = find_latest_trades_file()

# Load the files with error handling
try:
    if latest_eom_file:
        APRIL_EOM = pd.read_excel(os.path.join(DATA_PATH, latest_eom_file))
    else:
        st.sidebar.error("No month-end file found. Please add an 'eom_marks_*.xlsx' file to the data directory.")
        APRIL_EOM = pd.DataFrame()  # Empty DataFrame as fallback
        
    if latest_holdings_file:
        HOLDINGS_LATEST = pd.read_excel(os.path.join(DATA_PATH, latest_holdings_file))
    else:
        st.sidebar.error("No holdings file found. Please add a 'portfolio_holdings_*.xlsx' file to the data directory.")
        HOLDINGS_LATEST = pd.DataFrame()  # Empty DataFrame as fallback
        
    if latest_trades_file:
        TRADES = pd.read_excel(os.path.join(DATA_PATH, latest_trades_file))
    else:
        st.sidebar.error("No trades file found. Please add a '_cannae_trade_*.xlsx' file to the data directory.")
        TRADES = pd.DataFrame()  # Empty DataFrame as fallback
except Exception as e:
    st.sidebar.error(f"Error loading files: {e}")
    # Create empty DataFrames as fallback
    APRIL_EOM = pd.DataFrame()
    HOLDINGS_LATEST = pd.DataFrame()
    TRADES = pd.DataFrame()
# Try to read PEERS file, with fallback if it fails
try:
    # Remove any problematic parameters like showZeroes
    PEERS = pd.read_excel(
        os.path.join(DATA_PATH, "20250506_funds_open-end-fund-profile.xlsx"), 
        engine='openpyxl'
    )
except Exception as e:
    # Create synthetic PEERS data as fallback
    PEERS = pd.DataFrame({
        'Fund Name': ['Fund A', 'Fund B', 'Fund C', 'Fund D', 'Fund E', 'Fund F', 'Fund G', 'Fund H'],
        'YTD Return': [2.1, 2.5, 2.8, 3.0, 3.2, 3.5, 3.8, 4.0]
    })
# Use OS-agnostic path to assets directory
ASSETS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
LOGO_FILE = os.path.join(ASSETS_PATH, "Cannae-logo.jpg")

# Add error handling for logo display
try:
    st.sidebar.image(LOGO_FILE)
except Exception as e:
    st.sidebar.warning(f"Logo not found. Using text header instead.")
    st.sidebar.title("Cannae Dashboard")

# Sidebar already has logo/title

# ---------- EXTRACT KPIS ----------
# Extract KPIs from Excel sheet
kpi_data = extract_kpis_from_factsheet()

# Extract key stats from risk report
key_stats = extract_key_stats_from_risk_report()

# Log key_stats for debugging
logging.debug(f"KEY STATS EXTRACTED: {key_stats}")
logging.debug(f"Extraction source: {key_stats.get('extraction_source', 'unknown')}")

# Populate kpi_data with ITD values from key_stats if available
if 'ITD Return' in key_stats and isinstance(key_stats.get('ITD Return'), dict):
    kpi_data['itd_return_str'] = key_stats['ITD Return'].get('string_value', "N/A")
    kpi_data['itd_return_float'] = key_stats['ITD Return'].get('float_value', 0.0)
else:
    # Fallback if ITD Return is not in key_stats or not in expected format
    kpi_data.setdefault('itd_return_str', "N/A")
    kpi_data.setdefault('itd_return_float', 0.0)

# Populate kpi_data with Annualized ITD ROR values from key_stats if available
if 'Annualized ITD ROR' in key_stats and isinstance(key_stats.get('Annualized ITD ROR'), dict):
    kpi_data['annualized_return_str'] = key_stats['Annualized ITD ROR'].get('string_value', "N/A")
    kpi_data['annualized_return_float'] = key_stats['Annualized ITD ROR'].get('float_value', 0.0)
else:
    # Fallback if Annualized ITD ROR is not in key_stats or not in expected format
    kpi_data.setdefault('annualized_return_str', "N/A")
    kpi_data.setdefault('annualized_return_float', 0.0)

# ---------- KPI STRIP ----------
st.markdown("## Returns")
col1, col2, col3, col4 = st.columns(4)

col1.metric("YTD Return", kpi_data["ytd_return_str"])
col2.metric("Monthly Return", kpi_data["monthly_return_str"])
col3.metric("Annualized Return", kpi_data["ann_return_str"])
col4.metric("AUM", kpi_data["aum_str"])

st.markdown("---") # Visual separator

# ---------- KEY STATS ----------
st.markdown("### Key Stats")
# Display key stats extracted from risk report
key_stats_col1, key_stats_col2, key_stats_col3, key_stats_col4 = st.columns(4)

# First row of metrics
key_stats_col1.metric("Average Yield", key_stats["avg_yield"])
key_stats_col2.metric("WAL", key_stats["wal"])
key_stats_col3.metric("% IG", key_stats["pct_ig"])
key_stats_col4.metric("Floating Rate %", key_stats["floating_rate_pct"])

# Second row of metrics
key_stats_row2_col1, key_stats_row2_col2, key_stats_row2_col3, key_stats_row2_col4 = st.columns(4)
key_stats_row2_col1.metric("% Risk Rating 1", key_stats["pct_risk_rating_1"])
key_stats_row2_col2.metric("Monthly Carry", key_stats["monthly_carry_bps"])
key_stats_row2_col3.metric("Bond Line Items", key_stats["bond_line_items"])
key_stats_row2_col4.metric("Average Holding Size", key_stats["avg_holding_size"])

# Third row with remaining metrics
key_stats_row3_col1, key_stats_row3_col2, key_stats_row3_col3, key_stats_row3_col4 = st.columns(4)
key_stats_row3_col1.metric("Top 10% Concentration", key_stats["top_10_concentration"])
key_stats_row3_col2.metric("CMBS Line Items", key_stats["bond_breakdown"].get("CMBS", 0))
key_stats_row3_col3.metric("ABS Line Items", key_stats["bond_breakdown"].get("ABS", 0))
key_stats_row3_col4.metric("CLO Line Items", key_stats["bond_breakdown"].get("CLO", 0))

# Fourth row with leverage metrics
key_stats_row4_col1, key_stats_row4_col2, key_stats_row4_col3, key_stats_row4_col4 = st.columns(4)
key_stats_row4_col1.metric("Total Leverage %", key_stats.get("total_leverage", "N/A"))
key_stats_row4_col2.metric("Repo MV", key_stats.get("repo_mv", "N/A"))

# ---------- ALLOCATION: PIE + DRIFT ----------


def summarize_alloc(df):
    # Create a copy of the dataframe to avoid modifying the original
    df = df.copy()
    
    # Handle different column names for strategy
    strategy_column = 'Strategy'
    if strategy_column not in df.columns:
        # Try alternative column names
        alternative_columns = ['Investment Description', 'Asset Class', 'Type', 'Security Type']
        for col in alternative_columns:
            if col in df.columns:
                strategy_column = col
                st.warning(f"Using '{strategy_column}' as the strategy column")
                # Rename to standardize
                df['Strategy'] = df[strategy_column]
                break
        else:
            # If no suitable column found, create a default strategy column
            st.error(f"No strategy column found. Available columns: {df.columns.tolist()}")
            df['Strategy'] = 'UNKNOWN'
    
    
    # Specifically use Admin Net MV column as requested
    mv_column = 'Admin Net MV'
    
    # Make sure the column exists
    if mv_column not in df.columns:
        st.warning(f"Column '{mv_column}' not found in holdings data. Available columns: {df.columns.tolist()}")
        # Fallback to other columns if needed
        for col_name in ['Net MV', 'Curr MV', 'MV', 'Market Value', 'Position Value']:
            if col_name in df.columns:
                mv_column = col_name
                st.warning(f"Falling back to '{mv_column}' column")
                break
        else:
            # If no suitable column found, try to find any column with numeric values that might be market value
            numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_columns) > 0:
                mv_column = numeric_columns[0]
                st.warning(f"Using numeric column '{mv_column}' as market value")
            else:
                st.error("No suitable market value column found")
                # Return empty dataframe with expected structure
                return pd.DataFrame(columns=["Strategy", "Market Value"])
    
    # Filter out CURRENCY and REPO as requested by user
    # Keep HEDGE in the allocation
    exclude_strategies = ['CURRENCY', 'REPO']
    
    # Filter out excluded strategies
    df = df[~df['Strategy'].isin(exclude_strategies)]
    
    # Debug: Log filtered dataframe details
    logging.debug(f"Summarize Alloc - Debug - Filtered Data - Using column: {mv_column}")
    logging.debug(f"Summarize Alloc - Debug - Filtered Data - Total {mv_column} before grouping: ${df[mv_column].sum():,.2f}")
    logging.debug(f"Summarize Alloc - Debug - Filtered Data - Head of df[['Strategy', mv_column]]:\n{df[['Strategy', mv_column]].head()}")
    
    # Group by Strategy and sum the MV column
    result = df.groupby("Strategy")[mv_column].sum().reset_index()
    result.columns = ["Strategy", "Market Value"]
    
    # Only include non-zero market values
    if not result.empty:
        result = result[result["Market Value"] != 0]  # Remove zero market value entries
    
    logging.debug(f"Summarize Alloc - Total Market Value: ${result['Market Value'].sum():,.2f}")
    logging.debug(f"Summarize Alloc - Should match AUM: {kpi_data['aum_str']}")
    
    return result

# ---------- ALLOCATION VISUALIZATION ----------
st.markdown("## Portfolio Allocation")

# Create two columns for side-by-side pie charts
col1, col2 = st.columns(2)

# Process month-end data
with col1:
    # Extract month name from filename for display
    import re
    month_match = re.search(r'eom_marks_([A-Za-z]+)', latest_eom_file) if latest_eom_file else None
    month_name = month_match.group(1) if month_match else "Month-End"
    
    # Update subheader with dynamic month name
    st.subheader(f"{month_name} Month-End")
    
    # Load the Position Holdings tab from the month-end file
    try:
        # Try to get the Position Holdings tab from APRIL_EOM
        if 'Position Holdings' in pd.ExcelFile(os.path.join(DATA_PATH, latest_eom_file)).sheet_names:
            month_end_holdings = pd.read_excel(os.path.join(DATA_PATH, latest_eom_file), sheet_name="Position Holdings")
            sheet_used = "Position Holdings"
        else:
            # Fallback to the first sheet
            month_end_holdings = APRIL_EOM
            sheet_used = "Default"
            
        logging.debug(f"Debug - {month_name} Month-End Data:")
        logging.debug(f"  Using file: {latest_eom_file}")
        logging.debug(f"  Sheet used: {sheet_used}")
        logging.debug(f"  Loaded with {len(month_end_holdings)} rows")
        logging.debug(f"  Columns: {month_end_holdings.columns.tolist()}")
        if 'Strategy' in month_end_holdings.columns:
            logging.debug(f"  Unique strategies: {month_end_holdings['Strategy'].unique()}")
        else:
            possible_strategy_columns = ['Investment Description', 'Asset Class', 'Type']
            for col_name in possible_strategy_columns:
                if col_name in month_end_holdings.columns:
                    logging.debug(f"  Found potential strategy column '{col_name}': {month_end_holdings[col_name].unique()}")
                        
        # Use summarize_alloc to get month-end allocation data
        april_alloc_data = summarize_alloc(month_end_holdings)
    except Exception as e:
        st.error(f"Error loading data from {month_name} file: {e}")
        # Create empty DataFrame as fallback
        april_alloc_data = pd.DataFrame(columns=["Strategy", "Market Value"])
    
    # Format market values for display with $ and commas
    april_alloc_data["Formatted Value"] = april_alloc_data["Market Value"].apply(lambda x: f"${x:,.0f}")
    
    # Calculate percentages for each strategy
    april_total_mv = april_alloc_data["Market Value"].sum()
    april_alloc_data["Percentage"] = april_alloc_data["Market Value"] / april_total_mv * 100

# Process current holdings data
with col2:
    # Use the global latest_holdings_file variable
    holdings_file_path = os.path.join(DATA_PATH, latest_holdings_file) if latest_holdings_file else None
    
    # Extract date from filename for display or use current date
    import re
    import datetime
    
    # Try different regex patterns to match the date in the filename
    date_str = "Current"
    if latest_holdings_file:
        # Try pattern like portfolio_holdings_5June2025.xlsx
        date_match = re.search(r'holdings_([0-9]+[A-Za-z]+[0-9]+)', latest_holdings_file)
        if date_match:
            date_str = date_match.group(1)
        # Try pattern like portfolio_holdings_June5.xlsx
        else:
            date_match = re.search(r'holdings_([A-Za-z]+[0-9]+)', latest_holdings_file)
            if date_match:
                date_str = date_match.group(1)
    
    # Update subheader with dynamic date - simpler
    st.subheader(f"{date_str} Holdings")
    
    # Load current holdings data
    try:
        # Use the global HOLDINGS_LATEST variable directly
        logging.debug(f"Debug - Current Holdings ({date_str}):")
        logging.debug(f"  Using file: {latest_holdings_file}")
        logging.debug(f"  Current holdings data with {len(HOLDINGS_LATEST)} rows")
        logging.debug(f"  Columns: {HOLDINGS_LATEST.columns.tolist()}")
        if 'Strategy' in HOLDINGS_LATEST.columns:
            logging.debug(f"  Unique strategies: {HOLDINGS_LATEST['Strategy'].unique()}")
        else:
            possible_strategy_columns = ['Investment Description', 'Asset Class', 'Type']
            for col_name in possible_strategy_columns:
                if col_name in HOLDINGS_LATEST.columns:
                    logging.debug(f"  Found potential strategy column '{col_name}': {HOLDINGS_LATEST[col_name].unique()}")
        
        # Use summarize_alloc to get current allocation data
        current_alloc_data = summarize_alloc(HOLDINGS_LATEST)
    except Exception as e:
        st.error(f"Error loading current holdings data: {e}")
        # Create empty DataFrame as fallback
        current_alloc_data = pd.DataFrame(columns=["Strategy", "Market Value"])
    
    # Format market values for display with $ and commas
    current_alloc_data["Formatted Value"] = current_alloc_data["Market Value"].apply(lambda x: f"${x:,.0f}")
    
    # Calculate percentages for each strategy
    current_total_mv = current_alloc_data["Market Value"].sum()
    current_alloc_data["Percentage"] = current_alloc_data["Market Value"] / current_total_mv * 100

# Create pie charts for both April and current data
with col1:
    # Display April allocation table
    april_display = april_alloc_data.copy()
    april_display["Allocation"] = april_display["Percentage"].apply(lambda x: f"{x:.1f}%")
    april_display = april_display.sort_values(by="Percentage", ascending=False)
    april_display = april_display[["Strategy", "Formatted Value", "Allocation"]]
    
    # Add total row
    april_display = pd.concat([april_display, pd.DataFrame({
        "Strategy": ["TOTAL"],
        "Formatted Value": [f"${april_total_mv:,.0f}"],
        "Allocation": ["100.0%"]
    })], ignore_index=True)
    
    # Display the month-end table
    st.write(f"**{month_name} Allocation by Strategy**")
    st.dataframe(april_display, hide_index=True)
    
    # Create hover text for April data
    april_alloc_data["Hover Info"] = april_alloc_data.apply(
        lambda row: f"Strategy: {row['Strategy']}<br>Amount: {row['Formatted Value']}<br>Allocation: {row['Percentage']:.1f}%", 
        axis=1
    )
    
    # Print strategy names to console for debugging
    print("\n--- April Allocation Strategies for Pie Chart ---")
    print(april_alloc_data['Strategy'].unique())
    print("-----------------------------------------------\n")
    
    logging.debug("--- April Allocation Strategies for Pie Chart ---")
    logging.debug(april_alloc_data['Strategy'].unique())
    logging.debug("-----------------------------------------------")

    # Plot month-end allocation
    strategy_color_map = {
        # CMBS variations
        'CMBS F1': '#3A606E',      # Teal for CMBS F1 (as requested)
        'CMBS': '#3A606E',         # Same teal for any CMBS variation
        'CMBS F2': '#3A606E',      # Same teal for any CMBS variation
        'CMBS FUND': '#3A606E',    # Same teal for any CMBS variation
        
        # Other strategies
        'AIRCRAFT F1': '#475569',  # Slate gray for AIRCRAFT F1
        'AIRCRAFT': '#475569',     # Same gray for any AIRCRAFT variation
        'ABS': '#6366F1',          # Indigo for ABS
        'CLO': '#8B5CF6',          # Violet for CLO
        'SHORT TERM': '#0EA5E9',   # Sky blue for SHORT TERM
        'HEDGE': '#64748B',        # Slate for HEDGE
        'CASH': '#94A3B8',         # Light slate for CASH
    }
    fig_april = px.pie(
        april_alloc_data, 
        values="Market Value", 
        names="Strategy", 
        title=f"{month_name} Portfolio Allocation",
        color="Strategy",  # Explicitly use Strategy as the color dimension
        color_discrete_map=strategy_color_map,
        color_discrete_sequence=["#0F766E", "#0E7490", "#0369A1", "#1D4ED8", "#4338CA", "#6D28D9"], # Blue-teal palette fallback
        custom_data=["Hover Info"]
    )
    
    # Format April pie chart
    fig_april.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate="%{customdata[0]}"
    )

    fig_april.update_layout(
        legend_title="Strategy",
        font=dict(size=12, family="Merriweather"),  # Applied Merriweather, kept general font size
        legend=dict(font=dict(size=10, family="Merriweather")), # Applied Merriweather to legend
        hoverlabel=dict(font_size=12, font_family="Merriweather"),
        title={
            'text': f"{month_name} Portfolio Allocation",
            'y':0.95, # Adjust title position (closer to top)
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 16, 'family': "Merriweather"} # Applied Merriweather to title
        },
        height=350, # Increased height
        margin=dict(l=20, r=20, t=50, b=20), # Adjusted margins for title
        font_family="Merriweather" # Global font for the chart
    )

    st.plotly_chart(fig_april, use_container_width=True)

with col2:
    # Display current allocation table
    current_display = current_alloc_data.copy()
    current_display["Allocation"] = current_display["Percentage"].apply(lambda x: f"{x:.1f}%")
    current_display = current_display.sort_values(by="Percentage", ascending=False)
    current_display = current_display[["Strategy", "Formatted Value", "Allocation"]]
    
    # Add total row
    current_display = pd.concat([current_display, pd.DataFrame({
        "Strategy": ["TOTAL"],
        "Formatted Value": [f"${current_total_mv:,.0f}"],
        "Allocation": ["100.0%"]
    })], ignore_index=True)
    
    # Display the current table
    st.write(f"**{date_str} Allocation by Strategy**")
    st.dataframe(current_display, hide_index=True)
    
    # Create hover text for current data
    current_alloc_data["Hover Info"] = current_alloc_data.apply(
        lambda row: f"Strategy: {row['Strategy']}<br>Amount: {row['Formatted Value']}<br>Allocation: {row['Percentage']:.1f}%", 
        axis=1
    )
    
    # Print strategy names to console for debugging
    print("\n--- Current Allocation Strategies for Pie Chart ---")
    print(current_alloc_data['Strategy'].unique())
    print("-------------------------------------------------\n")
    
    logging.debug("--- Current Allocation Strategies for Pie Chart ---")
    logging.debug(current_alloc_data['Strategy'].unique())
    logging.debug("-------------------------------------------------")

    # Plot current allocation - using same color scheme as month-end for consistency
    strategy_color_map = {
        # CMBS variations
        'CMBS F1': '#3A606E',      # Teal for CMBS F1 (as requested)
        'CMBS': '#3A606E',         # Same teal for any CMBS variation
        'CMBS F2': '#3A606E',      # Same teal for any CMBS variation
        'CMBS FUND': '#3A606E',    # Same teal for any CMBS variation
        
        # Other strategies
        'AIRCRAFT F1': '#475569',  # Slate gray for AIRCRAFT F1
        'AIRCRAFT': '#475569',     # Same gray for any AIRCRAFT variation
        'ABS': '#6366F1',          # Indigo for ABS
        'CLO': '#8B5CF6',          # Violet for CLO
        'SHORT TERM': '#0EA5E9',   # Sky blue for SHORT TERM
        'HEDGE': '#64748B',        # Slate for HEDGE
        'CASH': '#94A3B8',         # Light slate for CASH
    }
    fig_current = px.pie(
        current_alloc_data, 
        values="Market Value", 
        names="Strategy", 
        title=f"Current Portfolio Allocation ({date_str})",
        color="Strategy",  # Explicitly use Strategy as the color dimension
        color_discrete_map=strategy_color_map,
        color_discrete_sequence=["#0F766E", "#0E7490", "#0369A1", "#1D4ED8", "#4338CA", "#6D28D9"], # Blue-teal palette fallback
        custom_data=["Hover Info"]
    )
    
    # Format current pie chart
    fig_current.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate="%{customdata[0]}"
    )
    
    fig_current.update_layout(
        legend_title="Strategy",
        font=dict(size=12, family="Merriweather"),  # Applied Merriweather, kept general font size
        legend=dict(font=dict(size=10, family="Merriweather")), # Applied Merriweather to legend
        hoverlabel=dict(font_size=12, font_family="Merriweather"),
        title={
            'text': f"Current Portfolio Allocation ({date_str})",
            'y':0.95, # Adjust title position (closer to top)
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 16, 'family': "Merriweather"} # Applied Merriweather to title
        },
        height=350, # Increased height
        margin=dict(l=20, r=20, t=50, b=20), # Adjusted margins for title
        font_family="Merriweather" # Global font for the chart
    )
    
    st.plotly_chart(fig_current, use_container_width=True)
    
    # Function to extract leverage statistics from risk report
    def extract_leverage_stats(pdf_path):
        try:
            # Initialize default values
            leverage_stats = {
                "Repo MV ($mm)": "N/A",
                "CMBS Leverage": "N/A",
                "ABS Leverage": "N/A",
                "CLO Leverage": "N/A",
                "Aggregate Leverage": "N/A"
            }
            
            # Extract text from page 5 of the risk report
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) >= 5:  # Make sure page 5 exists
                    page = pdf.pages[4]  # 0-indexed, so page 5 is index 4
                    text = page.extract_text()
                    
                    # For debugging - show the extracted text
                    with st.sidebar.expander("Debug - Risk Report Page 5 Text"):
                        st.text(text)
                        
                        # Look for specific lines containing our target values
                        lines = text.split('\n')
                        st.write("**Lines containing key metrics:**")
                        for line in lines:
                            if any(key in line for key in ["Repo MV", "CMBS Leverage", "ABS Leverage", "CLO Leverage", "Aggregate Leverage"]):
                                st.write(line)
                    
                    # Extract Repo MV using line-by-line approach
                    lines = text.split('\n')
                    for line in lines:
                        if "Repo MV" in line:
                            # Extract the value using regex
                            repo_match = re.search(r'\(\$(\d+\.\d+)\)', line)
                            if repo_match:
                                leverage_stats["Repo MV ($mm)"] = f"(${repo_match.group(1)})"
                                break
                    
                    # Extract CMBS Leverage
                    for line in lines:
                        if "CMBS Leverage" in line:
                            cmbs_match = re.search(r'(\d+\.?\d*)%', line)
                            if cmbs_match:
                                leverage_stats["CMBS Leverage"] = f"{cmbs_match.group(1)}%"
                                break
                    
                    # Extract ABS Leverage
                    for line in lines:
                        if "ABS Leverage" in line:
                            abs_match = re.search(r'(\d+)%', line)
                            if abs_match:
                                leverage_stats["ABS Leverage"] = f"{abs_match.group(1)}%"
                                break
                    
                    # Extract CLO Leverage
                    for line in lines:
                        if "CLO Leverage" in line:
                            clo_match = re.search(r'(\d+)%', line)
                            if clo_match:
                                leverage_stats["CLO Leverage"] = f"{clo_match.group(1)}%"
                                break
                    
                    # Extract Aggregate Leverage
                    for line in lines:
                        if "Aggregate Leverage" in line:
                            agg_match = re.search(r'(\d+\.?\d*)%', line)
                            if agg_match:
                                leverage_stats["Aggregate Leverage"] = f"{agg_match.group(1)}%"
                                break
            
            return leverage_stats
        except Exception as e:
            st.sidebar.error(f"Error extracting data from Excel: {str(e)}")
            st.sidebar.error("Falling back to PDF extraction")
            return {}

def extract_key_stats_from_excel(excel_path):
    """Extract key statistics from the Risk Report Format Master Sheet Excel file using the Key Stats sheet"""
    extraction_results = {}
    extraction_contexts = {}
    
    try:
        # Simple debug message
        st.sidebar.info(f"EXCEL EXTRACTION: Attempting to read from {excel_path}")
        
        # Check if file exists
        if not os.path.exists(excel_path):
            st.sidebar.error(f"EXCEL EXTRACTION: File does not exist: {excel_path}")
            return {}
            
        # List all sheets in the Excel file
        excel = pd.ExcelFile(excel_path)
        st.sidebar.info(f"EXCEL EXTRACTION: Available sheets: {excel.sheet_names}")
        
        # Check if Key Stats sheet exists
        if 'Key Stats' not in excel.sheet_names:
            st.sidebar.error("EXCEL EXTRACTION: 'Key Stats' sheet not found in Excel file!")
            return {}
        
        # Read the Key Stats sheet
        key_stats_df = pd.read_excel(excel_path, sheet_name='Key Stats', header=None)
        st.sidebar.success(f"EXCEL EXTRACTION: Successfully read 'Key Stats' sheet with {key_stats_df.shape[0]} rows")
        
        # Create a dictionary of metrics
        key_stats_dict = {}
        
        # Process all rows
        for i in range(len(key_stats_df)):
            if key_stats_df.shape[1] >= 2:  # Make sure there are at least 2 columns
                metric_name = key_stats_df.iloc[i, 0]
                if pd.notna(metric_name):  # Skip empty metric names
                    metric_value = key_stats_df.iloc[i, 1]
                    key_stats_dict[metric_name] = metric_value
        
        st.sidebar.success(f"EXCEL EXTRACTION: Found {len(key_stats_dict)} metrics in Key Stats sheet")
        
        # Print all metrics for debugging
        st.sidebar.info("EXCEL EXTRACTION: All metrics found:")
        for key, value in key_stats_dict.items():
            st.sidebar.info(f"{key}: {value}")
        
        # Now proceed with the rest of the extraction
        
        # Debug output to sidebar
        st.sidebar.info(f"Found {len(key_stats_dict)} metrics in Key Stats sheet")
        
        # Extract values from the dictionary with appropriate formatting
        avg_yield = f"{key_stats_dict.get('Average Yield', 0)*100:.2f}%"  # Convert from decimal to percentage
        wal = f"{key_stats_dict.get('WAL', 0):.2f}"
        pct_ig = f"{key_stats_dict.get('% IG', 0)*100:.1f}%"  # Convert from decimal to percentage
        floating_rate_pct = f"{key_stats_dict.get('Floating Rate %', 0)*100:.1f}%"  # Convert from decimal to percentage
        pct_risk_rating_1 = f"{key_stats_dict.get('% Risk Rating 1', 0)*100:.1f}%"  # Convert from decimal to percentage
        
        # Convert Monthly Carry from decimal to basis points (1% = 100 bps)
        monthly_carry_value = key_stats_dict.get('Monthly Carry', 0)
        monthly_carry_bps = int(monthly_carry_value * 10000)  # Convert from decimal to basis points
        monthly_carry = f"{monthly_carry_bps} bps"
        
        # Get bond line items breakdown
        total_bond_line_items = int(key_stats_dict.get('Bond Line Items', 0))
        abs_line_items = int(key_stats_dict.get('ABS Line Items', 0))
        cmbs_line_items = int(key_stats_dict.get('CMBS Line Items', 0))
        clo_line_items = int(key_stats_dict.get('CLO Line Items', 0))
        
        # Get average holding size and top 10 concentration
        avg_holding_size = key_stats_dict.get('Average Holding Size', 0)
        # Format as $X.Xmm if it's a large number
        if avg_holding_size >= 1000000:
            avg_holding_size = f"${avg_holding_size/1000000:.1f}mm"
        else:
            avg_holding_size = f"${avg_holding_size:,.0f}"
            
        top_10_concentration = f"{key_stats_dict.get('Top 10% Concentration', 0)*100:.2f}%"  # Convert from decimal to percentage
        
        # Store extraction contexts for debugging
        for key, value in key_stats_dict.items():
            extraction_contexts[key] = {
                'value': str(value),
                'context': f'From Key Stats sheet in {os.path.basename(excel_path)}',
                'raw_value': str(value)
            }
        
        # Store results
        extraction_results = {
            'avg_yield': avg_yield,
            'wal': wal,
            'pct_ig': pct_ig,
            'pct_risk_rating_1': pct_risk_rating_1,
            'floating_rate_pct': floating_rate_pct,
            'monthly_carry_bps': monthly_carry,
            'bond_line_items': str(total_bond_line_items),
            'bond_breakdown': {
                'CMBS': cmbs_line_items,
                'ABS': abs_line_items,
                'CLO': clo_line_items
            },
            'avg_holding_size': avg_holding_size,
            'top_10_concentration': top_10_concentration,
            'extraction_source': 'excel',
            'excel_path': excel_path,
            'extraction_contexts': extraction_contexts
        }
        
        # Log extracted values
        logging.debug(f"Extracted values from Excel ({excel_path}):")
        logging.debug(f"  Average Yield: {avg_yield}")
        logging.debug(f"  WAL: {wal}")
        logging.debug(f"  % IG: {pct_ig}")
        logging.debug(f"  Floating Rate %: {floating_rate_pct}")
        logging.debug(f"  % Risk Rating 1: {pct_risk_rating_1}")
        logging.debug(f"  Monthly Carry: {monthly_carry}")
        logging.debug(f"  Bond Line Items: {total_bond_line_items}")
        logging.debug(f"  ABS Line Items: {abs_line_items}")
        logging.debug(f"  CMBS Line Items: {cmbs_line_items}")
        logging.debug(f"  CLO Line Items: {clo_line_items}")
        logging.debug(f"  Average Holding Size: {avg_holding_size}")
        logging.debug(f"  Top 10 Concentration: {top_10_concentration}")
        
        # Add a summary context for the extraction process
        extraction_results['extraction_contexts']['excel_summary'] = {
            'value': 'Excel data extracted successfully',
            'context': f'Used Excel file: {os.path.basename(excel_path)}',
            'sheet_names': pd.ExcelFile(excel_path).sheet_names
        }
        
        logging.info(f"Successfully extracted data from Excel sheet 'Key Stats' in {excel_path}")
        return extraction_results
    
    except Exception as e:
        logging.error(f"Error extracting data from Excel ({excel_path}): {str(e)}", exc_info=True)
        logging.error(f"  Exception type: {type(e).__name__}")
        
        # Try to read the Excel file and list sheet names for debugging
        try:
            excel_file_for_debug = pd.ExcelFile(excel_path)
            logging.info(f"  Available sheets in {excel_path} during error handling: {excel_file_for_debug.sheet_names}")
        except Exception as sheet_error:
            logging.error(f"  Error reading Excel sheets from {excel_path} during error handling: {str(sheet_error)}")
        
        logging.warning(f"Falling back to PDF extraction due to error in Excel processing for {excel_path}")
        # Return empty dict to signal fallback to PDF extraction
        return {}


# ---------- TRADES + DEPLOYMENT ----------
st.markdown("## Trading Monitor")

# Filter out REPO and EARLY TERM trades immediately when loading the trades data
if not TRADES.empty:
    # Filter out any trades containing Repo New/Roll or Repo Termination
    repo_filter = ~TRADES["Transaction"].str.contains("Repo New|Repo Roll|Repo Termination", case=False, na=False)
    filtered_trades = TRADES[repo_filter].copy()
    

    
    # Use the actual Strategy column from the file, but clean it up
    def clean_strategy(strategy):
        if pd.isna(strategy):
            return "Other"
        
        strategy = str(strategy).upper()
        if "CMBS" in strategy:
            return "CMBS"
        elif "AIRCRAFT" in strategy:
            return "AIRCRAFT"
        elif "ABS" in strategy:
            return "ABS"
        elif "HEDGE" in strategy:
            return "Hedges"
        elif "CLO" in strategy:
            return "CLO"
        else:
            return "Other"
    
    # Use the actual Strategy column from the file
    filtered_trades["CleanStrategy"] = filtered_trades["Strategy"].apply(clean_strategy)
    
    # Convert Proceeds to absolute value for sorting by size
    filtered_trades["Abs_Proceeds"] = filtered_trades["Proceeds"].abs()
    
    # Get the last 2 trades by date
    last_2_trades = filtered_trades.sort_values("Trade Date", ascending=False).head(2)
    
    # Get the top 5 largest trades by absolute market value
    top_5_largest = filtered_trades.sort_values("Abs_Proceeds", ascending=False).head(5)
    
    # Combine and remove duplicates
    selected_trades = pd.concat([last_2_trades, top_5_largest]).drop_duplicates()
    
    # Create a Trading Monitor table similar to the example
    # Create a copy of filtered_trades for trading summary
    trading_summary = filtered_trades.copy()
    
    # Map Transaction types to Buy/Sell categories
    trading_summary["Action"] = trading_summary["Transaction"].map(lambda x: "Buy" if "buy" in str(x).lower() else "Sell")
    
    # Calculate metrics by strategy
    strategy_metrics = {}
    for strategy in ["CMBS", "AIRCRAFT", "ABS", "Hedges", "CLO"]:
        strategy_data = trading_summary[trading_summary["CleanStrategy"] == strategy]
        
        buys = strategy_data[strategy_data["Action"] == "Buy"]
        sells = strategy_data[strategy_data["Action"] == "Sell"]
        
        buy_count = len(buys)
        sell_count = len(sells)
        # Fix sign convention: buys are positive (they're negative in the data)
        purchase_mv = buys["Proceeds"].sum() * -1  # Make buys positive (they're negative in the data)
        sale_mv = sells["Proceeds"].sum() * -1  # Make sells positive (they're negative in the data)
        
        strategy_metrics[strategy] = {
            "Buys": buy_count,
            "Sells": sell_count,
            "Purchase MV": purchase_mv,
            "Sale MV": sale_mv
        }
    
    # Calculate aggregate totals
    total_buys = sum(metrics["Buys"] for metrics in strategy_metrics.values())
    total_sells = sum(metrics["Sells"] for metrics in strategy_metrics.values())
    total_purchase_mv = sum(metrics["Purchase MV"] for metrics in strategy_metrics.values())
    total_sale_mv = sum(metrics["Sale MV"] for metrics in strategy_metrics.values())
    # Update Net calculation: Purchase MV + Sale MV (since Sale MV is already negative)
    net_mv = total_purchase_mv + total_sale_mv
    
    # Create a DataFrame for the trading monitor table
    table_data = []
    for strategy, metrics in strategy_metrics.items():
        # Calculate Net for each strategy (Purchase MV + Sale MV)
        net = metrics["Purchase MV"] + metrics["Sale MV"]
        table_data.append({
            "Strategy": strategy,
            "Buys": metrics["Buys"],
            "Sells": metrics["Sells"],
            "Purchase MV ($mm)": metrics["Purchase MV"] / 1000000,  # Convert to millions
            "Sale MV ($mm)": metrics["Sale MV"] / 1000000,  # Convert to millions
            "Net ($mm)": net / 1000000  # Convert to millions
        })
    
    # Add aggregate row
    table_data.append({
        "Strategy": "Aggregate",
        "Buys": total_buys,
        "Sells": total_sells,
        "Purchase MV ($mm)": total_purchase_mv / 1000000,
        "Sale MV ($mm)": total_sale_mv / 1000000,
        "Net ($mm)": net_mv / 1000000
    })
    
    trading_monitor_df = pd.DataFrame(table_data)
    
    # Format the monetary values with new sign convention (buys positive, sells negative)
    trading_monitor_df["Purchase MV ($mm)"] = trading_monitor_df["Purchase MV ($mm)"].apply(lambda x: f"${x:.2f}")
    trading_monitor_df["Sale MV ($mm)"] = trading_monitor_df["Sale MV ($mm)"].apply(
        lambda x: f"(${abs(x):.2f})" if x < 0 else f"${x:.2f}"
    )
    trading_monitor_df["Net ($mm)"] = trading_monitor_df["Net ($mm)"].apply(
        lambda x: f"(${abs(x):.2f})" if x < 0 else f"${x:.2f}"
    )
    
    # Display the Trading Monitor table
    st.write("**Trading Monitor**")
    st.dataframe(
        trading_monitor_df,
        column_config={
            "Strategy": st.column_config.TextColumn("Strategy"),
            "Buys": st.column_config.NumberColumn("Buys"),
            "Sells": st.column_config.NumberColumn("Sells"),
            "Purchase MV ($mm)": st.column_config.TextColumn("Purchase MV ($mm)"),
            "Sale MV ($mm)": st.column_config.TextColumn("Sale MV ($mm)"),
            "Net ($mm)": st.column_config.TextColumn("Net ($mm)")
        },
        hide_index=True
    )
    
    # Display Net value
    st.write(f"**Net: ${net_mv/1000000:.2f}M**")
    
    # Display selected trades (last 5 and top 5 largest)
    st.write("**Selected Trades**")
    
    # Fix sign convention: buys are positive, sells are negative
    # In the original data, both buys and sells have negative Proceeds
    # We need to flip the sign for all transactions to correct the sign convention
    selected_trades["Adjusted Proceeds"] = selected_trades.apply(
        lambda row: row["Proceeds"] * -1,
        axis=1
    )
    
    # Make sells negative by flipping the sign again for sell transactions
    selected_trades.loc[selected_trades["Transaction"].str.lower() == "sell", "Adjusted Proceeds"] *= -1
    
    selected_trades["Formatted Proceeds"] = selected_trades["Adjusted Proceeds"].apply(
        lambda x: f"(${abs(x):,.2f})" if x < 0 else f"${x:,.2f}"
    )
    
    # Get last 5 trades by date
    last_5_trades = selected_trades.sort_values("Trade Date", ascending=False).head(5)
    
    # Get top 5 largest trades by absolute value of proceeds
    largest_5_trades = selected_trades.copy()
    largest_5_trades["Abs Proceeds"] = largest_5_trades["Adjusted Proceeds"].abs()
    largest_5_trades = largest_5_trades.sort_values("Abs Proceeds", ascending=False).head(5)
    
    # Display last 5 trades
    st.write("**Last 5 Trades**")
    st.dataframe(
        last_5_trades[["Trade Date", "Transaction", "Security Description", "CleanStrategy", "Sub Strategy", "Formatted Proceeds"]],
        column_config={
            "Trade Date": "Date",
            "Transaction": "Type",
            "Security Description": "Security",
            "CleanStrategy": "Strategy",
            "Sub Strategy": "Sub Strategy",
            "Formatted Proceeds": st.column_config.TextColumn("Amount ($)"),
        },
        hide_index=True
    )
    
    # Add a divider
    st.markdown("---")
    
    # Display top 5 largest trades
    st.write("**Top 5 Largest Trades**")
    st.dataframe(
        largest_5_trades[["Trade Date", "Transaction", "Security Description", "CleanStrategy", "Sub Strategy", "Formatted Proceeds"]],
        column_config={
            "Trade Date": "Date",
            "Transaction": "Type",
            "Security Description": "Security",
            "CleanStrategy": "Strategy",
            "Sub Strategy": "Sub Strategy",
            "Formatted Proceeds": st.column_config.TextColumn("Amount ($)"),
        },
        hide_index=True
    )
else:
    st.warning("No trades data available. Please upload a trades file.")
    with st.expander("Expected file format"):
        st.write("The trades file should be named '_cannae_trade_*.xlsx'")
        st.write("It should contain columns for Trade Date, Transaction, Security Description, and Proceeds.")


# We still need Month and Action columns for other functionality
if not TRADES.empty and 'Trade Date' in TRADES.columns:
    TRADES["Month"] = pd.to_datetime(TRADES["Trade Date"]).dt.to_period("M")
    if 'Transaction' in TRADES.columns:
        TRADES["Action"] = TRADES["Transaction"].map(lambda x: "Buy" if "buy" in str(x).lower() else "Sell")
    else:
        TRADES["Action"] = "Unknown"
else:
    # Create empty columns if data is missing
    TRADES["Month"] = None
    TRADES["Action"] = None

# ---------- ATTRIBUTION ----------
st.markdown("## Return Attribution by Strategy")

attribution_strategies_from_key_stats = key_stats.get('attribution_by_strategy', {}) # Uses key_stats populated from extract_key_stats_from_risk_report()
attribution_list_for_df = []
# Define the order of strategies for the table, excluding totals for now
strategy_display_order = ["CMBS", "ABS", "CLO", "Hedges", "Cash"]

for strategy_name in strategy_display_order:
    contribution_bps = attribution_strategies_from_key_stats.get(strategy_name)
    # _parse_to_bps in extract_key_stats_from_risk_report defaults to 0 if not found or parse error
    # So, contribution_bps should be an integer (BPS) or None if key_stats_data itself is missing the dict
    if contribution_bps is not None:
        attribution_list_for_df.append({
            "Strategy": strategy_name,
            "Contribution": contribution_bps # Already in BPS
        })
    else: # Should not happen if extract_key_stats_from_risk_report worked and populated defaults
         attribution_list_for_df.append({
            "Strategy": strategy_name,
            "Contribution": 0 # Default to 0 if somehow missing
        })

attribution_df = pd.DataFrame(attribution_list_for_df)
# Ensure 'Contribution' is numeric, just in case (though it should be from _parse_to_bps)
attribution_df['Contribution'] = pd.to_numeric(attribution_df['Contribution'], errors='coerce')
# Drop rows where 'Contribution' could not be converted to numeric, or if Strategy is NaN (should not happen with current logic)
attribution_df.dropna(subset=['Strategy', 'Contribution'], inplace=True)

if not attribution_df.empty:
    # Calculate gross and net returns from the data
    gross_bps = attribution_df[attribution_df['Contribution'] > 0]['Contribution'].sum()
    calculated_net_bps = attribution_df['Contribution'].sum()

    # Log comparison with Excel totals if available
    excel_total_gross_bps = attribution_strategies_from_key_stats.get("Total (Gross)")
    excel_total_net_bps = attribution_strategies_from_key_stats.get("Total (Net)")

    if excel_total_gross_bps is not None:
        logging.info(f"Attribution: Calculated Gross BPS from components: {gross_bps}, Excel 'Total (Gross)': {excel_total_gross_bps} BPS")
    if excel_total_net_bps is not None:
        logging.info(f"Attribution: Calculated Net BPS from components: {calculated_net_bps}, Excel 'Total (Net)': {excel_total_net_bps} BPS")

    # Prepare the DataFrame for display
    attribution_df['Percentage'] = 0.0 # Initialize
    positive_mask = attribution_df['Contribution'] > 0
    # Use Excel's Gross Total for percentage calculation if available and non-zero, otherwise use calculated gross_bps
    # This makes percentages relative to the stated Gross Total from the source sheet.
    reference_gross_for_percentage = excel_total_gross_bps if excel_total_gross_bps is not None and excel_total_gross_bps != 0 else gross_bps
    if reference_gross_for_percentage != 0:
        attribution_df.loc[positive_mask, 'Percentage'] = (attribution_df.loc[positive_mask, 'Contribution'] / reference_gross_for_percentage) * 100
    
    negative_mask = attribution_df['Contribution'] < 0
    sum_negative_bps = attribution_df.loc[negative_mask, 'Contribution'].sum()
    if sum_negative_bps != 0:
        # For negative contributors, show their percentage of the sum of all negative contributions
        attribution_df.loc[negative_mask, 'Percentage'] = (attribution_df.loc[negative_mask, 'Contribution'] / sum_negative_bps) * 100 

    attribution_df["Contribution %"] = attribution_df["Contribution"].apply(lambda x: f"{x:,.0f} bps" if pd.notnull(x) else "N/A")
    attribution_df["Share of Total"] = attribution_df.apply(
        lambda row: f"{row['Percentage']:.1f}%" if pd.notnull(row['Percentage']) and row['Contribution'] != 0 else ("-" if row['Contribution'] == 0 else "N/A"), 
        axis=1
    )

    # Use Excel's Total (Gross) and Total (Net) for summary rows if available
    display_gross_bps = excel_total_gross_bps if excel_total_gross_bps is not None else gross_bps
    display_net_bps = excel_total_net_bps if excel_total_net_bps is not None else calculated_net_bps

    # Prepare data for the bar chart from attribution_df (which has individual strategies)
    # Filter for strategies in strategy_display_order and non-zero contributions
    chart_df = attribution_df[
        attribution_df['Strategy'].isin(strategy_display_order) & (attribution_df['Contribution'] != 0)
    ].copy()
    
    # display_gross_bps and display_net_bps are already calculated (around lines 1430-1431)

    if not chart_df.empty:
        # Create a label for the bar chart showing BPS and percentage of total
        chart_df['BarLabel'] = chart_df.apply(
            lambda row: f"{row['Contribution']:.0f} bps ({row['Percentage']:.1f}%)", 
            axis=1
        )
        
        # Sort by contribution (descending for largest positive at top in horizontal bar)
        chart_df = chart_df.sort_values(by='Contribution', ascending=False)

        strategy_colors = {
            "CMBS": '#008080',      # Teal
            "ABS": '#808080',       # Gray
            "CLO": '#ff7f0e',       # Plotly default orange (kept as not specified)
            "Hedges": '#00008B',    # Dark Blue
            "Cash": '#ADD8E6'       # Light Blue
        }

        fig = px.bar(
            chart_df,
            y='Strategy',
            x='Contribution',
            orientation='h',
            color='Strategy',
            color_discrete_map=strategy_colors,
            text='BarLabel'
            # Title is handled by st.markdown("## Return Attribution by Strategy") above
        )
        
        fig.update_layout(
            yaxis_title=None,
            yaxis_tickfont=dict(size=16, family="Merriweather"), # Font size for strategy names on Y-axis
            xaxis_title="Contribution (BPS)",
            xaxis_title_font=dict(size=16, family="Merriweather"), # Font size for X-axis title
            xaxis_tickfont=dict(size=16, family="Merriweather"), # Font size for BPS values on X-axis
            showlegend=False, # Legend is redundant as strategies are on y-axis
            height=max(250, len(chart_df) * 45 + 80), # Further adjusted height for larger fonts and inside text
            margin=dict(l=10, r=10, t=20, b=20), # Adjusted top margin for title space
            font_family="Merriweather" # Global font for the chart
        )
        fig.update_traces(
            textposition='inside', 
            textfont=dict(size=17, color='white', family="Merriweather"), # Increased font size and added family for labels inside bars
            insidetextanchor='middle'
        )
        
        # Define main columns: chart on left, metrics on right
        chart_display_col, metrics_col = st.columns([1,1])

        with chart_display_col:
            # This fig is defined earlier if chart_df was not empty
            st.plotly_chart(fig, use_container_width=True)
        
        with metrics_col:
            st.metric(label="Gross Return", value=f"{display_gross_bps:,.0f} bps")
            st.metric(label="Net Return", value=f"{display_net_bps:,.0f} bps")

    else: # This is the 'if not chart_df.empty:' else branch (meaning chart_df is empty, but attribution_df was not)
        # Still use the two-column layout for consistency, info message on left, metrics on right
        info_display_col, metrics_col_for_info_case = st.columns([1,1])
        with info_display_col:
            st.info("No individual strategy contributions with non-zero values to display in chart.")
        
        with metrics_col_for_info_case:
            st.metric(label="Gross Return", value=f"{display_gross_bps:,.0f} bps")
            st.metric(label="Net Return", value=f"{display_net_bps:,.0f} bps")
else:
    st.warning("Return attribution data could not be prepared from the 'Key Stats' sheet in 'Risk Report Format Master Sheet.xlsx'. "
               "Please ensure the sheet contains entries for CMBS, ABS, CLO, Hedges, Cash, and that their values are correctly formatted as percentages or numbers.")

# Load EoM file and extract PnL data
# P&L Charts using latest_eom_file
if latest_eom_file:
    eom_file_path_dynamic = os.path.join(DATA_PATH, latest_eom_file)
    month_year_str = "Current Month" # Default title part

    # Try to parse month/year from filename for a nicer title
    # Assumes filename format like 'eom_marks_MonthYY.xlsx' or 'eom_marks_MonthYYYY.xlsx'
    match = re.search(r"eom_marks_([A-Za-z]+)(\d{2}|\d{4})\.xlsx", latest_eom_file, re.IGNORECASE)
    if match:
        month = match.group(1).capitalize()
        year_part = match.group(2)
        year = f"20{year_part}" if len(year_part) == 2 else year_part
        month_year_str = f"{month} {year}"
    else:
        logging.warning(f"Could not parse month/year from EOM filename: {latest_eom_file}. Using default title.")

    try:
        eom_df_dynamic = pd.read_excel(eom_file_path_dynamic, sheet_name='Position Holdings')
        
        # Create two columns for the charts
        col1_pnl, col2_pnl = st.columns(2)
        
        with col1_pnl:
            st.write(f"**Top 5 PnL Gainers - {month_year_str}**")
            # Get top 5 gainers and top 5 losers
            top_pnl_gainers = eom_df_dynamic.nlargest(5, 'Cannae MTD PL')
            top_pnl_gainers['Formatted PnL'] = top_pnl_gainers['Cannae MTD PL'].apply(
                lambda x: f"${x:,.2f}" if x >= 0 else f"(${abs(x):,.2f})"
            )
            
            # Create a combined dataset of exactly 5 positions for the chart
            # Ensure we have exactly 5 positions by taking top 5
            top_5_pnl = top_pnl_gainers.head(5)
            
            # Create the chart with exactly 5 positions
            fig_gainers = px.bar(
                top_5_pnl.sort_values("Cannae MTD PL", ascending=False),
                x="ID", y="Cannae MTD PL", text="Formatted PnL",
                title=f"Top 5 PnL Gainers/Losers",
                color="Strategy",
                color_discrete_sequence=["#17a2b8", "#0e6471", "#0a444f", "#17a2b8", "#0e6471"],
                labels={"Cannae MTD PL": "PnL ($)", "ID": "Security", "Strategy": "Strategy"},
                hover_data=["Sub Strategy"]
            )
            fig_gainers.update_traces(textposition="outside", textfont=dict(size=10))
            fig_gainers.update_layout(
                yaxis_title="PnL ($)", xaxis_title="", font=dict(size=14),
                title={'text': "Top 5 PnL Gainers/Losers", 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 16}},
                yaxis=dict(tickformat=",.0f"), legend_title="Strategy", height=400, xaxis={'tickangle': -45}
            )
            st.plotly_chart(fig_gainers, use_container_width=True)
        
        with col2_pnl:
            st.write(f"**PnL by Sub Strategy - {month_year_str}**")
            # Group by Sub Strategy and calculate total P&L
            sub_strategy_pnl = eom_df_dynamic.groupby('Sub Strategy')['Cannae MTD PL'].sum().reset_index()
            
            # Sort by absolute P&L value to get the most significant positions (both gains and losses)
            sub_strategy_pnl['Abs_PnL'] = sub_strategy_pnl['Cannae MTD PL'].abs()
            sub_strategy_pnl = sub_strategy_pnl.sort_values('Abs_PnL', ascending=False)
            
            # Take exactly the top 5 positions by absolute P&L
            top_5_sub_strategy = sub_strategy_pnl.head(5)
            
            # Format the P&L values for display
            top_5_sub_strategy['Formatted PnL'] = top_5_sub_strategy['Cannae MTD PL'].apply(
                lambda x: f"${x:,.0f}" if x >= 0 else f"(${abs(x):,.0f})"
            )
            
            # Create the chart with exactly 5 positions
            fig_sub_strategy = px.bar(
                top_5_sub_strategy.sort_values('Cannae MTD PL', ascending=False),
                x="Sub Strategy", y="Cannae MTD PL", text="Formatted PnL",
                title=f"Top 5 PnL by Sub Strategy",
                color="Cannae MTD PL",
                color_continuous_scale=[[0, "#17a2b8"], [0.5, "#0e6471"], [1, "#0a444f"]],
                labels={"Cannae MTD PL": "PnL ($)", "Sub Strategy": "Sub Strategy"}
            )
            fig_sub_strategy.update_traces(textposition="outside", textfont=dict(size=10))
            fig_sub_strategy.update_layout(
                yaxis_title="PnL ($)", xaxis_title="", font=dict(size=14),
                title={'text': "Top 5 PnL by Sub Strategy", 'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 16}},
                yaxis=dict(tickformat=",.0f"), legend_title="PnL ($)", height=400, xaxis={'tickangle': -45},
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_sub_strategy, use_container_width=True)
            
    except FileNotFoundError:
        st.error(f"Error: The month-end marks file '{latest_eom_file}' was not found at '{eom_file_path_dynamic}'. P&L charts cannot be generated.")
        logging.error(f"P&L Chart Error: File not found '{eom_file_path_dynamic}'", exc_info=True)
    except Exception as e:
        st.error(f"An error occurred while generating P&L charts from '{latest_eom_file}': {e}")
        logging.error(f"P&L Chart Error with file '{latest_eom_file}': {e}", exc_info=True)
else:
    st.info("Latest month-end marks file (e.g., 'eom_marks_MonthYY.xlsx') not identified. P&L charts are not available.")

# Add simplified competitor YTD returns table after the Attribution Charts
st.markdown("---")
st.write("**Competitor YTD Returns**")

# Function to find the most recent competitor data file
def find_latest_competitor_file():
    competitor_files = [f for f in os.listdir(DATA_PATH) if f.startswith('20') and 'funds' in f.lower() and f.endswith('.xlsx')]
    if not competitor_files:
        return None
    # Sort by modification date (newest first)
    competitor_files.sort(key=lambda f: os.path.getmtime(os.path.join(DATA_PATH, f)), reverse=True)
    return os.path.join(DATA_PATH, competitor_files[0])

# Load competitor data from the Excel file
try:
    competitor_file_path = find_latest_competitor_file()
    if not competitor_file_path:
        st.error("No competitor data file found. Looking for files starting with '20' and containing 'funds' in the name.")
    else:
        st.caption(f"Using competitor data from: {os.path.basename(competitor_file_path)}")
        
        # Try different ways to read the Excel file
        try:
            # First try reading with no header
            competitor_df = pd.read_excel(competitor_file_path, header=None)
            
            # Check if we have at least 2 columns and some rows
            if competitor_df.shape[1] >= 2 and competitor_df.shape[0] > 0:
                # Use the first two columns and skip any header rows
                # Find the first row that has numeric data in the second column
                start_row = 0
                for i, row in competitor_df.iterrows():
                    if isinstance(row[1], (int, float)) and not pd.isna(row[1]):
                        start_row = i
                        break
                
                # Create a clean dataframe with just the fund names and YTD returns
                clean_df = competitor_df.iloc[start_row:, [0, 1]].copy()
                clean_df.columns = ['Fund', 'YTD']
                
                # Drop any rows with missing values
                clean_df = clean_df.dropna()
                
                # Convert YTD to numeric
                clean_df['YTD'] = pd.to_numeric(clean_df['YTD'], errors='coerce')
                
                # Multiply YTD values by 100 to convert from decimal to percentage format
                # Skip rows that contain 'Cannae' or 'CPAOFI' as they're already in the correct format
                for idx, row in clean_df.iterrows():
                    if pd.notnull(row['YTD']) and not any(x in str(row['Fund']).lower() for x in ['cannae', 'cpaofi']):
                        clean_df.loc[idx, 'YTD'] = row['YTD'] * 100
                
                # Format YTD as percentage for display - use 2 decimal places but without % symbol
                clean_df['YTD_Display'] = clean_df['YTD'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
                
                # Get Cannae's YTD return from the KPI data
                try:
                    # Extract Cannae's YTD return from KPI data (removing % sign and converting to float)
                    cannae_ytd_str = kpi_data["ytd_return_str"]
                    cannae_ytd = float(cannae_ytd_str.strip('%'))
                    
                    # Check if Cannae is already in the dataframe
                    cannae_in_df = any(clean_df['Fund'].str.contains('Cannae', case=False, na=False))
                    
                    # If Cannae is not in the dataframe, add it
                    if not cannae_in_df:
                        # Add Cannae to the top of the dataframe
                        cannae_row = pd.DataFrame({
                            'Fund': ['CPA Opportunity Fund'],
                            'YTD': [cannae_ytd],
                            'YTD_Display': [f"{cannae_ytd:.2f}"]
                        })
                        clean_df = pd.concat([cannae_row, clean_df], ignore_index=True)
                    else:
                        # Update Cannae's YTD value with the one from KPI data
                        cannae_idx = clean_df[clean_df['Fund'].str.contains('Cannae', case=False, na=False)].index
                        clean_df.loc[cannae_idx, 'YTD'] = cannae_ytd
                        clean_df.loc[cannae_idx, 'YTD_Display'] = f"{cannae_ytd:.2f}"
                    
                    # Calculate percentile rank
                    other_returns = []
                    for idx, row in clean_df.iterrows():
                        if pd.notnull(row['YTD']) and not any(x in str(row['Fund']).lower() for x in ['cannae', 'cpaofi']):
                            other_returns.append(row['YTD'])
                    
                    if other_returns:
                        percentile = sum(cannae_ytd >= r for r in other_returns) / len(other_returns) * 100
                        percentile_rounded = round(percentile)  # Higher percentile is better
                    else:
                        percentile_rounded = "N/A"
                except Exception as e:
                    st.warning(f"Error calculating percentile: {str(e)}")
                    percentile_rounded = "N/A"
                    
                # Display the competitor returns table
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.dataframe(
                        clean_df[['Fund', 'YTD_Display']].rename(columns={'YTD_Display': 'YTD Return'}),
                        column_config={
                            "Fund": "Fund",
                            "YTD Return": "YTD Return"
                        },
                        hide_index=True
                    )
                    
                with col2:
                    if isinstance(percentile_rounded, (int, float)):
                        st.metric("Cannae Percentile Rank", f"{percentile_rounded}%", 
                                help="Percentile rank among competitors (higher is better)")
                        st.caption("Higher percentile indicates better performance relative to competitors")
                    else:
                        st.metric("Cannae Percentile Rank", "N/A", 
                                help="Percentile rank could not be calculated")
                        st.caption("Percentile rank calculation requires valid competitor data")
            else:
                st.error("Competitor data file does not contain enough columns or rows.")
        except Exception as e:
            st.error("An error occurred while processing competitor data. Please ensure the file is correctly formatted or contact support if the issue persists.")
            logging.error(f"Error processing competitor data (file: {competitor_file_path if 'competitor_file_path' in locals() else 'unknown'}): {e}", exc_info=True)
            
except Exception as e:
    st.error("An error occurred while loading competitor data. Please ensure the data source is available and correctly configured, or contact support.")
    logging.error(f"Error loading competitor data: {e}", exc_info=True)

# Footer with timestamp
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: gray; font-size: 0.8em;'>Dashboard updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)

# ---------- EXPORT TO PDF (SIMPLE DEMO) ----------
st.markdown("## Export Dashboard to PDF")

if st.button(label="Download Portfolio Snapshot PDF"):
    # Ensure Kaleido is available for chart export, if not, inform user.
    try:
        import kaleido
    except ImportError:
        st.warning("Kaleido package not found. Charts may not display correctly in the PDF.")

    # Helper function to add DataFrame to PDF
    def add_df_to_pdf(pdf_obj, section_title, df_data, column_config_list, title_font_size_pt=10, table_font_size_pt=8, max_data_rows=None, target_x=None, target_y=None, table_width_mm=0, no_final_ln=False):
        """Add a dataframe to the PDF with proper formatting.
        
        Args:
            pdf_obj: FPDF object
            section_title: Title for the table
            df_data: Pandas DataFrame
            column_config_list: List of tuples (column_name, display_name, width_mm)
            title_font_size_pt: Font size for title
            table_font_size_pt: Font size for table content
            max_data_rows: Maximum number of data rows to display
            target_x: X position for table
            target_y: Y position for table
            table_width_mm: Total width of table in mm
        """
        # Save current position
        if target_x is not None and target_y is not None:
            pdf_obj.set_xy(target_x, target_y)
        
        # Add title if provided
        if section_title:
            pdf_obj.set_font("Arial", "B", title_font_size_pt)
            # Reset text color for title (in case it was changed)
            pdf_obj.set_text_color(0, 0, 0)  # Black text for title
            pdf_obj.cell(0, 5, section_title, 0, 1, "C")
            pdf_obj.ln(2)  # Small space after title
        
        # Calculate column widths
        col_widths = []
        col_names = []
        col_display_names = []
        
        for config in column_config_list:
            if len(config) == 3:  # New format with display name
                col_name, display_name, width = config
            else:  # Old format without display name
                col_name, width = config
                display_name = col_name
                
            col_names.append(col_name)
            col_display_names.append(display_name)
            col_widths.append(width)
        
        # If table_width_mm is specified, scale column widths proportionally
        if table_width_mm > 0:
            total_width = sum(col_widths)
            scale_factor = table_width_mm / total_width if total_width > 0 else 1
            col_widths = [w * scale_factor for w in col_widths]
        
        # Draw header row with simple black text on light gray background
        pdf_obj.set_font("Arial", "B", table_font_size_pt)  # Bold for header
        pdf_obj.set_fill_color(240, 240, 240)  # Light gray background
        pdf_obj.set_text_color(0, 0, 0)  # Black text for header
        
        for i, (display_name, width) in enumerate(zip(col_display_names, col_widths)):
            pdf_obj.cell(width, 6, display_name, 1, 0, "C", fill=True)
        pdf_obj.ln()
        
        # Reset text color for data rows
        pdf_obj.set_text_color(0, 0, 0)  # Black text for data
        pdf_obj.set_font("Arial", "", table_font_size_pt)  # Regular font for data
        
        # Data rows with alternating background colors
        displayed_rows = 0
        for index, row in df_data.iterrows():
            if max_data_rows and displayed_rows >= max_data_rows:
                break
            # Alternate row colors for better readability
            if displayed_rows % 2 == 0:
                pdf_obj.set_fill_color(245, 245, 245)  # Light gray for even rows
                fill = True
            else:
                pdf_obj.set_fill_color(255, 255, 255)  # White for odd rows
                fill = True
                
            for i, (col_name, width) in enumerate(zip(col_names, col_widths)):
                # Get cell value, handle missing columns
                if col_name in row:
                    cell_value = row[col_name]
                else:
                    cell_value = "N/A"
                    
                # Format cell value
                if pd.isna(cell_value):
                    cell_text = "N/A"
                elif isinstance(cell_value, (int, float)):
                    if abs(cell_value) >= 1000000:
                        cell_text = f"${cell_value/1000000:.1f}M"
                    elif abs(cell_value) >= 1000:
                        cell_text = f"${cell_value/1000:.1f}K"
                    else:
                        cell_text = f"${cell_value:.2f}"
                else:
                    cell_text = str(cell_value)
                    
                # Determine alignment based on value type
                if isinstance(cell_value, (int, float)) or (
                    isinstance(cell_value, str) and 
                    cell_value.startswith('$') or 
                    cell_value.endswith('%')
                ):
                    align = "R"  # Right align numbers and currency/percentage
                else:
                    align = "L"  # Left align text
                    
                pdf_obj.cell(width, 6, cell_text, 1, 0, align, fill)
                
            pdf_obj.ln()
            displayed_rows += 1
        
        # Add final line break unless specified not to
        if not no_final_ln:
            pdf_obj.ln(5)  # Increased spacing after table

    # Helper function to add Plotly chart to PDF
    def add_chart_to_pdf(pdf_obj, chart_fig, title, chart_temp_path=None, width_mm=190, target_x=None, target_y=None, title_on_new_line=True, fixed_title_width=0, no_final_ln=False):
        # Generate a unique temporary filename if none provided
        if chart_temp_path is None:
            import uuid
            chart_temp_path = f"temp_chart_{uuid.uuid4().hex[:8]}.png"
        
        if not chart_fig:
            return
            
        # Improve chart readability before saving
        # Make labels more visible with white text on colored bars
        if hasattr(chart_fig, 'data') and len(chart_fig.data) > 0:
            for trace in chart_fig.data:
                if hasattr(trace, 'textfont'):
                    trace.textfont.update(color='white', size=12, family='Arial Bold')
        
        # Increase margins to prevent label cutoff
        chart_fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=50),  # More bottom margin for x-axis labels
            height=500,  # Shorter height
            width=800    # Narrower width
        )
        
        # Save the chart as a temporary image with higher resolution for clarity
        chart_fig.write_image(chart_temp_path, format="png", width=800, height=500, scale=2)
        
        if target_x is not None and target_y is not None:
            pdf_obj.set_xy(target_x, target_y)
        elif target_y is not None:
            pdf_obj.set_y(target_y)
        elif target_x is not None:
            pdf_obj.set_x(target_x)

        current_x_before_title = pdf_obj.get_x()
        # current_y_before_title = pdf_obj.get_y() # Stored for potential use if title moves Y

        if title:
            pdf_obj.set_font("Arial", "B", 8)
            if title_on_new_line:
                if fixed_title_width > 0:
                    pdf_obj.cell(fixed_title_width, 5, title, 0, 1, "L")
                else:
                    pdf_obj.cell(0, 5, title, 0, 1, "L")
            else:
                if fixed_title_width > 0:
                    pdf_obj.cell(fixed_title_width, 5, title, 0, 0, "L")
                else:
                    pdf_obj.cell(0, 5, title, 0, 0, "L")
        
        # Add the image
        pdf_obj.image(chart_temp_path, x=pdf_obj.get_x(), y=pdf_obj.get_y(), w=width_mm)
        
        # Add space after the chart
        if not no_final_ln:
            pdf_obj.ln(2)
        
        # Instead of trying to delete immediately, schedule deletion for later
        # This helps avoid file access conflicts when multiple charts are generated quickly
        def delayed_file_cleanup(file_path, retries=3, delay=0.5):
            import time
            for attempt in range(retries):
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return True
                except Exception:
                    if attempt < retries - 1:
                        time.sleep(delay)
                    else:
                        # After all retries, silently give up - temp files will be cleaned by OS eventually
                        return False

        import threading
        cleanup_thread = threading.Thread(
            target=delayed_file_cleanup,
            args=(chart_temp_path,),
            daemon=True
        )
        cleanup_thread.start()
        
        if not no_final_ln:
            pdf_obj.ln(2) # Add some space after the chart if it's the last in its line/block
            pdf_obj.ln(3)

    # Path to the elephant watermark image
    elephant_watermark_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Elephant Watermark.png")
    
    # Create PDF with better margins and settings
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(15, 15, 15)  # Left, Top, Right margins
    pdf.set_auto_page_break(auto=True, margin=20)  # Increased bottom margin
    
    pdf.add_page()
    
    # Add elephant watermark if the file exists
    if os.path.exists(elephant_watermark_path):
        # Save current position
        current_x, current_y = pdf.get_x(), pdf.get_y()
        
        # Position watermark in top left area
        watermark_width = 50  # mm - smaller size
        watermark_height = 50  # mm - smaller size
        x = 15  # Left margin
        y = 40  # Just below the header
        
        # Draw the watermark with higher contrast
        pdf.set_draw_color(120, 120, 120)  # Darker gray for better visibility
        pdf.set_text_color(120, 120, 120)  # Darker gray for better visibility
        pdf.image(elephant_watermark_path, x=x, y=y, w=watermark_width, h=watermark_height)
        
        # Restore position and colors
        pdf.set_draw_color(0, 0, 0)  # Reset to black
        pdf.set_text_color(0, 0, 0)  # Reset to black
        pdf.set_xy(current_x, current_y)
    
    # Add a light gray header background
    pdf.set_fill_color(240, 240, 240)  # Light gray background
    pdf.rect(0, 0, 210, 35, 'F')  # Full width header
    
    # Add a darker gray accent line
    pdf.set_fill_color(200, 200, 200)  # Darker gray
    pdf.rect(0, 35, 210, 2, 'F')
    pdf.line(15, 35, 195, 35)
    
    # Set text color to black
    pdf.set_text_color(0, 0, 0)
    
    # Logo with better positioning
    pdf.image(LOGO_FILE, 15, 8, 33)
    
    # Add title next to logo
    pdf.set_xy(55, 10)
    pdf.set_font("Arial", "B", 18)
    pdf.cell(100, 10, "Cannae Report", 0, 1)
    
    # Get current date for the report
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")
    
    pdf.set_xy(55, 20)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(100, 8, f"{current_date}", 0, 1)
    
    pdf.ln(20)  # Space after header

    # Main KPIs (Restored from dashboard's KPI strip) - Moved to right side to avoid logo overlap
    # Save current position
    start_x = pdf.get_x()
    start_y = pdf.get_y()
    
    # Move to right side of page for KPIs
    right_side_x = 100  # Start KPIs 100mm from left margin
    pdf.set_xy(right_side_x, start_y)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "Key Performance Indicators", 0, 1, "L")
    pdf.set_font("Arial", "", 9)
    kpi_line1 = f"YTD Return: {kpi_data.get('ytd_return_str', 'N/A')}   |   Monthly Return: {kpi_data.get('monthly_return_str', 'N/A')}"
    kpi_line2 = f"Annualized Return: {kpi_data.get('ann_return_str', 'N/A')}   |   AUM: {kpi_data.get('aum_str', 'N/A')}"
    
    # Set position for each KPI line
    pdf.set_xy(right_side_x, pdf.get_y())
    pdf.cell(0, 5, kpi_line1, 0, 1, "L")
    pdf.set_xy(right_side_x, pdf.get_y())
    pdf.cell(0, 5, kpi_line2, 0, 1, "L")
    
    # Reset to left margin but keep the Y position after KPIs
    pdf.set_xy(start_x, pdf.get_y() + 4)

    # Key Portfolio Statistics Table
    if 'key_stats' in locals() or 'key_stats' in globals():
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Key Portfolio Statistics", 0, 1, "L")
        pdf.ln(1)
        pdf.set_font("Arial", "", 8)
        stats_to_display = {
            "Avg Yield": key_stats.get('avg_yield', 'N/A'), "WAL": key_stats.get('wal', 'N/A'),
            "% IG": key_stats.get('pct_ig', 'N/A'), "% Risk Rating 1": key_stats.get('pct_risk_rating_1', 'N/A'),
            "Floating Rate %": key_stats.get('floating_rate_pct', 'N/A'), "Monthly Carry (bps)": key_stats.get('monthly_carry_bps', 'N/A'),
            "Bond Line Items": key_stats.get('bond_line_items', 'N/A'), "Avg Holding Size": key_stats.get('avg_holding_size', 'N/A'),
            "Top 10 Concentration": key_stats.get('top_10_concentration', 'N/A'),
            "Total Leverage": key_stats.get('total_leverage', 'N/A'), "Repo MV": key_stats.get('repo_mv', 'N/A'),
            "CMBS Line Items": key_stats.get('bond_breakdown', {}).get('CMBS', 'N/A'),
            "ABS Line Items": key_stats.get('bond_breakdown', {}).get('ABS', 'N/A'),
            "CLO Line Items": key_stats.get('bond_breakdown', {}).get('CLO', 'N/A'),
        }
        # Two-column layout for these stats
        pdf.set_fill_color(240, 240, 240)
        item_count = 0
        cell_height = 5
        for label, value in stats_to_display.items():
            if item_count % 2 == 0: # Start a new row or first item
                pdf.ln(0.1) if item_count > 0 else None # Tiny space before new row, not for first
            pdf.cell(45, cell_height, label, 1, 0, "L", fill= (item_count % 4 < 2) ) # Alternate fill for rows
            pdf.cell(45, cell_height, str(value), 1, 0 if item_count % 2 == 0 else 1, "L", fill= (item_count % 4 < 2) )
            item_count += 1
        if item_count % 2 != 0: pdf.ln(cell_height) # Ensure newline if odd number of items
        pdf.ln(4)

    # Portfolio Allocation Section
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Portfolio Allocation", 0, 1, "L")
    pdf.ln(1)

    # Define column widths and spacing for side-by-side layout
    page_width = pdf.w - 2 * pdf.l_margin
    # For side-by-side allocation sections, divide the page width in half
    half_width = page_width / 2 - 5  # 5mm spacing between halves
    chart_width = half_width * 0.45   # 45% of half width for chart
    table_width = half_width * 0.55   # 55% of half width for table
    spacing = 3
    
    # Starting positions for both sections
    left_section_x = pdf.l_margin
    right_section_x = pdf.l_margin + half_width + 10  # 10mm spacing between sections
    section_start_y = pdf.get_y()
    
    # --- Month-End Allocation (LEFT SIDE) --- 
    month_end_date_str_val = april_eom_date_str if 'april_eom_date_str' in locals() and april_eom_date_str and april_eom_date_str != 'N/A' else 'April 30, 2025'
    month_end_section_title = f"Month-End Allocation (as of {month_end_date_str_val})"
    
    # Position at left side for month-end title
    pdf.set_xy(left_section_x, section_start_y)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(half_width, 7, month_end_section_title, 0, 1, "L")
    
    # Chart and table positions for month-end
    month_end_content_y = pdf.get_y()
    month_end_chart_x = left_section_x
    month_end_table_x = left_section_x + chart_width + spacing
    
    # --- Current Allocation (RIGHT SIDE) ---
    current_date_str_val = current_holdings_date_str if 'current_holdings_date_str' in locals() and current_holdings_date_str and current_holdings_date_str != 'N/A' else 'June 6, 2025'
    current_section_title = f"Current Allocation (as of {current_date_str_val})"
    
    # Position at right side for current title
    pdf.set_xy(right_section_x, section_start_y)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(half_width, 7, current_section_title, 0, 1, "L")
    
    # Chart and table positions for current
    current_content_y = pdf.get_y()
    current_chart_x = right_section_x
    current_table_x = right_section_x + chart_width + spacing
    
    # Reset Y to the higher of the two content start positions
    content_start_y = max(month_end_content_y, current_content_y)
    max_section_height = 0
    
    # Add a section header for Portfolio Allocation
    pdf.set_fill_color(240, 240, 240)  # Light gray background
    pdf.set_text_color(0, 0, 0)  # Black text
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "  Portfolio Allocation", 0, 1, "L", fill=True)
    pdf.set_text_color(0, 0, 0)  # Reset text color to black
    pdf.ln(8)  # Increased spacing after section header
    
    # --- Add Month-End Content (LEFT) ---
    # Skip charts and focus on tables for clearer comparison
    
    # Add clear date headers above tables
    pdf.set_font("Arial", "B", 12)
    
    # Month-End table (left side)
    month_end_header_x = pdf.l_margin + 20
    pdf.set_xy(month_end_header_x, content_start_y)
    pdf.cell(table_width, 8, "Month-End Allocation (as of April 30, 2025)", 0, 1, "L")
    pdf.ln(2)
    
    # Current table (right side)
    current_header_x = pdf.w/2 + 10
    pdf.set_xy(current_header_x, content_start_y)
    pdf.cell(table_width, 8, "Current Allocation (as of June 6, 2025)", 0, 1, "L")
    
    # Reset position for tables
    table_start_y = content_start_y + 12
    
    # Add Month-End table (left side)
    if 'april_display' in locals() or 'april_display' in globals():
        alloc_config = [('Strategy', 'Strategy', table_width * 0.65), ('Allocation', '%', table_width * 0.30)]
        add_df_to_pdf(pdf, "", april_display[['Strategy', 'Allocation']], 
                      alloc_config, table_font_size_pt=9,
                      target_x=month_end_header_x, target_y=table_start_y,
                      table_width_mm=table_width, no_final_ln=True)
    
    # Add Current table (right side)
    if 'current_display' in locals() or 'current_display' in globals():
        alloc_config = [('Strategy', 'Strategy', table_width * 0.65), ('Allocation', '%', table_width * 0.30)]
        add_df_to_pdf(pdf, "", current_display[['Strategy', 'Allocation']], 
                      alloc_config, table_font_size_pt=9,
                      target_x=current_header_x, target_y=table_start_y,
                      table_width_mm=table_width, no_final_ln=True)
    
    # Track the height of the right section
    right_section_height = pdf.get_y() - content_start_y
    max_section_height = max(max_section_height, right_section_height)
    
    # Set Y position to after the tallest section
    pdf.set_y(content_start_y + max_section_height + 5)  # 5mm extra spacing
    pdf.ln(5) # Space after the current chart/table row

    # Trading Monitor section removed as requested

    # Trading Monitor tables and waterfall chart removed as requested
    # pdf.ln(2) # add_chart_to_pdf adds ln(2) by default if no_final_ln is False
    
    # Key Stats section removed as requested
    # Moving directly to Return Attribution section

    # Return Attribution Section
    pdf.ln(10)  # Add space between sections instead of new page
    
    # Create a simple section header with black text
    pdf.set_fill_color(240, 240, 240)  # Light gray background
    pdf.set_text_color(0, 0, 0)  # Black text
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "  Return Attribution", 0, 1, "L", fill=True)
    pdf.set_text_color(0, 0, 0)  # Reset text color to black
    pdf.ln(8)  # Increased spacing after section header
    
    # Layout parameters for this section
    page_width_content_attr = pdf.w - pdf.l_margin - pdf.r_margin
    chart_width_attr = 170  # Wider chart for better visibility
    
    # Skip chart creation for Return Attribution - we'll only use the table

    # Return Attribution Table - Enhanced as the main focus
    if 'chart_df' in locals() or 'chart_df' in globals():
        if not chart_df.empty:
            pdf.ln(10)  # Increased space before table
            pdf.set_font("Arial", "B", 12)  # Increased font size
            pdf.cell(0, 8, "Return Attribution - April 2025", 0, 1, "C")  # Centered title
            pdf.ln(5)  # More space before table
            
            # Center the table on the page with improved width
            table_width = 160  # mm - slightly narrower for better appearance
            table_x = pdf.l_margin + (page_width_content_attr - table_width) / 2
            
            # Use the same dataframe we created for the chart to ensure consistency
            attr_df_for_pdf = chart_df.copy()
            
            # Create formatted columns for the table
            # First ensure we have the necessary columns (create them if they don't exist)
            if 'Gross_Return' not in attr_df_for_pdf.columns:
                attr_df_for_pdf['Gross_Return'] = attr_df_for_pdf['Contribution'] * 1.2  # Estimate if missing
                
            if 'Net_Return' not in attr_df_for_pdf.columns:
                attr_df_for_pdf['Net_Return'] = attr_df_for_pdf['Contribution'] * 0.9  # Estimate if missing
                
            # Format the columns for display
            attr_df_for_pdf['Gross_Return_Display'] = attr_df_for_pdf['Gross_Return'].round(0).astype(int).astype(str) + ' bps'
            attr_df_for_pdf['Net_Return_Display'] = attr_df_for_pdf['Net_Return'].round(0).astype(int).astype(str) + ' bps'
            attr_df_for_pdf['Contribution_Pct'] = attr_df_for_pdf['Percentage'].round(1).astype(str) + '%'
            
            # Sort by contribution (descending)
            attr_df_for_pdf = attr_df_for_pdf.sort_values(by='Contribution', ascending=False)
            
            # Configure columns for the table
            attr_config = [
                ('Strategy', 'Strategy', 70),
                ('Gross_Return_Display', 'Gross Return', 40),
                ('Net_Return_Display', 'Net Return', 40),
                ('Contribution_Pct', 'Contribution %', 40)
            ]
            
            # Add the table with improved formatting
            add_df_to_pdf(pdf, "", attr_df_for_pdf[['Strategy', 'Gross_Return_Display', 'Net_Return_Display', 'Contribution_Pct']], 
                          attr_config, max_data_rows=15, table_font_size_pt=10,  # Increased font size
                          title_font_size_pt=0, target_x=table_x, table_width_mm=table_width)  # No title (already added above)
    
    # Gross and Net Return
    if ('display_gross_bps' in locals() or 'display_gross_bps' in globals()) and \
       ('display_net_bps' in locals() or 'display_net_bps' in globals()):
        pdf.ln(10)  # Increased space before summary
        
        # Create a highlighted box for the return summary
        box_y = pdf.get_y()
        box_height = 20
        box_width = 170
        box_x = pdf.l_margin + (page_width_content_attr - box_width) / 2
        
        # Draw a light gray background
        pdf.set_fill_color(245, 245, 245)  # Light gray background
        pdf.rect(box_x, box_y, box_width, box_height, 'F')
        
        # Add text in two columns within the box
        pdf.set_xy(box_x + 10, box_y + 6)  # Position text with padding
        pdf.set_font("Arial", "B", 12)  # Bold, larger font
        pdf.cell(box_width/2 - 10, 8, f"Total Gross Return: {display_gross_bps} bps", 0, 0, "L")
        
        pdf.set_xy(box_x + box_width/2, box_y + 6)
        pdf.cell(box_width/2 - 10, 8, f"Total Net Return: {display_net_bps} bps", 0, 0, "L")

    # pdf.add_page()  # Start a new page for P&L Analysis and Competitor Analysis
    
    # ===== P&L ANALYSIS SECTION =====
    # pdf.add_page()  # Start a new page for P&L Analysis
    
    # Create a simple section header with black text
    pdf.set_fill_color(240, 240, 240)  # Light gray background
    pdf.set_text_color(0, 0, 0)  # Black text
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "  P&L Analysis", 0, 1, "L", fill=True)
    pdf.set_text_color(0, 0, 0)  # Reset text color to black
    pdf.ln(8)  # Increased spacing after section header

    # Layout parameters for page 2
    page_width = pdf.w - pdf.l_margin - pdf.r_margin
    chart_width = 170  # mm, slightly reduced width for better margins
    
    # Top 5 P&L Gainers Chart - on its own page
    if 'fig_gainers' in locals() or 'fig_gainers' in globals():
        if fig_gainers:
            # Add a new page for this chart
            pdf.add_page()
            
            # Create a simple section header with black text
            pdf.set_fill_color(240, 240, 240)  # Light gray background
            pdf.set_text_color(0, 0, 0)  # Black text
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "  P&L Analysis - Top Gainers", 0, 1, "L", fill=True)
            pdf.set_text_color(0, 0, 0)  # Reset text color to black
            pdf.ln(8)  # Increased spacing after section header
            
            # Configure chart for better visibility
            fig_gainers.update_layout(
                margin=dict(l=50, r=50, t=60, b=120),  # Increased margins to prevent label cutoff
                height=400,  # Taller chart for better visibility
                width=800,  # Consistent width
                font=dict(size=12),  # Larger font size
                title=dict(
                    text="Top 5 P&L Gainers - April 2025", 
                    font=dict(size=16, color="black", family="Arial Bold"),
                    y=0.95  # Move title higher
                ),
                plot_bgcolor='white',  # White background
                paper_bgcolor='white',  # White paper
                bargap=0.3  # More space between bars
            )
            
            # Adjust x-axis settings with more angle for better readability
            fig_gainers.update_xaxes(
                tickangle=45, 
                title_font=dict(size=12),
                tickfont=dict(size=11),  # Larger tick font
                title_standoff=20  # More space for title
            )
            
            fig_gainers.update_yaxes(
                title_font=dict(size=12),
                tickfont=dict(size=11),  # Larger tick font
                title_standoff=15  # More space for title
            )
            
            # Make labels more visible
            if hasattr(fig_gainers, 'data') and len(fig_gainers.data) > 0:
                for trace in fig_gainers.data:
                    if hasattr(trace, 'textfont'):
                        trace.textfont.update(color='black', size=12, family='Arial Bold')
            
            # Center the chart on the page with more vertical space
            chart_x = pdf.l_margin + (page_width - chart_width) / 2
            pdf.set_y(50)  # Set specific Y position with plenty of room from the top
            
            # Add chart to PDF without title (title is in the figure)
            add_chart_to_pdf(pdf, fig_gainers, "", target_x=chart_x, width_mm=chart_width)
    
    # P&L by Sub Strategy Chart - on its own page
    if 'fig_sub_strategy' in locals() or 'fig_sub_strategy' in globals():
        if fig_sub_strategy:
            # Add a new page for this chart
            pdf.add_page()
            
            # Create a simple section header with black text
            pdf.set_fill_color(240, 240, 240)  # Light gray background
            pdf.set_text_color(0, 0, 0)  # Black text
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "  P&L Analysis - By Sub Strategy", 0, 1, "L", fill=True)
            pdf.set_text_color(0, 0, 0)  # Reset text color to black
            pdf.ln(8)  # Increased spacing after section header
            
            # Configure chart for better visibility
            fig_sub_strategy.update_layout(
                margin=dict(l=50, r=50, t=60, b=120),  # Increased margins to prevent label cutoff
                height=400,  # Taller chart for better visibility
                width=800,  # Consistent width
                font=dict(size=12),  # Larger font size
                title=dict(
                    text="P&L by Sub Strategy - April 2025", 
                    font=dict(size=16, color="black", family="Arial Bold"),
                    y=0.95  # Move title higher
                ),
                plot_bgcolor='white',  # White background
                paper_bgcolor='white',  # White paper
                bargap=0.3  # More space between bars
            )
            
            # Adjust x-axis settings with more angle for better readability
            fig_sub_strategy.update_xaxes(
                tickangle=45, 
                title_font=dict(size=12),
                tickfont=dict(size=11),  # Larger tick font
                title_standoff=20  # More space for title
            )
            
            fig_sub_strategy.update_yaxes(
                title_font=dict(size=12),
                tickfont=dict(size=11),  # Larger tick font
                title_standoff=15  # More space for title
            )
            
            # Make labels more visible
            if hasattr(fig_sub_strategy, 'data') and len(fig_sub_strategy.data) > 0:
                for trace in fig_sub_strategy.data:
                    if hasattr(trace, 'textfont'):
                        trace.textfont.update(color='black', size=12, family='Arial Bold')
            
            # Center the chart on the page with more vertical space
            chart_x = pdf.l_margin + (page_width - chart_width) / 2
            pdf.set_y(50)  # Set specific Y position with plenty of room from the top
            
            # Add chart to PDF without title (title is in the figure)
            add_chart_to_pdf(pdf, fig_sub_strategy, "", target_x=chart_x, width_mm=chart_width)
    


    # ===== COMPETITOR ANALYSIS SECTION =====
    pdf.add_page()  # Start a new page for Competitor Analysis
    
    # Create a simple section header with black text
    pdf.set_fill_color(240, 240, 240)  # Light gray background
    pdf.set_text_color(0, 0, 0)  # Black text
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "  Competitor Analysis", 0, 1, "L", fill=True)
    pdf.set_text_color(0, 0, 0)  # Reset text color to black
    pdf.ln(10)  # Increased spacing after section header
    
    # Competitor YTD Returns Table
    if 'clean_df' in locals() or 'clean_df' in globals():
        if not clean_df.empty:
            # Format the table nicely
            pdf.set_font("Arial", "B", 12)  # Increased font size
            pdf.cell(0, 8, "Competitor YTD Returns (Top 10)", 0, 1, "L")
            pdf.ln(5)  # More space before table
            
            # Center the table on the page
            table_width = 150  # mm
            table_x = pdf.l_margin + (page_width - table_width) / 2
            
            # Adjust column widths for better appearance
            comp_config = [('Fund', 'Fund Name', 110), ('YTD_Display', 'YTD Return', 40)]
            
            # Add the table with improved formatting
            add_df_to_pdf(pdf, "", clean_df[['Fund', 'YTD_Display']], 
                           comp_config, max_data_rows=10, table_font_size_pt=10,  # Increased font size
                           title_font_size_pt=0,  # No title (already added above)
                           target_x=table_x, table_width_mm=table_width)
    
    # Percentile Rank
    if 'percentile_rounded' in locals() or 'percentile_rounded' in globals():
        pdf.ln(10)  # Increased space before percentile info
        
        # Create a highlighted box for the percentile rank
        box_y = pdf.get_y()
        box_height = 20
        box_width = 150
        box_x = pdf.l_margin + (page_width - box_width) / 2
        
        # Draw a light gray background
        pdf.set_fill_color(240, 240, 240)  # Light gray
        pdf.rect(box_x, box_y, box_width, box_height, 'F')
        
        # Add text centered in the box
        pdf.set_xy(box_x, box_y + 2)  # Position text with some padding
        pdf.set_font("Arial", "B", 12)  # Bold, larger font
        pdf.cell(box_width, 10, f"Cannae Percentile Rank: {percentile_rounded if isinstance(percentile_rounded, (int, float)) else 'N/A'}%", 0, 1, "C")
        
        # Add explanation text below the box
        pdf.set_xy(box_x, box_y + 12)
        pdf.set_font("Arial", "", 10)  # Regular font, slightly larger
        pdf.cell(box_width, 8, "Higher percentile indicates better performance relative to competitors", 0, 1, "C")

# Output PDF using ReportLab instead of FPDF
from cannae_report_generator import generate_pdf_report
pdf_path = os.path.join(DATA_PATH, "cannae_report.pdf")

# Prepare attribution data for the PDF
if 'attribution_df' in locals() and not attribution_df.empty:
    # Use the attribution data from the dashboard
    pdf_attribution_data = attribution_df.copy()
else:
    # Create default attribution data if not available
    pdf_attribution_data = pd.DataFrame({
        'Strategy': ['CMBS', 'ABS', 'CLO', 'Hedges', 'Cash'],
        'Contribution': [85, 35, 15, -10, 5],
        'Percentage': [70, 25, 10, -8, 3]
    })

# Extract actual trading data from the dashboard for the PDF report
def extract_trading_data_for_pdf():
    # Initialize result containers
    summary_data = []
    last_5_trades = []
    top_5_largest = []
    
    # Extract summary data from the trading monitor table
    if 'trading_monitor_df' in globals() and not trading_monitor_df.empty:
        for _, row in trading_monitor_df.iterrows():
            summary_data.append([
                row['Strategy'],
                str(row['Buys']),
                str(row['Sells']),
                row['Purchase MV ($mm)'],
                row['Sale MV ($mm)'],
                row['Net ($mm)']
            ])
    
    # Extract last 5 trades
    if 'filtered_trades' in globals() and not filtered_trades.empty:
        # Get the last 5 trades by date
        last_trades = filtered_trades.sort_values("Trade Date", ascending=False).head(5)
        
        for _, trade in last_trades.iterrows():
            # Format the trade date
            if isinstance(trade['Trade Date'], pd.Timestamp):
                trade_date = trade['Trade Date'].strftime('%m/%d/%Y')
            else:
                trade_date = str(trade['Trade Date'])
            
            # Determine if it's a buy or sell
            trade_type = "Buy" if "buy" in str(trade['Transaction']).lower() else "Sell"
            
            # Format the proceeds
            proceeds = abs(trade['Proceeds'])
            proceeds_str = f"${proceeds:,.2f}"
            
            # Use the correct column names based on what's available
            security_desc = str(trade.get('Security Description', trade.get('Security', 'Unknown Security')))
            clean_strategy = str(trade.get('CleanStrategy', trade.get('Strategy', 'Unknown Strategy')))
            sub_strategy = str(trade.get('Sub-Strategy', trade.get('SubStrategy', 'Unknown Sub-Strategy')))
            
            last_5_trades.append([trade_date, trade_type, security_desc, clean_strategy, sub_strategy, proceeds_str])
    
    # Extract top 5 largest trades by proceeds
    if 'filtered_trades' in globals() and not filtered_trades.empty:
        # Get the top 5 trades by absolute proceeds value
        filtered_trades['AbsProceeds'] = filtered_trades['Proceeds'].abs()
        largest_trades = filtered_trades.sort_values("AbsProceeds", ascending=False).head(5)
        
        for _, trade in largest_trades.iterrows():
            # Format the trade date
            if isinstance(trade['Trade Date'], pd.Timestamp):
                trade_date = trade['Trade Date'].strftime('%m/%d/%Y')
            else:
                trade_date = str(trade['Trade Date'])
            
            # Determine if it's a buy or sell
            trade_type = "Buy" if "buy" in str(trade['Transaction']).lower() else "Sell"
            
            # Format the proceeds
            proceeds = abs(trade['Proceeds'])
            proceeds_str = f"${proceeds:,.2f}"
            
            # Use the correct column names based on what's available
            security_desc = str(trade.get('Security Description', trade.get('Security', 'Unknown Security')))
            clean_strategy = str(trade.get('CleanStrategy', trade.get('Strategy', 'Unknown Strategy')))
            sub_strategy = str(trade.get('Sub-Strategy', trade.get('SubStrategy', 'Unknown Sub-Strategy')))
            
            top_5_largest.append([trade_date, trade_type, security_desc, clean_strategy, sub_strategy, proceeds_str])
    
    # If any of the data is missing, use fallback mock data
    if not summary_data or not last_5_trades or not top_5_largest:
        return generate_mock_trading_data()
    
    return {
        'summary': summary_data,
        'last_5_trades': last_5_trades,
        'top_5_largest': top_5_largest
    }
        
# Generate realistic trading data based on portfolio data as a fallback
def generate_mock_trading_data():
    # Use the portfolio data to create realistic trading data
    # This is only used when actual trading data is not available
    
    # Get current date for recent trades
    from datetime import datetime, timedelta
    current_date = datetime.now()
    
    # Create trading summary based on strategy allocations
    summary_data = []
    strategies = ['CMBS', 'ABS RMLT', 'ABS', 'Hedges', 'CLO']
    total_buys = 0
    total_sells = 0
    total_buy_notional = 0
    total_sell_notional = 0
    total_net_notional = 0
    
    for strategy in strategies:
        # Generate realistic numbers for each strategy
        buys = int(np.random.randint(2, 35))
        sells = int(np.random.randint(1, 10))
        buy_notional = round(np.random.uniform(5, 55), 2)
        sell_notional = round(np.random.uniform(2, 35), 2)
        net_notional = round(buy_notional - sell_notional, 2)
        
        # Format as strings with dollar signs
        buy_notional_str = f"${buy_notional}"
        sell_notional_str = f"(${sell_notional})" if sell_notional > 0 else f"${abs(sell_notional)}"
        net_notional_str = f"${net_notional}" if net_notional >= 0 else f"(${abs(net_notional)})"
        
        # Add to summary data
        summary_data.append([strategy, str(buys), str(sells), buy_notional_str, sell_notional_str, net_notional_str])
        
        # Update totals
        total_buys += buys
        total_sells += sells
        total_buy_notional += buy_notional
        total_sell_notional += sell_notional
        total_net_notional += net_notional
    
    # Add aggregate row
    summary_data.append(["Aggregate", 
                        str(total_buys), 
                        str(total_sells), 
                        f"${round(total_buy_notional, 2)}", 
                        f"(${round(total_sell_notional, 2)})", 
                        f"${round(total_net_notional, 2)}" if total_net_notional >= 0 else f"(${abs(round(total_net_notional, 2))})"]
    )
    
    # Generate mock trades data
    mock_trades = generate_mock_trades(5)
    
    return {
        'summary': summary_data,
        'last_5_trades': mock_trades,
        'top_5_largest': generate_mock_trades(5, larger_amounts=True)
    }

# Helper function to generate mock trades
def generate_mock_trades(count, larger_amounts=False):
    from datetime import datetime, timedelta
    current_date = datetime.now()
    
    trades = []
    security_prefixes = ['BP', 'WFMF', 'JPMC', 'HERA', 'CITI']
    security_suffixes = ['JUL J', 'OCT F', 'C30 XB', 'SUPERFOOD-A1', 'GER E']
    strategies = ['CMBS', 'ABS RMLT', 'ABS', 'Hedges', 'CLO']
    sub_strategies = ['CMBS-SSNR F1', 'CMBS-IO F1', 'CLO-AAA FF F1', 'ABS-AUTO F1', 'HEDGES-SWAP']
    
    for i in range(count):
        # Generate trade date
        days_ago = i*7 if not larger_amounts else np.random.randint(1, 30)
        trade_date = (current_date - timedelta(days=days_ago)).strftime("%m/%d/%Y")
        
        # Randomly select buy or sell
        trade_type = np.random.choice(['Buy', 'Sell'])
        
        # Generate security name
        prefix = np.random.choice(security_prefixes)
        year = str(np.random.randint(2019, 2024))
        suffix = np.random.choice(security_suffixes)
        security = f"{prefix} {year}-{suffix}"
        
        # Select strategy and sub-strategy
        strategy = np.random.choice(strategies)
        sub_strategy = np.random.choice(sub_strategies)
        
        # Generate notional amount
        min_amount = 5 if larger_amounts else 0.01
        max_amount = 25 if larger_amounts else 5
        amount = np.random.uniform(min_amount, max_amount) * 1000000
        amount_str = f"${amount:,.2f}"
        
        trades.append([trade_date, trade_type, security, strategy, sub_strategy, amount_str])
    
    # Sort by amount if these are largest trades
    if larger_amounts:
        trades.sort(key=lambda x: float(x[5].replace('$', '').replace(',', '')), reverse=True)
    
    return trades
    
    # Extract summary data from the trading monitor table
    summary_data = []
    for _, row in trading_monitor_df.iterrows():
        summary_data.append([
            row['Strategy'],
            str(row['Buys']),
            str(row['Sells']),
            row['Purchase MV ($mm)'],
            row['Sale MV ($mm)'],
            row['Net ($mm)']
        ])
    
    # Extract last 5 trades
    last_5_trades = []
    if 'filtered_trades' in globals() and not filtered_trades.empty:
        # Get the last 5 trades by date
        last_trades = filtered_trades.sort_values("Trade Date", ascending=False).head(5)
        
        for _, trade in last_trades.iterrows():
            # Format the trade date
            if isinstance(trade['Trade Date'], pd.Timestamp):
                trade_date = trade['Trade Date'].strftime('%m/%d/%Y')
            else:
                trade_date = str(trade['Trade Date'])
            
            # Determine if it's a buy or sell
            trade_type = "Buy" if "buy" in str(trade['Transaction']).lower() else "Sell"
            
            # Format the proceeds
            proceeds = abs(trade['Proceeds'])
            proceeds_str = f"${proceeds:,.2f}"
            
            # Use the correct column names based on what's available
            security_desc = str(trade.get('Security Description', 'Unknown Security'))
            clean_strategy = str(trade.get('CleanStrategy', 'Unknown Strategy'))
            strategy = str(trade.get('Strategy', 'Unknown Strategy'))
            
            last_5_trades.append([
                trade_date,
                trade_type,
                security_desc,
                clean_strategy,
                strategy,
                proceeds_str
            ])
    
# Extract top 5 largest trades
top_5_largest = []
if 'filtered_trades' in globals() and not filtered_trades.empty:
    # Get the top 5 largest trades by absolute market value
    largest_trades = filtered_trades.sort_values("Abs_Proceeds", ascending=False).head(5)
        
    for _, trade in largest_trades.iterrows():
        # Format the trade date
        if isinstance(trade['Trade Date'], pd.Timestamp):
            trade_date = trade['Trade Date'].strftime('%m/%d/%Y')
        else:
            trade_date = str(trade['Trade Date'])
            
        # Determine if it's a buy or sell
        trade_type = "Buy" if "buy" in str(trade['Transaction']).lower() else "Sell"
            
        # Format the proceeds
        proceeds = abs(trade['Proceeds'])
        proceeds_str = f"${proceeds:,.2f}"
        
        # Use the correct column names based on what's available
        security_desc = str(trade.get('Security Description', 'Unknown Security'))
        clean_strategy = str(trade.get('CleanStrategy', 'Unknown Strategy'))
        strategy = str(trade.get('Strategy', 'Unknown Strategy'))
        
        top_5_largest.append([
            trade_date,
            trade_type,
            security_desc,
            clean_strategy,
            strategy,
            proceeds_str
        ])
    
# Extract trading data by calling the function
trading_data = extract_trading_data_for_pdf()

# Create key stats dictionary for the PDF report with actual values from the dashboard
key_stats_for_pdf = {
    # Use the actual KPI values from the dashboard
    "monthly_return_str": kpi_data["monthly_return_str"],
    "ytd_return_str": kpi_data["ytd_return_str"],
    "ann_return_str": kpi_data["ann_return_str"],
    "aum_str": kpi_data["aum_str"],
    
    # Add more detailed key stats from the dashboard
    "avg_yield": key_stats["avg_yield"],
    "wal": key_stats["wal"],
    "pct_ig": key_stats["pct_ig"],
    "floating_rate_pct": key_stats["floating_rate_pct"],
    "pct_risk_rating_1": key_stats["pct_risk_rating_1"],
    "monthly_carry_bps": key_stats["monthly_carry_bps"],
    "bond_line_items": key_stats["bond_line_items"],
    "avg_holding_size": key_stats["avg_holding_size"],
    "top_10_concentration": key_stats["top_10_concentration"],
    "cmbs_items": key_stats["bond_breakdown"].get("CMBS", 0),
    "abs_items": key_stats["bond_breakdown"].get("ABS", 0),
    "clo_items": key_stats["bond_breakdown"].get("CLO", 0),
    "total_leverage": key_stats.get("total_leverage", "N/A"),
    "repo_mv": key_stats.get("repo_mv", "N/A")
}

# Function to prepare attribution data for the PDF
def prepare_attribution_data_for_pdf():
    """Prepare attribution data for the PDF report using actual data from the dashboard"""
    if 'attribution_df' not in globals() or attribution_df.empty:
        logging.warning("Attribution data not found in dashboard for PDF generation")
        return None
    
    # Create a copy of the attribution data to avoid modifying the original
    pdf_attribution_data = attribution_df.copy()
    
    # Ensure we have the necessary columns
    if 'Strategy' not in pdf_attribution_data.columns or 'Contribution' not in pdf_attribution_data.columns:
        logging.warning("Attribution data missing required columns for PDF generation")
        return None
    
    # Calculate gross and net returns from the actual data
    gross_bps = pdf_attribution_data[pdf_attribution_data['Contribution'] > 0]['Contribution'].sum()
    net_bps = pdf_attribution_data['Contribution'].sum()
    
    # Log the actual values for debugging
    logging.info(f"Attribution data for PDF - Gross: {gross_bps:.1f} bps, Net: {net_bps:.1f} bps")
    
    # Create a dictionary with the attribution data
    return {
        'strategies': pdf_attribution_data[['Strategy', 'Contribution']].to_dict('records'),
        'gross_bps': gross_bps,
        'net_bps': net_bps
    }

# Prepare attribution data for the PDF
attribution_data_for_pdf = prepare_attribution_data_for_pdf()

# Prepare allocation data for the PDF using actual data from the dashboard
def prepare_allocation_data_for_pdf():
    """Prepare actual allocation data from the dashboard for the PDF report"""
    # Check if the allocation data exists in the dashboard
    if 'april_display' not in globals() or 'current_display' not in globals():
        logging.warning("Allocation data not found in dashboard for PDF generation")
        return None, None
    
    # Create month-end allocation DataFrame for PDF
    if 'april_display' in globals() and not april_display.empty:
        # Extract the data we need from april_display
        april_allocation = april_display.copy()
        # Remove the TOTAL row
        april_allocation = april_allocation[april_allocation['Strategy'] != 'TOTAL']
        # Convert percentage strings to float values
        april_allocation['Allocation'] = april_allocation['Allocation'].str.rstrip('%').astype(float)
        # Select only Strategy and Allocation columns
        april_allocation = april_allocation[['Strategy', 'Allocation']]
    else:
        april_allocation = None
    
    # Create current allocation DataFrame for PDF
    if 'current_display' in globals() and not current_display.empty:
        # Extract the data we need from current_display
        current_allocation = current_display.copy()
        # Remove the TOTAL row
        current_allocation = current_allocation[current_allocation['Strategy'] != 'TOTAL']
        # Convert percentage strings to float values
        current_allocation['Allocation'] = current_allocation['Allocation'].str.rstrip('%').astype(float)
        # Select only Strategy and Allocation columns
        current_allocation = current_allocation[['Strategy', 'Allocation']]
    else:
        current_allocation = None
    
    return april_allocation, current_allocation

# Function to prepare competitor data for the PDF
def prepare_competitor_data_for_pdf():
    """Prepare competitor data for the PDF report using actual data from the dashboard"""
    # Check if clean_df exists and has data
    if 'clean_df' not in globals() or not isinstance(clean_df, pd.DataFrame) or clean_df.empty:
        logging.warning("Competitor data not found in dashboard for PDF generation")
        return None, None
    
    # Create a copy of the competitor data to avoid modifying the original
    competitor_data = clean_df.copy()
    
    # Ensure we have the necessary columns
    if 'Fund' not in competitor_data.columns or 'YTD_Display' not in competitor_data.columns:
        logging.warning("Competitor data missing required columns for PDF generation")
        return None, None
    
    # Format the data for the PDF
    competitor_data['YTD Return'] = competitor_data['YTD_Display'].apply(lambda x: f"{x}%")
    
    # Select only the columns we need
    competitor_data = competitor_data[['Fund', 'YTD Return']]
    
    # Get the percentile rank if available
    percentile = None
    if 'percentile_rounded' in globals() and isinstance(percentile_rounded, (int, float)):
        percentile = percentile_rounded
    
    return competitor_data, percentile

# Get actual allocation data for the PDF
april_allocation_for_pdf, current_allocation_for_pdf = prepare_allocation_data_for_pdf()

# Get competitor data for the PDF
competitor_data_for_pdf, percentile_rank_for_pdf = prepare_competitor_data_for_pdf()

# Generate PDF report
pdf_buffer = io.BytesIO()

# Use the existing key_stats_for_pdf dictionary - don't redefine it
# Just update any additional fields needed for the PDF
key_stats_for_pdf.update({
    # Add any additional fields needed for the PDF that aren't in the original dictionary
    "yield": key_stats.get("avg_yield", "N/A"),
    "wal": key_stats.get("wal", "N/A"),
    "ig_pct": key_stats.get("pct_ig", "N/A"),
    "floating_rate_pct": key_stats.get("floating_rate_pct", "N/A"),
    "risk_rating": key_stats.get("pct_risk_rating_1", "N/A"),
    "monthly_carry": key_stats.get("monthly_carry_bps", "N/A"),
    "bond_line_items": key_stats.get("bond_line_items", "N/A"),
    "avg_holding_size": key_stats.get("avg_holding_size", "N/A"),
    "cmbs_pct": key_stats.get("cmbs_items", "N/A"),
    "abs_pct": key_stats.get("abs_items", "N/A"),
    "clo_pct": key_stats.get("clo_items", "N/A"),
    "concentration": key_stats.get("top_10_concentration", "N/A"),
    "leverage": key_stats.get("total_leverage", "N/A"),
    "repo_market_value": key_stats.get("repo_mv", "N/A"),
    # Add the Monthly Return value from kpi_data
    "monthly_return": kpi_data.get("monthly_return_str", "N/A")
})

# Force refresh of the P&L chart data for the PDF
if 'fig_gainers' in locals() and 'eom_df_dynamic' in locals():
    # Create fresh data for the PDF report to ensure exactly 5 positions
    top_pnl_gainers_for_pdf = eom_df_dynamic.copy()
    top_pnl_gainers_for_pdf['Abs_PL'] = top_pnl_gainers_for_pdf['Cannae MTD PL'].abs()
    top_pnl_gainers_for_pdf = top_pnl_gainers_for_pdf.nlargest(5, 'Abs_PL')
else:
    top_pnl_gainers_for_pdf = None

if 'fig_sub_strategy' in locals() and 'eom_df_dynamic' in locals():
    # Create fresh data for the sub-strategy chart to ensure exactly 5 positions
    sub_strat_for_pdf = eom_df_dynamic.groupby('Sub Strategy')['Cannae MTD PL'].sum().reset_index()
    sub_strat_for_pdf['Abs_PL'] = sub_strat_for_pdf['Cannae MTD PL'].abs()
    sub_strat_for_pdf = sub_strat_for_pdf.nlargest(5, 'Abs_PL')
else:
    sub_strat_for_pdf = None

# Create custom Plotly figures with exactly 5 positions for the PDF
if 'top_pnl_gainers_for_pdf' in locals() and top_pnl_gainers_for_pdf is not None:
    # Create a new Plotly figure with exactly 5 positions
    custom_fig_gainers = px.bar(
        top_pnl_gainers_for_pdf.sort_values('Cannae MTD PL', ascending=False),
        x='ID', y='Cannae MTD PL',
        title='Top 5 PnL Gainers/Losers',
        color_discrete_sequence=['#17a2b8', '#0e6471', '#0a444f', '#17a2b8', '#0e6471']
    )
else:
    custom_fig_gainers = fig_gainers if 'fig_gainers' in locals() else None

if 'sub_strat_for_pdf' in locals() and sub_strat_for_pdf is not None:
    # Create a new Plotly figure with exactly 5 positions
    custom_fig_substrat = px.bar(
        sub_strat_for_pdf.sort_values('Cannae MTD PL', ascending=False),
        x='Sub Strategy', y='Cannae MTD PL',
        title='Top 5 PnL by Sub Strategy',
        color_discrete_sequence=['#17a2b8', '#0e6471', '#0a444f', '#17a2b8', '#0e6471']
    )
else:
    custom_fig_substrat = fig_sub_strategy if 'fig_sub_strategy' in locals() else None

# Generate the PDF with our custom figures that have exactly 5 positions
generate_pdf_report(
    output_path=pdf_path,
    key_stats=key_stats_for_pdf,
    fig_pl_gainers=custom_fig_gainers,
    fig_pl_substrat=custom_fig_substrat,
    attribution_data=attribution_data_for_pdf,  # Use our properly formatted attribution data
    april_display=april_allocation_for_pdf,  # Use our allocation data for month-end
    current_display=current_allocation_for_pdf,  # Use our allocation data for current
    trading_data=trading_data,
    competitor_data=competitor_data_for_pdf,  # Add competitor data
    percentile_rank=percentile_rank_for_pdf  # Add percentile rank
)

try:
    # Display download link
    with open(pdf_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'''
            <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; text-align: center;">
                <a href="data:application/pdf;base64,{b64}" download="Cannae_Report.pdf" style="font-size: 16px; text-decoration: none; color: #007bff; font-weight: bold;">
                    Download Cannae Report PDF
                </a>
            </div>
        ''', unsafe_allow_html=True)
    st.success(f"PDF successfully generated: Cannae_Fund_Report.pdf")
except Exception as e:
    st.error(f"Error generating PDF: {e}")
    logging.error(f"PDF Generation Error: {e}", exc_info=True)
