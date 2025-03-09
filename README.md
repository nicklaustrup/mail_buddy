# Simple Desktop Email Client

A desktop email client application built with Python and PyQt6. This application provides a simple interface to view and send emails.

## Features

- Email account login (currently supports Gmail)
- View inbox emails
- Send new emails
- Modern and clean user interface
- Password visibility toggle for secure input

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone this repository or download the source code
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Gmail Setup Instructions

Before using the application with Gmail, you need to set up an App Password. This is required because Gmail's security settings don't allow direct password login from third-party applications.

### Setting up Gmail App Password:

1. Go to your Google Account settings:
   - Visit https://myaccount.google.com/
   - Sign in with your Gmail account

2. Enable 2-Step Verification (if not already enabled):
   - Go to Security → 2-Step Verification
   - Follow the steps to enable it
   - You may need to provide a phone number and verify it

3. Create an App Password:
   - Visit: https://myaccount.google.com/apppasswords
   - Go to Security → App passwords
   - (Note: This option only appears if 2-Step Verification is enabled)
   - Select "App" from the dropdown menu
   - Choose "Other (Custom name)"
   - Enter a name (e.g., "Python Email Client")
   - Click "Generate"
   - Google will display a 16-character password
   - **Copy this password immediately** - you won't be able to see it again

5. Using the App Password:
   - When logging into the email client:
     - Use your full Gmail address (e.g., yourname@gmail.com)
     - Use the 16-character App Password instead of your regular Gmail password
     - You can click the "Show" button to verify the password is entered correctly

## Usage

1. Run the application:
```bash
python main.py
```

2. Login Screen:
   - Enter your Gmail address
   - Enter your App Password (use the Show/Hide button to verify)
   - Click Login

3. Main Interface:
   - View your inbox emails
   - Click on an email to read its contents
   - Use the Compose button to write new emails
   - Use the Refresh button to update your inbox

## Security Note

- The application stores credentials only in memory and not on disk
- Always keep your App Password secure
- Don't share your App Password with others
- You can revoke App Passwords at any time from your Google Account settings

## Troubleshooting

If you cannot log in:
1. Verify you're using an App Password, not your regular Gmail password
2. Ensure 2-Step Verification is enabled
3. Try generating a new App Password
4. Check your internet connection

## Future Improvements

- Support for other email providers
- Email attachments
- Multiple email accounts
- Folder management
- Email filters and search
- Message threading
 
