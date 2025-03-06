import json
from pathlib import Path

import pytest

from app.utils import JsonFileManager, JsonFileManagerError

# ---------------------------
# Tests for ensure_file_exists
# ---------------------------


@pytest.mark.parametrize("default_content", [None, [{"key": "value"}], []])
@pytest.mark.parametrize("file_path_type", [str, Path])
def test_ensure_file_exists_creates_file(
    tmp_path, default_content, file_path_type
) -> None:
    """Test that ensure_file_exists creates a file with correct content."""
    # Create a file path that does not exist.
    file_path = tmp_path / "nonexistent.json"
    file_path_input = str(file_path) if file_path_type == str else file_path
    if file_path.exists():
        file_path.unlink()
    # Call ensure_file_exists; it should create the file with default content.
    JsonFileManager.ensure_file_exists(file_path_input, default_content)
    assert file_path.exists()
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    expected = [] if default_content is None else default_content
    assert data == expected


@pytest.mark.parametrize("file_path_type", [str, Path])
def test_ensure_file_exists_already_exists(tmp_path, file_path_type) -> None:
    """Test that ensure_file_exists doesn't modify existing files."""
    # Create a file that already exists with some content.
    file_path = tmp_path / "existing.json"
    content = [{"a": 1}]
    file_path.write_text(json.dumps(content))
    file_path_input = str(file_path) if file_path_type == str else file_path
    # Call ensure_file_exists with a different default; file should remain unchanged.
    JsonFileManager.ensure_file_exists(file_path_input, [{"b": 2}])
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == content


def test_ensure_file_exists_io_error(monkeypatch, tmp_path) -> None:
    """Test that ensure_file_exists handles IO errors correctly."""
    # Simulate an IOError when trying to open the file for writing.
    file_path = tmp_path / "error.json"

    def fake_open(*args, **kwargs):
        raise IOError("fake error")

    monkeypatch.setattr("builtins.open", fake_open)
    with pytest.raises(JsonFileManagerError, match="Could not create file"):
        JsonFileManager.ensure_file_exists(file_path)


# ---------------------------
# Tests for read_json
# ---------------------------
@pytest.mark.parametrize("file_path_type", [str, Path])
def test_read_json_valid(tmp_path, file_path_type) -> None:
    """Test reading valid JSON data from a file."""
    # Create a file with valid JSON.
    file_path = tmp_path / "valid.json"
    content = [{"key": "value"}]
    file_path.write_text(json.dumps(content))
    file_path_input = str(file_path) if file_path_type == str else file_path
    data = JsonFileManager.read_json(file_path_input)
    assert data == content


@pytest.mark.parametrize("file_path_type", [str, Path])
def test_read_json_file_not_found(tmp_path, file_path_type) -> None:
    """Test reading from a non-existent file returns empty list."""
    # Provide a path to a file that doesn't exist.
    file_path = tmp_path / "nonexistent.json"
    file_path_input = str(file_path) if file_path_type == str else file_path
    data = JsonFileManager.read_json(file_path_input)
    assert data == []


def test_read_json_invalid_json(tmp_path) -> None:
    """Test reading invalid JSON raises appropriate error."""
    file_path = tmp_path / "invalid.json"
    file_path.write_text("this is not json", encoding="utf-8")
    with pytest.raises(JsonFileManagerError, match="Invalid JSON in"):
        JsonFileManager.read_json(file_path)


def test_read_json_io_error(monkeypatch, tmp_path) -> None:
    """Test read_json handles IO errors correctly."""
    file_path = tmp_path / "io_error.json"

    def fake_open(*args, **kwargs):
        raise IOError("fake read error")

    monkeypatch.setattr("builtins.open", fake_open)
    with pytest.raises(JsonFileManagerError, match="Could not read file"):
        JsonFileManager.read_json(file_path)


# ---------------------------
# Tests for write_json
# ---------------------------
@pytest.mark.parametrize("file_path_type", [str, Path])
def test_write_json_success(tmp_path, file_path_type) -> None:
    """Test writing JSON data to a file successfully."""
    file_path = tmp_path / "output.json"
    data_to_write = [{"key": "value"}]
    file_path_input = str(file_path) if file_path_type == str else file_path
    JsonFileManager.write_json(file_path_input, data_to_write)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == data_to_write


def test_write_json_io_error(monkeypatch, tmp_path) -> None:
    """Test write_json handles IO errors correctly."""
    file_path = tmp_path / "output_error.json"

    def fake_open(*args, **kwargs):
        raise IOError("fake write error")

    monkeypatch.setattr("builtins.open", fake_open)
    with pytest.raises(JsonFileManagerError, match="Could not write to file"):
        JsonFileManager.write_json(file_path, [{"key": "value"}])
