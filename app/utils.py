import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class JsonFileManagerError(Exception):
    """Custom exception for JSON file management errors."""

    pass


class JsonFileManager:
    """This class provides a set of methods to handle common JSON file operations."""

    @staticmethod
    def ensure_file_exists(
        file_path: Union[str, Path],
        default_content: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Ensure a JSON file exists, creating it with default content if not.

        Args:
            file_path: Path to the JSON file
            default_content: Optional default content to write if file doesn't exist
        """
        file_path = Path(file_path)

        # Use empty list as default if no content provided
        if default_content is None:
            default_content = []

        # Create parent directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file with default content if it doesn't exist
        if not file_path.exists():
            try:
                with open(file_path, "w") as f:
                    json.dump(default_content, f, indent=2)
            except IOError as e:
                raise JsonFileManagerError(f"Could not create file {file_path}: {e}")

    @staticmethod
    def read_json(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Read JSON content from a file.

        Args:
            file_path: Path to the JSON file

        Returns:
            List of dictionaries from the JSON file
        """
        file_path = Path(file_path)

        try:
            with open(file_path, "r") as f:
                # Use parse method for more robust parsing
                return json.load(f)
        except FileNotFoundError:
            # Return empty list if file not found
            return []
        except json.JSONDecodeError as e:
            # Log or handle JSON decoding errors
            raise JsonFileManagerError(f"Invalid JSON in {file_path}: {e}")
        except IOError as e:
            # Handle other IO errors
            raise JsonFileManagerError(f"Could not read file {file_path}: {e}")

    @staticmethod
    def write_json(file_path: Union[str, Path], data: List[Dict[str, Any]]) -> None:
        """
        Write data to a JSON file.

        Args:
            file_path: Path to the JSON file
            data: Data to write to the file
        """
        file_path = Path(file_path)

        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise JsonFileManagerError(f"Could not write to file {file_path}: {e}")


class AuthenticationError(Exception):
    """Exception raised for authentication errors."""
