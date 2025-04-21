editor font size prompt:
    def apply_stylesheet(self):

                /* --- ADD Individual Font Size Rules --- */
            QLineEdit#PromptTitleInput {
                font-size: 11pt; /* Example size for Title */
            }
            QPlainTextEdit#PromptDescriptionInput {
                font-size: 10pt; /* Example size for Description */
            }
            QTextEdit#PromptContentEditor {
                font-size: 12pt; /* Example size for Content */
            }
            /* --- END Individual Font Size Rules --- */


=========

change editor window size 

    def initUI(self):
        self.setWindowTitle('Prompt Editor')
        # User specified geometry and minimum size
        self.setGeometry(18, 50, 1400, 800)
        self.setMinimumSize(800, 800)



===========

        self.prompt_title_input.setMaximumHeight(40)



        self.prompt_description_input.setMaximumHeight(50)

==========
# --- Configuration ---
HOTKEY = "ctrl+alt+p" # The key combination to trigger the search UI
ICON_PATH = "icon.png" # Path to your tray icon image

