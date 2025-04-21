# --- START OF FILE editor_ui.py ---

import sys
import os
import functools # For partial function application in menus
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSizeGrip, QSplitter, QTextEdit, QDialog,
    QLineEdit, QColorDialog, QComboBox, QToolBar, QMessageBox, # Keep QColorDialog import for now, just in case, but we won't use it for the grid
    QInputDialog, QListWidget, QListWidgetItem, QFrame, QScrollArea,
    QPlainTextEdit, QMenu, QToolTip, QStyle, QSizePolicy,
    QGridLayout # <--- Added QGridLayout
)
# Ensure QPoint is imported
from PyQt6.QtCore import Qt, QSize, QPoint, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QColor, QAction, QFont, QTextCursor, QKeySequence, QMouseEvent # Import QMouseEvent

# Import the custom title bar
try:
    # --- CHANGE: Relative import assuming TitleBar.py is in a 'Template' subdirectory ---
    # Adjust this path if your structure is different
    from Template.TitleBar import CustomTitleBar
    # --- END CHANGE ---
except ImportError:
    print("WARNING: Could not import CustomTitleBar from Template.TitleBar. Using dummy.")
    # Define a dummy class if needed for testing without the title bar
    class CustomTitleBar(QWidget):
        closing = pyqtSignal()
        minimizing = pyqtSignal()
        maximizing = pyqtSignal()
        def __init__(self, parent):
            super().__init__(parent)
            layout = QHBoxLayout(self)
            self.title_label = QLabel(f"Dummy Title Bar for {parent.windowTitle()}")
            layout.addWidget(self.title_label)
            self.btn_close = QPushButton("X")
            self.btn_minimize = QPushButton("_")
            self.btn_maximize = QPushButton("[]")
            layout.addWidget(self.btn_minimize)
            layout.addWidget(self.btn_maximize)
            layout.addWidget(self.btn_close)
            self.setFixedHeight(30)
            self.setObjectName("CustomTitleBar") # Add object name for styling
            # Connect dummy signals/slots
            self.btn_close.clicked.connect(parent.close)
            self.btn_minimize.clicked.connect(parent.showMinimized)
            self.btn_maximize.clicked.connect(self._toggle_maximize_dummy)
            self._maximized = False

        def setWindowTitle(self, title):
            if hasattr(self, 'title_label'):
                self.title_label.setText(title)

        def _toggle_maximize_dummy(self):
             if self._maximized:
                 self.parent().showNormal()
             else:
                 self.parent().showMaximized()
             self._maximized = not self._maximized


# Import database functions
import database as db

# Dialog for adding/renaming Category/Section/Prompt
class ItemDialog(QDialog):
    def __init__(self, title, label, current_value="", parent=None):
        super().__init__(parent)
        # --- ADD Frameless Hint ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        # --- Store drag position ---
        self._drag_pos = None

        # --- Main container and layout ---
        container_widget = QWidget(self)
        container_widget.setObjectName("DialogContainer") # For potential styling
        main_layout = QVBoxLayout(self) # Layout for the QDialog itself
        main_layout.setContentsMargins(1, 1, 1, 1) # Border effect
        main_layout.setSpacing(0)
        main_layout.addWidget(container_widget) # Add container to dialog layout

        # --- Layout for content inside the container ---
        content_layout = QVBoxLayout(container_widget)
        content_layout.setContentsMargins(0, 0, 0, 0) # No margins for inner content
        content_layout.setSpacing(0)

        # --- ADD Custom Title Bar ---
        self.title_bar = CustomTitleBar(self)
        self.title_bar.setWindowTitle(title) # Set title on custom bar
        # Dialogs typically don't maximize, so hide or disable the maximize button
        if hasattr(self.title_bar, 'btn_maximize'):
            self.title_bar.btn_maximize.hide() # Or setEnabled(False)
        # Connect close button to dialog's reject slot
        if hasattr(self.title_bar, 'btn_close'):
             # Disconnect default parent.close if it exists (might not in dummy)
             try: self.title_bar.btn_close.clicked.disconnect()
             except TypeError: pass # No connection to disconnect
             self.title_bar.btn_close.clicked.connect(self.reject) # Connect to reject
        # Hide minimize button for dialogs
        if hasattr(self.title_bar, 'btn_minimize'):
             self.title_bar.btn_minimize.hide()

        content_layout.addWidget(self.title_bar)

        # --- Widget for the actual form elements ---
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(15, 10, 15, 15) # Padding for form elements
        form_layout.setSpacing(10) # Spacing between label, input, buttons

        self.name_input = QLineEdit()
        self.name_input.setText(current_value) # Pre-fill for renaming
        form_layout.addWidget(QLabel(label))
        form_layout.addWidget(self.name_input)

        button_layout = QHBoxLayout()
        button_layout.addStretch() # Push buttons to the right
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("DialogCancelButton")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("DialogSaveButton")
        self.save_btn.setDefault(True) # Make Save default
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)

        form_layout.addLayout(button_layout)
        # --- Add form widget to content layout ---
        content_layout.addWidget(form_widget)

        # --- Apply Stylesheet (can be refined) ---
        self.setStyleSheet("""
            #DialogContainer {
                background-color: #191a1f; /* Match main window bg */
            }
            QDialog {
                 border: 1px solid #464766; /* Add border to the dialog itself */
            }
            QLabel {
                color: #b3b0ad;
                font-size: 10pt;
                margin-top: 0px; /* Reset margin if needed */
                padding-bottom: 5px; /* Space below label */
                background-color: transparent; /* Ensure labels are transparent */
            }
            QLineEdit {
                background-color: #1e1e24;
                border: 1px solid #464766;
                border-radius: 3px;
                padding: 5px;
                color: #b3b0ad;
                font-size: 10pt;
            }
            QPushButton#DialogCancelButton, QPushButton#DialogSaveButton {
                background-color: #2a2b30;
                color: #b3b0ad;
                border: 1px solid #464766;
                border-radius: 3px;
                padding: 6px 15px; /* Adjust padding */
                min-width: 70px; /* Ensure minimum width */
            }
            QPushButton#DialogCancelButton:hover, QPushButton#DialogSaveButton:hover {
                background-color: #3a3b40;
                border-color: #5a5b70;
            }
            QPushButton#DialogSaveButton {
                /* Optional: Make save button stand out */
                /* background-color: #4a95eb; */
                /* color: white; */
            }
            QPushButton#DialogSaveButton:hover {
                 /* background-color: #5aa5fc; */
            }
            QPushButton#DialogCancelButton:pressed, QPushButton#DialogSaveButton:pressed {
                background-color: #464766;
            }
            /* Style the custom title bar within the dialog */
            #CustomTitleBar {
                background-color: #25262b;
                border-bottom: 1px solid #464766;
            }
             #CustomTitleBar QLabel { /* Title text */
                 color: #b3b0ad;
                 font-size: 10pt;
                 padding-bottom: 0px; /* Override default label padding */
             }
             #CustomTitleBar QPushButton { /* Buttons on title bar */
                 background-color: transparent;
                 border: none;
                 color: #b3b0ad;
                 padding: 0px;
                 margin: 0px;
                 font-size: 14pt;
                 font-weight: normal;
             }
             #CustomTitleBar QPushButton:hover {
                 background-color: #4a4b50;
             }
             #CustomTitleBar #CloseButton:hover { /* Specific hover for close */
                 background-color: #e81123;
                 color: white;
             }
             #CustomTitleBar QPushButton:pressed {
                 background-color: #6b6c70;
             }
        """)

        self.name_input.setFocus() # Focus input field

    def get_value(self):
        return self.name_input.text().strip()

    # --- ADD Mouse Events for Dragging ---
    def mousePressEvent(self, event):
        # Check if the press is within the custom title bar's geometry
        if hasattr(self, 'title_bar') and self.title_bar.geometry().contains(event.pos()):
             if event.button() == Qt.MouseButton.LeftButton:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
             else:
                 self._drag_pos = None
                 super().mousePressEvent(event) # Pass other button presses
        else:
            self._drag_pos = None
            super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

