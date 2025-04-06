"""
This module is responsible for loading the configuration data from a JSON file.
"""

import os
import json

# Create a function to get config data that can be called when needed
def get_config():
    # Get the directory of the parent folder (root directory)
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Construct the path to the config.json file in the root directory
    config_path = os.path.join(parent_dir, "config.json")
    
    try:
        # Load the JSON data
        with open(config_path, "r", encoding="utf8") as jfile:
            return json.load(jfile)
    except FileNotFoundError:
        print(f"Warning: Config file not found at {config_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Config file at {config_path} contains invalid JSON")
        return {}

# Create a function to update the config.json file
def set_config(new_config):
    # Get the directory of the parent folder (root directory)
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Construct the path to the config.json file in the root directory
    config_path = os.path.join(parent_dir, "config.json")
    
    try:
        # Write the new configuration data to the JSON file
        with open(config_path, "w", encoding="utf8") as jfile:
            json.dump(new_config, jfile, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error: Unable to write to config file at {config_path}. {e}")

# Load config at import time for immediate use
bot_settings = get_config()