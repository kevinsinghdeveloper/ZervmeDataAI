import json
import logging
import os
import io
from dataclasses import is_dataclass, asdict
from datetime import datetime
from typing import Dict, Any, TypeVar, List, Type
import re

T = TypeVar("T")


class Utility:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        os.makedirs('logs', exist_ok=True)
        log_filename = (
            f"logs/app_{datetime.now().strftime('%Y-%m-%d')}.log"
        )
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )

        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    @staticmethod
    def log(message: str) -> None:
        Utility.logger.info(message)

    @staticmethod
    def debug_log(message: str) -> None:
        Utility.logger.debug(message)

    @staticmethod
    def warning_log(message: str) -> None:
        Utility.logger.warning(message)

    @staticmethod
    def error_log(message: str) -> None:
        Utility.logger.error(message)

    @staticmethod
    def critical_log(message: str) -> None:
        Utility.logger.critical(message)

    @staticmethod
    def read_in_json_file(json_path: str) -> Dict[str, Any]:
        try:
            with open(json_path, 'r') as file:
                content = file.read()
                config = json.loads(content)
                return config
        except json.JSONDecodeError as e:
            Utility.error_log(
                f"JSONDecodeError: {e.msg} at line {e.lineno} column {e.colno}"
            )
            Utility.error_log(f"Problematic JSON content: {content}")
        except FileNotFoundError:
            Utility.error_log(f"File not found: {json_path}")
            return None
        except Exception as e:
            Utility.error_log(f"An error occurred: {e}")
        raise

    @staticmethod
    def write_dict_to_json_file(data: dict, file_path: str):
        try:
            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            Utility.log(
                f"Dictionary successfully written to {file_path}"
            )
        except Exception as e:
            Utility.error_log(
                f"An error occurred while writing to the JSON file: {e}"
            )

    @staticmethod
    def read_image(image_path: str) -> bytes:
        try:
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
                Utility.log(f"Image read successfully from {image_path}.")
                return content
        except FileNotFoundError:
            Utility.error_log(f"Image file not found: {image_path}")
            raise
        except Exception as e:
            Utility.error_log(f"Failed to read image file: {e}")
            raise

    @staticmethod
    def trim_spaces(input_string):
        trimmed_string = ' '.join(input_string.split())
        return trimmed_string

    @staticmethod
    def clean_and_convert(value) -> float | int:
        if isinstance(value, (int, float)):
            return value
        cleaned_value = re.sub(r"[^\d.-]", "", str(value))

        if not cleaned_value or cleaned_value in {"-", "."}:
            return 0

        try:
            return (
                int(cleaned_value) if "." not in cleaned_value
                else float(cleaned_value)
            )
        except ValueError:
            return 0
