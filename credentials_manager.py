import json
import os
from base64 import b64encode, b64decode

class CredentialsManager:
    def __init__(self):
        self.credentials_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "email_credentials.json"
        )
    
    def save_credentials(self, email, password, remember=False):
        """Save credentials if remember is True"""
        try:
            if remember:
                # Simple encoding (Note: this is not secure encryption)
                encoded_password = b64encode(password.encode()).decode()
                data = {
                    "email": email,
                    "password": encoded_password
                }
                with open(self.credentials_file, "w") as f:
                    json.dump(data, f)
            elif os.path.exists(self.credentials_file):
                # If not remembering, delete any existing credentials
                os.remove(self.credentials_file)
        except Exception as e:
            print(f"Failed to save credentials: {str(e)}")
    
    def load_credentials(self):
        """Load saved credentials if they exist"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, "r") as f:
                    data = json.load(f)
                    password = b64decode(data["password"].encode()).decode()
                    return data["email"], password
        except Exception as e:
            print(f"Failed to load credentials: {str(e)}")
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
        return None, None
    
    def clear_credentials(self):
        """Clear saved credentials"""
        try:
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
        except Exception as e:
            print(f"Failed to clear credentials: {str(e)}") 