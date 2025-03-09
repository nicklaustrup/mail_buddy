from PyQt6.QtCore import QObject, pyqtSignal
from email_handler import EmailHandler


class EmailWorker(QObject):
    """Worker class to handle email operations in a separate thread"""
    
    finished = pyqtSignal()
    error = pyqtSignal(str)
    emails_fetched = pyqtSignal(list)
    email_sent = pyqtSignal(bool)
    connected = pyqtSignal(bool, EmailHandler)
    
    def __init__(self):
        super().__init__()
        self.handler = None
        print("[EmailWorker.__init__] Worker created")
    
    def connect_account(self, email, password):
        """Connect to email account"""
        print("[EmailWorker.connect_account] Attempting to connect")
        try:
            print("[EmailWorker.connect_account] Creating handler")
            self.handler = EmailHandler(email, password)
            print("[EmailWorker.connect_account] Connecting to email server")
            success = self.handler.connect()
            print(f"[EmailWorker.connect_account] Connection result: {success}")
            self.connected.emit(success, self.handler if success else None)
        except Exception as e:
            print(f"[EmailWorker.connect_account] Error: {str(e)}")
            self.error.emit(str(e))
        finally:
            print("[EmailWorker.connect_account] Emitting finished signal")
            self.finished.emit()
    
    def fetch_emails(self, limit=50):
        """Fetch emails in background"""
        print(f"[EmailWorker.fetch_emails] Fetching {limit} emails")
        try:
            if not self.handler:
                raise Exception("Email handler not initialized")
            
            print("[EmailWorker.fetch_emails] Getting emails from handler")
            emails = self.handler.get_emails(limit=limit)
            print(f"[EmailWorker.fetch_emails] Found {len(emails)} emails")
            self.emails_fetched.emit(emails)
        except Exception as e:
            print(f"[EmailWorker.fetch_emails] Error: {str(e)}")
            self.error.emit(str(e))
        finally:
            print("[EmailWorker.fetch_emails] Emitting finished signal")
            self.finished.emit()
    
    def send_email(self, to_addr, subject, body):
        """Send email in background"""
        print("[EmailWorker.send_email] Attempting to send email")
        try:
            if not self.handler:
                raise Exception("Email handler not initialized")
            
            print("[EmailWorker.send_email] Sending email via handler")
            success = self.handler.send_email(to_addr, subject, body)
            print(f"[EmailWorker.send_email] Send result: {success}")
            self.email_sent.emit(success)
        except Exception as e:
            print(f"[EmailWorker.send_email] Error: {str(e)}")
            self.error.emit(str(e))
        finally:
            print("[EmailWorker.send_email] Emitting finished signal")
            self.finished.emit() 