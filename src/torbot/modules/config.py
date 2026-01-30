import os

from dotenv import load_dotenv
from pathlib import Path

config_file_path = Path(__file__).resolve()
modules_directory = config_file_path.parent
torbot_directory = modules_directory.parent
project_root_directory = str(torbot_directory.parent)
dotenv_path = os.path.join(project_root_directory, ".env")
load_dotenv(dotenv_path=dotenv_path, verbose=True)


def get_data_directory():
    data_directory = os.getenv("TORBOT_DATA_DIR")
    # if a path is not set, write data to the config directory
    if not data_directory or data_directory.strip() == "":
        data_directory = project_root_directory

    # create directory if it doesn't exist
    if not os.path.exists(data_directory):
        os.mkdir(data_directory)

    return data_directory
