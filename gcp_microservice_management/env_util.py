import os
from glob import glob
from dotenv import load_dotenv
import sys
from .util import color_text
from .constants import FAIL


def find_key_file():
    key_files = glob("./terraform/hephaestus-418809-*.json")
    if not key_files:
        print(color_text("No service account key file found", FAIL))
        sys.exit(1)
    return key_files[0]


def find_env_file():
    current_dir = os.getcwd()
    while current_dir != os.path.dirname(current_dir):
        env_path = os.path.join(current_dir, ".env")
        if os.path.isfile(env_path):
            return env_path
        current_dir = os.path.dirname(current_dir)
    print(color_text(".env file not found", FAIL))
    sys.exit(1)


def load_env_variables(env_file):
    load_dotenv(env_file)
    return {
        key: os.getenv(key)
        for key in os.environ
        if key.startswith("DATABASE_")
    }
