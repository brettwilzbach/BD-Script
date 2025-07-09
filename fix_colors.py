# Script to test and fix color issues in the Cannae Dashboard
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Sample data similar to what we see in the dashboard
data = pd.DataFrame({
    'Strategy': ['CMBS F1', 'AIRCRAFT F1', 'CLO F1', 'HEDGE', 'SHORT TERM'],
    'Market Value': [5000000, 3000000, 2000000, 1000000, 500000],
})

# Calculate percentages
data['Percentage'] = data['Market Value'] / data['Market Value'].sum() * 100
data['Formatted Value'] = data['Market Value'].apply(lambda x: f"${x:,.0f}")
data['Hover Info'] = data.apply(
    lambda row: f"Strategy: {row['Strategy']}<br>Amount: {row['Formatted Value']}<br>Allocation: {row['Percentage']:.1f}%", 
    axis=1
)

st.title("Color Test for Cannae Dashboard")

# Define the color map with CMBS F1 as teal (#3A606E)
strategy_color_map = {
    'CMBS F1': '#3A606E',      # Teal for CMBS F1 (as requested)
    'AIRCRAFT F1': '#475569',  # Slate gray for AIRCRAFT F1
    'CLO F1': '#8B5CF6',       # Violet for CLO
    'HEDGE': '#64748B',        # Slate for HEDGE
    'SHORT TERM': '#0EA5E9',   # Sky blue for SHORT TERM
}

# Create the pie chart
fig = px.pie(
    data, 
    values="Market Value", 
    names="Strategy", 
    title="Portfolio Allocation",
    color="Strategy",  # Explicitly use Strategy as the color dimension
    color_discrete_map=strategy_color_map,
    custom_data=["Hover Info"]
)

# Format pie chart
fig.update_traces(
    textposition='inside',
    textinfo='percent+label',
    hovertemplate="%{customdata[0]}"
)

fig.update_layout(
    legend_title="Strategy",
    font=dict(size=12),
    height=400,
    margin=dict(l=20, r=20, t=50, b=20)
)

st.plotly_chart(fig, use_container_width=True)

# Show the color mapping for verification
st.subheader("Color Mapping")
for strategy, color in strategy_color_map.items():
    st.markdown(f"<div style='background-color:{color}; padding:10px; color:white; margin-bottom:5px;'>{strategy}: {color}</div>", unsafe_allow_html=True)
