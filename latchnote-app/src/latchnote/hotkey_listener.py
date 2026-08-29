"""Global micro-note hotkey and lightweight PySide6 popup."""

from collections.abc import Callable

import keyboard
from PySide6.QtCore import QObject, QPoint, Qt, Signal
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QVBoxLayout

NoteHandler = Callable[[str], None]


class HotkeyError(RuntimeError):
    """Raised when the global micro-note hotkey cannot be registered."""


class MicroNoteDialog(QDialog):
    """A compact, keyboard-first input dialog for a personal note."""

    submitted = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Latchnote micro-note")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        label = QLabel("Add a quick note")
        self._input = QLineEdit()
        self._input.setAccessibleName("Micro-note")
        self._input.setPlaceholderText("e.g. review append")
        self._input.returnPressed.connect(self._submit)
        hint = QLabel("Enter to save · Esc to cancel")

        layout.addWidget(label)
        layout.addWidget(self._input)
        layout.addWidget(hint)
        self.setFixedWidth(320)

    def open_near_cursor(self) -> None:
        """Show the dialog next to the cursor and focus its input."""
        if self.isVisible():
            self._input.setFocus()
            return
        self._input.clear()
        self.adjustSize()
        self.move(self._popup_position())
        self.show()
        self.raise_()
        self.activateWindow()
        self._input.setFocus()

    def _submit(self) -> None:
        text = self._input.text().strip()
        if text:
            self.submitted.emit(text)
            self.accept()

    def _popup_position(self) -> QPoint:
        cursor = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor) or QGuiApplication.primaryScreen()
        if screen is None:
            return cursor
        available = screen.availableGeometry()
        x = min(cursor.x() + 12, available.right() - self.width())
        y = min(cursor.y() + 12, available.bottom() - self.height())
        return QPoint(max(available.left(), x), max(available.top(), y))


class MicroNoteController(QObject):
    """Bridge keyboard-hook callbacks safely into Qt's GUI event loop."""

    show_requested = Signal()

    def __init__(self, on_submit: NoteHandler) -> None:
        if QApplication.instance() is None:
            raise HotkeyError("Create QApplication before enabling micro-notes.")
        super().__init__()
        self._dialog = MicroNoteDialog()
        self._dialog.submitted.connect(on_submit)
        self.show_requested.connect(self._dialog.open_near_cursor)

    def request_show(self) -> None:
        """Request the popup from any thread."""
        self.show_requested.emit()


class GlobalHotkeyListener:
    """Register and remove a focus-independent micro-note hotkey."""

    def __init__(self, on_hotkey: Callable[[], None], hotkey: str = "ctrl+space") -> None:
        self._on_hotkey = on_hotkey
        self._hotkey = hotkey
        self._hotkey_id: int | None = None

    def start(self) -> None:
        """Register the global hotkey without suppressing the user's keypress."""
        if self._hotkey_id is not None:
            return
        try:
            self._hotkey_id = keyboard.add_hotkey(self._hotkey, self._on_hotkey)
        except (OSError, ValueError) as error:
            raise HotkeyError(f"Unable to register {self._hotkey}: {error}") from error

    def stop(self) -> None:
        """Remove the registered hotkey if it is active."""
        if self._hotkey_id is not None:
            keyboard.remove_hotkey(self._hotkey_id)
            self._hotkey_id = None
