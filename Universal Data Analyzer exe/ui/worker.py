from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    result_ready = Signal(object, str, list)   # results, path, chart_types (list)
    error_occurred = Signal(str, str, list)    # msg, path, chart_types

    def __init__(
        self,
        controller,
        path: str | None,
        chart_types: list[str],
        strategies: list[str],
        x: str,
        y: str | None,
        file_type: str,
        connection_string: str,
        table_name: str,
        width: int,
        height: int,
    ):
        super().__init__()
        self.controller = controller
        self.path = path
        self.chart_types = chart_types
        self.strategies = strategies
        self.x = x
        self.y = y
        self.file_type = file_type
        self.connection_string = connection_string
        self.table_name = table_name
        self.width = width
        self.height = height

    def run(self):
        try:
            results = self.controller.run(
                path=self.path or "",
                chart_types=self.chart_types,
                strategies=self.strategies,
                x=self.x,
                y=self.y,
                file_type=self.file_type,
                connection_string=self.connection_string,
                table_name=self.table_name,
                width=self.width,
                height=self.height,
            )
            self.result_ready.emit(results, self.path or "SQL", self.chart_types)
        except Exception as e:
            self.error_occurred.emit(str(e), self.path or "SQL", self.chart_types)