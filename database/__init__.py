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
                            
            exp INTEGER DEFAULT 0,
            joined_at TEXT DEFAULT NULL
        )
        ''')
        
        # Command logs table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            command TEXT,
            timestamp TEXT
        )
        ''')
        
        # Server settings table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_settings (
            guild_id TEXT PRIMARY KEY,
            welcome_channel_id TEXT,
            leave_channel_id TEXT,
            dynamic_channel_id TEXT,
            prefix TEXT DEFAULT "="
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
    def get_user(self, user_id):
        """Get user data from database"""
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (str(user_id),))
        return self.cursor.fetchone()
    
    def ensure_user_exists(self, user_id, username):
        """Ensure user exists in database"""
        if not self.get_user(user_id):
            self.cursor.execute(
                'INSERT INTO users (user_id, username, joined_at) VALUES (?, ?, ?)',
                (str(user_id), username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            self.conn.commit()
            return True
        return False
    
    def log_command(self, user_id, command):
        """Log command usage"""
        self.cursor.execute(
            'INSERT INTO command_logs (user_id, command, timestamp) VALUES (?, ?, ?)',
            (str(user_id), command, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        self.conn.commit()

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