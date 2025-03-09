from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QTextEdit, QPushButton, QListWidgetItem, QMessageBox,
    QFrame, QSplitter, QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import Qt, QTimer, QDateTime, QThread, QSize, QRect
from PyQt6.QtGui import QCursor, QPainter, QFont, QColor, QIcon
from email_handler import EmailHandler
from compose_dialog import ComposeDialog
from search_filter_widget import CompactSearchWidget
from email_worker import EmailWorker


class EmailItemDelegate(QStyledItemDelegate):
    """Custom delegate for rendering email list items with proper formatting"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paint(self, painter, option, index):
        # Get the email data from the item
        email_data = index.data(Qt.ItemDataRole.UserRole)
        if not email_data:
            super().paint(painter, option, index)
            return
            
        # Draw the selection background if selected
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#e1f0ff"))
            # Draw a left border for selected items
            painter.fillRect(
                QRect(option.rect.left(), option.rect.top(), 3, option.rect.height()),
                QColor("#0078d4")
            )
        elif option.state & QStyle.StateFlag.State_MouseOver:
            # Highlight on hover
            painter.fillRect(option.rect, QColor("#f5f5f5"))
        else:
            painter.fillRect(option.rect, QColor("white"))
            
        # Draw bottom border
        painter.setPen(QColor("#ccc"))
        painter.drawLine(
            option.rect.left(), option.rect.bottom(),
            option.rect.right(), option.rect.bottom()
        )
            
        # Set up the painter
        painter.save()
        
        # Calculate text rectangles with proper margins
        margin = 12
        rect = option.rect.adjusted(margin, margin, -margin, -margin)
        
        # Draw sender name (bold)
        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor("#000"))
        sender_rect = QRect(rect.left(), rect.top(), rect.width(), 20)
        painter.drawText(
            sender_rect, Qt.AlignmentFlag.AlignLeft, email_data['from']
        )
        
        # Draw subject (normal)
        font.setBold(False)
        font.setPointSize(9)
        painter.setFont(font)
        subject_rect = QRect(
            rect.left(), sender_rect.bottom() + 6, rect.width(), 20
        )
        painter.drawText(
            subject_rect, Qt.AlignmentFlag.AlignLeft, email_data['subject']
        )
        
        # Draw date (gray) - use consistent format
        formatted_date = "Date not available"
        try:
            if 'date' in email_data and email_data['date']:
                date_str = email_data['date']
                
                # Parse date using the helper function
                date = parse_date(date_str)
                
                # Format date consistently
                if date.isValid():
                    # Use a consistent format for all dates
                    formatted_date = date.toString('MM/dd/yyyy hh:mm AP')
                else:
                    # Just use the raw date string as fallback
                    formatted_date = date_str
            else:
                print("Date field missing in email data")
        except Exception as e:
            print(f"Error formatting date: {str(e)}")
            
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(QColor("#666"))
        date_rect = QRect(
            rect.left(), subject_rect.bottom() + 6, rect.width(), 20
        )
        painter.drawText(
            date_rect, Qt.AlignmentFlag.AlignLeft, formatted_date
        )
        
        painter.restore()
    
    def sizeHint(self, option, index):
        # Return a size that accommodates three lines of text plus margins
        return QSize(option.rect.width(), 90)


class EmailListItem(QListWidgetItem):
    def __init__(self, email_data):
        super().__init__()
        self.email_data = email_data
        self.update_display()
        
    def update_display(self):
        # Store the email data in the UserRole
        self.setData(Qt.ItemDataRole.UserRole, self.email_data)
        # Set a placeholder text (won't be displayed with our custom delegate)
        self.setText(self.email_data['subject'])
        # Set a fixed height for the item
        self.setSizeHint(QSize(0, 90))


class EmailWindow(QMainWindow):
    def __init__(self, email):
        print("[EmailWindow.__init__] Starting initialization")
        super().__init__()
        self.email = email
        self._email_handler = None
        self.filtered_emails = []
        self.search_text = ""
        self.start_date = None
        self.end_date = None
        self.worker = None
        self.thread = None
        
        print("[EmailWindow.__init__] Setting window properties")
        self.setWindowTitle(f"Mail Buddy - {email}")
        # Set window icon to bear emoji
        self.setWindowIcon(QIcon("icon.png"))
        self.setMinimumSize(1000, 700)
        
        # Setup menu bar
        self.setup_menu()
        
        # Create central widget and main layout
        print("[EmailWindow.__init__] Creating central widget")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add loading indicator
        print("[EmailWindow.__init__] Adding loading indicator")
        self.loading_label = QLabel("Loading email client...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 16px;
                padding: 20px;
            }
        """)
        self.main_layout.addWidget(self.loading_label)
        
        # Setup UI in the next event loop iteration
        print("[EmailWindow.__init__] Scheduling UI setup")
        QTimer.singleShot(0, self.setup_ui)
        print("[EmailWindow.__init__] Basic initialization complete")
    
    def set_loading(self, is_loading):
        """Set the loading state of the window"""
        if is_loading:
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        else:
            QApplication.restoreOverrideCursor()
    
    @property
    def email_handler(self):
        return self._email_handler
    
    @email_handler.setter
    def email_handler(self, handler):
        """Set the email handler and start fetching emails"""
        print("[EmailWindow.email_handler] Setting email handler")
        if handler:
            self._email_handler = handler
            
            # Clean up any existing thread/worker
            self.cleanup_thread()
            
            # Create worker and thread for email operations
            self.worker = EmailWorker()
            self.worker.handler = handler
            
            # Start refresh timer
            print("[EmailWindow.email_handler] Starting refresh timer")
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self.refresh_emails)
            self.refresh_timer.start(60000)  # Refresh every minute
            
            # Start initial refresh
            print("[EmailWindow.email_handler] Starting initial refresh")
            self.refresh_emails()
    
    def cleanup_thread(self):
        """Clean up thread and worker after operation is complete"""
        print("[EmailWindow.cleanup_thread] Starting cleanup")
        
        # Disconnect any signals to prevent memory leaks
        if hasattr(self, 'worker') and self.worker:
            try:
                self.worker.finished.disconnect()
                self.worker.emails_fetched.disconnect()
                self.worker.error.disconnect()
            except Exception:
                pass  # Ignore if signals weren't connected
        
        # Stop and wait for thread
        if hasattr(self, 'thread') and self.thread and self.thread.isRunning():
            print("[EmailWindow.cleanup_thread] Cleaning up thread")
            self.thread.quit()
            if not self.thread.wait(1000):  # Wait up to 1 second
                print("[EmailWindow.cleanup_thread] Thread did not quit, terminating")
                self.thread.terminate()
                self.thread.wait()
        
        # Delete worker
        if hasattr(self, 'worker') and self.worker:
            print("[EmailWindow.cleanup_thread] Cleaning up worker")
            self.worker.deleteLater()
            self.worker = None
        
        # Delete thread
        if hasattr(self, 'thread') and self.thread:
            print("[EmailWindow.cleanup_thread] Deleting thread")
            self.thread.deleteLater()
            self.thread = None
            
        print("[EmailWindow.cleanup_thread] Cleanup complete")
    
    def handle_emails_fetched(self, emails):
        """Handle fetched emails"""
        print(f"[EmailWindow.handle_emails_fetched] Received {len(emails)} emails")
        
        if not hasattr(self, 'ui_ready') or not self.ui_ready:
            print("[EmailWindow.handle_emails_fetched] UI not ready, storing emails for later")
            self.pending_emails = emails
            return
            
        print("[EmailWindow.handle_emails_fetched] UI ready, processing emails")
        
        # Sort emails by date (newest first)
        try:
            # Convert string dates to QDateTime objects for sorting
            for email in emails:
                if 'date' in email and email['date']:
                    date_str = email['date']
                    date = parse_date(date_str)
                    # Store the parsed date for sorting
                    email['parsed_date'] = date
                else:
                    # If no date, use epoch start (will appear at the end)
                    email['parsed_date'] = QDateTime.fromSecsSinceEpoch(0)
            
            # Sort emails by parsed_date in descending order (newest first)
            emails.sort(key=lambda x: x['parsed_date'].toSecsSinceEpoch(), reverse=True)
        except Exception as e:
            print(f"[EmailWindow.handle_emails_fetched] Error sorting emails: {str(e)}")
        
        self.emails = emails
        self.filtered_emails = emails.copy()  # Store a copy for filtering
        self.statusBar().showMessage(f"Last updated: {QDateTime.currentDateTime().toString()}")
        
        # If email list is ready, populate it
        if hasattr(self, 'email_list') and self.email_list:
            print(f"[EmailWindow.handle_emails_fetched] Email list ready, displaying emails, id: {id(self.email_list)}")
            self.populate_email_list()
        else:
            print("[EmailWindow.handle_emails_fetched] Email list not ready, will display later")
            # Try to find the email list
            try:
                for child in self.findChildren(QListWidget, "email_list"):
                    self.email_list = child
                    print(f"[EmailWindow.handle_emails_fetched] Found email list widget, id: {id(self.email_list)}")
                    self.populate_email_list()
                    break
            except Exception as e:
                print(f"[EmailWindow.handle_emails_fetched] Error finding email list: {str(e)}")
        
        current_time = QDateTime.currentDateTime()
        refresh_time = current_time.toString('MM/dd/yyyy hh:mm:ss AP')
        print(f"[EmailWindow.handle_emails_fetched] Processed {len(emails)} emails at {refresh_time}")
        self.set_loading(False)
    
    def handle_error(self, error_msg):
        """Handle worker errors"""
        self.set_loading(False)
        QMessageBox.warning(self, "Error", str(error_msg))
    
    def refresh_emails(self):
        """Refresh emails from server"""
        print("[EmailWindow.refresh_emails] Starting refresh")
        if not self.email_handler:
            print("[EmailWindow.refresh_emails] Email handler not initialized")
            return
            
        # Clean up any existing thread first
        self.cleanup_thread()
        
        self.set_loading(True)
        
        # Create new thread and worker
        self.thread = QThread()
        self.worker = EmailWorker()
        self.worker.handler = self.email_handler
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.worker.emails_fetched.connect(self.handle_emails_fetched)
        self.worker.error.connect(self.handle_error)
        self.worker.finished.connect(self.cleanup_thread)
        
        # Start thread and fetch emails
        self.thread.started.connect(lambda: self.worker.fetch_emails(50))
        self.thread.start()
        
        print("[EmailWindow.refresh_emails] Thread started")
    
    def setup_ui(self):
        """Setup the UI components"""
        print("[EmailWindow.setup_ui] Starting UI setup")
        try:
            # Remove loading indicator
            print("[EmailWindow.setup_ui] Removing loading indicator")
            if hasattr(self, 'loading_label'):
                self.loading_label.setVisible(False)
                self.loading_label.deleteLater()
            
            # Split UI setup into smaller chunks using QTimer
            print("[EmailWindow.setup_ui] Setting up UI in chunks")
            self.setup_top_bar()
            QTimer.singleShot(100, self.setup_content_area)
            QTimer.singleShot(200, self.setup_email_list)
            QTimer.singleShot(300, self.setup_email_content)
            QTimer.singleShot(400, self.finalize_setup)
            
        except Exception as e:
            print(f"[EmailWindow.setup_ui] Error during UI setup: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to initialize email window: {str(e)}")
    
    def setup_top_bar(self):
        """Setup the top bar with search widget"""
        print("[EmailWindow.setup_ui] Creating top bar")
        try:
            top_bar = QWidget()
            top_bar.setFixedHeight(50)
            top_bar.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border-bottom: 1px solid #ddd;
                }
            """)
            top_layout = QHBoxLayout(top_bar)
            top_layout.setContentsMargins(10, 5, 10, 5)
            
            # Add search widget
            print("[EmailWindow.setup_ui] Adding search widget")
            self.search_widget = CompactSearchWidget()
            self.search_widget.setMaximumWidth(400)
            
            # Connect refresh button signal
            self.search_widget.refresh_clicked.connect(self.refresh_emails)
            
            top_layout.addWidget(self.search_widget)
            top_layout.addStretch()
            
            self.main_layout.addWidget(top_bar)
            print("[EmailWindow.setup_ui] Top bar setup complete")
        except Exception as e:
            print(f"[EmailWindow.setup_ui] Error setting up top bar: {str(e)}")
            raise
    
    def setup_content_area(self):
        """Setup the main content area"""
        print("[EmailWindow.setup_ui] Creating content area")
        try:
            self.content_widget = QWidget()
            self.content_layout = QVBoxLayout(self.content_widget)
            self.content_layout.setContentsMargins(10, 10, 10, 10)
            self.content_layout.setSpacing(10)
            
            # Create splitter for email list and content
            self.splitter = QSplitter(Qt.Orientation.Horizontal)
            print("[EmailWindow.setup_ui] Content area base setup complete")
        except Exception as e:
            print(f"[EmailWindow.setup_ui] Error setting up content area: {str(e)}")
            raise
    
    def setup_email_list(self):
        """Setup the email list panel"""
        print("[EmailWindow.setup_ui] Setting up email list")
        try:
            self.list_panel = QWidget()
            list_layout = QVBoxLayout(self.list_panel)
            list_layout.setContentsMargins(0, 0, 0, 0)
            
            # Compose button
            compose_button = QPushButton("✉ Compose")
            compose_button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
            """)
            
            # Create email list widget
            print("[EmailWindow.setup_email_list] Creating email list widget")
            self.email_list = QListWidget()
            self.email_list.setObjectName("email_list")  # Set object name for easier finding
            self.email_list.setStyleSheet("""
                QListWidget {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                QListWidget::item {
                    border-bottom: 1px solid #ccc;
                    padding-top: 4px;
                    padding-bottom: 4px;
                    margin: 0px;
                }
                QListWidget::item:last-child {
                    border-bottom: none;
                }
                QListWidget::item:selected {
                    background-color: #e1f0ff;
                    color: black;
                    border-left: 3px solid #0078d4;
                }
                QListWidget::item:hover:!selected {
                    background-color: #f5f5f5;
                }
            """)
            
            # Set custom delegate for rendering items
            self.email_list.setItemDelegate(EmailItemDelegate(self.email_list))
            
            list_layout.addWidget(compose_button)
            list_layout.addWidget(self.email_list)
            
            self.splitter.addWidget(self.list_panel)
            print(f"[EmailWindow.setup_email_list] Email list setup complete, id: {id(self.email_list)}")
            
            # Connect signals
            compose_button.clicked.connect(self.compose_email)
            self.email_list.itemClicked.connect(self.display_email)
            
            # If we have pending filtered emails, display them now
            if hasattr(self, 'filtered_emails') and self.filtered_emails:
                print(f"[EmailWindow.setup_email_list] Displaying {len(self.filtered_emails)} pending filtered emails")
                self.populate_email_list()
                
        except Exception as e:
            print(f"[EmailWindow.setup_ui] Error setting up email list: {str(e)}")
            raise
            
    def populate_email_list(self):
        """Populate the email list with filtered emails"""
        if not hasattr(self, 'email_list'):
            print("[EmailWindow.populate_email_list] Email list attribute not found")
            return
            
        if self.email_list is None:
            print("[EmailWindow.populate_email_list] Email list is None")
            return
            
        print(f"[EmailWindow.populate_email_list] Adding {len(self.filtered_emails)} emails to list, id: {id(self.email_list)}")
        try:
            self.email_list.clear()
            
            filtered_count = 0
            for email_data in self.filtered_emails:
                item = EmailListItem(email_data)
                self.email_list.addItem(item)
                filtered_count += 1
                
            print(f"[EmailWindow.populate_email_list] Added {filtered_count} emails to list")
        except Exception as e:
            print(f"[EmailWindow.populate_email_list] Error populating list: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def setup_email_content(self):
        """Setup the email content panel"""
        print("[EmailWindow.setup_ui] Setting up email content")
        try:
            self.content_panel = QWidget()
            content_layout = QVBoxLayout(self.content_panel)
            content_layout.setContentsMargins(0, 0, 0, 0)
            
            # Email header info
            header_widget = QWidget()
            header_widget.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin-bottom: 10px;
                }
                QLabel {
                    color: #444;
                    font-size: 13px;
                }
                QLabel.header_label {
                    font-weight: bold;
                    color: #666;
                    min-width: 60px;
                    max-width: 60px;
                }
                QLabel.value_label {
                    font-weight: normal;
                }
                QLabel#from_value {
                    font-weight: bold;
                }
            """)
            header_layout = QVBoxLayout(header_widget)
            header_layout.setSpacing(5)
            header_layout.setContentsMargins(10, 10, 10, 10)
            
            # Create rows for each field with label and value
            self.email_values = {}
            
            # From field
            from_row = QHBoxLayout()
            from_row.setSpacing(5)
            from_label = QLabel("From:")
            from_label.setObjectName("from_label")
            from_label.setProperty("class", "header_label")
            from_value = QLabel("")
            from_value.setObjectName("from_value")
            from_value.setProperty("class", "value_label")
            from_value.setWordWrap(True)
            from_row.addWidget(from_label)
            from_row.addWidget(from_value, 1)  # Give the value label stretch factor of 1
            header_layout.addLayout(from_row)
            self.email_values['from'] = from_value
            
            # To field
            to_row = QHBoxLayout()
            to_row.setSpacing(5)
            to_label = QLabel("To:")
            to_label.setObjectName("to_label")
            to_label.setProperty("class", "header_label")
            to_value = QLabel("")
            to_value.setObjectName("to_value")
            to_value.setProperty("class", "value_label")
            to_value.setWordWrap(True)
            to_row.addWidget(to_label)
            to_row.addWidget(to_value, 1)  # Give the value label stretch factor of 1
            header_layout.addLayout(to_row)
            self.email_values['to'] = to_value
            
            # Subject field
            subject_row = QHBoxLayout()
            subject_row.setSpacing(5)
            subject_label = QLabel("Subject:")
            subject_label.setObjectName("subject_label")
            subject_label.setProperty("class", "header_label")
            subject_value = QLabel("")
            subject_value.setObjectName("subject_value")
            subject_value.setProperty("class", "value_label")
            subject_value.setWordWrap(True)
            subject_row.addWidget(subject_label)
            subject_row.addWidget(subject_value, 1)  # Give the value label stretch factor of 1
            header_layout.addLayout(subject_row)
            self.email_values['subject'] = subject_value
            
            # Date field
            date_row = QHBoxLayout()
            date_row.setSpacing(5)
            date_label = QLabel("Date:")
            date_label.setObjectName("date_label")
            date_label.setProperty("class", "header_label")
            date_value = QLabel("")
            date_value.setObjectName("date_value")
            date_value.setProperty("class", "value_label")
            date_value.setStyleSheet("color: #666; font-weight: normal;")
            date_value.setWordWrap(True)
            date_row.addWidget(date_label)
            date_row.addWidget(date_value, 1)  # Give the value label stretch factor of 1
            header_layout.addLayout(date_row)
            self.email_values['date'] = date_value
            
            # Add a separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            separator.setStyleSheet("background-color: #ddd;")
            header_layout.addWidget(separator)
            
            # Email content
            self.content_view = QTextEdit()
            self.content_view.setReadOnly(True)
            self.content_view.setStyleSheet("""
                QTextEdit {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 10px;
                    font-size: 13px;
                }
            """)
            
            content_layout.addWidget(header_widget)
            content_layout.addWidget(self.content_view)
            
            self.splitter.addWidget(self.content_panel)
            self.splitter.setStretchFactor(0, 1)
            self.splitter.setStretchFactor(1, 2)
            print("[EmailWindow.setup_ui] Email content setup complete")
        except Exception as e:
            print(f"[EmailWindow.setup_ui] Error setting up email content: {str(e)}")
            raise
    
    def finalize_setup(self):
        """Finalize the UI setup"""
        print("[EmailWindow.setup_ui] Finalizing setup")
        try:
            # Add splitter to content layout
            self.content_layout.addWidget(self.splitter)
            
            # Add content widget to main layout
            self.main_layout.addWidget(self.content_widget)
            
            # Setup status bar
            self.statusBar().showMessage("Loading emails...")
            self.statusBar().setStyleSheet("""
                QStatusBar {
                    background-color: #f8f9fa;
                    border-top: 1px solid #ddd;
                    padding: 5px;
                    color: #666;
                }
            """)
            
            # Connect search widget signals
            self.search_widget.search_changed.connect(self.handle_search)
            self.search_widget.date_filter_changed.connect(self.handle_date_filter)
            
            # Apply global styling
            self.setStyleSheet("""
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                             stop:0 #e6f2ff, stop:1 #ffffff);
                }
                QWidget#central_widget {
                    background: transparent;
                }
                QSplitter::handle {
                    background-color: #ddd;
                    margin: 1px;
                }
                QSplitter::handle:hover {
                    background-color: #ccc;
                }
                QListWidget, QTextEdit, QLineEdit {
                    border-radius: 8px;
                    border: 1px solid #ddd;
                }
                QPushButton {
                    border-radius: 5px;
                }
            """)
            
            print("[EmailWindow.setup_ui] Setup complete")
            
            # Mark UI as ready
            self.ui_ready = True
            
            # Check if we have an email list
            if not hasattr(self, 'email_list') or not self.email_list:
                print("[EmailWindow.finalize_setup] WARNING: Email list not initialized!")
                # Try to find the email list
                try:
                    for child in self.findChildren(QListWidget, "email_list"):
                        self.email_list = child
                        print(f"[EmailWindow.finalize_setup] Found email list widget, id: {id(self.email_list)}")
                        break
                except Exception as e:
                    print(f"[EmailWindow.finalize_setup] Error finding email list: {str(e)}")
            
            # Process any pending emails
            if hasattr(self, 'pending_emails') and self.pending_emails:
                print(f"[EmailWindow.finalize_setup] Processing {len(self.pending_emails)} pending emails")
                emails = self.pending_emails
                self.pending_emails = None
                QTimer.singleShot(200, lambda: self.handle_emails_fetched(emails))
                
        except Exception as e:
            print(f"[EmailWindow.setup_ui] Error during finalization: {str(e)}")
            raise
    
    def handle_search(self, text):
        """Filter emails based on search text"""
        self.search_text = text.lower()
        self.apply_filters()
    
    def handle_date_filter(self, start_date, end_date):
        """Filter emails based on date range"""
        self.start_date = start_date
        self.end_date = end_date
        self.apply_filters()
    
    def apply_filters(self):
        """Apply both search and date filters"""
        if not hasattr(self, 'email_list') or not self.email_list:
            print("[EmailWindow.apply_filters] Email list not ready")
            return
            
        if not hasattr(self, 'emails') or not self.emails:
            print("[EmailWindow.apply_filters] No emails to filter")
            return
            
        print(f"[EmailWindow.apply_filters] Applying filters to {len(self.emails)} emails")
        
        # Apply filters to create filtered_emails list
        self.filtered_emails = []
        for email_data in self.emails:
            # Apply search filter
            searchable_text = (
                f"{email_data['subject']} {email_data['from']} "
                f"{email_data['content']}"
            ).lower()
            
            if self.search_text and self.search_text not in searchable_text:
                continue
            
            # Apply date filter
            if self.start_date and self.end_date:
                date = QDateTime.fromString(
                    email_data['date'],
                    Qt.DateFormat.TextDate
                )
                if not (self.start_date <= date.date() <= self.end_date):
                    continue
            
            # Add matching email to filtered list
            self.filtered_emails.append(email_data)
        
        # Populate the email list with filtered emails
        self.populate_email_list()
        print(f"[EmailWindow.apply_filters] Displayed {len(self.filtered_emails)} emails after filtering")
    
    def display_email(self, item):
        """Display the selected email's content"""
        email_data = item.email_data
        
        # Format the date
        formatted_date = "Date not available"
        try:
            if 'date' in email_data and email_data['date']:
                date_str = email_data['date']
                date = parse_date(date_str)
                
                # Format date consistently
                if date.isValid():
                    # Use a consistent format for all dates
                    formatted_date = date.toString('MM/dd/yyyy hh:mm AP')
                else:
                    # Just use the raw date string as fallback
                    formatted_date = date_str
            else:
                print("Date field missing in email data for preview")
        except Exception as e:
            print(f"Error formatting date for preview: {str(e)}")
        
        # Set the email details
        self.email_values['from'].setText(email_data['from'])
        self.email_values['subject'].setText(email_data['subject'])
        self.email_values['date'].setText(formatted_date)
        
        # Set the To field (use recipient from email or default to user's email)
        to_field = email_data.get('to', self.email)
        self.email_values['to'].setText(to_field)
        
        # Set the email content
        self.content_view.setText(email_data['content'])
    
    def compose_email(self):
        """Open the compose email dialog"""
        if not self.email_handler:
            QMessageBox.warning(self, "Error", "Email handler not initialized")
            return
        
        dialog = ComposeDialog(self.email_handler, self)
        if dialog.exec():
            QMessageBox.information(
                self,
                "Success",
                "Email sent successfully!"
            )
            self.refresh_emails()
        # Removed the error message when dialog is canceled/rejected 

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
    
    def handle_logout(self):
        # Close this window and show login window
        from main import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()
    
    def show_coming_soon(self):
        QMessageBox.information(self, "Coming Soon", "This feature is coming soon!")

def parse_date(date_str):
    """Parse date string into QDateTime object using multiple formats"""
    # Try parsing with Qt.DateFormat.TextDate first
    date = QDateTime.fromString(date_str, Qt.DateFormat.TextDate)
    
    # If that fails, try other formats
    if not date.isValid():
        date = QDateTime.fromString(date_str, Qt.DateFormat.ISODate)
    
    # If still not valid, try RFC 2822 format
    if not date.isValid():
        date = QDateTime.fromString(date_str, Qt.DateFormat.RFC2822Date)
    
    # If still not valid, try a custom format for dates with timezone info
    if not date.isValid() and "(" in date_str:
        # Remove timezone name in parentheses
        clean_date = date_str.split("(")[0].strip()
        date = QDateTime.fromString(clean_date, "ddd, dd MMM yyyy hh:mm:ss")
    
    # If still not valid, try a custom format
    if not date.isValid():
        date = QDateTime.fromString(date_str, "ddd, dd MMM yyyy hh:mm:ss")
    
    # If still not valid, create a default date
    if not date.isValid():
        date = QDateTime.currentDateTime()
        
    return date 