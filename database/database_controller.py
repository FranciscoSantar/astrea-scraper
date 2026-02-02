import sqlite3
import logging
from pathlib import Path

class DatabaseController:
    def __init__(self, db_name: str = 'games.db', path:str = 'data'):
        self.target_dir = Path(path)
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.target_dir / db_name
        self.connection = None
        self.logger = logging.getLogger(__name__)

    def connect(self) -> sqlite3.Connection:
        """Establishes a connection to the SQLite database."""

        try:
            self.logger.info("🔌 Connecting to the database...")
            if self.connection is None:
                self.connection = sqlite3.connect(str(self.db_path))

            self.logger.info("✅ Database connected successfully.")
            return self.connection
        except sqlite3.Error as e:
            self.logger.error(f"❌ Error connecting to database: {e}")
            raise

    def disconnect(self) -> None:
        """Closes the connection to the SQLite database."""
        self.logger.info("🔚 Closing database connection...")

        if self.connection:
            self.connection.close()
            self.connection = None

        self.logger.info("✅ Database connection closed.")
    
    def database_initialization(self) -> None:
        """Initializes the database and creates the necessary tables.
        
        Creates tables for:
        - games
        - categories
        - game_category (table for many-to-many relationship between games and categories)
        """

        if not self.connection:
            self.logger.error("❌ No connection available. Can't create tables")
            return

        self.logger.info("🛠️  Initializing database and creating tables...")
    
        cursor = self.connection.cursor()
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS games 
                        (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            website_id INTEGER, 
                            name TEXT UNIQUE NOT NULL, 
                            description TEXT, 
                            price REAL NOT NULL, 
                            image_url TEXT,
                            has_stock BOOLEAN,
                            url TEXT,
                            sale_price REAL
                        );
                    '''
        )
        
        cursor.execute(''' 
                    CREATE TABLE IF NOT EXISTS categories 
                        (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            name TEXT UNIQUE
                        );
                        '''
        )

        cursor.execute(''' 
                    CREATE TABLE IF NOT EXISTS game_category 
                        (
                            game_id INTEGER,
                            category_id INTEGER,
                            PRIMARY KEY (game_id, category_id),
                            FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
                            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE 
                        );
                        '''
        )

        self.connection.commit()
        self.logger.info("✅ Database initialized and tables created successfully.")
