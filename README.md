# 🏢 Enterprise Management Dashboard

A **high-end, enterprise-grade interactive management dashboard** built with Python, Streamlit, and Plotly. Features a premium dark-grey theme optimized for executive-level decision-making with real-time financial analytics.

## ✨ Features

### 🎯 **Key Performance Indicators (KPIs)**
- **Premium KPI Cards** with category-specific icons (💰, 📦, 🏢)
- **Real-time calculations** for Current Year vs Last Year comparisons
- **Trend indicators** with color-coded growth rates
- **Responsive design** with hover animations

### 📊 **Interactive Visualizations**
- **Stacked bar charts** for Expense, PD, and CH analysis
- **Drill-down capabilities** for detailed expense breakdowns
- **Treemap & Sunburst charts** for hierarchical data visualization
- **Trend analysis** with YoY growth comparisons
- **Plotly Dark theme** with custom styling

### 🔍 **Advanced Filtering & Controls**
- **Multi-select filters** for account types
- **Search functionality** for expense categories
- **Date range controls** (configurable)
- **Toggle between absolute values and percentages**
- **Real-time data filtering**

### 🎨 **Premium UI/UX**
- **Dark Grey Color Scheme** (#121212 background)
- **Gradient backgrounds** and card styling
- **Custom CSS** for professional appearance
- **Responsive design** for desktop, tablet, and mobile
- **Smooth animations** and hover effects

### 💾 **Export & Data Management**
- **CSV export** with formatted data
- **Chart downloads** as PNG
- **Data caching** for performance optimization
- **Persistent settings** (remembers filters)

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Excel file with trial balance data

### Installation

1. **Clone or download** the project files
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare your data**:
   - Ensure your Excel file has the required columns:
     - `Account ID`
     - `Account Description`
     - `Debit Amt`
     - `Credit Amt`
     - `Last FYE Bal`
     - `Type`

4. **Update file paths** in `app.py`:
   ```python
   DEFAULT_FILE = r"path\to\your\trial_balance.xlsx"
   LOGO_PATH = r"path\to\your\logo.png"  # Optional
   ```

5. **Run the dashboard**:
   ```bash
   streamlit run app.py
   ```

6. **Open your browser** and navigate to `http://localhost:8501`

## 📁 Data Format Requirements

Your Excel file should contain the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `Account ID` | Unique identifier | "1001" |
| `Account Description` | Account name | "Office Supplies" |
| `Debit Amt` | Debit amount | 15000.00 |
| `Credit Amt` | Credit amount | 0.00 |
| `Last FYE Bal` | Previous year balance | 12000.00 |
| `Type` | Account category | "EXPENSE" |

### Supported Account Types
- `EXPENSE` - Operating expenses
- `PD` - Prepaid expenses
- `CH` - Capital expenditures
- `LIABILITY` - Liabilities
- `ASSET` - Assets
- `EQUITY` - Equity accounts
- `INCOME` - Revenue accounts

## 🎨 Customization

### Color Scheme
The dashboard uses a premium dark theme with the following colors:

```python
COLORS = {
    "background": "#121212",      # Main background
    "surface": "#1E1E1E",         # Cards and surfaces
    "primary_text": "#E0E0E0",    # Main text
    "secondary_text": "#B0B0B0",  # Secondary text
    "accent": "#1E88E5",          # Primary accent
    "expense": "#4CAF50",         # Expense category
    "pd": "#FF9800",              # PD category
    "ch": "#03A9F4",              # CH category
    "positive": "#00E676",        # Positive trends
    "negative": "#F44336",        # Negative trends
}
```

### Adding New Features
The dashboard is modular and easily extensible:

1. **New Charts**: Add functions in the utility section
2. **New KPIs**: Extend the KPI cards section
3. **New Filters**: Add controls to the sidebar
4. **Custom Styling**: Modify the CSS section

## 📊 Dashboard Sections

### 1. **Header Section**
- Company logo and branding
- Dashboard title and timestamp
- Live status indicator

### 2. **KPI Cards**
- **Total Expenses** with YoY comparison
- **PD Amount** with trend analysis
- **CH Amount** with growth indicators
- **Grand Total** with overall performance

### 3. **Analysis Tabs**
- **📊 Expense Analysis**: Top expenses and drill-downs
- **📈 Trends & Comparisons**: YoY analysis and growth rates
- **🌳 Hierarchical View**: Treemap and sunburst visualizations
- **📋 Detailed Data**: Raw data with search functionality

### 4. **Sidebar Controls**
- Data file configuration
- Filter settings
- View options
- Export controls
- Performance settings

## 🔧 Configuration Options

### Sidebar Settings
- **Excel File Path**: Path to your trial balance file
- **Worksheet Name**: Name of the Excel sheet
- **Top N Lines**: Number of top expense lines to display
- **Account Types**: Multi-select filter for account categories
- **Show Comparisons**: Toggle for YoY comparisons
- **Export Settings**: Customize export filenames

### Performance Optimization
- **Data Caching**: Improves load times for large datasets
- **Max Rows**: Limit displayed data for better performance
- **Chart Optimization**: Responsive charts with hover tooltips

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Deploy automatically

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

### Enterprise Server
- Deploy on internal servers
- Configure with reverse proxy
- Set up authentication if needed

## 📈 Performance Tips

1. **Data Optimization**:
   - Use Excel files under 100MB
   - Limit to essential columns
   - Consider data preprocessing

2. **Caching**:
   - Enable data caching for large datasets
   - Use `@st.cache_data` decorators
   - Implement session state for user preferences

3. **Charts**:
   - Limit chart data points for better performance
   - Use appropriate chart types for data size
   - Enable chart optimization settings

## 🐛 Troubleshooting

### Common Issues

1. **File Not Found Error**:
   - Check file path in `app.py`
   - Ensure Excel file exists and is accessible
   - Verify worksheet name is correct

2. **Missing Columns**:
   - Ensure all required columns are present
   - Check column names match exactly
   - Verify data types are correct

3. **Performance Issues**:
   - Reduce data size or enable caching
   - Limit displayed rows
   - Optimize chart configurations

4. **Styling Issues**:
   - Clear browser cache
   - Check CSS compatibility
   - Verify color codes are valid

## 📞 Support

For issues or feature requests:
1. Check the troubleshooting section
2. Review data format requirements
3. Verify all dependencies are installed
4. Test with sample data first

## 📄 License

This project is developed for Iqra University. Please contact the development team for usage permissions.

---

**Built with ❤️ for Executive Decision Making**
