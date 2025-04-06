import logging
import os

def setup_logger(script_dir):
    """
    Set up loggers for the bot.
    
    Args:
        script_dir: The directory where the script is located
    
    Returns:
        Tuple of (bot_logger, client_logger, music_logger)
    """
    # Create separate loggers for bot events and client events
    bot_logger = logging.getLogger("bot_events")
    client_logger = logging.getLogger("client_events")
    music_logger = logging.getLogger("music_events")

    # 設置日誌級別 (重要!)
    bot_logger.setLevel(logging.INFO)
    client_logger.setLevel(logging.INFO)
    music_logger.setLevel(logging.INFO)

    # 確保先清理任何已存在的處理器，避免重複
    for logger in [bot_logger, client_logger, music_logger]:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # Configure bot logger
    # Ensure the logs directory exists
    logs_dir = os.path.join(script_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # 添加控制台處理器，這樣你也能看到日誌輸出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    
    # 配置 bot logger
    bot_log_file = os.path.join(logs_dir, "bot.log")
    bot_handler = logging.FileHandler(bot_log_file, encoding="utf-8", mode="a")
    bot_handler.setLevel(logging.INFO)
    bot_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    bot_logger.addHandler(bot_handler)
    bot_logger.addHandler(console_handler)
    bot_logger.propagate = False

    # 配置 client logger
    client_log_file = os.path.join(logs_dir, "client.log")
    client_handler = logging.FileHandler(client_log_file, encoding="utf-8", mode="a")
    client_handler.setLevel(logging.INFO)
    client_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    client_logger.addHandler(client_handler)
    client_logger.propagate = False

    # 配置 music logger
    music_log_file = os.path.join(logs_dir, "music.log")
    music_handler = logging.FileHandler(music_log_file, encoding="utf-8", mode="a")
    music_handler.setLevel(logging.INFO)
    music_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    music_logger.addHandler(music_handler)
    music_logger.propagate = False

    return bot_logger, client_logger, music_logger

def get_logger(name):
    """
    Get a logger with the given name.
    
    Args:
        name: The name of the logger
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)