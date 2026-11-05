# Universal Data Analyzer (Desktop)

A simple, user-friendly desktop tool for Exploratory Data Analysis (EDA) built with Python, PySide6, pandas, matplotlib, and seaborn.[web:262][web:356]

Load your datasets (CSV, Excel, or directly from SQL databases), handle missing values with various strategies, view summary statistics, and generate multiple visualizations — all in an intuitive GUI. Compare different chart types side by side in separate tabs.[web:360]

---

## Features

### Data Loading
- CSV files  
- Excel files (`.xlsx`, `.xls`)  
- SQL tables (via SQLAlchemy-style connection string + table name)

### Data Cleaning
- Missing-value handling strategies:
  - Drop rows
  - Fill with mean
  - Fill with median
  - Forward fill
  - Backward fill
  - Fill with a constant value
- Basic data validation and optional schema detection[web:320][web:325]

### Analysis & Visualization
- Summary statistics for the cleaned dataset  
- One cleaning pass, then multiple chart types generated from the same cleaned data:
  - Line
  - Bar
  - Scatter
  - Histogram
  - Box plot
  - Violin plot
  - KDE (Kernel Density Estimate)[web:292][web:360]
- Each chart appears in its own tab for easy comparison  
- DataFrame preview tab to inspect the cleaned data

### Export
- Export the current plot as:
  - PNG
  - JPEG
  - PDF
  - (optional) SVG, if enabled in your matplotlib backend[web:262][web:333]

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/wilson-adhikari/Universal-Data-Analyzer-Desktop-Version.git
   cd Universal Data Analyzer exe
   ```
2. **Create and activate a virtual environment** (recommended)
   ```bash
   python -m venv venv
   venv\Scripts\activate # Windows
   or
   source venv/bin/activate # Linux / macOS
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
  
   `requirements.txt` should include packages such as:
   - pandas  
   - numpy  
   - matplotlib  
   - seaborn  
   - PySide6[web:262][web:356]
 ---

## Usage

1. **Start the application**

2. **Load data**

- Select the **file type** (`csv`, `excel`, or `sql`) from the dropdown.
- For CSV / Excel:
  - Click **Load Data** and choose your file.
- For SQL:
  - Set file type to `sql`.
  - Enter a **connection string** and **table name** in the input fields.
- Once loaded, the top bar shows the file name and **Run Analysis** becomes enabled.[web:262][web:356]

3. **Select cleaning strategy**

- Use the **Missing-value strategies** multi-select dropdown.
- You can check several strategies. They run in the order listed (forward_fill → backward_fill → mean → median → constant → drop), and each one fills what the previous left. Drop always runs last.

4. **Configure charts**

- Use the **Chart types** multi-select to choose one or more plots:
  - `line`, `bar`, `scatter`, `histogram`, `box`, `violin`, `kde`.
- Choose **X column** and (optionally) **Y column**:
  - Single-variable charts (histogram, KDE, some box/violin) can use only X.
  - Two-variable charts (scatter, line, bar) require both X and Y.

5. **Run analysis**

- Click **Run Analysis**.
- The app will:
  - Load the dataset.
  - Clean it once using the selected missing-value strategy.
  - Compute summary statistics.
  - Generate one plot for each selected chart type from the cleaned data.
- New tabs appear for each plot and for the DataFrame preview.

6. **Export plots**

- Select the plot tab you want to export.
- Click **Export Plot**.
- Choose a file name and format (PNG / JPEG / PDF / SVG).
- The current figure is saved to disk using matplotlib’s export tools.[web:262][web:333]

---

## Project Structure
```
  universal-data-analyzer/
  ├── main.py # Entry point (starts the GUI)
  ├── core/
  │ └── controller.py # Main orchestrator
  ├── ui/
  │ ├── main_window.py # Main GUI window
  │ ├── worker.py # Background thread for analysis
  │ └── multi_select_combo.py # Custom multi-select dropdown
  ├── ingestion/
  │ ├── csv_loader.py
  │ ├── excel_loader.py
  │ ├── sql_loader.py
  │ └── schema_detector.py
  ├── cleaning/
  │ ├── missing_values.py
  │ ├── duplicates.py
  │ ├── outliers.py
  │ └── type_casting.py
  ├── eda/
  │ ├── summary_stats.py
  │ ├── correlations.py
  │ ├── distributions.py
  │ └── group_analysis.py
  ├── visualization/
  │ ├── plot_factory.py
  │ └── chart_selector.py
  ├── reporting/
  │ ├── export_plots.py
  │ ├── export_data.py
  │ └── report_builder.py
  ├── utils/
  │ ├── exceptions.py
  │ ├── helpers.py
  │ └── validators.py
  └── requirements.txt
```