# --- Custom Confirmation Dialog ---
class ConfirmDialog(QDialog):
    def __init__(self, title, message, informative_text="", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowTitle(title)
        self.setMinimumWidth(400) # Adjust as needed
        self._drag_pos = None

        container_widget = QWidget(self)
        container_widget.setObjectName("DialogContainer")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1) # Border effect
        main_layout.setSpacing(0)
        main_layout.addWidget(container_widget)

        content_layout = QVBoxLayout(container_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # --- Custom Title Bar ---
        self.title_bar = CustomTitleBar(self)
        self.title_bar.setWindowTitle(title)
        # Hide Maximize/Minimize for confirmation dialog
        if hasattr(self.title_bar, 'btn_maximize'): self.title_bar.btn_maximize.hide()
        if hasattr(self.title_bar, 'btn_minimize'): self.title_bar.btn_minimize.hide()
        # Connect Close button to reject the dialog
        if hasattr(self.title_bar, 'btn_close'):
            try: self.title_bar.btn_close.clicked.disconnect()
            except TypeError: pass
            self.title_bar.btn_close.clicked.connect(self.reject)

        content_layout.addWidget(self.title_bar)

        # --- Content Area (Icon + Text) ---
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget) # Use QHBox for icon + text
        body_layout.setContentsMargins(15, 15, 15, 15) # Padding around content
        body_layout.setSpacing(15) # Space between icon and text

        # Icon (Standard Question Icon)
        icon_label = QLabel()
        # Get standard icon from the current style, resize it
        icon_pixmap = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion).pixmap(QSize(48, 48))
        icon_label.setPixmap(icon_pixmap)
        icon_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed) # Don't stretch icon
        body_layout.addWidget(icon_label)

        # Text Area (Main Message + Informative Text)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5) # Space between main and informative text
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True) # Allow text wrapping
        self.message_label.setObjectName("ConfirmMessageLabel") # For specific styling
        text_layout.addWidget(self.message_label)

        if informative_text:
            self.info_label = QLabel(informative_text)
            self.info_label.setWordWrap(True)
            self.info_label.setObjectName("ConfirmInfoLabel") # For specific styling
            text_layout.addWidget(self.info_label)

        text_layout.addStretch() # Push text towards the top
        body_layout.addLayout(text_layout, 1) # Text layout takes expanding space

        content_layout.addWidget(body_widget)

        # --- Button Area ---
        button_widget = QWidget()
        # Use a separate widget for bottom padding if needed, or adjust margins
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(15, 0, 15, 15) # Padding below buttons
        button_layout.setSpacing(10) # Space between buttons
        button_layout.addStretch() # Push buttons to the right

        self.no_btn = QPushButton("No")
        self.no_btn.setObjectName("DialogNoButton") # Style ID
        self.no_btn.clicked.connect(self.reject) # No rejects the dialog
        self.no_btn.setDefault(True) # Make "No" the default action (safer)

        self.yes_btn = QPushButton("Yes")
        self.yes_btn.setObjectName("DialogYesButton") # Style ID
        self.yes_btn.clicked.connect(self.accept) # Yes accepts the dialog

        button_layout.addWidget(self.no_btn)
        button_layout.addWidget(self.yes_btn)

        content_layout.addWidget(button_widget)

        # --- Apply Stylesheet ---
        self.setStyleSheet("""
            #DialogContainer {
                background-color: #191a1f; /* Dark background */
            }
            QDialog {
                 border: 1px solid #464766; /* Border for the dialog */
            }
            QLabel { /* General text color */
                color: #b3b0ad;
                background-color: transparent; /* Ensure labels are transparent */
            }
            #ConfirmMessageLabel {
                font-size: 11pt; /* Slightly larger main message */
                color: #cccccc; /* Brighter color for main message */
            }
            #ConfirmInfoLabel {
                color: #888899; /* Subdued color for informative text */
                font-size: 9pt;
            }

            /* Button Styles */
            QPushButton#DialogNoButton, QPushButton#DialogYesButton {
                background-color: #2a2b30;
                color: #b3b0ad;
                border: 1px solid #464766;
                border-radius: 3px;
                padding: 6px 15px; /* Adjust padding */
                min-width: 70px; /* Ensure minimum width */
            }
            QPushButton#DialogNoButton:hover, QPushButton#DialogYesButton:hover {
                background-color: #3a3b40;
                border-color: #5a5b70;
            }
            QPushButton#DialogYesButton {
                /* Optional: Make Yes button red or distinct */
                /* background-color: #c0392b; */
                /* color: white; */
                /* border-color: #e74c3c; */
            }
            QPushButton#DialogYesButton:hover {
                 /* background-color: #e74c3c; */
            }
            QPushButton#DialogNoButton:pressed, QPushButton#DialogYesButton:pressed {
                background-color: #464766;
            }

            /* Title Bar Styles (Copied from ItemDialog) */
            #CustomTitleBar {
                background-color: #25262b;
                border-bottom: 1px solid #464766;
            }
             #CustomTitleBar QLabel { /* Title text */
                 color: #b3b0ad;
                 font-size: 10pt;
                 padding-bottom: 0px; /* Override default label padding */
             }
             #CustomTitleBar QPushButton { /* Buttons on title bar */
                 background-color: transparent;
                 border: none;
                 color: #b3b0ad;
                 padding: 0px;
                 margin: 0px;
                 font-size: 14pt;
                 font-weight: normal;
             }
             #CustomTitleBar QPushButton:hover {
                 background-color: #4a4b50;
             }
             #CustomTitleBar #CloseButton:hover { /* Specific hover for close */
                 background-color: #e81123;
                 color: white;
             }
             #CustomTitleBar QPushButton:pressed {
                 background-color: #6b6c70;
             }
        """)

    # --- Mouse Events for Dragging (Copied from ItemDialog) ---
    def mousePressEvent(self, event):
        if hasattr(self, 'title_bar') and self.title_bar.geometry().contains(event.pos()):
             if event.button() == Qt.MouseButton.LeftButton:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
             else:
                 self._drag_pos = None
                 super().mousePressEvent(event)
        else:
            self._drag_pos = None
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
# --- End of ConfirmDialog ---

