# --- START OF FILE search_ui.py ---

import sys
import os
# Conditionally import ctypes for Windows features (console hiding)
if os.name == 'nt':
    import ctypes

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QSpacerItem, QSizePolicy, QGraphicsOpacityEffect
)
# --- Add QPoint import ---
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QEvent, pyqtSignal, pyqtSlot, QPoint
# --- End Add ---
# Import QTextDocument for HTML to plain text conversion
from PyQt6.QtGui import QIcon, QFont, QColor, QKeySequence, QShortcut, QGuiApplication, QTextDocument

# Import database functions
import database as db

# ==================================
#      UI Size & Position Configuration
# ==================================
MAIN_WINDOW_WIDTH = 635
MAIN_WINDOW_HEIGHT = 59  # Initial height (search bar only)
EXPANDED_HEIGHT = 450    # Maximum expanded height (adjust as needed)
SEARCH_BAR_HEIGHT = 40
LIST_ITEM_HEIGHT = 65   # Increased height for two lines
MAX_VISIBLE_ITEMS = 5   # Max items before scroll (adjust as needed)
NO_RESULT_ITEM_HEIGHT = 40 # Height for the "No results" item

# ==================================
#      Global Dark Style Sheet (QSS) - Modified for two-line items
# ==================================
DARK_STYLE_SHEET = """
/* Global settings */
QWidget {
    background-color: #181c21; /* Primary background color */
    color: #f0f0f0;            /* Light gray text */
    font-family: Segoe UI, Arial, sans-serif;
    font-size: 10pt;
    border: none;
}

/* Main Window Container */
#MainWindowContainer {
    background-color: #181c21;
    border: 1px solid #3c3c3c;
    border-radius: 4px; /* Subtle rounded corners */
}

/* Search Input Field */
QLineEdit#SearchInput {
    background-color: #181c21;
    color: #f0f0f0;
    font-size: 14pt;
    border: none;
    padding: 6px;
    selection-background-color: #4a535e;
}

/* Editor Icon Button */
QPushButton#EditorIcon {
    background-color: transparent;
    color: #e0e0e0;
    font-size: 16pt; /* Adjust if needed */
    min-width: 30px;
    border: none;
    padding: 0px 5px; /* Adjust padding */
}

QPushButton#EditorIcon:hover {
    color: #ffffff;
    background-color: #3a3b40; /* Subtle hover background */
    border-radius: 3px;
}

QPushButton#EditorIcon:pressed {
    color: #cccccc;
    background-color: #464766;
}

/* Separators */
#HorizontalLine {
    background-color: #2a3038;
    max-height: 1px;
    min-height: 1px;
}

/* List Widget for Results */
QListWidget {
    background-color: #181c21;
    color: #f0f0f0;
    border: none;
    outline: none; /* Remove focus outline */
    padding: 5px 0px; /* Adjust padding */
}

QListWidget::item {
    background-color: #181c21;
    padding: 0px; /* Padding handled by item widget */
    border: none;
    /* border-left: 2px solid transparent; */ /* Removed, handled by item widget style */
    margin: 1px 0px; /* Small margin between items */
}

QListWidget::item:selected {
    background-color: #1c2026; /* Slightly darker selection */
    color: #f0f0f0;
    /* border-left: 2px solid #4a95eb; */ /* Removed */
}

QListWidget::item:hover {
    background-color: #1c2026; /* Same as selected for simplicity */
    /* border-left: 2px solid #3a7fcb; */ /* Removed */
}

/* Custom List Item Styling */
QWidget#ResultItemWidget {
    background-color: transparent;
    border-left: 3px solid transparent; /* Default border */
    border-radius: 3px;
}
QWidget#ResultItemWidget:hover {
    background-color: #2a3038;
    border-left: 3px solid #3a7fcb; /* Hover border */
}
QWidget#ResultItemWidget.selected { /* Custom property for selection */
    background-color: #2c323a;
    border-left: 3px solid #4a95eb; /* Selected border */
}


QLabel#ItemTitle {
    background-color: transparent;
    font-size: 10pt; /* Slightly smaller for path */
    font-weight: normal;
    color: #a0a0a0; /* Grayish color for path */
    padding: 0px 8px;
}

QLabel#ItemDescription {
    background-color: transparent;
    color: #e0e0e0; /* Main description color */
    font-size: 9pt;
    font-weight: normal; /* Normal weight for description */
    padding: 0px 8px;
}

/* Styling for the "No results" label */
QLabel#NoResultLabel {
    background-color: transparent;
    color: #888;
    font-size: 10pt;
    padding: 10px; /* Add padding */
    alignment: AlignCenter; /* Use Qt alignment property */
}


/* Scrollbar styling */
QScrollBar:vertical {
    border: none;
    background: #181c21;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #3c3c3c;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover { background: #4c4c4c; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
"""

