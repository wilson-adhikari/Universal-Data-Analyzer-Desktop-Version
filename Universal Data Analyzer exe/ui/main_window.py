import sys
from pathlib import Path

import pandas as pd

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTabWidget,
    QTextEdit,
    QLineEdit,
    QMessageBox,
    QInputDialog,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from core.controller import Controller
from ui.worker import Worker
from ui.multi_select_combo import MultiSelectComboBox
from reporting.export_plots import PlotExporter
from cleaning.missing_values import MissingValueHandler
import licensing


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._licence = licensing.current()
        self._update_title()
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction("Activate licence…", self.activate_licence)
        self.resize(1400, 900)

        self.controller = Controller()
        self.path: str | None = None
        self.worker: Worker | None = None
        self._plot_canvases = []
        self._last_plot = None  # (fig, ax)

        # === Main layout ===
        root_widget = QWidget()
        main_layout = QVBoxLayout()

        # === Top control bar ===
        control_bar = QHBoxLayout()

        self.load_button = QPushButton("Load Data")
        self.run_button = QPushButton("Run Analysis")
        self.run_button.setEnabled(False)

        self.export_button = QPushButton("Export Current Plot")
        self.export_button.setEnabled(False)

        # File type selector
        self.file_type_selector = QComboBox()
        self.file_type_selector.addItems(["csv", "excel", "sql"])

        # Missing value strategies (multi-select), listed in the order they are applied
        self.strategy_selector = MultiSelectComboBox(max_visible_names=4)
        self.strategy_selector.add_checkable_items(MissingValueHandler.STRATEGY_ORDER)
        self.strategy_selector.setToolTip(
            "Selected strategies run top to bottom; each fills what the previous one left."
        )

        # Chart types (multi-select)
        self.chart_selector = MultiSelectComboBox(max_visible_names=4)
        self.chart_selector.add_checkable_items([
            "line",
            "bar",
            "scatter",
            "histogram",
            "box",
            "violin",
            "kde",
        ])

        # X and Y column selectors (populated after load)
        self.x_col_selector = QComboBox()
        self.x_col_selector.setMinimumWidth(150)
        self.y_col_selector = QComboBox()
        self.y_col_selector.addItem("None")  # For univariate plots
        self.y_col_selector.setMinimumWidth(150)

        # SQL fields
        self.conn_edit = QLineEdit()
        self.conn_edit.setPlaceholderText("e.g. postgresql://user:pass@host:5432/db")
        self.conn_edit.setMinimumWidth(300)
        self.table_edit = QLineEdit()
        self.table_edit.setPlaceholderText("Table name")
        self.table_edit.setMinimumWidth(150)

        # Add widgets to control bar
        control_bar.addWidget(self.load_button)
        control_bar.addWidget(self.file_type_selector)
        control_bar.addWidget(QLabel("Strategies:"))
        control_bar.addWidget(self.strategy_selector)
        control_bar.addWidget(QLabel("Charts:"))
        control_bar.addWidget(self.chart_selector)
        control_bar.addWidget(QLabel("X:"))
        control_bar.addWidget(self.x_col_selector)
        control_bar.addWidget(QLabel("Y:"))
        control_bar.addWidget(self.y_col_selector)
        control_bar.addWidget(self.conn_edit)
        control_bar.addWidget(self.table_edit)
        control_bar.addWidget(self.run_button)
        control_bar.addWidget(self.export_button)
        control_bar.addStretch()

        # === Tabs for results ===
        self.tabs = QTabWidget()
        self.summary_tab = QLabel("Load data and run analysis to see results.")
        self.summary_tab.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.summary_tab.setWordWrap(True)
        self.tabs.addTab(self.summary_tab, "Summary")

        # Main layout assembly
        main_layout.addLayout(control_bar)
        main_layout.addWidget(self.tabs, stretch=1)

        root_widget.setLayout(main_layout)
        self.setCentralWidget(root_widget)

        # === Connections ===
        self.load_button.clicked.connect(self.select_file)
        self.run_button.clicked.connect(self.run_analysis)
        self.export_button.clicked.connect(self.export_current_plot)
        self.file_type_selector.currentTextChanged.connect(self.on_file_type_changed)

    def on_file_type_changed(self, file_type: str):
        is_sql = file_type.lower() == "sql"
        self.conn_edit.setVisible(is_sql)
        self.table_edit.setVisible(is_sql)
        self.load_button.setEnabled(not is_sql)

    def select_file(self):
        file_type = self.file_type_selector.currentText().lower()

        if file_type == "sql":
            QMessageBox.information(self, "SQL Mode", "For SQL, enter connection string and table name, then click 'Run Analysis'.")
            return

        filters = {
            "csv": "CSV Files (*.csv *.txt);;All Files (*)",
            "excel": "Excel Files (*.xlsx *.xls);;All Files (*)",
        }
        filter_str = filters.get(file_type, "All Files (*)")

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Data File",
            "",
            filter_str,
        )
        if file_path:
            self.path = file_path
            self.load_button.setText(f"Loaded: {Path(file_path).name}")
            self.run_button.setEnabled(True)
            try:  # header only, so large files stay fast
                reader = pd.read_csv if file_type == "csv" else pd.read_excel
                self._set_columns([str(c) for c in reader(file_path, nrows=0).columns])
            except Exception as e:
                QMessageBox.warning(self, "Could not read columns", f"The file could not be read:\n{e}")

    def _set_columns(self, columns):
        """Refill the X/Y pickers, keeping the current choices when they still exist."""
        x, y = self.x_col_selector.currentText(), self.y_col_selector.currentText()
        self.x_col_selector.clear()
        self.y_col_selector.clear()
        self.x_col_selector.addItems(columns)
        self.y_col_selector.addItems(["None", *columns])
        if x in columns:
            self.x_col_selector.setCurrentText(x)
        if y in columns:
            self.y_col_selector.setCurrentText(y)

    def run_analysis(self):
        # === Validation ===
        strategies = self.strategy_selector.checked_items()
        if not strategies:
            QMessageBox.warning(self, "Input Required", "Please select at least one missing-value strategy.")
            return

        chart_items = self.chart_selector.checked_items()
        if not chart_items:
            QMessageBox.warning(self, "Input Required", "Please select at least one chart type.")
            return

        # Normalize chart types
        valid_charts = {"line", "bar", "scatter", "histogram", "box", "violin", "kde"}
        chart_types = [c.strip().lower() for c in chart_items if c.strip().lower() in valid_charts]
        if not chart_types:
            QMessageBox.warning(self, "Invalid Charts", "Selected chart types are not supported.")
            return

        file_type = self.file_type_selector.currentText().lower()

        conn = self.conn_edit.text().strip()
        table = self.table_edit.text().strip()

        if file_type != "sql" and not self.path:
            QMessageBox.warning(self, "File Required", "Please load a data file first.")
            return
        if file_type == "sql" and (not conn or not table):
            QMessageBox.warning(self, "SQL Required", "Please provide both connection string and table name.")
            return

        x_col = self.x_col_selector.currentText()
        y_col = self.y_col_selector.currentText()
        y_col = None if y_col == "None" else y_col

        # === Start worker ===
        self.run_button.setEnabled(False)
        self.run_button.setText("Running...")

        self.worker = Worker(
            controller=self.controller,
            path=self.path,
            chart_types=chart_types,
            strategies=strategies,
            x=x_col,
            y=y_col,
            file_type=file_type,
            connection_string=conn,
            table_name=table,
            width=12,
            height=6,
        )
        self.worker.result_ready.connect(self.display_results)
        self.worker.error_occurred.connect(self.display_error)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_finished(self):
        self.run_button.setEnabled(True)
        self.run_button.setText("Run Analysis")

    def display_results(self, results, path_info, chart_types):
        if not results:
            self.summary_tab.setText("No results returned.")
            return

        # Clear previous plot tabs (keep Summary and DataFrame View)
        for i in reversed(range(self.tabs.count())):
            if self.tabs.tabText(i) not in ["Summary", "DataFrame View"]:
                self.tabs.removeTab(i)

        # Shared data from first result
        _, df_clean, summary, _ = results[0]

        # Update summary
        summary_text = summary if isinstance(summary, str) else str(summary)
        self.summary_tab.setText(summary_text)

        self._set_columns(list(df_clean.columns))
        if self.controller.last_issues:
            QMessageBox.warning(self, "Data quality warnings", "\n".join(self.controller.last_issues))

        # DataFrame view tab (create once)
        df_view = self.tabs.findChild(QTextEdit, "DataFrameView")
        if df_view is None:
            df_view = QTextEdit()
            df_view.setObjectName("DataFrameView")
            df_view.setReadOnly(True)
            self.tabs.addTab(df_view, "DataFrame View")
        df_view.setText(df_clean.to_string())

        # Add each plot as a tab
        for chart_type, _, _, (fig, ax) in results:
            canvas = FigureCanvas(fig)
            self._plot_canvases.append(canvas)
            self._last_plot = (fig, ax)

            tab_title = chart_type.capitalize()
            self.tabs.addTab(canvas, tab_title)

        # Switch to first plot
        self.tabs.setCurrentIndex(2)  # After Summary (0) and DataFrame View (1)
        self.export_button.setEnabled(True)

    def display_error(self, error_msg: str, path_info: str, chart_types):
        QMessageBox.critical(self, "Analysis Error", f"{error_msg}")
        self.summary_tab.setText(f"Error: {error_msg}")

    def export_current_plot(self):
        if not self._last_plot:
            QMessageBox.information(self, "No Plot", "No plot available to export.")
            return

        fig, _ = self._last_plot

        file_path, filter_selected = QFileDialog.getSaveFileName(
            self,
            "Export Plot",
            "",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;PDF (*.pdf);;SVG (*.svg)",
        )
        if not file_path:
            return

        try:
            ext = Path(file_path).suffix.lower()
            if ext == ".png":
                PlotExporter.export_plot_to_png(fig, file_path)
            elif ext in {".jpg", ".jpeg"}:
                PlotExporter.export_plot_to_jpeg(fig, file_path)
            elif ext == ".pdf":
                PlotExporter.export_plot_to_pdf(fig, file_path)
            elif ext == ".svg":
                PlotExporter.export_plot_to_svg(fig, file_path)
            else:
                QMessageBox.warning(self, "Unsupported", "File format not supported.")
                return

            QMessageBox.information(self, "Success", f"Plot exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error saving plot:\n{str(e)}")


    def _update_title(self):
        suffix = f" — Licensed to {self._licence.get('email') or 'you'}" if self._licence else ""
        self.setWindowTitle("Universal Data Analyzer - Desktop" + suffix)

    def activate_licence(self):
        key, ok = QInputDialog.getMultiLineText(
            self, "Activate licence", "Paste the licence key from your Gumroad receipt:"
        )
        if not ok or not key.strip():
            return
        try:
            self._licence = licensing.activate(key)
        except licensing.LicenceError as e:
            QMessageBox.warning(self, "Licence not activated", str(e))
            return
        self._update_title()
        QMessageBox.information(self, "Licence activated", f"Licensed to {self._licence.get('email') or 'you'}.")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
