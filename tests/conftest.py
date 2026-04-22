import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_keyring():
    with patch("shane_skills.config.keyring") as mock_kr:
        mock_kr.get_password.return_value = "mock_password"
        yield mock_kr

@pytest.fixture(autouse=True)
def mock_config_dir(tmp_path):
    with patch("shane_skills.config.CONFIG_DIR", tmp_path / ".shane-skills"), \
         patch("shane_skills.config.CONFIG_FILE", tmp_path / ".shane-skills" / "config.toml"):
        yield tmp_path