class SearchUIWindow(QMainWindow):
    # Signal to request opening the editor
    open_editor_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Set window flags: Frameless, Stay on Top (optional but common for launchers)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        # Make background transparent for potential acrylic effect (requires OS support)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.initUI()
        self.drag_position = None # For window dragging

        # Timer to auto-hide if focus is lost (Optional - can be enabled)
        # self.focus_timer = QTimer(self)
        # self.focus_timer.setInterval(200) # Check every 200ms
        # self.focus_timer.timeout.connect(self.check_focus)
        # self.focus_timer.start() # Start checking focus

    def center_window(self):
         # Center the window on the primary screen
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        # Position slightly above center vertically (e.g., 1/3 down)
        y = (screen_geometry.height() // 3) - (self.height() // 2)
        # Ensure y is not negative if window is tall
        y = max(20, y) # Keep at least 20px from top
        self.move(x, y)

    @pyqtSlot() # Decorator to ensure it's callable via invokeMethod
    def show_and_prepare(self):
        """Shows the window, clears input, centers, and sets focus."""
        print("SearchUIWindow.show_and_prepare() called") # DEBUG
        self.search_input.clear()
        self.results_list.clear()
        self.results_list.setVisible(False)
        self.separator.setVisible(False)
        # Reset height before centering, in case it was expanded
        self.setFixedHeight(MAIN_WINDOW_HEIGHT)
        self.center_window()

        # --- MODIFICATION START ---
        self.show()
        self.raise_() # Raise visually first

        # Use a timer to delay both activation and focus setting
        # Increased delay slightly to 100ms for robustness on first launch
        QTimer.singleShot(100, self._activate_and_focus)
        # --- MODIFICATION END ---

        # self.focus_timer.start() # Restart focus check if using it

    # --- ADDED HELPER METHOD ---
    def _activate_and_focus(self):
        """Helper function called by timer to activate window and set focus."""
        print("Timer executing _activate_and_focus") # DEBUG
        self.activateWindow() # Now activate
        self.search_input.setFocus() # Set focus to the input field
    # --- END ADDED HELPER METHOD ---

    @pyqtSlot() # Decorator to ensure it's callable via invokeMethod
    def hide_window(self):
        """Hides the window and clears state."""
        print("SearchUIWindow.hide_window() called") # DEBUG
        # self.focus_timer.stop() # Stop checking focus when hidden
        self.hide()
        # Clear input/results when hiding
        self.search_input.clear()
        self.results_list.clear()
        self.results_list.setVisible(False)
        self.separator.setVisible(False)
        self.setFixedHeight(MAIN_WINDOW_HEIGHT) # Reset height


    def initUI(self):
        self.setWindowTitle('Prompt Search')
        # Start with fixed small size - important for initial centering
        self.setFixedSize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)

        # Main container widget
        self.central_widget = QWidget()
        self.central_widget.setObjectName("MainWindowContainer")
        self.setCentralWidget(self.central_widget)

        # Main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Search bar container
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        # Reduced margins for a tighter look
        search_layout.setContentsMargins(5, 5, 10, 5) # Left, Top, Right, Bottom

        # Editor icon button
        self.editor_icon = QPushButton("⚙️") # Settings gear icon
        self.editor_icon.setObjectName("EditorIcon")
        self.editor_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.editor_icon.setToolTip("Open Prompt Editor (Ctrl+E)")
        self.editor_icon.setFixedSize(30, 30) # Ensure fixed size
        self.editor_icon.clicked.connect(self.request_open_editor)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search prompt titles...")
        self.search_input.setFixedHeight(SEARCH_BAR_HEIGHT)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.on_return_pressed) # Handle Enter key

        # Add to search layout
        search_layout.addWidget(self.editor_icon)
        search_layout.addWidget(self.search_input)

        # Horizontal line separator
        self.separator = QWidget()
        self.separator.setObjectName("HorizontalLine")
        self.separator.setFixedHeight(1)
        self.separator.setVisible(False) # Hide initially

        # Results list
        self.results_list = QListWidget()
        self.results_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.results_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results_list.setVisible(False)  # Hide initially
        self.results_list.setObjectName("ResultsList")
        self.results_list.setFocusPolicy(Qt.FocusPolicy.NoFocus) # Prevent list from taking focus

        # --- CHANGE: Connect itemPressed instead of itemActivated ---
        # self.results_list.itemActivated.connect(self.on_item_selected) # Triggered by Enter/Double-click
        self.results_list.itemPressed.connect(self.on_item_selected) # Triggered by Mouse Press Down
        # --- END CHANGE ---

        self.results_list.itemSelectionChanged.connect(self.highlight_selected_item)
        self.results_list.setUniformItemSizes(True) # Optimization

        # Add widgets to main layout
        main_layout.addWidget(search_container)
        main_layout.addWidget(self.separator)
        main_layout.addWidget(self.results_list, 1)  # Give results list stretch factor

        # Apply stylesheet
        self.setStyleSheet(DARK_STYLE_SHEET)

        # Setup shortcuts
        QShortcut(QKeySequence("Ctrl+E"), self, self.request_open_editor)
        QShortcut(QKeySequence(Qt.Key.Key_Down), self, self.select_next_item)
        QShortcut(QKeySequence(Qt.Key.Key_Up), self, self.select_previous_item)
        # Use hide_window for Escape
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.hide_window)


    def add_search_results(self, search_text=""):
        """Add search results based on the search text (prompt title)."""
        self.results_list.clear()

        if not search_text:
            self.results_list.setVisible(False)
            self.separator.setVisible(False)
            self.adjust_window_height(False) # Collapse window
            return

        # Query database
        results = db.search_prompts_by_title(search_text)

        if not results:
            # --- FIX: Create "No results" item ---
            item_widget = QWidget() # Simple widget container
            item_layout = QHBoxLayout(item_widget) # Use QHBoxLayout for centering
            item_layout.setContentsMargins(0, 0, 0, 0)
            no_result_label = QLabel("No matching prompts found.")
            no_result_label.setObjectName("NoResultLabel") # For specific styling
            no_result_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center text
            item_layout.addWidget(no_result_label) # Add label to layout

            list_item = QListWidgetItem()
            # Set a fixed height for this specific item
            list_item.setSizeHint(QSize(self.results_list.width(), NO_RESULT_ITEM_HEIGHT))
            list_item.setFlags(list_item.flags() & ~Qt.ItemFlag.ItemIsSelectable) # Not selectable
            self.results_list.addItem(list_item)
            self.results_list.setItemWidget(list_item, item_widget)
            # --- END FIX ---

        else:
            for result in results:
                # Create widget for list item
                item_widget = QWidget()
                item_widget.setObjectName("ResultItemWidget") # For styling selected state
                item_layout = QVBoxLayout(item_widget)
                item_layout.setContentsMargins(5, 5, 5, 5) # Padding inside the item
                item_layout.setSpacing(2) # Spacing between title and description

                # Title/Path Label
                path_text = f"{result['category_name']} > {result['section_name']} > {result['prompt_title']}"
                title_label = QLabel(path_text)
                title_label.setObjectName("ItemTitle")
                title_label.setWordWrap(True) # Allow wrapping if too long

                # Description Label
                desc_text = result['prompt_description'] or "No description"
                desc_label = QLabel(desc_text)
                desc_label.setObjectName("ItemDescription")
                desc_label.setWordWrap(True)

                item_layout.addWidget(title_label)
                item_layout.addWidget(desc_label)

                # Create list item and set widget
                list_item = QListWidgetItem()
                # Store the full prompt content in the item's data
                list_item.setData(Qt.ItemDataRole.UserRole, result['prompt_content'])
                list_item.setSizeHint(QSize(self.results_list.width() - 10, LIST_ITEM_HEIGHT)) # Adjust width slightly for scrollbar

                self.results_list.addItem(list_item)
                self.results_list.setItemWidget(list_item, item_widget)

        # Show results list and separator
        self.results_list.setVisible(True)
        self.separator.setVisible(True)

        # Select the first item if results exist
        if results:
            self.results_list.setCurrentRow(0)

        # Adjust window height smoothly
        # Pass the count of actual results, or 1 if only the "No results" message is shown
        item_count_for_height = len(results) if results else 1
        self.adjust_window_height(True, item_count_for_height)


    def adjust_window_height(self, expand, item_count=0):
        """Animates window height change."""
        current_height = self.height()
        target_height = MAIN_WINDOW_HEIGHT

        if expand and item_count > 0:
            # Calculate height needed for items + search bar + padding/separator
            # Use specific height for "No results" item if item_count is 1 and results were empty
            height_per_item = NO_RESULT_ITEM_HEIGHT if item_count == 1 and not self.results_list.item(0).flags() & Qt.ItemFlag.ItemIsSelectable else LIST_ITEM_HEIGHT
            list_height = min(item_count, MAX_VISIBLE_ITEMS) * height_per_item
            # Add some padding/margins/separator height
            extra_space = 10 # Adjust as needed
            target_height = MAIN_WINDOW_HEIGHT + list_height + extra_space
            target_height = min(target_height, EXPANDED_HEIGHT) # Cap at max height

        if current_height != target_height:
            # Simple resize for now, animation can be added if needed
            # Use setFixedHeight to prevent user resizing during animation/adjustment
            self.setFixedHeight(target_height)


    def highlight_selected_item(self):
        """Applies a visual style to the selected item's widget."""
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            widget = self.results_list.itemWidget(item)
            if widget:
                # Only apply selected style if the item is actually selectable
                is_selectable = bool(item.flags() & Qt.ItemFlag.ItemIsSelectable)
                if item.isSelected() and is_selectable:
                    widget.setProperty("class", "selected") # Use custom property for styling
                else:
                    widget.setProperty("class", "") # Reset property
                # Re-apply stylesheet to update appearance
                widget.style().unpolish(widget)
                widget.style().polish(widget)


    def on_search_text_changed(self, text):
        """Handle search text changes."""
        self.add_search_results(text.strip())

    def on_item_selected(self, item):
        """Handle item press (mouse down)."""
        print(f"on_item_selected (itemPressed) called for item: {item.text() if item else 'None'}") # Debug print
        if item and (item.flags() & Qt.ItemFlag.ItemIsSelectable): # Ensure item is valid and selectable
            self.copy_prompt_and_hide(item)

    def on_return_pressed(self):
        """Handle Enter key press."""
        print("on_return_pressed called") # Debug print
        current_item = self.results_list.currentItem()
        if current_item and (current_item.flags() & Qt.ItemFlag.ItemIsSelectable): # Check if selectable
            self.copy_prompt_and_hide(current_item)

    def copy_prompt_and_hide(self, item):
        """Copies the prompt content to clipboard and hides the window."""
        print("copy_prompt_and_hide called") # Debug print
        html_content = item.data(Qt.ItemDataRole.UserRole)
        if html_content:
            # Convert HTML to Plain Text
            temp_doc = QTextDocument()
            temp_doc.setHtml(html_content)
            plain_text_content = temp_doc.toPlainText()

            clipboard = QApplication.clipboard()
            clipboard.setText(plain_text_content) # Copy plain text
            print(f"Copied plain text: {plain_text_content[:50]}...") # Log snippet
            self.hide_window() # Hide after copying
        else:
            print("No content found in selected item data.")


    def select_next_item(self):
        current_row = self.results_list.currentRow()
        count = self.results_list.count()
        if count > 0:
            # Ensure only selectable items are counted if "No results" item exists
            selectable_indices = [i for i in range(count) if self.results_list.item(i).flags() & Qt.ItemFlag.ItemIsSelectable]
            if not selectable_indices: return # No selectable items

            try:
                current_selectable_index = selectable_indices.index(current_row)
                next_selectable_index = (current_selectable_index + 1) % len(selectable_indices)
            except ValueError: # current_row might be -1 or the non-selectable item
                next_selectable_index = 0 # Select the first selectable item

            next_row = selectable_indices[next_selectable_index]
            self.results_list.setCurrentRow(next_row)


    def select_previous_item(self):
        current_row = self.results_list.currentRow()
        count = self.results_list.count()
        if count > 0:
            selectable_indices = [i for i in range(count) if self.results_list.item(i).flags() & Qt.ItemFlag.ItemIsSelectable]
            if not selectable_indices: return # No selectable items

            try:
                current_selectable_index = selectable_indices.index(current_row)
                prev_selectable_index = (current_selectable_index - 1 + len(selectable_indices)) % len(selectable_indices)
            except ValueError: # current_row might be -1 or the non-selectable item
                 prev_selectable_index = len(selectable_indices) - 1 # Select the last selectable item

            prev_row = selectable_indices[prev_selectable_index]
            self.results_list.setCurrentRow(prev_row)


    def request_open_editor(self):
        """Emits the signal to open the editor and hides itself."""
        print("Requesting to open editor...")
        self.open_editor_requested.emit()
        self.hide_window() # Hide search UI

    def check_focus(self):
        """Hides the window if it loses focus."""
        if not self.isActiveWindow():
            # Add a small delay in case focus is briefly lost (e.g., context menu)
            # QTimer.singleShot(300, lambda: self.hide() if not self.isActiveWindow() else None)
            # Simpler: hide immediately if focus lost
             self.hide_window()


    # --- Window Dragging ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
             # Check if the press is within the search container area (draggable area)
            search_container_rect = self.central_widget.layout().itemAt(0).widget().geometry()
            if search_container_rect.contains(event.pos()):
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
            else:
                # If click is outside draggable area (e.g., on results list), ignore for dragging
                self.drag_position = None
                # Don't ignore the event here, let the list widget handle its press
                # event.ignore()
                super().mousePressEvent(event) # Pass event to base class
        else:
            # event.ignore()
             super().mousePressEvent(event) # Pass event to base class


    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        else:
            # event.ignore()
            super().mouseMoveEvent(event) # Pass event to base class

    def mouseReleaseEvent(self, event):
        self.drag_position = None
        # event.accept()
        super().mouseReleaseEvent(event) # Pass event to base class

    # --- Event Filter for Focus ---
    # def event(self, event):
    #     # Override event handling to detect focus loss
    #     if event.type() == QEvent.Type.WindowDeactivate:
    #         self.hide_window() # Hide when focus is lost
    #     return super().event(event)


# Example usage (for testing search UI independently)
if __name__ == '__main__':
    # Hide Console Window (Windows Specific) - Keep disabled for testing
    # if os.name == 'nt':
    #     try:
    #         hwnd_console = ctypes.windll.kernel32.GetConsoleWindow()
    #         if hwnd_console != 0:
    #             ctypes.windll.user32.ShowWindow(hwnd_console, 0) # SW_HIDE = 0
    #     except Exception as e:
    #         print(f"Info: Could not hide console window ({e})", file=sys.stderr)

    app = QApplication(sys.argv)
    db.initialize_database() # Ensure DB exists

    window = SearchUIWindow()
    window.show_and_prepare() # Use the correct show method

    sys.exit(app.exec())
# --- END OF FILE search_ui.py ---