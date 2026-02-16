import logging
from typing import Optional
from PyQt6.QtWidgets import QMessageBox, QWidget

# Setup logging
logger = logging.getLogger("pee.gui")

def show_error(parent: Optional[QWidget], message: str, details: str = "") -> None:
    """
    Shows an error message box.

    Args:
        parent: The parent widget.
        message: The main error message.
        details: Additional details about the error.
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText(message)
    if details:
        msg.setInformativeText(details)
    msg.setWindowTitle("Error")
    logger.error(f"{message}: {details}")
    msg.exec()

def show_warning(parent: Optional[QWidget], message: str, details: str = "") -> None:
    """
    Shows a warning message box.

    Args:
        parent: The parent widget.
        message: The main warning message.
        details: Additional details about the warning.
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setText(message)
    if details:
        msg.setInformativeText(details)
    msg.setWindowTitle("Warning")
    logger.warning(f"{message}: {details}")
    msg.exec()

def show_info(parent: Optional[QWidget], message: str) -> None:
    """
    Shows an info message box.

    Args:
        parent: The parent widget.
        message: The information message.
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setText(message)
    msg.setWindowTitle("Information")
    msg.exec()
