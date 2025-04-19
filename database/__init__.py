import os
import sqlite3
from datetime import datetime

class DatabaseManager:
    _instance = None  # Singleton instance
    
    def __new__(cls, script_dir=None, logger=None):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, script_dir=None, logger=None):
        # Skip initialization if already done
        if self._initialized:
            return
            
        self.script_dir = script_dir
        self.logger = logger
        self.conn = None
        self.cursor = None
        
        if script_dir:
            self.initialize_db(script_dir, logger)
        
        self._initialized = True
    
    def initialize_db(self, script_dir, logger=None):
        """Initialize database connection and create necessary tables"""
        self.script_dir = script_dir
        self.logger = logger
        
        # Set up database connection
        db_dir = os.path.join(script_dir, "data")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "bot_data.db")
        
        if logger:
            logger.info(f"Initializing database at {db_path}")
        
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Create necessary tables
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary database tables if they don't exist"""
        # Users table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT DEFAULT NULL,
            sign_in_count INTEGER DEFAULT 0,
            exp INTEGER DEFAULT 0
        )
        ''')
        
        # Sign-in records table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS sign_in_records (
            user_id TEXT,
            date TEXT,
            PRIMARY KEY(user_id, date),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        ''')

        # fortune table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS fortune_record (
            user_id TEXT,
            date TEXT,
            fortune TEXT,
            PRIMARY KEY(user_id, date),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        ''')

        # rock-paper-scissors table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS rps_record (
            builder_id TEXT,
            receiver_id TEXT,
            date TEXT,
            result TEXT,
            FOREIGN KEY(builder_id) REFERENCES users(user_id)
            FOREIGN KEY(receiver_id) REFERENCES users(user_id)
        )
        ''')

        self.conn.commit()
        if self.logger:
            self.logger.info("Database tables initialized")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            if self.logger:
                self.logger.info("Database connection closed")
    
    # Helper methods for common operations
    def get_user(self, user_id) -> tuple:
        """Get user data from database"""
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (str(user_id),))
        return self.cursor.fetchone()

    def get_all_users(self) -> list:
        """Get all users from database"""
        self.cursor.execute('SELECT * FROM users')
        return self.cursor.fetchall()

    def ensure_user_exists(self, user_id, username) -> bool:
        """
        Ensure user exists in database.
        
        Args:
            user_id: The user's Discord ID
            username: The user's Discord username
            
        Returns:
            bool: True if a new user was created, False if the user already existed
        """
        if not self.get_user(user_id):
            self.cursor.execute(
                'INSERT INTO users (user_id, username) VALUES (?, ?)',
                (str(user_id), username)
            )
            self.conn.commit()
            return True
        return False
    
    def update_user(self, user_id, username):
        """Update user data in database"""
        self.cursor.execute(
            'UPDATE users SET username = ? WHERE user_id = ?',
            (username, str(user_id))
        )
        self.conn.commit()

    def update_exp(self, user_id, exp):
        """Update user's experience points"""
        self.ensure_user_exists(user_id, None)  # Ensure user exists
        self.cursor.execute(
            'UPDATE users SET exp = exp + ? WHERE user_id = ?',
            (exp, str(user_id))
        )
        self.conn.commit()

    def get_all_fortune(self, user_id) -> list:
        """Get fortune analysis for a user"""
        self.cursor.execute('SELECT * FROM fortune_record WHERE user_id = ?', (str(user_id),))
        return self.cursor.fetchall()



# Global instance for easy access from other modules
db_manager = None

def init_db(script_dir, logger=None):
    """Initialize the global database manager"""
    global db_manager
    db_manager = DatabaseManager(script_dir, logger)
    return db_manager

def get_db():
    """Get the global database manager instance"""
    global db_manager
    if db_manager is None:
        raise RuntimeError("Database manager not initialized. Call init_database first.")
    return db_manager