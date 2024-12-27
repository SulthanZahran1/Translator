from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QLabel, QPushButton, QToolTip,
                             QProgressBar, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QTextCursor, QFont, QPalette, QColor, QCursor
import sys
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.hide()

    def setup_ui(self):
        """Setup the loading overlay UI."""
        # Set up the semi-transparent background
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 128))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        # Create a container for the loading elements with white background
        self.container = QFrame(self)
        self.container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        self.container.setFixedSize(300, 150)

        # Layout for the container
        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setSpacing(15)

        # Loading label
        self.loading_label = QLabel("Loading Model...")
        self.loading_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Indeterminate progress
        self.progress_bar.setFixedWidth(250)
        self.progress_bar.setFixedHeight(8)  # Make it thinner
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                background-color: #f5f5f5;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)

        # Add widgets to container layout
        container_layout.addWidget(self.loading_label)
        container_layout.addWidget(self.progress_bar)

        # Main layout for the overlay
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.container)

    def resizeEvent(self, event):
        """Ensure overlay covers the entire parent widget and centers the container."""
        if self.parent():
            self.resize(self.parent().size())
            # Center the container
            container_x = (self.width() - self.container.width()) // 2
            container_y = (self.height() - self.container.height()) // 2
            self.container.move(container_x, container_y)
        super().resizeEvent(event)

class TranslationWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    manual_translation_requested = pyqtSignal(str, str, str)  # text, source_lang, target_lang
    def __init__(self, model, text: str, source_lang: str, target_lang: str):
        super().__init__()
        self.model = model
        self.text = text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.logger = logging.getLogger(__name__)

    def run(self):
        try:
            self.logger.info(f"Translation worker starting: {self.text[:50]}...")
            self.logger.info(f"Source lang: {self.source_lang}, Target lang: {self.target_lang}")
            
            # Add prompt based on direction
            if self.source_lang == "ko" and self.target_lang == "en":
                prompt = f"Translate this Korean text to English: {self.text}"
            else:
                prompt = f"Translate this English text to Korean: {self.text}"
            
            self.logger.info("Calling model.translate")
            translation = self.model.translate(prompt)
            self.logger.info(f"Translation completed: {translation[:50]}...")
            
            self.finished.emit(translation)
            
        except Exception as e:
            self.logger.error(f"Error in translation worker: {str(e)}")
            self.error.emit(str(e))

class TranslatorWidget(QWidget):
    translation_requested = pyqtSignal(str, str, str)  # text, source_lang, target_lang
    word_translation_requested = pyqtSignal(str, str)  # word, context

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.loading_overlay = LoadingOverlay(self)
        self.last_translation = {"source": "", "target": ""}  # Store last translation for context

    def init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout()
        editors_layout = QHBoxLayout()
        
        # Korean text editor
        korean_layout = QVBoxLayout()
        korean_label = QLabel("Korean Text")
        self.korean_editor = QTextEdit()
        self.korean_editor.setMouseTracking(True)  # Enable mouse tracking for hover
        korean_layout.addWidget(korean_label)
        korean_layout.addWidget(self.korean_editor)
        
        # Buttons layout in the middle
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Ko->En button
        self.ko_to_en_button = QPushButton("한국어 → English")
        self.ko_to_en_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        # En->Ko button
        self.en_to_ko_button = QPushButton("English → 한국어")
        self.en_to_ko_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.ko_to_en_button)
        buttons_layout.addWidget(self.en_to_ko_button)
        buttons_layout.addStretch()
        
        # English text editor
        english_layout = QVBoxLayout()
        english_label = QLabel("English Text")
        self.english_editor = QTextEdit()
        self.english_editor.setMouseTracking(True)  # Enable mouse tracking for hover
        english_layout.addWidget(english_label)
        english_layout.addWidget(self.english_editor)
        
        # Add all layouts to the horizontal layout
        editors_layout.addLayout(korean_layout)
        editors_layout.addLayout(buttons_layout)
        editors_layout.addLayout(english_layout)
        
        # Set the stretch factors for better layout
        editors_layout.setStretch(0, 10)  # Korean editor
        editors_layout.setStretch(1, 1)   # Buttons
        editors_layout.setStretch(2, 10)  # English editor
        
        # Add to main layout
        main_layout.addLayout(editors_layout)
        
        self.setLayout(main_layout)
        
        # Connect button signals
        self.ko_to_en_button.clicked.connect(self.on_ko_to_en_clicked)
        self.en_to_ko_button.clicked.connect(self.on_en_to_ko_clicked)
        
        # Connect text selection signals
        self.korean_editor.selectionChanged.connect(lambda: self.handle_text_selection(self.korean_editor))
        self.english_editor.selectionChanged.connect(lambda: self.handle_text_selection(self.english_editor))
        
        # Setup tooltip
        QToolTip.setFont(QFont('SansSerif', 10))

    def handle_text_selection(self, editor):
        """Handle text selection in either editor."""
        cursor = editor.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            if selected_text.strip():
                # Determine which editor was used and get appropriate context
                if editor == self.korean_editor:
                    context = self.last_translation.get("source", "")
                else:
                    context = self.last_translation.get("target", "")
                
                # Emit signal for word translation
                self.word_translation_requested.emit(selected_text, context)

    def show_word_translation(self, translations: dict):
        """Show word translation in a tooltip."""
        if not translations:
            return
            
        tooltip_text = f"Direct Translation: {translations['direct_translation']}\n"
        if translations.get('contextual_translation'):
            tooltip_text += f"\nContextual Meaning:\n{translations['contextual_translation']}"
        
        # Show tooltip near the cursor
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        QToolTip.showText(self.mapToGlobal(cursor_pos), tooltip_text)

    def on_ko_to_en_clicked(self):
        """Handle Korean to English translation."""
        text = self.korean_editor.toPlainText()
        if text.strip():
            self.last_translation["source"] = text
            self.translation_requested.emit(text, "ko", "en")

    def on_en_to_ko_clicked(self):
        """Handle English to Korean translation."""
        text = self.english_editor.toPlainText()
        if text.strip():
            self.last_translation["source"] = text
            self.translation_requested.emit(text, "en", "ko")

    def show_translation(self, text: str, target_lang: str):
        """Display translation in the appropriate editor."""
        if target_lang == "en":
            self.english_editor.setText(text)
            self.last_translation["target"] = text
        else:
            self.korean_editor.setText(text)
            self.last_translation["target"] = text

    def show_loading(self, message: str = "Loading Model..."):
        """Show the loading overlay."""
        self.loading_overlay.loading_label.setText(message)
        self.loading_overlay.show()
        self.loading_overlay.raise_()

    def hide_loading(self):
        """Hide the loading overlay."""
        self.loading_overlay.hide()

class TranslatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the main window UI."""
        self.setWindowTitle('Korean-English Translator')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        self.translator_widget = TranslatorWidget()
        self.setCentralWidget(self.translator_widget)
        
        # Setup menubar
        self.setup_menubar()
        
        self.show()

    def setup_menubar(self):
        """Setup the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        # Help menu
        help_menu = menubar.addMenu('Help')

def main():
    app = QApplication(sys.argv)
    translator = TranslatorWindow()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 