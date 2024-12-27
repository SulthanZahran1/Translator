import sqlite3
import json
from typing import Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, db_path: str = "translation_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS translations (
                        source_text TEXT PRIMARY KEY,
                        translated_text TEXT,
                        source_lang TEXT,
                        target_lang TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise

    def cache_translation(self, source_text: str, translated_text: str,
                         source_lang: str = 'ko', target_lang: str = 'en') -> None:
        """Store a translation in the cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO translations 
                    (source_text, translated_text, source_lang, target_lang)
                    VALUES (?, ?, ?, ?)
                """, (source_text, translated_text, source_lang, target_lang))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error caching translation: {str(e)}")
            raise

    def get_cached_translation(self, source_text: str,
                             source_lang: str = 'ko',
                             target_lang: str = 'en') -> Optional[str]:
        """Retrieve a cached translation if available."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT translated_text FROM translations
                    WHERE source_text = ? AND source_lang = ? AND target_lang = ?
                """, (source_text, source_lang, target_lang))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving cached translation: {str(e)}")
            return None

    def save_preference(self, key: str, value: Any) -> None:
        """Save a user preference."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO preferences (key, value)
                    VALUES (?, ?)
                """, (key, json.dumps(value)))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving preference: {str(e)}")
            raise

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Retrieve a user preference."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
                result = cursor.fetchone()
                return json.loads(result[0]) if result else default
        except sqlite3.Error as e:
            logger.error(f"Error retrieving preference: {str(e)}")
            return default

    def clear_cache(self, older_than_days: Optional[int] = None) -> None:
        """Clear the translation cache, optionally only entries older than specified days."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if older_than_days is not None:
                    cursor.execute("""
                        DELETE FROM translations
                        WHERE julianday('now') - julianday(timestamp) > ?
                    """, (older_than_days,))
                else:
                    cursor.execute("DELETE FROM translations")
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error clearing cache: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    cache = CacheManager()
    cache.save_preference("default_source_lang", "ko")
    print(f"Saved preference: {cache.get_preference('default_source_lang')}") 