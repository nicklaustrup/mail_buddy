import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox, QScrollArea)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QCursor
from dotenv import load_dotenv

from email_handler import EmailHandler
from email_window import EmailWindow
from credentials_manager import CredentialsManager
from email_worker import EmailWorker


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.credentials_manager = CredentialsManager()
        self.worker = None
        self.thread = None
        
        self.setWindowTitle("Email Client - Login")
        self.setFixedSize(400, 600)  # Adjusted size for the new mascot
        self.setup_ui()
        self.load_saved_credentials()
    
    def setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        
        # Add mascot
        with open('mascot.txt', 'r') as f:
            mascot_art = f.read()
        
        mascot_label = QLabel(mascot_art)
        mascot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mascot_label.setStyleSheet("""
            QLabel {
                font-family: monospace;
                color: #0078d4;
                margin: 10px;
                padding: 0px;
                font-size: 14px;
                line-height: 1;
                letter-spacing: 0px;
                white-space: pre;
            }
        """)
        
        layout.addWidget(mascot_label)
        
        # Create form elements
        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.password_label = QLabel("Password:")
        
        # Create password input with show/hide button
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.toggle_password_button = QPushButton("Show")
        self.toggle_password_button.setFixedWidth(60)
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.toggle_password_button)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember me")
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        
        # Add widgets to layout
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_label)
        layout.addLayout(password_layout)
        layout.addWidget(self.remember_checkbox)
        layout.addWidget(self.login_button)
        
        # Center elements
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Connect login button to function
        self.login_button.clicked.connect(self.handle_login)
        
        # Apply styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QLabel {
                color: #444;
                font-size: 13px;
            }
            QCheckBox {
                color: #444;
                font-size: 13px;
            }
        """)
    
    def load_saved_credentials(self):
        """Load saved credentials if they exist"""
        email, password = self.credentials_manager.load_credentials()
        if email and password:
            self.email_input.setText(email)
            self.password_input.setText(password)
            self.remember_checkbox.setChecked(True)
    
    def toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_button.setText("Hide")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_button.setText("Show")
    
    def set_loading(self, is_loading):
        """Set the loading state of the window"""
        if is_loading:
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
            self.login_button.setEnabled(False)
            self.login_button.setText("Connecting...")
        else:
            QApplication.restoreOverrideCursor()
            self.login_button.setEnabled(True)
            self.login_button.setText("Login")
    
    def handle_login(self):
        print("[LoginWindow.handle_login] Starting login process")
        email = self.email_input.text()
        password = self.password_input.text()
        
        if not email or not password:
            print("[LoginWindow.handle_login] Missing credentials")
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return
        
        # Clean up any existing thread/worker
        if self.thread and self.thread.isRunning():
            print("[LoginWindow.handle_login] Cleaning up existing thread")
            try:
                self.thread.started.disconnect()
                self.worker.connected.disconnect()
                self.worker.error.disconnect()
                self.worker.finished.disconnect()
            except Exception as e:
                print(f"[LoginWindow.handle_login] Disconnect error: {str(e)}")
            self.thread.quit()
            self.thread.wait()
            print("[LoginWindow.handle_login] Thread cleanup complete")
        
        if self.worker:
            print("[LoginWindow.handle_login] Deleting old worker")
            self.worker.deleteLater()
        
        if self.thread:
            print("[LoginWindow.handle_login] Deleting old thread")
            self.thread.deleteLater()
        
        # Set loading state
        self.set_loading(True)
        
        # Create worker and thread
        print("[LoginWindow.handle_login] Creating new worker and thread")
        self.worker = EmailWorker()
        self.thread = QThread()
        
        # Move worker to thread BEFORE connecting signals
        self.worker.moveToThread(self.thread)
        print("[LoginWindow.handle_login] Worker moved to thread")
        
        # Connect worker signals
        print("[LoginWindow.handle_login] Connecting signals")
        self.worker.connected.connect(self.handle_connection_result)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.cleanup_thread)
        
        # Connect thread signals
        self.thread.started.connect(
            lambda: self.worker.connect_account(email, password)
        )
        
        # Start the thread
        print("[LoginWindow.handle_login] Starting thread")
        self.thread.start()
        print("[LoginWindow.handle_login] Thread started")
    
    def handle_connection_result(self, success, handler):
        print(f"[LoginWindow.handle_connection_result] Connection result: {success}")
        if success:
            print("[LoginWindow.handle_connection_result] Saving credentials")
            # Save credentials if remember me is checked
            self.credentials_manager.save_credentials(
                self.email_input.text(),
                self.password_input.text(),
                self.remember_checkbox.isChecked()
            )
            
            print("[LoginWindow.handle_connection_result] Opening email window")
            # Open main window
            self.email_window = EmailWindow(self.email_input.text())
            self.email_window.email_handler = handler
            self.email_window.show()
            self.close()
        else:
            print("[LoginWindow.handle_connection_result] Login failed")
            QMessageBox.warning(
                self,
                "Error",
                "Login failed. Please check your credentials and ensure "
                "you're using an App Password."
            )
    
    def handle_error(self, error_msg):
        print(f"[LoginWindow.handle_error] Error: {error_msg}")
        QMessageBox.warning(self, "Error", str(error_msg))
    
    def cleanup_thread(self):
        """Clean up thread and worker after operation is complete"""
        print("[LoginWindow.cleanup_thread] Starting cleanup")
        self.set_loading(False)
        
        if self.thread:
            print("[LoginWindow.cleanup_thread] Cleaning up thread")
            self.thread.quit()
            self.thread.wait()
            self.thread.deleteLater()
            self.thread = None
        
        if self.worker:
            print("[LoginWindow.cleanup_thread] Cleaning up worker")
            self.worker.deleteLater()
            self.worker = None
        print("[LoginWindow.cleanup_thread] Cleanup complete")


def main():
    load_dotenv()
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 