# --- START: ColorGridDialog with FULL Flat UI Colors ---
class ColorGridDialog(QDialog):
    colorSelected = pyqtSignal(str) # Signal emitting the hex color string

    def __init__(self, title="Select Color", initial_color=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowTitle(title)
        # --- ADJUSTED MIN WIDTH TO FIT PALETTE BETTER ---
        # 10 columns * (22px + 4px spacing) - 4px + 2*10px margin = 10*26 - 4 + 20 = 260 - 4 + 20 = 276
        self.setMinimumWidth(300) # Increased width for 10 columns
        # --- END ADJUSTMENT ---
        self._drag_pos = None
        self._selected_color = None # Store the chosen color

        # --- Define the FULL Flat UI color palette ---
        # Extracted from flat_design_colors_full.css
        # Organized by color group, 10 shades each (50-900)
        self.colors = [
            # Turquoise
            "#e8f8f5", "#d1f2eb", "#a3e4d7", "#76d7c4", "#48c9b0", "#1abc9c", "#17a589", "#148f77", "#117864", "#0e6251",
            # Green Sea
            "#e8f6f3", "#d0ece7", "#a2d9ce", "#73c6b6", "#45b39d", "#16a085", "#138d75", "#117a65", "#0e6655", "#0b5345",
            # Emerald
            "#eafaf1", "#d5f5e3", "#abebc6", "#82e0aa", "#58d68d", "#2ecc71", "#28b463", "#239b56", "#1d8348", "#186a3b",
            # Nephritis
            "#e9f7ef", "#d4efdf", "#a9dfbf", "#7dcea0", "#52be80", "#27ae60", "#229954", "#1e8449", "#196f3d", "#145a32",
            # Peter River
            "#ebf5fb", "#d6eaf8", "#aed6f1", "#85c1e9", "#5dade2", "#3498db", "#2e86c1", "#2874a6", "#21618c", "#1b4f72",
            # Belize Hole
            "#eaf2f8", "#d4e6f1", "#a9cce3", "#7fb3d5", "#5499c7", "#2980b9", "#2471a3", "#1f618d", "#1a5276", "#154360",
            # Amethyst
            "#f5eef8", "#ebdef0", "#d7bde2", "#c39bd3", "#af7ac5", "#9b59b6", "#884ea0", "#76448a", "#633974", "#512e5f",
            # Wisteria
            "#f4ecf7", "#e8daef", "#d2b4de", "#bb8fce", "#a569bd", "#8e44ad", "#7d3c98", "#6c3483", "#5b2c6f", "#4a235a",
            # Wet Asphalt
            "#ebedef", "#d6dbdf", "#aeb6bf", "#85929e", "#5d6d7e", "#34495e", "#2e4053", "#283747", "#212f3c", "#1b2631",
            # Midnight Blue
            "#eaecee", "#d5d8dc", "#abb2b9", "#808b96", "#566573", "#2c3e50", "#273746", "#212f3d", "#1c2833", "#17202a",
            # Sunflower
            "#fef9e7", "#fcf3cf", "#f9e79f", "#f7dc6f", "#f4d03f", "#f1c40f", "#d4ac0d", "#b7950b", "#9a7d0a", "#7d6608",
            # Orange
            "#fef5e7", "#fdebd0", "#fad7a0", "#f8c471", "#f5b041", "#f39c12", "#d68910", "#b9770e", "#9c640c", "#7e5109",
            # Carrot
            "#fdf2e9", "#fae5d3", "#f5cba7", "#f0b27a", "#eb984e", "#e67e22", "#ca6f1e", "#af601a", "#935116", "#784212",
            # Pumpkin
            "#fbeee6", "#f6ddcc", "#edbb99", "#e59866", "#dc7633", "#d35400", "#ba4a00", "#a04000", "#873600", "#6e2c00",
            # Alizarin
            "#fdedec", "#fadbd8", "#f5b7b1", "#f1948a", "#ec7063", "#e74c3c", "#cb4335", "#b03a2e", "#943126", "#78281f",
            # Pomegranate
            "#f9ebea", "#f2d7d5", "#e6b0aa", "#d98880", "#cd6155", "#c0392b", "#a93226", "#922b21", "#7b241c", "#641e16",
            # Clouds
            "#fdfefe", "#fbfcfc", "#f7f9f9", "#f4f6f7", "#f0f3f4", "#ecf0f1", "#d0d3d4", "#b3b6b7", "#979a9a", "#7b7d7d",
            # Silver
            "#f8f9f9", "#f2f3f4", "#e5e7e9", "#d7dbdd", "#cacfd2", "#bdc3c7", "#a6acaf", "#909497", "#797d7f", "#626567",
            # Concrete
            "#f4f6f6", "#eaeded", "#d5dbdb", "#bfc9ca", "#aab7b8", "#95a5a6", "#839192", "#717d7e", "#5f6a6a", "#4d5656",
            # Asbestos
            "#f2f4f4", "#e5e8e8", "#ccd1d1", "#b2babb", "#99a3a4", "#7f8c8d", "#707b7c", "#616a6b", "#515a5a", "#424949",
        ]
        self.columns = 10 # Set to 10 columns to match shade groups

        # --- Main container and layout ---
        container_widget = QWidget(self)
        container_widget.setObjectName("DialogContainer")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1) # Border effect
        main_layout.setSpacing(0)
        main_layout.addWidget(container_widget)

        # --- Layout for content inside the container ---
        content_layout = QVBoxLayout(container_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # --- Custom Title Bar ---
        self.title_bar = CustomTitleBar(self)
        self.title_bar.setWindowTitle(title)
        if hasattr(self.title_bar, 'btn_maximize'): self.title_bar.btn_maximize.hide()
        if hasattr(self.title_bar, 'btn_minimize'): self.title_bar.btn_minimize.hide()
        if hasattr(self.title_bar, 'btn_close'):
            try: self.title_bar.btn_close.clicked.disconnect()
            except TypeError: pass
            self.title_bar.btn_close.clicked.connect(self.reject) # Close rejects

        content_layout.addWidget(self.title_bar)

        # --- Color Grid Area ---
        # --- Wrap grid in a ScrollArea for large palettes ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) # No horizontal scroll
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setObjectName("ColorGridScrollArea") # For styling scrollbar if needed

        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(10, 10, 10, 10) # Padding around grid
        grid_layout.setSpacing(4) # Spacing between swatches

        row, col = 0, 0
        for color_hex in self.colors:
            swatch = QPushButton()
            swatch.setFixedSize(22, 22) # Size of color squares
            swatch.setObjectName("ColorSwatch")
            # --- ADDED BORDER TO SWATCH STYLE ---
            swatch.setStyleSheet(f"""
                QPushButton#ColorSwatch {{
                    background-color: {color_hex};
                    border: 1px solid #555; /* Add a subtle border */
                    border-radius: 2px;
                }}
                QPushButton#ColorSwatch:hover {{
                    border: 1px solid #eee; /* Highlight border on hover */
                }}
            """)
            # --- END BORDER ADD ---
            swatch.setToolTip(color_hex.upper())
            # Use partial to pass the color to the handler
            swatch.clicked.connect(functools.partial(self._color_clicked, color_hex))
            grid_layout.addWidget(swatch, row, col)

            col += 1
            if col >= self.columns:
                col = 0
                row += 1

        grid_widget.setLayout(grid_layout) # Set layout on the widget
        scroll_area.setWidget(grid_widget) # Put the grid widget inside the scroll area

        # --- Adjust height based on content ---
        # Calculate approximate height needed for the grid content
        num_rows = (len(self.colors) + self.columns - 1) // self.columns
        grid_height = num_rows * (22 + 4) - 4 + 20 # rows * (swatch+spacing) - last_spacing + margins
        # Set a reasonable maximum height for the scroll area, e.g., 600px
        max_scroll_height = 600
        # Set the scroll area's height (or let it expand up to a max)
        scroll_area.setFixedHeight(min(grid_height, max_scroll_height))

        content_layout.addWidget(scroll_area) # Add scroll area instead of grid_widget directly

        # --- Apply Stylesheet ---
        self.setStyleSheet("""
            #DialogContainer {
                background-color: #191a1f; /* Dark background */
            }
            QDialog {
                 border: 1px solid #464766; /* Border for the dialog */
            }
            /* Title Bar Styles (Copied from ItemDialog) */
            #CustomTitleBar {
                background-color: #25262b;
                border-bottom: 1px solid #464766;
            }
             #CustomTitleBar QLabel { /* Title text */
                 color: #b3b0ad;
                 font-size: 10pt;
                 padding-bottom: 0px;
             }
             #CustomTitleBar QPushButton { /* Buttons on title bar */
                 background-color: transparent;
                 border: none;
                 color: #b3b0ad;
                 padding: 0px;
                 margin: 0px;
                 font-size: 14pt;
                 font-weight: normal;
             }
             #CustomTitleBar QPushButton:hover {
                 background-color: #4a4b50;
             }
             #CustomTitleBar #CloseButton:hover { /* Specific hover for close */
                 background-color: #e81123;
                 color: white;
             }
             #CustomTitleBar QPushButton:pressed {
                 background-color: #6b6c70;
             }
             QToolTip { /* Style the tooltip */
                background-color: #1e1e24;
                color: #b3b0ad;
                border: 1px solid #464766;
                padding: 4px;
                border-radius: 3px;
                opacity: 230; /* Slightly transparent */
            }
            /* Style the ScrollArea and its contents */
            #ColorGridScrollArea {
                border: none; /* Remove border from scroll area */
                background-color: #191a1f; /* Match container background */
            }
            #ColorGridScrollArea QWidget { /* Ensure background of widget inside scroll area is correct */
                 background-color: #191a1f;
            }
            /* Style Scrollbars within the dialog */
            QScrollBar:vertical {
                border: none;
                background: #25262b; /* Slightly different from main bg */
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #464766; /* Handle color */
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px; /* Hide arrows */
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none; /* Hide page area background */
            }

        """)
        # --- Adjust overall dialog height ---
        # Let the layout determine the height, but ensure it's not excessively tall initially
        self.adjustSize() # Adjust size based on content and fixed height of scroll area


    def _color_clicked(self, color_hex):
        """Called when a color swatch is clicked."""
        self._selected_color = color_hex
        self.colorSelected.emit(color_hex) # Emit the signal (optional)
        self.accept() # Close the dialog with Accepted status

    def get_selected_color(self):
        """Returns the hex string of the selected color, or None."""
        return self._selected_color

    # --- Mouse Events for Dragging (Copied from ItemDialog) ---
    def mousePressEvent(self, event):
        if hasattr(self, 'title_bar') and self.title_bar.geometry().contains(event.pos()):
             if event.button() == Qt.MouseButton.LeftButton:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
             else:
                 self._drag_pos = None
                 super().mousePressEvent(event)
        else:
            self._drag_pos = None
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
# --- END: ColorGridDialog ---


# Main window class for the Prompt Editor
class PromptEditorWindow(QMainWindow):
    closing = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.current_category_id = None
        self.current_section_id = None
        self.current_prompt_id = None
        self.clipboard = None # For copy/paste simulation {'id': id, 'type': type}
        self.initUI()
        self.apply_stylesheet() # Apply main window styles

    @pyqtSlot()
    def show_and_activate(self):
        print("PromptEditorWindow.show_and_activate() called")
        self.show()
        self.activateWindow()
        self.raise_()

    def initUI(self):
        self.setWindowTitle('Prompt Editor')
        # User specified geometry and minimum size
        self.setGeometry(18, 50, 1400, 800)
        self.setMinimumSize(800, 800)

        self.container_widget = QWidget()
        self.container_widget.setObjectName("ContainerWidget")
        main_layout = QVBoxLayout(self.container_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.sidebar_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.sidebar_splitter.setObjectName("SidebarSplitter")

        # ====== Categories Panel ======
        categories_panel = QWidget()
        categories_panel.setObjectName("CategoriesPanel")
        categories_layout = QVBoxLayout(categories_panel)
        categories_layout.setContentsMargins(0, 0, 0, 0)
        categories_layout.setSpacing(0)

        categories_header = QWidget()
        categories_header.setObjectName("PanelHeader")
        categories_header_layout = QHBoxLayout(categories_header)
        categories_header_layout.setContentsMargins(10, 10, 10, 10)
        categories_title = QLabel("Categories")
        categories_title.setObjectName("PanelTitle")
        categories_header_layout.addWidget(categories_title)
        categories_header_layout.addStretch()

        self.categories_list_widget = QScrollArea()
        self.categories_list_widget.setWidgetResizable(True)
        self.categories_list_widget.setObjectName("CategoriesList")
        self.categories_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.categories_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.categories_list_widget.customContextMenuRequested.connect(
            lambda pos: self._show_panel_context_menu('category', pos)
        )
        categories_list_container = QWidget()
        self.categories_layout = QVBoxLayout(categories_list_container)
        self.categories_layout.setContentsMargins(0, 0, 0, 0)
        self.categories_layout.setSpacing(1)
        self.categories_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.categories_list_widget.setWidget(categories_list_container)

        categories_layout.addWidget(categories_header)
        categories_layout.addWidget(self.categories_list_widget, 1)

        # ====== Sections Panel ======
        sections_panel = QWidget()
        sections_panel.setObjectName("SectionsPanel")
        sections_layout = QVBoxLayout(sections_panel)
        sections_layout.setContentsMargins(0, 0, 0, 0)
        sections_layout.setSpacing(0)

        sections_header = QWidget()
        sections_header.setObjectName("PanelHeader")
        sections_header_layout = QHBoxLayout(sections_header)
        sections_header_layout.setContentsMargins(10, 10, 10, 10)
        self.sections_title = QLabel("Sections") # Default title
        self.sections_title.setObjectName("PanelTitle")
        sections_header_layout.addWidget(self.sections_title)
        sections_header_layout.addStretch()

        self.sections_list_widget = QScrollArea()
        self.sections_list_widget.setWidgetResizable(True)
        self.sections_list_widget.setObjectName("SectionsList")
        self.sections_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sections_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sections_list_widget.customContextMenuRequested.connect(
             lambda pos: self._show_panel_context_menu('section', pos)
        )
        sections_list_container = QWidget()
        self.sections_layout = QVBoxLayout(sections_list_container)
        self.sections_layout.setContentsMargins(0, 0, 0, 0)
        self.sections_layout.setSpacing(1)
        self.sections_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sections_list_widget.setWidget(sections_list_container)

        sections_layout.addWidget(sections_header)
        sections_layout.addWidget(self.sections_list_widget, 1)

        # ====== Prompts Panel ======
        prompts_panel = QWidget()
        prompts_panel.setObjectName("PromptsPanel")
        prompts_layout = QVBoxLayout(prompts_panel)
        prompts_layout.setContentsMargins(0, 0, 0, 0)
        prompts_layout.setSpacing(0)

        prompts_header = QWidget()
        prompts_header.setObjectName("PanelHeader")
        prompts_header_layout = QHBoxLayout(prompts_header)
        prompts_header_layout.setContentsMargins(10, 10, 10, 10)
        self.prompts_title = QLabel("Prompts") # Default title
        self.prompts_title.setObjectName("PanelTitle")
        prompts_header_layout.addWidget(self.prompts_title)
        prompts_header_layout.addStretch()

        self.prompts_list_widget = QScrollArea()
        self.prompts_list_widget.setWidgetResizable(True)
        self.prompts_list_widget.setObjectName("PromptsList")
        self.prompts_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.prompts_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.prompts_list_widget.customContextMenuRequested.connect(
             lambda pos: self._show_panel_context_menu('prompt', pos)
        )
        prompts_list_container = QWidget()
        self.prompts_layout = QVBoxLayout(prompts_list_container)
        self.prompts_layout.setContentsMargins(0, 0, 0, 0)
        self.prompts_layout.setSpacing(1)
        self.prompts_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.prompts_list_widget.setWidget(prompts_list_container)

        prompts_layout.addWidget(prompts_header)
        prompts_layout.addWidget(self.prompts_list_widget, 1)

        self.sidebar_splitter.addWidget(categories_panel)
        self.sidebar_splitter.addWidget(sections_panel)
        self.sidebar_splitter.addWidget(prompts_panel)
        # Set initial sizes for the 3 sidebar panels (equally distributed within the sidebar)
        self.sidebar_splitter.setSizes([100, 100, 100]) # These will adjust proportionally

        # ====== Editor Area ======
        main_area = QWidget()
        main_area.setObjectName("MainArea")
        main_area_layout = QVBoxLayout(main_area)
        main_area_layout.setContentsMargins(10, 10, 10, 10)
        main_area_layout.setSpacing(5)

        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self.toggle_sidebar_btn = QPushButton("◀")
        self.toggle_sidebar_btn.setObjectName("ToggleSidebarButton")
        self.toggle_sidebar_btn.setToolTip("Toggle Sidebar")
        self.toggle_sidebar_btn.setFixedSize(30, 30)
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)
        toolbar_layout.addWidget(self.toggle_sidebar_btn)
        toolbar_layout.addStretch(1)

        # --- Add Copy Button ---
        self.copy_prompt_btn = QPushButton("Copy Content")
        self.copy_prompt_btn.setObjectName("CopyButton") # Style name
        self.copy_prompt_btn.setToolTip("Copy prompt content to clipboard")
        self.copy_prompt_btn.clicked.connect(self.copy_current_prompt_content)
        self.copy_prompt_btn.setEnabled(False) # Initially disabled
        toolbar_layout.addWidget(self.copy_prompt_btn) # Add BEFORE delete

        self.delete_prompt_btn = QPushButton("Delete Prompt")
        self.delete_prompt_btn.setObjectName("DeleteButton")
        self.delete_prompt_btn.setToolTip("Delete selected prompt (or use Right-Click)")
        self.delete_prompt_btn.clicked.connect(self.delete_current_prompt)
        self.delete_prompt_btn.setEnabled(False) # Initially disabled
        toolbar_layout.addWidget(self.delete_prompt_btn)

        self.prompt_title_input = QLineEdit()
        self.prompt_title_input.setPlaceholderText("Prompt Title")
        self.prompt_title_input.setObjectName("PromptTitleInput")
        self.prompt_title_input.setEnabled(False)
        # Increased height for title input
        self.prompt_title_input.setMaximumHeight(45)
        self.prompt_title_input.editingFinished.connect(self.save_current_prompt_details)

        self.prompt_description_input = QPlainTextEdit()
        self.prompt_description_input.setPlaceholderText("Prompt Description (optional)")
        self.prompt_description_input.setObjectName("PromptDescriptionInput")
        self.prompt_description_input.setMaximumHeight(60)
        self.prompt_description_input.setEnabled(False)
        self.prompt_description_input.textChanged.connect(self.save_current_prompt_details)

        format_toolbar = QToolBar()
        format_toolbar.setObjectName("FormatToolbar")
        bold_action = QAction("B", self)
        bold_action.setToolTip("Bold")
        bold_action.triggered.connect(lambda: self.format_text("bold"))
        format_toolbar.addAction(bold_action)
        italic_action = QAction("I", self)
        italic_action.setToolTip("Italic")
        italic_action.triggered.connect(lambda: self.format_text("italic"))
        format_toolbar.addAction(italic_action)
        underline_action = QAction("U", self)
        underline_action.setToolTip("Underline")
        underline_action.triggered.connect(lambda: self.format_text("underline"))
        format_toolbar.addAction(underline_action)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Select a prompt to view/edit its content...")
        self.editor.setObjectName("PromptContentEditor")
        self.editor.setEnabled(False)
        self.editor.textChanged.connect(self.save_current_prompt_content)

        editor_font = QFont()
        editor_font.setFamily("Segoe UI")
        editor_font.setPointSize(12)
        self.editor.setFont(editor_font)

        main_area_layout.addWidget(toolbar)
        main_area_layout.addWidget(QLabel("Title:"))
        main_area_layout.addWidget(self.prompt_title_input)
        main_area_layout.addWidget(QLabel("Description:"))
        main_area_layout.addWidget(self.prompt_description_input)
        main_area_layout.addWidget(QLabel("Content:"))
        # main_area_layout.addWidget(format_toolbar) # Uncomment if you want the format toolbar
        main_area_layout.addWidget(self.editor, 1)

        self.main_splitter.addWidget(self.sidebar_splitter)
        self.main_splitter.addWidget(main_area)

        # Calculate initial sizes based on window width
        initial_width = self.geometry().width() # Use actual initial width
        sidebar_width = int(initial_width * 0.40) # 40%
        editor_width = initial_width - sidebar_width # Remaining 60%
        self.main_splitter.setSizes([sidebar_width, editor_width])


        content_layout.addWidget(self.main_splitter, 1)
        main_layout.addWidget(content_widget, 1)

        sizegrip = QSizeGrip(self.container_widget)
        main_layout.addWidget(sizegrip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        sizegrip.raise_()

        self.setCentralWidget(self.container_widget)
        self.setup_shortcuts()

        self.load_categories()

    def toggle_sidebar(self):
        current_sizes = self.main_splitter.sizes()
        total_width = sum(current_sizes)
        if current_sizes[0] > 0:
            # Store the current ratio before collapsing
            self.sidebar_ratio = current_sizes[0] / total_width if total_width > 0 else 0.4 # Default to 40% if total is 0
            self.main_splitter.setSizes([0, total_width])
            self.toggle_sidebar_btn.setText("▶")
        else:
            # Restore using the stored ratio or default
            ratio = getattr(self, 'sidebar_ratio', 0.4)
            sidebar_size = int(total_width * ratio)
            editor_size = total_width - sidebar_size
            self.main_splitter.setSizes([sidebar_size, editor_size])
            self.toggle_sidebar_btn.setText("◀")

    def apply_stylesheet(self):
        # Main window stylesheet - Dialog styles are now self-contained
        self.setStyleSheet("""
            #ContainerWidget { background-color: #191a1f; border: 1px solid #464766; }
            QWidget { background-color: transparent; color: #b3b0ad; font-family: 'Segoe UI', Arial; font-size: 10pt; }
            /* Styles for the main window's custom title bar */
            #CustomTitleBar { background-color: #25262b; border-bottom: 1px solid #464766; }
             #CustomTitleBar QLabel { color: #b3b0ad; margin-left: 5px; }
             #CustomTitleBar #MinimizeButton, #CustomTitleBar #MaximizeButton, #CustomTitleBar #CloseButton {
                 background-color: transparent;
                 border: none;
                 color: #b3b0ad;
                 padding: 0px;
                 margin: 0px;
                 font-size: 14pt;
                 font-weight: normal; /* Changed from bold */
             }
             #CustomTitleBar #MinimizeButton { padding-bottom: 8px; }
             #CustomTitleBar #MinimizeButton:hover, #CustomTitleBar #MaximizeButton:hover { background-color: #4a4b50; }
             #CustomTitleBar #CloseButton:hover { background-color: #e81123; color: white; }
             #CustomTitleBar #MinimizeButton:pressed, #CustomTitleBar #MaximizeButton:pressed, #CustomTitleBar #CloseButton:pressed { background-color: #6b6c70; }
            /* End Main Window Title Bar Styles */

            #SidebarSplitter::handle { background-color: #464766; width: 1px; }
            #CategoriesPanel, #SectionsPanel, #PromptsPanel { background-color: #25262b; border-right: 1px solid #464766; }
            #PanelHeader { background-color: #25262b; border-bottom: 1px solid #464766; }
            #CategoriesList, #SectionsList, #PromptsList { background-color: #25262b; border: none; }
            #PanelTitle { font-weight: bold; font-size: 11pt; padding-left: 5px; }

            /* --- Toolbar Button Styles --- */
            #ToggleSidebarButton, #CopyButton, #DeleteButton {
                background-color: transparent;
                color: #b3b0ad;
                border: 1px solid #464766;
                border-radius: 3px;
                padding: 5px 10px; /* Adjusted padding */
                min-width: 60px; /* Ensure minimum width */
            }
            #ToggleSidebarButton:hover, #CopyButton:hover, #DeleteButton:hover {
                background-color: #464766;
            }
            #CopyButton { /* Optional: Slightly different look for Copy */
                 /* color: #4a95eb; */
            }
            #CopyButton:hover {
                 /* background-color: #3a85d6; */
                 /* color: white; */
            }
            #DeleteButton {
                color: #e74c3c; /* Red color for delete */
            }
            #DeleteButton:hover {
                background-color: #c0392b;
                color: white;
            }
            /* --- Disabled State for Toolbar Buttons --- */
            #CopyButton:disabled, #DeleteButton:disabled {
                background-color: #2a2b30; /* Darker background */
                color: #777; /* Greyed out text */
                border-color: #3a3b40; /* Darker border */
            }
            /* --- End Toolbar Button Styles --- */

            #MainArea { background-color: #191a1f; }

            #PromptTitleInput, #PromptDescriptionInput, #PromptContentEditor {
                background-color: #1e1e24; border: 1px solid #464766; border-radius: 3px; padding: 5px; color: #b3b0ad;
            }
            QLineEdit#PromptTitleInput { font-size: 16pt; }
            QPlainTextEdit#PromptDescriptionInput { font-size: 16pt; }
            QTextEdit#PromptContentEditor { font-size: 18pt; }

            #PromptTitleInput:disabled, #PromptDescriptionInput:disabled, #PromptContentEditor:disabled {
                 background-color: #2a2b30; color: #777; border-color: #3a3b40;
            }
            QLabel { color: #888; font-size: 9pt; margin-top: 5px; background-color: transparent; } /* General Labels */
            QPushButton { background-color: transparent; border: none; padding: 8px 16px; border-radius: 3px; } /* General Buttons */
            QPushButton:hover { background-color: #464766; }
            QLineEdit { background-color: #1e1e24; border: 1px solid #464766; border-radius: 3px; padding: 5px; } /* General LineEdits */

            .ListItemWidget { background-color: transparent; padding: 6px 8px; border: none; border-radius: 3px; }
            .ListItemWidget:hover { background-color: #3a3b40; }
            .ListItemWidget.selected { background-color: #464766; }
            .ListItemWidget QLabel { color: #b3b0ad; font-size: 10pt; margin-top: 0px; }
            .ListItemWidget .ColorIndicator { border-radius: 3px; margin-right: 5px; }
            QScrollArea { border: none; }
            QScrollBar:vertical { border: none; background: #25262b; width: 10px; margin: 0px; }
            QScrollBar::handle:vertical { background: #464766; min-height: 20px; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
            QMenu { background-color: #2a2b30; border: 1px solid #464766; color: #b3b0ad; }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #464766; }
            QMenu::separator { height: 1px; background-color: #464766; margin: 4px 0px; }
            QToolTip { /* Style the tooltip */
                background-color: #1e1e24;
                color: #b3b0ad;
                border: 1px solid #464766;
                padding: 4px;
                border-radius: 3px;
                opacity: 230; /* Slightly transparent */
            }
        """)

    def _clear_layout(self, layout):
        if layout is not None:
            if hasattr(layout, 'count'):
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    elif item.layout() is not None:
                        self._clear_layout(item.layout())
            else:
                print(f"Warning: _clear_layout called with non-layout object: {type(layout)}")


    def _create_list_item(self, item_data, item_type):
        """Creates a widget for a list item with context menu."""
        item_id = item_data['id']
        item_data_dict = dict(item_data)

        name = f"Error ({item_type})"
        try:
            if item_type == 'category' or item_type == 'section':
                raw_name = item_data_dict.get('name')
                name = raw_name if raw_name else f"Unnamed {item_type.capitalize()}"
            elif item_type == 'prompt':
                raw_name = item_data_dict.get('title')
                name = raw_name if raw_name else "Untitled Prompt"
            else:
                name = 'Unknown Item'
        except Exception as e:
             print(f"ERROR in _create_list_item getting name for ID={item_id}, Type={item_type}: {e}")
             name = f"Error ({item_type})"

        item_widget = QWidget()
        item_widget.setObjectName(f"item_{item_type}_{item_id}")
        item_widget.setProperty("class", "ListItemWidget")
        item_widget.setProperty("itemId", item_id)
        item_widget.setProperty("itemType", item_type)
        item_widget.setProperty("itemData", item_data_dict)

        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 2, 5, 2)
        item_layout.setSpacing(5)

        if item_type == 'category' or item_type == 'section':
            color_indicator = QLabel()
            color_indicator.setFixedSize(15, 15)
            color_indicator.setObjectName("ColorIndicator")
            default_color = '#e0e0e0' if item_type == 'category' else '#d0d0d0'
            item_color = item_data_dict.get('color', default_color)
            if not item_color or not item_color.startswith('#') or len(item_color) not in [4, 7]:
                 item_color = default_color
            # Ensure the color indicator style is applied correctly
            color_indicator.setStyleSheet(f"background-color: {item_color}; border-radius: 3px; border: 1px solid #333;") # Added border for visibility
            item_layout.addWidget(color_indicator)

        name_label = QLabel(name)
        item_layout.addWidget(name_label)
        item_layout.addStretch()

        item_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        item_widget.customContextMenuRequested.connect(
            functools.partial(self._show_item_context_menu, item_widget)
        )
        item_widget.mousePressEvent = functools.partial(self._item_clicked, item_data=item_data_dict, item_type=item_type)

        selected = False
        if item_type == 'category' and self.current_category_id == item_id: selected = True
        elif item_type == 'section' and self.current_section_id == item_id: selected = True
        elif item_type == 'prompt' and self.current_prompt_id == item_id: selected = True

        if selected:
            item_widget.setProperty("class", "ListItemWidget selected")
        else:
            item_widget.setProperty("class", "ListItemWidget") # Ensure non-selected style

        # Re-apply stylesheet to ensure dynamic property changes take effect
        item_widget.setStyleSheet(self.styleSheet())

        return item_widget

    def _item_clicked(self, event: QMouseEvent, item_data: dict, item_type: str):
        """Handles left-click selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"_item_clicked - Type: {item_type}, ID: {item_data.get('id')}")
            if item_type == 'category': self.category_clicked(item_data)
            elif item_type == 'section': self.section_clicked(item_data)
            elif item_type == 'prompt': self.prompt_clicked(item_data)
        else:
            pass # Allow other events like right-click

    # --- Context Menu Handlers ---

    def _show_item_context_menu(self, widget, position):
        """Shows context menu for a specific item widget."""
        item_id = widget.property("itemId")
        item_type = widget.property("itemType")
        item_data = widget.property("itemData")
        if not item_id or not item_type or not item_data:
            print(f"Context menu requested for invalid widget state: ID={item_id}, Type={item_type}")
            return

        menu = QMenu(self)

        rename_action = QAction("Rename", self)
        current_name_key = 'title' if item_type == 'prompt' else 'name'
        rename_action.triggered.connect(lambda: self._handle_rename(item_id, item_type, item_data.get(current_name_key, '')))
        menu.addAction(rename_action)

        move_up_action = QAction("Move Up", self)
        move_up_action.triggered.connect(lambda: self._handle_move(item_id, item_type, "up"))
        menu.addAction(move_up_action)

        move_down_action = QAction("Move Down", self)
        move_down_action.triggered.connect(lambda: self._handle_move(item_id, item_type, "down"))
        menu.addAction(move_down_action)

        copy_action = QAction("Copy (Prepare to Duplicate)", self)
        copy_action.triggered.connect(lambda: self._handle_copy(item_id, item_type))
        menu.addAction(copy_action)

        paste_action = QAction("Paste (Duplicate Here)", self)
        paste_action.setEnabled(self.clipboard is not None and self.clipboard['type'] == item_type)
        paste_action.triggered.connect(lambda: self._handle_paste(item_id, item_type))
        menu.addAction(paste_action)

        if item_type == 'category':
            set_color_action = QAction("Set Color", self)
            # --- Connect to the MODIFIED handler ---
            set_color_action.triggered.connect(lambda: self._handle_set_category_color(item_id))
            menu.addAction(set_color_action)
        elif item_type == 'section':
             add_prompt_action = QAction("Add New Prompt Here", self)
             add_prompt_action.triggered.connect(lambda: self.add_prompt(section_id=item_id))
             menu.addAction(add_prompt_action)
             set_color_action = QAction("Set Color", self)
             # --- Connect to the MODIFIED handler ---
             set_color_action.triggered.connect(lambda: self._handle_set_section_color(item_id))
             menu.addAction(set_color_action)

        menu.addSeparator()
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._handle_delete(item_id, item_type))
        menu.addAction(delete_action)

        menu.exec(widget.mapToGlobal(position))

    def _show_panel_context_menu(self, panel_type, position):
        """Shows context menu for the panel background."""
        menu = QMenu(self)
        target_widget = None

        print(f"_show_panel_context_menu for '{panel_type}', current_category_id = {self.current_category_id}, current_section_id = {self.current_section_id}")

        if panel_type == 'category':
            add_action = QAction("Add New Category", self)
            add_action.triggered.connect(self.add_category)
            menu.addAction(add_action)
            target_widget = self.categories_list_widget
        elif panel_type == 'section':
            current_cat_id = self.current_category_id
            if current_cat_id:
                add_action = QAction("Add New Section", self)
                add_action.triggered.connect(functools.partial(self.add_section, category_id=current_cat_id))
                menu.addAction(add_action)
            else:
                no_cat_action = QAction("Select a Category first", self)
                no_cat_action.setEnabled(False)
                menu.addAction(no_cat_action)
            target_widget = self.sections_list_widget
        elif panel_type == 'prompt':
            current_sec_id = self.current_section_id
            if current_sec_id:
                add_action = QAction("Add New Prompt", self)
                add_action.triggered.connect(functools.partial(self.add_prompt, section_id=current_sec_id))
                menu.addAction(add_action)
            else:
                no_sec_action = QAction("Select a Section first", self)
                no_sec_action.setEnabled(False)
                menu.addAction(no_sec_action)
            target_widget = self.prompts_list_widget

        if self.clipboard and self.clipboard['type'] == panel_type:
             can_paste = False
             if panel_type == 'category': can_paste = True
             elif panel_type == 'section' and self.current_category_id: can_paste = True
             elif panel_type == 'prompt' and self.current_section_id: can_paste = True

             if can_paste:
                 paste_action = QAction(f"Paste {self.clipboard['type'].capitalize()} Here", self)
                 paste_action.triggered.connect(lambda: self._handle_paste(None, panel_type))
                 menu.addAction(paste_action)

        if target_widget and menu.actions():
            menu.exec(target_widget.mapToGlobal(position))

    # --- Action Handlers ---

    def _handle_rename(self, item_id, item_type, current_name):
        dialog = ItemDialog(f"Rename {item_type.capitalize()}", "New Name:", current_name, self)
        if dialog.exec():
            new_name = dialog.get_value()
            if new_name and new_name != current_name:
                try:
                    if item_type == 'category':
                        db.update_category(item_id, new_name)
                        self.load_categories()
                    elif item_type == 'section':
                        db.update_section(item_id, new_name)
                        self.load_sections()
                    elif item_type == 'prompt':
                        prompt_data = db.get_prompt(item_id)
                        if prompt_data:
                            db.update_prompt(item_id, new_name, prompt_data['description'], prompt_data['content'])
                            self.load_prompts()
                            if self.current_prompt_id == item_id:
                                self.prompt_title_input.setText(new_name)
                except Exception as e:
                     QMessageBox.critical(self, "Error", f"Failed to rename {item_type}: {e}")
            elif not new_name:
                 QMessageBox.warning(self, "Input Error", "Name cannot be empty.")

    def _handle_move(self, item_id, item_type, direction):
        parent_id_col = None
        parent_id = None
        table_name = f"{item_type}s" if item_type != 'category' else 'categories'

        if item_type == 'section':
            parent_id_col = 'category_id'
            parent_id = self.current_category_id
        elif item_type == 'prompt':
            parent_id_col = 'section_id'
            parent_id = self.current_section_id

        if db.move_item(table_name, item_id, direction, parent_id_col, parent_id):
            if item_type == 'category': self.load_categories()
            elif item_type == 'section': self.load_sections()
            elif item_type == 'prompt': self.load_prompts()
        else:
             QMessageBox.warning(self, "Move Failed", f"Could not move {item_type} {direction}.")

    def _handle_copy(self, item_id, item_type):
        self.clipboard = {'id': item_id, 'type': item_type}
        print(f"Copied {item_type} with ID {item_id} to internal clipboard.")
        QMessageBox.information(self, "Copied", f"Prepared to duplicate {item_type}: {item_id}.\nRight-click where you want to paste.")

    def _handle_paste(self, target_item_id, target_type):
        if not self.clipboard:
            QMessageBox.warning(self, "Paste Error", "Nothing copied to paste.")
            return
        if self.clipboard['type'] != target_type:
             QMessageBox.warning(self, "Paste Error", f"Cannot paste a {self.clipboard['type']} here (expecting {target_type}).")
             return

        source_id = self.clipboard['id']
        source_type = self.clipboard['type']
        print(f"Pasting {source_type} ID {source_id} as target type {target_type}")

        try:
            if source_type == 'category':
                source_cat = db.get_categories()
                source_data = next((c for c in source_cat if c['id'] == source_id), None)
                if source_data:
                    s_dict = dict(source_data)
                    new_id = db.add_category(f"{s_dict['name']} (Copy)", s_dict.get('color')) # Pass color
                    self.load_categories()
                else: raise ValueError("Source category not found")

            elif source_type == 'section':
                paste_target_category_id = self.current_category_id
                if not paste_target_category_id: raise ValueError("No target category selected for paste")

                conn = db.get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM sections WHERE id = ?", (source_id,))
                source_data_row = cur.fetchone()
                conn.close()
                source_data = dict(source_data_row) if source_data_row else None

                if source_data:
                    new_id = db.add_section(f"{source_data['name']} (Copy)", paste_target_category_id)
                    if new_id and 'color' in source_data and source_data['color']:
                         db.update_section_color(new_id, source_data['color'])
                    self.load_sections()
                else: raise ValueError("Source section not found")

            elif source_type == 'prompt':
                paste_target_section_id = self.current_section_id
                if not paste_target_section_id: raise ValueError("No target section selected for paste")

                source_data = db.get_prompt(source_id)
                if source_data:
                    source_data_dict = dict(source_data)
                    new_id = db.add_prompt(
                        f"{source_data_dict['title']} (Copy)",
                        source_data_dict['description'],
                        source_data_dict['content'],
                        paste_target_section_id
                    )
                    self.load_prompts()
                else: raise ValueError("Source prompt not found")

            QMessageBox.information(self, "Pasted", f"Successfully duplicated {source_type}.")
            self.clipboard = None # Clear clipboard after paste

        except Exception as e:
             QMessageBox.critical(self, "Paste Error", f"Failed to duplicate {source_type}: {e}")

    # --- MODIFIED: Use ColorGridDialog ---
    def _handle_set_category_color(self, item_id):
        current_color_hex = '#e0e0e0' # Default
        cats = db.get_categories()
        cat_data = next((c for c in cats if c['id'] == item_id), None)
        if cat_data:
             cat_data_dict = dict(cat_data)
             if cat_data_dict.get('color'):
                 current_color_hex = cat_data_dict['color']

        # Use the new ColorGridDialog
        dialog = ColorGridDialog("Select Category Color", initial_color=current_color_hex, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted: # Check if user clicked a color
            selected_color = dialog.get_selected_color()
            if selected_color: # Make sure a color was actually selected
                db.update_category_color(item_id, selected_color)
                self.load_categories() # Reload to show the new color

    # --- MODIFIED: Use ColorGridDialog ---
    def _handle_set_section_color(self, item_id):
        current_color_hex = '#d0d0d0' # Default
        if self.current_category_id:
            secs = db.get_sections(self.current_category_id)
            sec_data = next((s for s in secs if s['id'] == item_id), None)
            if sec_data:
                 sec_data_dict = dict(sec_data)
                 if sec_data_dict.get('color'):
                      current_color_hex = sec_data_dict['color']
        else:
             print("Warning: Cannot get current section color, no category selected.")

        # Use the new ColorGridDialog
        dialog = ColorGridDialog("Select Section Color", initial_color=current_color_hex, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted: # Check if user clicked a color
            selected_color = dialog.get_selected_color()
            if selected_color: # Make sure a color was actually selected
                db.update_section_color(item_id, selected_color)
                self.load_sections() # Reload to show the new color

    def _handle_delete(self, item_id, item_type):
        # --- Use the custom ConfirmDialog ---
        dialog = ConfirmDialog(
            title='Confirm Delete',
            message=f"Are you sure you want to delete this {item_type}?",
            informative_text="(Sections/Prompts within will also be deleted!)",
            parent=self # Set parent for proper modality and positioning
        )

        # --- Execute the dialog and check the result ---
        if dialog.exec(): # Returns True if accepted (Yes clicked), False if rejected (No or Close clicked)
            # --- Original delete logic ---
            try:
                if item_type == 'category':
                    db.delete_category(item_id)
                    if self.current_category_id == item_id:
                        self.current_category_id = None
                        self.current_section_id = None
                        self.current_prompt_id = None
                        self.sections_title.setText("Sections")
                        self.prompts_title.setText("Prompts")
                        self.clear_editor_fields() # Disables buttons
                    self.load_categories()
                    self.load_sections()
                    self.load_prompts()
                elif item_type == 'section':
                    db.delete_section(item_id)
                    if self.current_section_id == item_id:
                        self.current_section_id = None
                        self.current_prompt_id = None
                        self.prompts_title.setText("Prompts")
                        self.clear_editor_fields() # Disables buttons
                    self.load_sections()
                    self.load_prompts()
                elif item_type == 'prompt':
                    db.delete_prompt(item_id)
                    if self.current_prompt_id == item_id:
                        self.current_prompt_id = None
                        self.clear_editor_fields() # Disables buttons
                    self.load_prompts()
            except Exception as e:
                 QMessageBox.critical(self, "Error", f"Failed to delete {item_type}: {e}")
        # else: User clicked No or closed the dialog, so do nothing.

    # --- Category Loading and Handling ---
    def load_categories(self):
        self._clear_layout(self.categories_layout)
        categories = db.get_categories()
        for category in categories:
            item_widget = self._create_list_item(category, 'category')
            self.categories_layout.addWidget(item_widget)
        self.categories_layout.addStretch()
        if self.current_category_id not in [c['id'] for c in categories]:
             self.current_category_id = None
             self.current_section_id = None
             self.current_prompt_id = None
             self.sections_title.setText("Sections")
             self.prompts_title.setText("Prompts")
             self.clear_editor_fields() # Ensure buttons disabled
        self.load_sections()

    def category_clicked(self, category_data):
        category_data_dict = dict(category_data)
        category_id = category_data_dict.get('id')
        if self.current_category_id != category_id:
            self.current_category_id = category_id
            self.current_section_id = None
            self.current_prompt_id = None
            self.sections_title.setText("Sections") # Reset title
            self.prompts_title.setText("Prompts") # Reset title
            self.load_categories() # Reload to update selection highlight
            # load_sections() is called by load_categories()
            self.clear_editor_fields() # Disables buttons
        else:
            # If clicking the already selected category, ensure highlight is correct
            self.load_categories()


    def add_category(self):
        dialog = ItemDialog("Add New Category", "Category Name:", "", self)
        if dialog.exec():
            name = dialog.get_value()
            if name:
                new_id = db.add_category(name)
                if new_id:
                    self.current_category_id = new_id
                    self.current_section_id = None
                    self.current_prompt_id = None
                    self.load_categories() # Calls load_sections -> load_prompts
                    self.sections_title.setText("Sections")
                    self.prompts_title.setText("Prompts")
                    self.clear_editor_fields() # Disables buttons
                else:
                     QMessageBox.warning(self, "Database Error", "Failed to add category.")
            elif name is not None:
                 QMessageBox.warning(self, "Input Error", "Category name cannot be empty.")

    # --- Section Loading and Handling ---
    def load_sections(self):
        self._clear_layout(self.sections_layout)
        sections = []
        category_name = "Sections" # Default title
        if self.current_category_id:
            # Get category name for the title
            cats = db.get_categories()
            cat_data = next((c for c in cats if c['id'] == self.current_category_id), None)
            if cat_data: category_name = f"Sections in '{dict(cat_data)['name']}'"

            sections = db.get_sections(self.current_category_id)
            for section in sections:
                item_widget = self._create_list_item(section, 'section')
                self.sections_layout.addWidget(item_widget)

        self.sections_title.setText(category_name) # Update title
        self.sections_layout.addStretch()
        if self.current_section_id not in [s['id'] for s in sections]:
             self.current_section_id = None
             self.current_prompt_id = None
             self.prompts_title.setText("Prompts")
             self.clear_editor_fields() # Ensure buttons disabled
        self.load_prompts()

    def section_clicked(self, section_data):
        section_data_dict = dict(section_data)
        section_id = section_data_dict.get('id')
        if self.current_section_id != section_id:
            self.current_section_id = section_id
            self.current_prompt_id = None
            self.prompts_title.setText("Prompts") # Reset title
            self.load_sections() # Reload to update selection highlight
            # load_prompts() is called by load_sections()
            self.clear_editor_fields() # Disables buttons
        else:
            # If clicking the already selected section, ensure highlight is correct
            self.load_sections()


    def add_section(self, category_id=None):
        target_category_id = category_id if category_id is not None else self.current_category_id
        if not target_category_id:
            QMessageBox.warning(self, "Warning", "Please select a category first.")
            return

        target_category_name = ""
        cats = db.get_categories()
        cat_data = next((c for c in cats if c['id'] == target_category_id), None)
        if cat_data: target_category_name = dict(cat_data)['name']

        dialog = ItemDialog(f"Add Section to '{target_category_name}'", "Section Name:", "", self)
        if dialog.exec():
            name = dialog.get_value()
            if name:
                new_id = db.add_section(name, target_category_id)
                if new_id:
                    # If added via panel context menu and it's not the current category, switch
                    if category_id is not None and category_id != self.current_category_id:
                         self.current_category_id = category_id
                         self.load_categories() # Reload categories to show selection

                    self.current_section_id = new_id
                    self.current_prompt_id = None
                    self.load_sections() # Reload sections to show new one and highlight
                    # load_prompts() called by load_sections()
                    self.clear_editor_fields() # Disables buttons
                else:
                    QMessageBox.warning(self, "Database Error", "Failed to add section.")
            elif name is not None:
                 QMessageBox.warning(self, "Input Error", "Section name cannot be empty.")

    # --- Prompt Loading and Handling ---
    def load_prompts(self):
        self._clear_layout(self.prompts_layout)
        prompts = []
        section_name = "Prompts" # Default title
        if self.current_section_id:
             # Get section name for the title
             if self.current_category_id:
                 secs = db.get_sections(self.current_category_id)
                 sec_data = next((s for s in secs if s['id'] == self.current_section_id), None)
                 if sec_data: section_name = f"Prompts in '{dict(sec_data)['name']}'"

             prompts = db.get_prompts(self.current_section_id)
             for prompt in prompts:
                 item_widget = self._create_list_item(prompt, 'prompt')
                 self.prompts_layout.addWidget(item_widget)

        self.prompts_title.setText(section_name) # Update title
        self.prompts_layout.addStretch()
        if self.current_prompt_id not in [p['id'] for p in prompts]:
             self.current_prompt_id = None
             self.clear_editor_fields() # Ensure buttons disabled
        elif self.current_prompt_id:
             # If a prompt is selected, ensure editor fields are loaded/enabled
             self.load_prompt_details(self.current_prompt_id)


    def prompt_clicked(self, prompt_data):
        prompt_data_dict = dict(prompt_data)
        prompt_id = prompt_data_dict.get('id')
        if self.current_prompt_id != prompt_id:
            self.current_prompt_id = prompt_id
            self.load_prompts() # Reload list to highlight and load details
            # load_prompt_details() is called by load_prompts() if current_prompt_id is set
        else:
            # If clicking the already selected prompt, ensure highlight is correct
            self.load_prompts()


    def add_prompt(self, section_id=None):
        target_section_id = section_id if section_id is not None else self.current_section_id
        if not target_section_id:
            QMessageBox.warning(self, "Warning", "Please select a section first.")
            return

        target_section_name = ""
        if self.current_category_id:
            secs = db.get_sections(self.current_category_id)
            sec_data = next((s for s in secs if s['id'] == target_section_id), None)
            if sec_data: target_section_name = dict(sec_data)['name']

        dialog = ItemDialog(f"Add Prompt to '{target_section_name}'", "Prompt Title:", "", self)
        if dialog.exec():
            title = dialog.get_value()
            if title:
                new_id = db.add_prompt(title, "", "", target_section_id)
                if new_id:
                     # If added via item context menu and it's not the current section, switch
                    if section_id is not None and section_id != self.current_section_id:
                         self.current_section_id = section_id
                         self.load_sections() # Reload sections to show selection

                    self.current_prompt_id = new_id
                    self.load_prompts() # Reload prompts to show new one, highlight, and load details
                    # load_prompt_details() called by load_prompts()
                    self.prompt_title_input.setFocus()
                else:
                     QMessageBox.warning(self, "Database Error", "Failed to add prompt.")
            elif title is not None:
                 QMessageBox.warning(self, "Input Error", "Prompt title cannot be empty.")

    def delete_current_prompt(self):
        if self.current_prompt_id:
             self._handle_delete(self.current_prompt_id, 'prompt')
        # else: Button should be disabled if no prompt selected

    def copy_current_prompt_content(self):
        """Copies the plain text content of the current prompt to the clipboard."""
        if self.current_prompt_id and self.editor.isEnabled():
            clipboard = QApplication.clipboard()
            text_content = self.editor.toPlainText() # Get plain text
            clipboard.setText(text_content)
            print(f"Copied content of prompt {self.current_prompt_id} to clipboard.")
            # Show a temporary tooltip confirmation
            QToolTip.showText(self.copy_prompt_btn.mapToGlobal(QPoint(0, -30)), "Content Copied!", self.copy_prompt_btn, self.copy_prompt_btn.rect(), 1500)
        # else: Button should be disabled if no prompt selected

    # --- Editor Field Handling ---
    def load_prompt_details(self, prompt_id):
        prompt = db.get_prompt(prompt_id)
        if prompt:
            prompt_dict = dict(prompt)
            self.prompt_title_input.blockSignals(True)
            self.prompt_description_input.blockSignals(True)
            self.editor.blockSignals(True)

            self.prompt_title_input.setText(prompt_dict.get('title', ''))
            self.prompt_description_input.setPlainText(prompt_dict.get('description', ''))
            self.editor.setHtml(prompt_dict.get('content', ''))

            # --- Enable editor fields AND buttons ---
            self.prompt_title_input.setEnabled(True)
            self.prompt_description_input.setEnabled(True)
            self.editor.setEnabled(True)
            self.copy_prompt_btn.setEnabled(True) # Enable Copy button
            self.delete_prompt_btn.setEnabled(True) # Enable Delete button

            self.prompt_title_input.blockSignals(False)
            self.prompt_description_input.blockSignals(False)
            self.editor.blockSignals(False)
        else:
            print(f"Warning: Prompt ID {prompt_id} not found in database.")
            self.clear_editor_fields() # Clear fields and disable buttons

    def clear_editor_fields(self):
        self.prompt_title_input.blockSignals(True)
        self.prompt_description_input.blockSignals(True)
        self.editor.blockSignals(True)

        self.prompt_title_input.clear()
        self.prompt_description_input.clear()
        self.editor.clear()

        # --- Disable editor fields AND buttons ---
        self.prompt_title_input.setEnabled(False)
        self.prompt_description_input.setEnabled(False)
        self.editor.setEnabled(False)
        self.copy_prompt_btn.setEnabled(False) # Disable Copy button
        self.delete_prompt_btn.setEnabled(False) # Disable Delete button

        self.prompt_title_input.blockSignals(False)
        self.prompt_description_input.blockSignals(False)
        self.editor.blockSignals(False)

    def save_current_prompt_details(self):
        """Saves Title and Description when editing finishes or text changes."""
        if self.current_prompt_id and self.prompt_title_input.isEnabled():
            # Check if the sender is one of the inputs we care about
            sender = self.sender()
            if sender not in [self.prompt_title_input, self.prompt_description_input]:
                 # If called manually (e.g., focus out), proceed
                 pass
            elif sender and sender.signalsBlocked():
                 return # Don't save if signals are blocked

            title = self.prompt_title_input.text().strip()
            description = self.prompt_description_input.toPlainText().strip()

            current_prompt = db.get_prompt(self.current_prompt_id)
            if current_prompt:
                current_prompt_dict = dict(current_prompt)
                content = current_prompt_dict.get('content', '')

                if title: # Title must not be empty
                    # Only update if title or description actually changed
                    if (title != current_prompt_dict.get('title', '') or
                        description != current_prompt_dict.get('description', '')):
                        print(f"Saving details for prompt {self.current_prompt_id}")
                        db.update_prompt(self.current_prompt_id, title, description, content)
                        # Reload prompts list ONLY if title changed
                        if title != current_prompt_dict.get('title', ''):
                            self.load_prompts() # Reload list to update title
                else:
                    # Don't show message box on every keystroke if title becomes empty
                    # Maybe just revert visually? Or handle on focus out?
                    # For now, just prevent saving an empty title
                    print(f"Prevented saving empty title for prompt {self.current_prompt_id}")
                    # Optionally revert the title input visually
                    # self.prompt_title_input.blockSignals(True)
                    # self.prompt_title_input.setText(current_prompt_dict.get('title', ''))
                    # self.prompt_title_input.blockSignals(False)
            else:
                 print(f"Error: Cannot save details, prompt {self.current_prompt_id} not found.")

    def save_current_prompt_content(self):
        """Saves only the main Content when editor text changes."""
        if self.current_prompt_id and self.editor.isEnabled():
            if self.editor.signalsBlocked(): return

            content = self.editor.toHtml()

            current_prompt = db.get_prompt(self.current_prompt_id)
            if current_prompt:
                 current_prompt_dict = dict(current_prompt)
                 # Only update if content actually changed
                 if content != current_prompt_dict.get('content', ''):
                     print(f"Saving content for prompt {self.current_prompt_id}")
                     db.update_prompt(self.current_prompt_id,
                                      current_prompt_dict.get('title',''),
                                      current_prompt_dict.get('description',''),
                                      content)
            else:
                 print(f"Error: Cannot save content, prompt {self.current_prompt_id} not found.")

    def format_text(self, format_type):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection(): return

        text_format = cursor.charFormat()

        if format_type == "bold":
            current_weight = text_format.fontWeight()
            target_weight = QFont.Weight.Normal if current_weight > QFont.Weight.Normal else QFont.Weight.Bold
            text_format.setFontWeight(target_weight)
        elif format_type == "italic":
            text_format.setFontItalic(not text_format.fontItalic())
        elif format_type == "underline":
            text_format.setFontUnderline(not text_format.fontUnderline())

        cursor.mergeCharFormat(text_format)
        self.editor.setTextCursor(cursor)

    def setup_shortcuts(self):
        bold_shortcut = QAction("Bold", self)
        bold_shortcut.setShortcut(QKeySequence("Ctrl+B"))
        bold_shortcut.triggered.connect(lambda: self.format_text("bold"))
        self.addAction(bold_shortcut)

        italic_shortcut = QAction("Italic", self)
        italic_shortcut.setShortcut(QKeySequence("Ctrl+I"))
        italic_shortcut.triggered.connect(lambda: self.format_text("italic"))
        self.addAction(italic_shortcut)

        underline_shortcut = QAction("Underline", self)
        underline_shortcut.setShortcut(QKeySequence("Ctrl+U"))
        underline_shortcut.triggered.connect(lambda: self.format_text("underline"))
        self.addAction(underline_shortcut)

    def closeEvent(self, event):
        print("Editor closing")
        # Ensure any pending edits are saved before hiding
        if self.current_prompt_id:
             # Check if focus is currently in an editable field and trigger save if needed
             focused_widget = QApplication.focusWidget()
             if focused_widget == self.prompt_title_input:
                 self.save_current_prompt_details()
             elif focused_widget == self.prompt_description_input:
                 self.save_current_prompt_details()
             elif focused_widget == self.editor:
                 self.save_current_prompt_content() # Content saves on textChanged, but maybe force here?

        self.closing.emit()
        self.hide()
        event.ignore() # Prevent destruction, just hide

# Example usage (for testing editor independently)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # --- CHANGE: Ensure Template directory exists or adjust path ---
    # Create a dummy Template directory if it doesn't exist for the import to work
    if not os.path.exists("Template"):
        os.makedirs("Template")
        # Create a dummy TitleBar.py if it doesn't exist
        if not os.path.exists("Template/TitleBar.py"):
             with open("Template/TitleBar.py", "w") as f:
                 # Add minimal content to avoid import errors during testing
                 f.write("from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton\n")
                 f.write("from PyQt6.QtCore import pyqtSignal\n")
                 f.write("class CustomTitleBar(QWidget):\n")
                 f.write("    closing = pyqtSignal()\n")
                 f.write("    minimizing = pyqtSignal()\n")
                 f.write("    maximizing = pyqtSignal()\n")
                 f.write("    def __init__(self, parent):\n")
                 f.write("        super().__init__(parent)\n")
                 f.write("        layout = QHBoxLayout(self)\n")
                 f.write("        self.title_label = QLabel('Dummy Title')\n")
                 f.write("        layout.addWidget(self.title_label)\n")
                 f.write("        self.btn_close = QPushButton('X'); self.btn_close.setObjectName('CloseButton')\n")
                 f.write("        self.btn_minimize = QPushButton('_'); self.btn_minimize.setObjectName('MinimizeButton')\n")
                 f.write("        self.btn_maximize = QPushButton('[]'); self.btn_maximize.setObjectName('MaximizeButton')\n")
                 f.write("        layout.addWidget(self.btn_minimize)\n")
                 f.write("        layout.addWidget(self.btn_maximize)\n")
                 f.write("        layout.addWidget(self.btn_close)\n")
                 f.write("        self.setFixedHeight(30)\n")
                 f.write("        self.setObjectName('CustomTitleBar')\n")
                 f.write("        self.btn_close.clicked.connect(self.closing)\n") # Emit signal
                 f.write("        self.btn_minimize.clicked.connect(self.minimizing)\n") # Emit signal
                 f.write("        self.btn_maximize.clicked.connect(self.maximizing)\n") # Emit signal\n")
                 f.write("    def setWindowTitle(self, title):\n")
                 f.write("        self.title_label.setText(title)\n")

    # --- END CHANGE ---
    db.initialize_database() # Ensure DB is ready
    window = PromptEditorWindow()
    window.show_and_activate()
    sys.exit(app.exec())
# --- END OF FILE editor_ui.py ---