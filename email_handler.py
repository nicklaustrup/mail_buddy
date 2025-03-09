import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional


class EmailHandler:
    def __init__(self, email_address: str, password: str):
        self.email_address = email_address
        self.password = password
        self.imap_server = "imap.gmail.com"  # Default to Gmail
        self.smtp_server = "smtp.gmail.com"
        self.imap_port = 993
        self.smtp_port = 587
        
        self.imap = None
        self.smtp = None
    
    def connect(self) -> bool:
        """Connect to both IMAP and SMTP servers."""
        try:
            # Connect to IMAP
            self.imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.imap.login(self.email_address, self.password)
            
            # Connect to SMTP
            self.smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.smtp.starttls()
            self.smtp.login(self.email_address, self.password)
            
            return True
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from both servers."""
        if self.imap:
            try:
                self.imap.logout()
            except:
                pass
        if self.smtp:
            try:
                self.smtp.quit()
            except:
                pass
    
    def get_emails(self, folder: str = "INBOX", limit: int = 10) -> List[Dict]:
        """Fetch emails from specified folder."""
        if not self.imap:
            return []
        
        try:
            self.imap.select(folder)
            _, messages = self.imap.search(None, "ALL")
            email_list = []
            
            # Get the last 'limit' number of emails
            message_numbers = messages[0].split()
            for num in message_numbers[-limit:]:
                _, msg_data = self.imap.fetch(num, "(RFC822)")
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract email details
                subject = email_message["subject"]
                from_addr = email_message["from"]
                date = email_message["date"]
                
                # Get email content
                content = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            content = part.get_payload(decode=True).decode()
                            break
                else:
                    content = email_message.get_payload(decode=True).decode()
                
                email_list.append({
                    "id": num.decode(),
                    "subject": subject,
                    "from": from_addr,
                    "date": date,
                    "content": content
                })
            
            return email_list
        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
            return []
    
    def send_email(self, to_addr: str, subject: str, body: str) -> bool:
        """Send an email."""
        if not self.smtp:
            return False
        
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = to_addr
            msg["Subject"] = subject
            
            msg.attach(MIMEText(body, "plain"))
            
            self.smtp.send_message(msg)
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False 