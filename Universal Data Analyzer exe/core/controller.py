import logging
from typing import List, Tuple , Optional
import matplotlib.figure
import matplotlib.axes
import pandas as pd
from ingestion.csv_loader import CSVLoader
from ingestion.excel_loader import ExcelLoader
from ingestion.sql_loader import load_sql_table
from ingestion.schema_detector import SchemaDetector

from cleaning.duplicates import DuplicateHandler
from cleaning.outliers import OutlierHandler
from cleaning.type_casting import TypeCaster
from cleaning.missing_values import MissingValueHandler

from eda.correlations import CorrelationAnalyzer
from eda.distributions import DistributionAnalyzer
from eda.group_analysis import GroupAnalyzer
from eda.summary_stats import SummaryStats

from insights.text_generator import InsightGenerator
from insights.thresholds import ThresholdCalculator

from reporting.export_data import DataExporter
from reporting.export_plots import PlotExporter
from reporting.report_builder import ReportBuilder

from visualization.chart_selector import ChartSelector
from visualization.plot_factory import PlotFactory

from utils.exceptions import (
    DataAnalyzerException,
    DataLoadingException,
    DataValidationException,
    DataCleaningException,
    AnalysisException,
    VisualizationException,
    ReportGenerationException,
)
from utils.helpers import (
    setup_logger,
    load_config,
    ensure_directory,
    format_large_number,
    get_file_size,
    sanitize_column_name,
    describe_chart_type,
)
from utils.validators import DataValidator


logger = logging.getLogger(__name__)


class Controller:
    """
    High-level orchestrator used by the desktop UI.

    Current responsibilities:
    - Load data (CSV / Excel / SQL)
    - Apply one or more missing-value strategies
    - Compute summary statistics
    - Create matplotlib plots via PlotFactory
    """

    def __init__(self, config_path: str | None = None):
        self.config = load_config(config_path) if config_path else {}
        self.csv_loader = CSVLoader()
        self.excel_loader = ExcelLoader()
        self.schema_detector = SchemaDetector()
        self.missing_value_handler = MissingValueHandler()
        self.summary_stats = SummaryStats()
        self.plot_factory = PlotFactory()
        self.validator = DataValidator()

        # Other components available for future extensions
        self.duplicate_handler = DuplicateHandler()
        self.outlier_handler = OutlierHandler()
        self.type_caster = TypeCaster()
        self.corr_analyzer = CorrelationAnalyzer()
        self.dist_analyzer = DistributionAnalyzer()
        self.group_analyzer = GroupAnalyzer()
        self.text_generator = InsightGenerator()
        self.threshold_calc = ThresholdCalculator()
        self.data_exporter = DataExporter()
        self.plot_exporter = PlotExporter()
        self.report_builder = ReportBuilder()
        self.chart_selector = ChartSelector()

    def run(
        self,
        path: str,
        chart_types: List[str],
        strategies: List[str],
        x: str,
        y: Optional[str],
        file_type: str,
        connection_string: str = "",
        table_name: str = "",
        width: int = 12,
        height: int = 6,
    ) -> List[Tuple[str, pd.DataFrame, dict, Tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]]]:
        """
        Clean data once, then create one plot per chart_type.
        """
        try:
            df = self._load_data(path, file_type, connection_string, table_name)
            if df.empty:
                raise DataValidationException("Loaded dataset is empty.")

            self.validator.validate_dataframe(df)

            if not strategies:
                raise DataValidationException("Please select at least one strategy.")
            strategy = strategies[0]

            if not x:
                x = df.columns[0]

            logger.info(f"Cleaning data with strategy '{strategy}'")
            df_clean = self.missing_value_handler.handle(df.copy(), strategy=strategy)

            summary = self.summary_stats.get_summary(df_clean)

            results = []

            single_var_charts = {"histogram", "kde", "box", "violin"}

            for chart_type in chart_types:
                ct_lower = chart_type.lower()

                y_eff = None if ct_lower in single_var_charts else (y or None)

                if y_eff is None and ct_lower not in single_var_charts:
                    if len(df_clean.columns) < 2:
                        raise DataValidationException("Need at least 2 columns for bivariate plot.")
                    y_eff = next(c for c in df_clean.columns if c != x)

                if x not in df_clean.columns:
                    raise DataValidationException(f"Column '{x}' not found.")
                if y_eff and y_eff not in df_clean.columns:
                    raise DataValidationException(f"Column '{y_eff}' not found.")

                fig, ax = self.plot_factory.create_plot(
                    df_clean,
                    x_col=x,
                    y_col=y_eff,
                    chart_type=chart_type,
                    figsize=(width, height),
                )

                results.append((chart_type, df_clean, summary, (fig, ax)))

            return results

        except (DataLoadingException, DataValidationException, DataCleaningException):
            logger.exception("Data error in controller.run")
            raise
        except Exception as e:
            logger.exception("Unexpected error in controller.run")
            raise DataAnalyzerException(str(e)) from e

    def _load_data(self, path: str, file_type: str, connection_string: str = "", table_name: str = "") -> pd.DataFrame:
        try:
            file_type = file_type.lower()

            if file_type == "csv":
                logger.info(f"Loading CSV: {path}")
                df = self.csv_loader.load(path)

            elif file_type in {"excel", "xlsx", "xls"}:
                logger.info(f"Loading Excel: {path}")
                df = self.excel_loader.load(path)

            elif file_type == "sql":
                if not connection_string or not table_name:
                    raise DataLoadingException("SQL requires connection string and table name.")
                logger.info(f"Loading SQL table '{table_name}'")
                df = load_sql_table(connection_string, table_name)

            else:
                raise DataLoadingException(f"Unsupported file type: {file_type}")

            self.schema_detector.detect_schema(df)
            logger.info(f"Loaded DataFrame: {df.shape}")
            return df

        except Exception as e:
            logger.exception("Load failed")
            raise DataLoadingException(str(e)) from e