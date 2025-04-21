# --- START OF FILE main.py ---

import sys
import os
import ctypes # For console hiding on Windows
import threading # To run hotkey listener in background
import time # For potential delays

# --- Third-party libraries ---
try:
    import keyboard
except ImportError:
    print("Error: 'keyboard' library not found.")
    print("Please install it using: pip install keyboard")
    sys.exit(1)
try:
    from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
    from PyQt6.QtGui import QIcon, QAction
    from PyQt6.QtCore import QTimer, QMetaObject, Qt, pyqtSlot
except ImportError:
     print("Error: 'PyQt6' library not found.")
     print("Please install it using: pip install PyQt6")
     sys.exit(1)


# --- Local imports ---
import database as db
from search_ui import SearchUIWindow
from editor_ui import PromptEditorWindow

# --- Configuration ---
HOTKEY = "ctrl+alt+p" # The key combination to trigger the search UI
ICON_PATH = "icon.png" # Path to your tray icon image

# --- Global Variables ---
app = None
search_window = None
editor_window = None
tray_icon = None # <-- Added for tray icon
editor_visible = False # Track editor state

# --- Console Hiding ---
def hide_console():
    """Hides the console window on Windows systems."""
    # --- ENABLED FOR PRODUCTION ---
    if os.name == 'nt':
        try:
            print("Attempting to hide console window...") # Keep a print before hiding
            hwnd_console = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd_console != 0:
                ctypes.windll.user32.ShowWindow(hwnd_console, 0) # SW_HIDE = 0
                # Don't print after hiding, it won't be seen
            else:
                print("Info: Could not get console window handle.", file=sys.stderr)
        except Exception as e:
            print(f"Info: Could not hide console window ({e})", file=sys.stderr)
    else:
        print("Console hiding is only implemented for Windows.")
    # --- END OF ENABLED SECTION ---
    # print("Console visibility enabled.") # Remove this line as it's now misleading


# --- UI Interaction Functions ---

@pyqtSlot()
def show_search_ui_safe():
    """Safely shows the search UI from any thread."""
    global search_window, editor_visible
    # print(f"show_search_ui_safe called (Editor visible: {editor_visible})") # DEBUG PRINT (Optional)
    if search_window and not editor_visible:
        # print("Invoking search_window.show_and_prepare()") # DEBUG PRINT (Optional)
        # Ensure it runs on the main GUI thread
        QMetaObject.invokeMethod(search_window, "show_and_prepare", Qt.ConnectionType.QueuedConnection)
    # else:
        # print("Search window not shown (already open or editor is visible).") # DEBUG PRINT (Optional)


@pyqtSlot()
def show_editor_ui_safe():
    """Safely shows the editor UI from any thread."""
    global editor_window, editor_visible, search_window
    # print("show_editor_ui_safe called") # DEBUG PRINT (Optional)
    if editor_window:
        editor_visible = True
        # Hide search window if it's somehow visible
        if search_window and search_window.isVisible():
             # print("Hiding search window before showing editor") # DEBUG (Optional)
             QMetaObject.invokeMethod(search_window, "hide_window", Qt.ConnectionType.QueuedConnection)

        # --- CHANGE THIS BLOCK ---
        # print("Invoking editor_window.show_and_activate()") # DEBUG PRINT (Optional)
        # Ensure it runs on the main GUI thread using the new dedicated slot
        QMetaObject.invokeMethod(editor_window, "show_and_activate", Qt.ConnectionType.QueuedConnection)
        # --- END OF CHANGE ---
    # else:
        # print("Editor window instance not found.") # DEBUG PRINT (Optional)


@pyqtSlot()
def editor_closed_safe():
    """Handles editor closing signal."""
    global editor_visible
    editor_visible = False
    # print("Editor UI closed signal received.") # DEBUG PRINT (Optional)
    # Optionally, re-show the search UI immediately after closing editor?
    # show_search_ui_safe() # Uncomment if desired


