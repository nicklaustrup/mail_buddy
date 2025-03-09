from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QListWidget, QTextEdit,
                            QPushButton, QListWidgetItem, QMessageBox, QFrame,
                            QSplitter)
from PyQt6.QtCore import Qt, QTimer, QDateTime, QThread
from PyQt6.QtGui import QCursor
from email_handler import EmailHandler
from compose_dialog import ComposeDialog
from search_filter_widget import CompactSearchWidget
from email_worker import EmailWorker


class EmailListItem(QListWidgetItem):
    def __init__(self, email_data):
        super().__init__()
        self.email_data = email_data
        self.update_display()
        
    def update_display(self):
        date = QDateTime.fromString(
            self.email_data['date'],
            Qt.DateFormat.TextDate
        )
        formatted_date = date.toString('MM/dd/yyyy hh:mm AP')
        
        # Create a display with bold sender name
        display_text = (
            f"<b>{self.email_data['from']}</b>\n"
            f"{self.email_data['subject']}\n"
            f"{formatted_date}"
        )
        self.setText(display_text)
        self.setTextAlignment(Qt.AlignmentFlag.AlignLeft)


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
        self.setWindowTitle(f"Email Client - {email}")
        self.setMinimumSize(1000, 700)
        
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
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                }
                QListWidget::item:selected {
                    background-color: #e1f0ff;
                    color: black;
                }
            """)
            
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
                    padding: 10px;
                    margin-bottom: 10px;
                }
                QLabel {
                    color: #444;
                    font-size: 13px;
                    padding: 5px 0;
                }
                QLabel#subject_label, QLabel#from_label, QLabel#to_label, QLabel#date_label {
                    font-weight: normal;
                }
                QLabel#from_label {
                    font-weight: bold;
                }
            """)
            header_layout = QVBoxLayout(header_widget)
            header_layout.setSpacing(5)
            
            # Create labels
            self.email_labels = {}
            for key in ['subject', 'from', 'to', 'date']:
                label = QLabel("")
                label.setObjectName(f"{key}_label")
                header_layout.addWidget(label)
                self.email_labels[key] = label
            
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
                    background-color: #f5f5f5;
                }
                QSplitter::handle {
                    background-color: #ddd;
                    margin: 1px;
                }
                QSplitter::handle:hover {
                    background-color: #ccc;
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
        date = QDateTime.fromString(
            email_data['date'],
            Qt.DateFormat.TextDate
        )
        formatted_date = date.toString('MM/dd/yyyy hh:mm AP')
        
        # Set the email details
        self.email_labels['subject'].setText(email_data['subject'])
        self.email_labels['from'].setText(email_data['from'])
        self.email_labels['date'].setText(formatted_date)
        
        # Set the To field (use recipient from email or default to user's email)
        to_field = email_data.get('to', self.email)
        self.email_labels['to'].setText(to_field)
        
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