import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as SessionType
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, List
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    echo=True,  # 设为 True 可以看到 SQL 查询日志
    pool_pre_ping=True,  # 验证连接是否有效
    pool_recycle=3600,   # 每小时回收连接
)

# 创建基类
Base = declarative_base()

# 数据库模型定义
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    discord_id = Column(String(20), unique=True, nullable=False)
    username = Column(String(100), nullable=False)
    display_name = Column(String(100))
    joined_at = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<User(discord_id='{self.discord_id}', username='{self.username}')>"

class Guild(Base):
    __tablename__ = 'guilds'
    
    id = Column(Integer, primary_key=True)
    discord_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    owner_id = Column(String(20))
    member_count = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Guild(discord_id='{self.discord_id}', name='{self.name}')>"

class UserActivity(Base):
    __tablename__ = 'user_activities'
    
    id = Column(Integer, primary_key=True)
    user_discord_id = Column(String(20), nullable=False)
    guild_discord_id = Column(String(20), nullable=False)
    activity_type = Column(String(50), nullable=False)  # 'message', 'command', 'join', 'leave'
    activity_data = Column(Text)  # JSON 数据存储具体信息
    timestamp = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<UserActivity(user='{self.user_discord_id}', type='{self.activity_type}')>"

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 上下文管理器用于会话管理
@contextmanager
def get_db_session():
    """提供数据库会话的上下文管理器"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()

# 数据库操作函数
class DatabaseManager:
    
    @staticmethod
    def init_database():
        """初始化数据库表"""
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    @staticmethod
    def get_or_create_user(discord_id: str, username: str, display_name: str = None) -> Optional[User]:
        """获取或创建用户"""
        with get_db_session() as session:
            user = session.query(User).filter_by(discord_id=discord_id).first()
            
            if not user:
                user = User(
                    discord_id=discord_id,
                    username=username,
                    display_name=display_name or username,
                    joined_at=datetime.now(),
                    last_seen=datetime.now()
                )
                session.add(user)
                logger.info(f"Created new user: {username} ({discord_id})")
            else:
                # 更新用户信息
                user.username = username
                user.display_name = display_name or username
                user.last_seen = datetime.now()
                logger.info(f"Updated user: {username} ({discord_id})")
            
            return user
    
    @staticmethod
    def get_user_by_discord_id(discord_id: str) -> Optional[User]:
        """根据 Discord ID 获取用户"""
        with get_db_session() as session:
            return session.query(User).filter_by(discord_id=discord_id).first()
    
    @staticmethod
    def get_all_users() -> List[User]:
        """获取所有用户"""
        with get_db_session() as session:
            return session.query(User).filter_by(is_active=True).all()
    
    @staticmethod
    def get_or_create_guild(discord_id: str, name: str, owner_id: str = None, member_count: int = 0) -> Optional[Guild]:
        """获取或创建服务器"""
        with get_db_session() as session:
            guild = session.query(Guild).filter_by(discord_id=discord_id).first()
            
            if not guild:
                guild = Guild(
                    discord_id=discord_id,
                    name=name,
                    owner_id=owner_id,
                    member_count=member_count,
                    joined_at=datetime.now()
                )
                session.add(guild)
                logger.info(f"Created new guild: {name} ({discord_id})")
            else:
                # 更新服务器信息
                guild.name = name
                guild.owner_id = owner_id
                guild.member_count = member_count
                logger.info(f"Updated guild: {name} ({discord_id})")
            
            return guild
    
    @staticmethod
    def log_user_activity(user_discord_id: str, guild_discord_id: str, activity_type: str, activity_data: str = None):
        """记录用户活动"""
        with get_db_session() as session:
            activity = UserActivity(
                user_discord_id=user_discord_id,
                guild_discord_id=guild_discord_id,
                activity_type=activity_type,
                activity_data=activity_data,
                timestamp=datetime.now()
            )
            session.add(activity)
            logger.info(f"Logged activity: {activity_type} for user {user_discord_id}")
    
    @staticmethod
    def get_user_activity_count(user_discord_id: str, activity_type: str = None) -> int:
        """获取用户活动次数"""
        with get_db_session() as session:
            query = session.query(UserActivity).filter_by(user_discord_id=user_discord_id)
            if activity_type:
                query = query.filter_by(activity_type=activity_type)
            return query.count()
    
    @staticmethod
    def deactivate_user(discord_id: str):
        """停用用户"""
        with get_db_session() as session:
            user = session.query(User).filter_by(discord_id=discord_id).first()
            if user:
                user.is_active = False
                logger.info(f"Deactivated user: {user.username} ({discord_id})")
    
    @staticmethod
    def deactivate_guild(discord_id: str):
        """停用服务器"""
        with get_db_session() as session:
            guild = session.query(Guild).filter_by(discord_id=discord_id).first()
            if guild:
                guild.is_active = False
                logger.info(f"Deactivated guild: {guild.name} ({discord_id})")

# 数据库管理器实例
db_manager = DatabaseManager()

# 初始化数据库
def init_db():
    """初始化数据库"""
    db_manager.init_database()

if __name__ == "__main__":
    # 如果直接运行此文件，初始化数据库
    init_db()
    print("Database initialized successfully!")