# --- Hotkey Handling ---
def hotkey_callback():
    """Callback function executed when hotkey is pressed."""
    # print(f"Hotkey '{HOTKEY}' detected by keyboard library!") # DEBUG PRINT (Optional)
    # Use the safe function to interact with Qt GUI
    show_search_ui_safe()

def setup_hotkey():
    """Sets up the global hotkey listener."""
    # print(f"Attempting to register hotkey: {HOTKEY}") # DEBUG PRINT (Optional)
    try:
        # Use the separate callback function
        keyboard.add_hotkey(HOTKEY, hotkey_callback, trigger_on_release=False)
        print(f"Hotkey '{HOTKEY}' registration attempted. Listener active.") # Keep this print
        # Keep the script running to listen for hotkeys
        # keyboard.wait() # This blocks, so run in a separate thread or use QApplication's loop
    except ImportError as e:
         print(f"ERROR: Failed to register hotkey '{HOTKEY}'. Import error: {e}", file=sys.stderr)
         print("       This might happen if running in an environment without proper display access (like some SSH sessions).", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: Failed to register hotkey '{HOTKEY}': {e}", file=sys.stderr)
        print("       Try running this script with administrator privileges (Windows) or check input monitoring permissions (macOS/Linux).", file=sys.stderr)


def hotkey_listener_thread():
    """Function to run in a separate thread for listening."""
    # print("Hotkey listener thread started.") # DEBUG PRINT (Optional)
    setup_hotkey()
    # The keyboard library manages its own loop/hooks after add_hotkey
    # We just need to keep this thread alive. A simple loop can do that
    # if keyboard.wait() isn't used.
    while True:
        time.sleep(3600) # Keep thread alive without busy-waiting, check less often

# --- System Tray Icon Setup ---
def setup_tray_icon():
    global tray_icon, app
    # print("Setting up system tray icon.") # DEBUG PRINT (Optional)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("ERROR: System tray not available on this system.", file=sys.stderr)
        return

    # Check if icon file exists before creating QIcon
    if not os.path.exists(ICON_PATH):
        print(f"ERROR: Icon file not found at '{ICON_PATH}'. Tray icon will not be set.", file=sys.stderr)
        # Attempt to use a default Qt icon as fallback
        # tray_icon = QSystemTrayIcon(QIcon.fromTheme("application-x-executable"), parent=app) # Example fallback
        # if tray_icon.icon().isNull():
        #      print("ERROR: Could not load default fallback icon either.")
        #      return # Exit if no icon possible
        return # Exit setup if icon is missing

    tray_icon = QSystemTrayIcon(QIcon(ICON_PATH), parent=app) # Pass app as parent
    if tray_icon.icon().isNull():
         print(f"ERROR: Failed to load icon from '{ICON_PATH}'. Check file format/integrity.", file=sys.stderr)
         # Optionally return here or continue without a visible icon
         # return

    tray_icon.setToolTip("Prompt Manager\n"
                         f"Hotkey: {HOTKEY}\n"
                         "Left-click to search\n"
                         "Right-click for menu")

    # Create Menu
    menu = QMenu()

    # --- APPLY STYLESHEET TO MENU ---
    menu.setStyleSheet("""
        QMenu {
            background-color: #2a2b30; /* Dark background */
            border: 1px solid #464766; /* Border matching editor */
            color: #b3b0ad; /* Light text */
            padding: 5px; /* Padding around items */
        }
        QMenu::item {
            background-color: transparent; /* Default item background */
            padding: 5px 25px 5px 20px; /* Top, Right, Bottom, Left padding */
            margin: 2px 0px; /* Margin between items */
            border-radius: 3px;
        }
        QMenu::item:selected { /* Hover/Selection */
            background-color: #464766; /* Selection color matching editor */
            color: #ffffff; /* White text on selection */
        }
        QMenu::item:disabled {
            color: #777777; /* Grayed out text for disabled items */
            background-color: transparent;
        }
        QMenu::separator {
            height: 1px;
            background-color: #464766; /* Separator color */
            margin: 4px 0px; /* Margin above/below separator */
        }
    """)
    # --- END STYLESHEET ---


    # Show Search Action
    show_search_action = QAction("Show Search", parent=app) # Pass app as parent
    show_search_action.triggered.connect(show_search_ui_safe)
    menu.addAction(show_search_action)

    # Show Editor Action
    show_editor_action = QAction("Show Editor", parent=app) # Pass app as parent
    show_editor_action.triggered.connect(show_editor_ui_safe)
    menu.addAction(show_editor_action)

    menu.addSeparator()

    # Quit Action
    quit_action = QAction("Quit Prompt Manager", parent=app) # Pass app as parent
    quit_action.triggered.connect(app.quit) # Connect directly to app.quit
    menu.addAction(quit_action)

    tray_icon.setContextMenu(menu)

    # Connect left-click (Trigger) to show search
    tray_icon.activated.connect(handle_tray_activation)

    tray_icon.show()
    # Use isVisible() for a more reliable check after show()
    if tray_icon.isVisible():
        print("System tray icon is visible.") # Keep this print
    else:
        # This might happen if the icon loaded but the system tray itself has issues
        print("WARNING: System tray icon was shown but might not be visible.", file=sys.stderr)

def handle_tray_activation(reason):
    """Handles tray icon activation signals."""
    # Trigger = Left Click, Context = Right Click (handled by menu)
    if reason == QSystemTrayIcon.ActivationReason.Trigger:
        # print("Tray icon left-clicked.") # DEBUG PRINT (Optional)
        show_search_ui_safe()
    # elif reason == QSystemTrayIcon.ActivationReason.Context:
         # print("Tray icon right-clicked (Menu shown).") # DEBUG PRINT (Optional)
    elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
         # print("Tray icon double-clicked.") # DEBUG PRINT (Optional)
         show_search_ui_safe() # Also show search on double-click


# --- Main Application ---
def main():
    global app, search_window, editor_window

    # Hide console window (on Windows)
    hide_console()
    # Print statements after hide_console might not be visible in the hidden console,
    # but are useful if running from an existing terminal or if hiding fails.
    # Redirect important errors to stderr if possible.
    print("--- Starting Prompt Manager ---")

    # Initialize Database
    print("Initializing database...")
    db.initialize_database()
    print("Database ready.")

    # Create Qt Application
    app = QApplication(sys.argv)
    # Keep app running even if windows are hidden, rely on Tray Quit
    app.setQuitOnLastWindowClosed(False)
    print("QApplication created.")

    # Create UI Windows
    print("Creating UI windows...")
    search_window = SearchUIWindow()
    editor_window = PromptEditorWindow()
    print("UI windows created.")

    # Connect signals
    print("Connecting signals...")
    search_window.open_editor_requested.connect(show_editor_ui_safe)
    editor_window.closing.connect(editor_closed_safe) # Connect editor close signal
    print("Signals connected.")

    # Setup System Tray Icon
    setup_tray_icon() # Call the setup function

    # Start hotkey listener in a separate thread
    print("Starting hotkey listener thread...")
    listener_thread = threading.Thread(target=hotkey_listener_thread, daemon=True)
    listener_thread.start()
    # Give the thread a moment to register the hotkey
    # QTimer.singleShot(500, lambda: print("Hotkey listener thread likely running.")) # Optional debug print


    print(f"--- Prompt Manager Ready ---")
    print(f"Press '{HOTKEY}' to open search.")
    print(f"Or use the system tray icon.")
    # print(f"Check this terminal for messages.") # Less relevant if console is hidden
    print(f"----------------------------")

    # Start the Qt event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
# --- END OF FILE main.py ---