import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QCursor, QIcon
from dotenv import load_dotenv

from email_window import EmailWindow
from credentials_manager import CredentialsManager
from email_worker import EmailWorker


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.credentials_manager = CredentialsManager()
        self.worker = None
        self.thread = None
        
        self.setWindowTitle("Mail Buddy - Login")
        # Set window icon to bear emoji
        self.setWindowIcon(QIcon("icon.png"))
        self.setFixedSize(400, 600)  # Adjusted size for the new mascot
        self.setup_ui()
        self.setup_menu()
        self.load_saved_credentials()
    
    def setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        
        # Set rounded corners and gradient background
        central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #e6f2ff, stop:1 #ffffff);
                border-radius: 10px;
            }
        """)
        
        # Add mascot
        # with open('mascot.txt', 'r') as f:
        #     mascot_art = f.read()
        
        mascot_label = QLabel("""
∩_∩
(^ᴥ^)
/     \\
/|  o  |\\
|_____|
U   U

MAIL BUDDY
Your friendly email companion!
                               """)
        mascot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mascot_label.setStyleSheet("""
            QLabel {
                font-family: 'Courier New', monospace;
                color: #0078d4;
                margin: 10px;
                padding: 0px;
                font-size: 18px;
                line-height: 1.0;
                letter-spacing: 0px;
                white-space: pre;
                background: transparent;
                font-weight: bold;
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
        self.toggle_password_button.setObjectName("toggle_button")
        self.toggle_password_button.setFixedWidth(60)
        self.toggle_password_button.clicked.connect(
            self.toggle_password_visibility
        )
        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.toggle_password_button)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember me")
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setObjectName("login_button")
        self.login_button.setStyleSheet("""
            QPushButton#login_button {
                background-color: #0078d4;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton#login_button:hover {
                background-color: #106ebe;
            }
            QPushButton#login_button:disabled {
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
    
    def setup_menu(self):
        # Create menu bar
        menu_bar = self.menuBar()
        
        # Create File menu
        file_menu = menu_bar.addMenu("File")
        
        # Add Logout action
        logout_action = file_menu.addAction("Logout")
        logout_action.triggered.connect(self.handle_logout)
        
        # Add Exit action
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Create Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        
        # Add Switch Accounts action
        switch_accounts_action = edit_menu.addAction("Switch Accounts")
        switch_accounts_action.triggered.connect(self.show_coming_soon)
    
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
    
    def handle_logout(self):
        # Clear saved credentials and reset fields
        self.credentials_manager.clear_credentials()
        self.email_input.clear()
        self.password_input.clear()
        self.remember_checkbox.setChecked(False)
    
    def show_coming_soon(self):
        QMessageBox.information(self, "Coming Soon", "This feature is coming soon!")


def main():
    load_dotenv()
    app = QApplication(sys.argv)
    
    # Set application-wide style
    app.setStyleSheet("""
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #e6f2ff, stop:1 #ffffff);
        }
        QPushButton {
            border-radius: 5px;
            background-color: white;
            color: #0078d4;
            border: 1px solid #0078d4;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #f0f8ff;
        }
        QPushButton#login_button {
            background-color: #0078d4;
            color: white;
            border: none;
            font-weight: bold;
        }
        QPushButton#login_button:hover {
            background-color: #106ebe;
        }
        QPushButton#login_button:disabled {
            background-color: #ccc;
        }
        QPushButton#toggle_button {
            background-color: white;
            color: #0078d4;
            border: 1px solid #ccc;
            padding: 5px;
        }
        QPushButton#toggle_button:hover {
            background-color: #f0f8ff;
            border-color: #0078d4;
        }
        QLineEdit {
            border-radius: 5px;
            padding: 8px;
            border: 1px solid #ccc;
            background-color: white;
        }
        QLineEdit:focus {
            border: 1px solid #0078d4;
        }
        QCheckBox {
            border-radius: 3px;
            background: transparent;
        }
    """)
    
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 