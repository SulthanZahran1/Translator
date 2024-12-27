import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal
from translator_ui import TranslatorWindow, TranslationWorker
from model_setup import TranslationModel
from korean_processor import KoreanProcessor
from cache_manager import CacheManager
from typing import Optional
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelLoader(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, model: TranslationModel, device: str):
        super().__init__()
        self.model = model
        self.device = device

    def run(self):
        try:
            self.model.load_model(self.device)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class TranslatorApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = TranslatorWindow()
        self.setup_components()
        self.connect_signals()

    def setup_components(self):
        """Initialize and setup all components."""
        try:
            # Initialize components
            self.cache = CacheManager()
            self.korean_processor = KoreanProcessor()
            self.translation_model = TranslationModel()
            
            # Show loading overlay
            self.window.translator_widget.show_loading("Initializing Translation Model...")
            
            # Load model in background
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            self.model_loader = ModelLoader(self.translation_model, device)
            self.model_loader.finished.connect(self.on_model_loaded)
            self.model_loader.error.connect(self.on_model_load_error)
            self.model_loader.start()
            
            # Load preferences
            self.load_preferences()
            
        except Exception as e:
            logger.error(f"Error setting up components: {str(e)}")
            raise

    def on_model_loaded(self):
        """Handle successful model loading."""
        self.window.translator_widget.hide_loading()
        logger.info("Model loaded successfully")

    def on_model_load_error(self, error_msg: str):
        """Handle model loading error."""
        self.window.translator_widget.hide_loading()
        logger.error(f"Model loading error: {error_msg}")
        # You might want to show an error dialog here

    def load_preferences(self):
        """Load user preferences from cache."""
        self.source_lang = self.cache.get_preference("source_lang", "ko")
        self.target_lang = self.cache.get_preference("target_lang", "en")

    def connect_signals(self):
        """Connect UI signals to handlers."""
        widget = self.window.translator_widget
        widget.translation_requested.connect(self.handle_translation_request)
        widget.word_translation_requested.connect(self.handle_word_translation)

    def handle_translation_request(self, text: str, source_lang: str, target_lang: str):
        """Handle translation requests."""
        if not text.strip():
            return

        try:
            logger.info(f"Starting translation request: {text[:50]}... ({source_lang} -> {target_lang})")
            # Check cache first
            cached_translation = self.cache.get_cached_translation(
                text, source_lang, target_lang
            )
            
            if cached_translation:
                logger.info("Found cached translation, using it")
                self.window.translator_widget.show_translation(cached_translation, target_lang)
                return

            # Show loading for longer translations
            if len(text.split()) > 5:  # Only show loading for longer texts
                logger.info("Showing loading overlay for long text")
                self.window.translator_widget.show_loading("Translating...")

            # Create and start translation worker
            logger.info("Creating translation worker thread")
            self.translation_worker = TranslationWorker(
                self.translation_model, text, source_lang, target_lang
            )
            self.translation_worker.finished.connect(
                lambda translation: self.handle_translation_complete(
                    translation, text, source_lang, target_lang
                )
            )
            self.translation_worker.error.connect(self.handle_translation_error)
            logger.info("Starting translation worker thread")
            self.translation_worker.start()

        except Exception as e:
            logger.error(f"Translation error in request handler: {str(e)}")
            self.window.translator_widget.hide_loading()
            self.window.translator_widget.show_translation(
                "Error occurred during translation. Please try again.",
                target_lang
            )

    def handle_translation_complete(self, translation: str, source_text: str, 
                                  source_lang: str, target_lang: str):
        """Handle completed translation."""
        logger.info("Translation completed successfully")
        self.window.translator_widget.hide_loading()
        
        # Cache the result
        logger.info("Caching translation result")
        self.cache.cache_translation(
            source_text, translation, source_lang, target_lang
        )
        
        # Update UI
        logger.info("Updating UI with translation")
        self.window.translator_widget.show_translation(translation, target_lang)

    def handle_translation_error(self, error_msg: str):
        """Handle translation error."""
        logger.error(f"Translation error in worker thread: {error_msg}")
        self.window.translator_widget.hide_loading()
        self.window.translator_widget.show_translation(
            "Error occurred during translation. Please try again.",
            "en"  # Default to English for error messages
        )

    def handle_word_translation(self, word: str, context: str):
        """Handle word translation requests."""
        try:
            # Get both direct and contextual translations
            translations = self.translation_model.translate_word(word, context)
            
            # Show translations in tooltip
            self.window.translator_widget.show_word_translation(translations)
            
        except Exception as e:
            logger.error(f"Word translation error: {str(e)}")
            # Show error in tooltip
            self.window.translator_widget.show_word_translation({
                "word": word,
                "direct_translation": "Translation error",
                "contextual_translation": str(e)
            })

    def run(self):
        """Run the application."""
        try:
            return self.app.exec()
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            return 1

def main():
    try:
        app = TranslatorApp()
        sys.exit(app.run())
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 