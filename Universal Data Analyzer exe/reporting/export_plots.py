

from pathlib import Path
from typing import Union
import logging

from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


class PlotExporter:
    """Export matplotlib plots to various formats."""

    @staticmethod
    def _ensure_dir(file_path: Union[str, Path]) -> Path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def export_plot_to_png(fig: Figure, file_path: str) -> None:
        """
        Export plot to PNG file.

        Args:
            fig: Matplotlib Figure object
            file_path: Path to save the PNG file
        """
        try:
            path = PlotExporter._ensure_dir(file_path)
            fig.savefig(path, format="png", bbox_inches="tight", dpi=150)
            logger.info(f"Plot exported successfully to {path}")
        except Exception as e:
            logger.error(f"Failed to export plot to PNG: {e}")
            raise

    @staticmethod
    def export_plot_to_jpeg(fig: Figure, file_path: str) -> None:
        """
        Export plot to JPEG file.

        Args:
            fig: Matplotlib Figure object
            file_path: Path to save the JPEG file
        """
        try:
            path = PlotExporter._ensure_dir(file_path)
            fig.savefig(path, format="jpeg", bbox_inches="tight", dpi=150)
            logger.info(f"Plot exported successfully to {path}")
        except Exception as e:
            logger.error(f"Failed to export plot to JPEG: {e}")
            raise

    @staticmethod
    def export_plot_to_pdf(fig: Figure, file_path: str) -> None:
        """
        Export plot to PDF file.

        Args:
            fig: Matplotlib Figure object
            file_path: Path to save the PDF file
        """
        try:
            path = PlotExporter._ensure_dir(file_path)
            fig.savefig(path, format="pdf", bbox_inches="tight")
            logger.info(f"Plot exported successfully to {path}")
        except Exception as e:
            logger.error(f"Failed to export plot to PDF: {e}")
            raise

    @staticmethod
    def export_plot_to_svg(fig: Figure, file_path: str) -> None:
        """Export plot to SVG file (vector, editable in Inkscape/Illustrator)."""
        try:
            path = PlotExporter._ensure_dir(file_path)
            fig.savefig(path, format="svg", bbox_inches="tight")
            logger.info(f"Plot exported successfully to {path}")
        except Exception as e:
            logger.error(f"Failed to export plot to SVG: {e}")
            raise
