def create_attribution_table(attribution_df, gross_bps, net_bps):
    """Create a compact table for the return attribution data"""
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib.units import inch
    import pandas as pd
    
    # Create header row
    header = ["Strategy", "Contribution (bps)", "% of Gross"]
    
    # Create data rows
    data = [header]
    
    # Add strategy rows
    for _, row in attribution_df.iterrows():
        strategy = row['Strategy']
        contribution = row['Contribution']
        percentage = row['Percentage'] if 'Percentage' in attribution_df.columns else 0
        
        # Format the values
        contribution_str = f"{contribution:.0f}" if pd.notnull(contribution) else "N/A"
        percentage_str = f"{percentage:.1f}%" if pd.notnull(percentage) and percentage > 0 else ""
        
        data.append([strategy, contribution_str, percentage_str])
    
    # Add summary row for gross and net returns
    data.append(["Gross Return", f"{gross_bps:.0f}", "100.0%"])
    data.append(["Net Return", f"{net_bps:.0f}", ""])
    
    # Create the table
    table = Table(data, colWidths=[1.5*inch, 1*inch, 1*inch])
    
    # Apply styles
    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),  # Smaller font
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),  # Less padding
        ('TOPPADDING', (0, 0), (-1, 0), 2),  # Less padding
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -3), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),  # Smaller font
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 1),  # Minimal padding
        ('TOPPADDING', (0, 1), (-1, -1), 1),  # Minimal padding
        
        # Summary rows (gross and net)
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -2), (-1, -2), 0.5, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.black),
    ]))
    
    return table
