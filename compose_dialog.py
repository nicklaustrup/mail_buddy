from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QTextEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt


class ComposeDialog(QDialog):
    def __init__(self, email_handler, parent=None):
        super().__init__(parent)
        self.email_handler = email_handler
        self.setWindowTitle("Compose Email")
        self.setMinimumSize(600, 500)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # To field
        to_layout = QHBoxLayout()
        to_label = QLabel("To:")
        to_label.setFixedWidth(60)
        self.to_input = QLineEdit()
        to_layout.addWidget(to_label)
        to_layout.addWidget(self.to_input)
        
        # Subject field
        subject_layout = QHBoxLayout()
        subject_label = QLabel("Subject:")
        subject_label.setFixedWidth(60)
        self.subject_input = QLineEdit()
        subject_layout.addWidget(subject_label)
        subject_layout.addWidget(self.subject_input)
        
        # Message body
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Write your message here...")
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.send_button = QPushButton("Send")
        self.send_button.setFixedWidth(100)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedWidth(100)
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add all elements to main layout
        layout.addLayout(to_layout)
        layout.addLayout(subject_layout)
        layout.addWidget(self.message_input)
        layout.addLayout(button_layout)
        
        # Connect buttons
        self.send_button.clicked.connect(self.send_email)
        self.cancel_button.clicked.connect(self.reject)
        
        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLineEdit, QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #0078d4;
            }
            QLabel {
                color: #444;
                font-size: 13px;
            }
            QPushButton {
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton#send_button {
                background-color: #0078d4;
                color: white;
                border: none;
            }
            QPushButton#send_button:hover {
                background-color: #106ebe;
            }
            QPushButton#cancel_button {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
            }
            QPushButton#cancel_button:hover {
                background-color: #e5e5e5;
            }
        """)
        
        # Set object names for styling
        self.send_button.setObjectName("send_button")
        self.cancel_button.setObjectName("cancel_button")
    
    def send_email(self):
        to_addr = self.to_input.text()
        subject = self.subject_input.text()
        body = self.message_input.toPlainText()
        
        if not all([to_addr, subject, body]):
            QMessageBox.warning(
                self,
                "Error",
                "Please fill in all fields before sending."
            )
            return
        
        if self.email_handler.send_email(to_addr, subject, body):
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Failed to send email. Please try again."
            ) 