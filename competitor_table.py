def create_competitor_returns_table(competitor_data, percentile_rank=None):
    """Create a compact table for the competitor YTD returns"""
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib.units import inch
    import pandas as pd
    
    if competitor_data is None or not isinstance(competitor_data, pd.DataFrame) or competitor_data.empty:
        # Create a placeholder table if no data
        data = [["No competitor data available"]]
        table = Table(data, colWidths=[3*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Oblique'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        return table
    
    # Create header row
    header = ["Fund", "YTD Return"]
    
    # Create data rows
    data = [header]
    
    # Add fund rows - limit to top 10 funds to save space
    for idx, (_, row) in enumerate(competitor_data.iterrows()):
        if idx >= 10:  # Limit to top 10 funds
            break
            
        fund = row['Fund']
        ytd_return = row['YTD Return']
        
        # Highlight Cannae's fund (without label)
        if 'cannae' in str(fund).lower() or 'cpa' in str(fund).lower() or 'opportunity' in str(fund).lower():
            data.append([fund, ytd_return])
        else:
            data.append([fund, ytd_return])
    
    # Add percentile rank if available
    if percentile_rank is not None and isinstance(percentile_rank, (int, float)):
        data.append([f"Percentile Rank", f"{percentile_rank:.0f}%"])
    
    # Create the table
    table = Table(data, colWidths=[2*inch, 1*inch])
    
    # Apply styles
    styles = [
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),  # Smaller font
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),  # Less padding
        ('TOPPADDING', (0, 0), (-1, 0), 2),  # Less padding
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),  # Smaller font
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 1),  # Minimal padding
        ('TOPPADDING', (0, 1), (-1, -1), 1),  # Minimal padding
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]
    
    # Highlight our fund row
    for i in range(1, len(data)):
        if i < len(data) - 1 and "Our Fund" in str(data[i][0]):
            styles.append(('BACKGROUND', (0, i), (-1, i), colors.lightblue))
            styles.append(('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold'))
    
    # Highlight percentile rank row if present
    if percentile_rank is not None:
        styles.append(('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.black))
        styles.append(('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'))
    
    table.setStyle(TableStyle(styles))
    
    return table
