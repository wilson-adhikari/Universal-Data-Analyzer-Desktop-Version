from PySide6.QtWidgets import QComboBox, QListView
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QMouseEvent, QStandardItemModel, QStandardItem
from PySide6.QtCore import QModelIndex


class MultiSelectComboBox(QComboBox):
    """
    A proper multi-select QComboBox with checkboxes in the dropdown.
    Displays either all selected names (if ≤3) or "N selected".
    Popup stays open during selection.
    """

    def __init__(self, parent=None, show_all_names=True, max_visible_names=3):
        super().__init__(parent)

        self._show_all_names = show_all_names
        self._max_visible_names = max_visible_names

        # Use QStandardItemModel for better control
        self.setModel(QStandardItemModel(self))

        # Use QListView for the popup
        view = QListView()
        view.setEditTriggers(view.EditTrigger.NoEditTriggers)
        self.setView(view)

        # Prevent popup from closing on item click
        self.view().viewport().installEventFilter(self)

        # Editable for custom text display
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("Select strategies")

        # Update display when checks change
        self.model().dataChanged.connect(self.update_text)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.MouseButtonRelease and isinstance(event, QMouseEvent):
            index = self.view().indexAt(event.pos())
            if index.isValid():
                current = index.data(Qt.ItemDataRole.CheckStateRole)
                new_state = Qt.CheckState.Unchecked if current == Qt.CheckState.Checked else Qt.CheckState.Checked
                self.model().setData(index, new_state, Qt.ItemDataRole.CheckStateRole)
                return True  # Consume event
        return super().eventFilter(source, event)

    def add_checkable_items(self, items):
        model = self.model()
        for text in items:
            item = QStandardItem(text)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            item.setData(Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
            model.appendRow(item)
        self.update_text()

    def checked_items(self):
        checked = []
        model = self.model()
        for row in range(model.rowCount()):
            item = model.item(row)
            if item.checkState() == Qt.CheckState.Checked:
                checked.append(item.text())
        return checked

    def update_text(self):
        checked = self.checked_items()
        if not checked:
            self.lineEdit().setText("")
            self.lineEdit().setPlaceholderText("Select strategies")
        elif self._show_all_names and len(checked) <= self._max_visible_names:
            self.lineEdit().setText(", ".join(checked))
        else:
            self.lineEdit().setText(f"{len(checked)} selected")

    def set_checked_items(self, items_to_check):
        model = self.model()
        for row in range(model.rowCount()):
            item = model.item(row)
            checked = item.text() in items_to_check
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.update_text()