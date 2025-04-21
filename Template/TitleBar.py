# --- START OF FILE TitleBar.py ---

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QPoint, QSize, pyqtSlot # Import pyqtSlot
from PyQt6.QtGui import QIcon, QFont # Keep QFont import for potential styling

class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.setAutoFillBackground(True)
        self.setFixedHeight(35) # Adjust height as needed
        self.setObjectName("CustomTitleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 0, 0) # Left margin for icon, no right margin for buttons
        layout.setSpacing(0)

        # Optional: Window Icon
        self.icon_label = QLabel(self)
        # Check if parent has windowIcon before trying to set pixmap
        if not parent.windowIcon().isNull():
             self.icon_label.setPixmap(parent.windowIcon().pixmap(QSize(16, 16)))
        self.icon_label.setFixedSize(20, 20)
        self.icon_label.setStyleSheet("margin-left: 5px;") # Space after icon
        layout.addWidget(self.icon_label)

        # Title Label
        self.title_label = QLabel(parent.windowTitle(), self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #b3b0ad; margin-left: 5px;") # Style as needed
        layout.addWidget(self.title_label)

        # Spacer to push buttons to the right
        layout.addStretch()

        # --- Window Control Buttons ---
        # Minimize Button (Underscore)
        self.btn_minimize = QPushButton("_", self)
        self.btn_minimize.setFixedSize(40, self.height())
        self.btn_minimize.setObjectName("MinimizeButton")
        self.btn_minimize.setToolTip("Minimize")
        self.btn_minimize.clicked.connect(parent.showMinimized)
        layout.addWidget(self.btn_minimize)

        # Maximize/Restore Button (Square / Two Squares)
        # Initial state depends on parent window's initial state, but default to Maximize symbol
        initial_max_symbol = "❐" if parent.isMaximized() else "□"
        initial_tooltip = "Restore" if parent.isMaximized() else "Maximize"
        self.btn_maximize = QPushButton(initial_max_symbol, self) # U+25A1 White Square / U+2750 Restore
        self.btn_maximize.setFixedSize(40, self.height())
        self.btn_maximize.setObjectName("MaximizeButton")
        self.btn_maximize.setToolTip(initial_tooltip)
        self.btn_maximize.clicked.connect(self.toggle_maximize_restore)
        layout.addWidget(self.btn_maximize)

        # Close Button (X)
        self.btn_close = QPushButton("✕", self) # U+2715 Multiplication X
        self.btn_close.setFixedSize(40, self.height())
        self.btn_close.setObjectName("CloseButton")
        self.btn_close.setToolTip("Close")
        self.btn_close.clicked.connect(parent.close)
        layout.addWidget(self.btn_close)

        # Connect parent window's state change signal
        # This is the primary mechanism for updating the button's appearance
        if hasattr(parent, 'windowStateChanged'):
            parent.windowStateChanged.connect(self.update_maximize_button)
        else:
             print("Warning: Parent window does not have 'windowStateChanged' signal.")


        self.setStyleSheet("""
            #CustomTitleBar {
                background-color: #25262b;
                border-bottom: 1px solid #464766;
            }
            #MinimizeButton, #MaximizeButton, #CloseButton {
                background-color: transparent;
                border: none;
                color: #b3b0ad;
                padding: 0px;
                margin: 0px;
                font-size: 14pt; /* Adjust size if symbols look wrong */
                font-weight: normal; /* Normal weight might render symbols better */
            }
            #MinimizeButton {
                /* Optional: Adjust vertical position for underscore */
                padding-bottom: 8px;
            }
            #MinimizeButton:hover, #MaximizeButton:hover {
                background-color: #4a4b50;
            }
            #CloseButton:hover {
                background-color: #e81123;
                color: white;
            }
            #MinimizeButton:pressed, #MaximizeButton:pressed, #CloseButton:pressed {
                background-color: #6b6c70;
            }
        """)

        # Variables for dragging
        self._mouse_press_pos = None
        self._mouse_move_pos = None

    def toggle_maximize_restore(self):
        # This function *only* toggles the state.
        # The appearance update is handled by the windowStateChanged signal -> update_maximize_button slot.
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()

    @pyqtSlot(Qt.WindowState) # Ensure this is decorated as a slot
    def update_maximize_button(self, state):
        """Updates the maximize button icon based on window state."""
        # Check specifically for the Maximized state flag
        if self.parent_window.windowState() & Qt.WindowState.WindowMaximized:
            self.btn_maximize.setText("❐") # Restore symbol (U+2750)
            self.btn_maximize.setToolTip("Restore")
        else:
            self.btn_maximize.setText("□") # Maximize symbol (U+25A1)
            self.btn_maximize.setToolTip("Maximize")

    def mousePressEvent(self, event):
        """Handles mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on the title bar area itself, not on buttons
            if event.pos().x() < self.width() - (self.btn_minimize.width() + self.btn_maximize.width() + self.btn_close.width()): # More precise check
                 self._mouse_press_pos = event.globalPosition().toPoint()
                 # Correct calculation for move position offset
                 self._mouse_move_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
                 event.accept()
            else:
                 # Click was on buttons, ignore for dragging
                 self._mouse_press_pos = None
                 self._mouse_move_pos = None
                 event.ignore() # Let button handle its click
        else:
            event.ignore() # Ignore non-left clicks

    def mouseMoveEvent(self, event):
        """Handles mouse move for dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton and self._mouse_move_pos:
            # --- FIX: Allow moving window from maximized state ---
            # If dragging starts while maximized, restore first then move
            if self.parent_window.isMaximized():
                 # Calculate the position relative to the mouse press
                 # This helps snap the window correctly when un-maximizing via drag
                 norm_width = self.parent_window.normalGeometry().width()
                 # Calculate offset based on where the mouse was pressed relative to the title bar width
                 x_offset_ratio = self._mouse_press_pos.x() / self.width()
                 # Apply this ratio to the normal width to estimate the new x position
                 new_x = event.globalPosition().toPoint().x() - int(norm_width * x_offset_ratio)
                 new_y = event.globalPosition().toPoint().y() - (self.height() // 2) # Center vertically roughly

                 self.parent_window.showNormal()
                 self.parent_window.move(new_x, new_y)
                 # Update the move offset for subsequent moves in the restored state
                 self._mouse_move_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()

            else:
                # Standard move when not maximized
                new_pos = event.globalPosition().toPoint() - self._mouse_move_pos
                self.parent_window.move(new_pos)
            event.accept()
            # --- END FIX ---
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        """Handles mouse release after dragging."""
        self._mouse_press_pos = None
        self._mouse_move_pos = None
        event.accept()

    def mouseDoubleClickEvent(self, event):
        """Handles double-click to maximize/restore."""
        if event.button() == Qt.MouseButton.LeftButton:
             if event.pos().x() < self.width() - (self.btn_minimize.width() + self.btn_maximize.width() + self.btn_close.width()): # More precise check
                self.toggle_maximize_restore()
                event.accept()
             else:
                 event.ignore() # Double click on buttons
        else:
            event.ignore()

    def setWindowTitle(self, title):
        """Sets the window title displayed on the custom bar."""
        self.title_label.setText(title)
# --- END OF FILE TitleBar.py ---