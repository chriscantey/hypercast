import sqlite3
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        # Ensure data directory exists relative to project root
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)

        # Set database path
        self.db_path = self.data_dir / 'hypercast.db'

        # Initialize database if it doesn't exist
        self._initialize_db()

    def _initialize_db(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            # Create new database with proper permissions
            if not self.db_path.exists():
                self.db_path.touch(mode=0o600)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create episodes table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS episodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        pub_date TEXT NOT NULL,
                        duration TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

    def add_episode(self, filename: str, title: str, description: str, pub_date: str, duration: str = None) -> bool:
        """Add a new episode to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO episodes (filename, title, description, pub_date, duration)
                       VALUES (?, ?, ?, ?, ?)''',
                    (filename, title, description, pub_date, duration)
                )
                conn.commit()
                logger.info(f"Added episode: {title}")
                return True
        except Exception as e:
            logger.error(f"Error adding episode: {str(e)}")
            return False

    def get_all_episodes(self):
        """Retrieve all episodes for the feed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''SELECT filename, title, description, pub_date, duration
                       FROM episodes
                       ORDER BY created_at DESC'''
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error retrieving episodes: {str(e)}")
            return []

# Create a singleton instance
db = DatabaseService()
