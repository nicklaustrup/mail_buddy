from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QDateEdit,
                            QLabel, QComboBox, QPushButton, QDialog,
                            QVBoxLayout, QFrame)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QIcon


class FilterDialog(QDialog):
    """Dialog for advanced filtering options"""
    
    filter_changed = pyqtSignal(QDate, QDate)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter Emails")
        self.setFixedSize(300, 200)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Date filter
        self.date_filter = QComboBox()
        self.date_filter.addItems([
            "All time",
            "Today",
            "Last 7 days",
            "Last 30 days",
            "Custom range"
        ])
        
        # Custom date range
        date_range = QFrame()
        date_layout = QHBoxLayout(date_range)
        
        self.start_date = QDateEdit()
        self.end_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.end_date.setDate(QDate.currentDate())
        
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.end_date)
        
        # Add widgets
        layout.addWidget(QLabel("Date Range:"))
        layout.addWidget(self.date_filter)
        layout.addWidget(date_range)
        
        # Apply button
        apply_button = QPushButton("Apply Filters")
        apply_button.clicked.connect(self.apply_filters)
        layout.addWidget(apply_button)
        
        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #444;
                font-size: 13px;
            }
            QComboBox, QDateEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        
        # Connect signals
        self.date_filter.currentTextChanged.connect(self.handle_date_filter_change)
    
    def handle_date_filter_change(self, text):
        show_custom = text == "Custom range"
        self.start_date.setVisible(show_custom)
        self.end_date.setVisible(show_custom)
    
    def apply_filters(self):
        text = self.date_filter.currentText()
        today = QDate.currentDate()
        
        if text == "All time":
            start_date = today.addYears(-10)
            end_date = today
        elif text == "Today":
            start_date = end_date = today
        elif text == "Last 7 days":
            start_date = today.addDays(-7)
            end_date = today
        elif text == "Last 30 days":
            start_date = today.addDays(-30)
            end_date = today
        else:  # Custom range
            start_date = self.start_date.date()
            end_date = self.end_date.date()
        
        self.filter_changed.emit(start_date, end_date)
        self.accept()


class CompactSearchWidget(QWidget):
    """Compact search widget with filter button"""
    
    search_changed = pyqtSignal(str)
    date_filter_changed = pyqtSignal(QDate, QDate)
    refresh_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Refresh button with circular arrow icon
        refresh_button = QPushButton("↻")
        refresh_button.setFixedSize(30, 30)
        refresh_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #0078d4;
                background-color: #f0f0f0;
                border-radius: 15px;
            }
        """)
        
        # Search input with magnifying glass icon in placeholder
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search emails...")
        self.search_input.setFixedHeight(30)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 15px;
                padding: 5px 10px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
        
        # Filter button with improved hover effect
        filter_button = QPushButton("⚙")
        filter_button.setFixedSize(30, 30)
        filter_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #0078d4;
                background-color: #f0f0f0;
                border-radius: 15px;
            }
        """)
        
        # Add widgets to layout
        layout.addWidget(refresh_button)
        layout.addWidget(self.search_input)
        layout.addWidget(filter_button)
        
        # Create filter dialog
        self.filter_dialog = FilterDialog(self)
        
        # Connect signals
        self.search_input.textChanged.connect(self.search_changed.emit)
        filter_button.clicked.connect(self.show_filter_dialog)
        refresh_button.clicked.connect(self.refresh_clicked.emit)
        self.filter_dialog.filter_changed.connect(self.date_filter_changed.emit)
    
    def show_filter_dialog(self):
        self.filter_dialog.exec() 