import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

class PlotFactory:
    """Factory for creating various plots using matplotlib and seaborn"""
    
    @staticmethod
    def create_plot(
        df: pd.DataFrame,
        x_col: str,
        y_col: Optional[str] = None,
        chart_type: str = "scatter",
        figsize: Tuple[int, int] = (12, 6),
    ) -> Tuple:
        try:
            fig, ax = plt.subplots(figsize=figsize)

            ct = chart_type.lower().strip()

            if ct == "scatter":
                if y_col is None:
                    raise ValueError("scatter plot requires y_col")
                ax.scatter(df[x_col], df[y_col], alpha=0.6, s=50,
                           edgecolors="k", linewidth=0.5)
                ax.set_xlabel(x_col, fontsize=12, fontweight="bold")
                ax.set_ylabel(y_col, fontsize=12, fontweight="bold")
                ax.set_title(f"{x_col} vs {y_col}", fontsize=14, fontweight="bold")

            elif ct == "line":
                if y_col is None:
                    raise ValueError("line plot requires y_col")
                ax.plot(df[x_col], df[y_col], marker="o", linewidth=2, markersize=6)
                ax.set_xlabel(x_col, fontsize=12, fontweight="bold")
                ax.set_ylabel(y_col, fontsize=12, fontweight="bold")
                ax.set_title(f"{x_col} vs {y_col}", fontsize=14, fontweight="bold")
                ax.grid(True, alpha=0.3)

            elif ct == "bar":
                if y_col is None:
                    raise ValueError("bar plot requires y_col")
                grouped = df.groupby(x_col)[y_col].mean()
                ax.bar(range(len(grouped)), grouped.values,
                       color="steelblue", edgecolor="black")
                ax.set_xticks(range(len(grouped)))
                ax.set_xticklabels(grouped.index, rotation=45, ha="right")
                ax.set_xlabel(x_col, fontsize=12, fontweight="bold")
                ax.set_ylabel(y_col, fontsize=12, fontweight="bold")
                ax.set_title(f"{y_col} by {x_col}", fontsize=14, fontweight="bold")

            elif ct == "histogram":
                ax.hist(df[x_col].dropna(), bins=30, color="steelblue",
                        edgecolor="black", alpha=0.7)
                ax.set_xlabel(x_col, fontsize=12, fontweight="bold")
                ax.set_ylabel("Frequency", fontsize=12, fontweight="bold")
                ax.set_title(f"Distribution of {x_col}", fontsize=14, fontweight="bold")
                ax.grid(True, alpha=0.3, axis="y")

            elif ct == "box":
                if y_col is None:
                    # fall back to 1‑variable box on x_col
                    ax.boxplot(df[x_col].dropna())
                    ax.set_ylabel(x_col, fontsize=12, fontweight="bold")
                    ax.set_title(f"Box Plot of {x_col}", fontsize=14, fontweight="bold")
                elif df[x_col].dtype == "object":
                    sns.boxplot(x=x_col, y=y_col, data=df, ax=ax, palette="Set2")
                else:
                    ax.boxplot(df[y_col].dropna())
                    ax.set_ylabel(y_col, fontsize=12, fontweight="bold")
                    ax.set_title(f"Box Plot of {y_col}", fontsize=14, fontweight="bold")

            elif ct == "violin":
                if y_col is None:
                    sns.violinplot(y=x_col, data=df, ax=ax, palette="Set2")
                    ax.set_title(f"Violin Plot of {x_col}", fontsize=14, fontweight="bold")
                elif df[x_col].dtype == "object":
                    sns.violinplot(x=x_col, y=y_col, data=df, ax=ax, palette="Set2")
                    ax.set_title(f"Violin Plot of {y_col} by {x_col}", fontsize=14, fontweight="bold")
                else:
                    sns.violinplot(y=y_col, data=df, ax=ax, palette="Set2")
                    ax.set_title(f"Violin Plot of {y_col}", fontsize=14, fontweight="bold")

            elif ct == "kde":
                df[x_col].dropna().plot(kind="kde", ax=ax,
                                        color="steelblue", linewidth=2)
                ax.set_xlabel(x_col, fontsize=12, fontweight="bold")
                ax.set_ylabel("Density", fontsize=12, fontweight="bold")
                ax.set_title(f"KDE of {x_col}", fontsize=14, fontweight="bold")
                ax.grid(True, alpha=0.3)

            else:
                raise ValueError(f"Unknown chart_type: {chart_type!r}")

            plt.tight_layout()
            logger.info(f"Created {ct} plot for {x_col} / {y_col}")
            return fig, ax

        except Exception as e:
            logger.error(f"Error creating plot: {e}")
            raise
    
    @staticmethod
    def create_subplots(df: pd.DataFrame, columns: list, chart_type: str = 'histogram',
                       figsize: Tuple[int, int] = (15, 10)) -> Tuple:
        """Create subplots for multiple columns"""
        try:
            n_cols = len(columns)
            n_rows = (n_cols + 1) // 2
            
            fig, axes = plt.subplots(n_rows, 2, figsize=figsize)
            axes = axes.flatten()
            
            for idx, col in enumerate(columns):
                ax = axes[idx]
                
                if chart_type == 'histogram':
                    ax.hist(df[col].dropna(), bins=20, color='steelblue', edgecolor='black', alpha=0.7)
                    ax.set_title(f"Distribution of {col}", fontweight='bold')
                    ax.set_xlabel('Value')
                    ax.set_ylabel('Frequency')
                
                elif chart_type == 'box':
                    ax.boxplot(df[col].dropna())
                    ax.set_title(f"Box Plot of {col}", fontweight='bold')
                    ax.set_ylabel('Value')
                
                elif chart_type == 'kde':
                    df[col].dropna().plot(kind='kde', ax=ax, color='steelblue', linewidth=2)
                    ax.set_title(f"KDE of {col}", fontweight='bold')
                    ax.set_ylabel('Density')
            
            # Hide unused subplots
            for idx in range(len(columns), len(axes)):
                axes[idx].axis('off')
            
            plt.tight_layout()
            logger.info(f"Created subplots for {len(columns)} columns")
            return fig, axes
        
        except Exception as e:
            logger.error(f"Error creating subplots: {str(e)}")
            raise
    
    @staticmethod
    def create_regression_plot(df: pd.DataFrame, x_col: str, y_col: str,
                              figsize: Tuple[int, int] = (12, 6)) -> Tuple:
        """Create scatter plot with regression line"""
        try:
            fig, ax = plt.subplots(figsize=figsize)
            sns.regplot(x=x_col, y=y_col, data=df, ax=ax, scatter_kws={'alpha': 0.6, 's': 50},
                       line_kws={'color': 'red', 'linewidth': 2})
            ax.set_xlabel(x_col, fontsize=12, fontweight='bold')
            ax.set_ylabel(y_col, fontsize=12, fontweight='bold')
            ax.set_title(f"{x_col} vs {y_col} (with regression)", fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            logger.info(f"Created regression plot for {x_col} vs {y_col}")
            return fig, ax
        
        except Exception as e:
            logger.error(f"Error creating regression plot: {str(e)}")
            raise
    