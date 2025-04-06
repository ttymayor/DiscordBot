import logging
import os

def setup_logger(script_dir):
    """
    Set up loggers for the bot.
    
    Args:
        script_dir: The directory where the script is located
    
    Returns:
        Tuple of (bot_logger, client_logger)
    """
    # Configure logging
    log_file = os.path.join(script_dir, "bot.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8")
        ]
    )
    
    # Create separate loggers for bot events and client events
    bot_logger = logging.getLogger("bot_events")
    client_logger = logging.getLogger("client_events")

    # Add a handler for client events
    client_log_file = os.path.join(script_dir, "client.log")
    client_handler = logging.FileHandler(client_log_file, encoding="utf-8")
    client_handler.setLevel(logging.INFO)
    client_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    client_logger.addHandler(client_handler)
    
    return bot_logger, client_logger

def get_logger(name):
    """
    Get a logger with the given name.
    
    Args:
        name: The name of the logger
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)