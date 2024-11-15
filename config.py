import json
import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConfigFileNotFoundError(Exception):
    def __init__(self, message="Config not found."):
        self.message = message
        super().__init__(self.message)


def config_ini():
    config = {
        "database": {
            "host": "",
            "user": "",
            "password": "",
            "name": ""
        }
    }

    while True:
        user_input = input("Use DEFAULT? Y/N: ").strip().upper()
        if user_input in ["Y", "N"]:
            break
        else:
            print("Invalid input. Please enter 'Y' or 'N'.")

    if user_input == "N":
        config["database"]["host"] = input("New Host: ")
        config["database"]["user"] = input("New User: ")
        config["database"]["password"] = input("New Password: ")
        config["database"]["name"] = input("New Name: ")

        with open("config.json", "w") as json_file:
            json.dump(config, json_file, indent=4)

    else:
        try:
            with open("config.json", "r") as json_file:
                config = json.load(json_file)
        except Exception:
            raise ConfigFileNotFoundError("CANNOT find an existing DEFAULT, please press 'N' to create one.")

    return config
