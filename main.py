import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from dotenv import load_dotenv

from email_handler import EmailHandler
from email_window import EmailWindow


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Email Client - Login")
        self.setFixedSize(400, 200)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create form elements
        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_button = QPushButton("Login")
        
        # Add widgets to layout
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        
        # Center elements
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Connect login button to function
        self.login_button.clicked.connect(self.handle_login)
    
    def handle_login(self):
        email = self.email_input.text()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return
        
        # Try to connect to email servers
        email_handler = EmailHandler(email, password)
        if email_handler.connect():
            # Login successful, open main window
            self.email_window = EmailWindow(email)
            self.email_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Login failed. Please check your credentials.")


def main():
    load_dotenv()
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 