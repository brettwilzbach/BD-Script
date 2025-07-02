def create_allocation_table(allocation_df, title):
    """Create a compact table for the allocation data"""
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib.units import inch
    import pandas as pd
    
    # Create header row
    header = ["Strategy", "Allocation"]
    
    # Create data rows
    data = [header]
    
    # Add strategy rows
    for _, row in allocation_df.iterrows():
        strategy = row['Strategy']
        allocation = row['Allocation']
        
        # Format the allocation as a percentage
        allocation_str = f"{allocation:.1f}%" if pd.notnull(allocation) else "N/A"
        
        data.append([strategy, allocation_str])
    
    # Create the table
    table = Table(data, colWidths=[1.5*inch, 1.3*inch])
    
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
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),  # Smaller font
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 1),  # Minimal padding
        ('TOPPADDING', (0, 1), (-1, -1), 1),  # Minimal padding
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    
    return table
