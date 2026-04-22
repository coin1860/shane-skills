import pytest
from pathlib import Path
from shane_skills.config import Config, APP_NAME

def test_config_load_save(mock_config_dir):
    cfg = Config.load()
    assert cfg.jira_url == ""
    assert cfg.jira_username == ""
    
    cfg.jira_url = "https://jira.test"
    cfg.jira_username = "test_user"
    cfg.save()
    
    cfg2 = Config.load()
    assert cfg2.jira_url == "https://jira.test"
    assert cfg2.jira_username == "test_user"

def test_jira_token(mock_keyring):
    cfg = Config()
    cfg.jira_username = "jira_u"
    
    cfg.set_jira_token("token123")
    mock_keyring.set_password.assert_called_with(f"{APP_NAME}:jira_token", "jira_u", "token123")
    
    token = cfg.get_jira_token()
    assert token == "mock_password"
    mock_keyring.get_password.assert_called_with(f"{APP_NAME}:jira_token", "jira_u")

def test_confluence_token(mock_keyring):
    cfg = Config()
    cfg.confluence_username = "conf_u"
    
    cfg.set_confluence_token("token456")
    mock_keyring.set_password.assert_called_with(f"{APP_NAME}:confluence_token", "conf_u", "token456")
    
    token = cfg.get_confluence_token()
    assert token == "mock_password"
    mock_keyring.get_password.assert_called_with(f"{APP_NAME}:confluence_token", "conf_u")

def test_db_connections(mock_keyring):
    cfg = Config()
    
    cfg.add_db_connection(
        name="test_db",
        host="localhost",
        port=5432,
        username="db_u",
        driver="postgresql+psycopg2",
        service_name="test_svc",
        password="db_password"
    )
    
    assert "test_db" in cfg.get_db_connections()
    assert cfg.db_connections["test_db"]["host"] == "localhost"
    assert cfg.db_connections["test_db"]["port"] == 5432
    assert cfg.db_connections["test_db"]["username"] == "db_u"
    assert cfg.db_connections["test_db"]["driver"] == "postgresql+psycopg2"
    assert cfg.db_connections["test_db"]["service_name"] == "test_svc"
    
    mock_keyring.set_password.assert_called_with(f"{APP_NAME}:db:test_db", "db_u", "db_password")
    
    pw = cfg.get_db_password("test_db")
    assert pw == "mock_password"
    mock_keyring.get_password.assert_called_with(f"{APP_NAME}:db:test_db", "db_u")
    
    url = cfg.build_db_url("test_db")
    assert url == "postgresql+psycopg2://db_u:mock_password@localhost:5432/test_svc"
    
    display = cfg.get_db_dsn_display("test_db")
    assert display == "postgresql+psycopg2://db_u@localhost:5432/test_svc"
    
    # test remove
    cfg.remove_db_connection("test_db")
    assert "test_db" not in cfg.get_db_connections()
    mock_keyring.delete_password.assert_called_with(f"{APP_NAME}:db:test_db", "db_u")

def test_build_db_url_errors():
    cfg = Config()
    with pytest.raises(KeyError):
        cfg.build_db_url("non_existent")

def test_build_db_url_oracle():
    cfg = Config()
    cfg.add_db_connection(
        name="ora_db",
        host="ora.host",
        port=1521,
        username="ora_u",
        driver="oracle+oracledb",
        service_name="ORA_SVC"
    )
    url = cfg.build_db_url("ora_db")
    assert url == "oracle+oracledb://ora_u:mock_password@ora.host:1521/?service_name=ORA_SVC"

def test_build_db_url_mssql():
    cfg = Config()
    cfg.add_db_connection(
        name="ms_db",
        host="ms.host",
        port=1433,
        username="ms_u",
        driver="mssql+pyodbc",
        database="ms_db"
    )
    url = cfg.build_db_url("ms_db")
    assert url == "mssql+pyodbc://ms_u:mock_password@ms.host:1433/ms_db?driver=ODBC+Driver+17+for+SQL+Server"

def test_resolved_skills_root():
    cfg = Config()
    
    # Custom root
    cfg.skills_root = "/tmp/skills"
    assert cfg.resolved_skills_root() == Path("/tmp/skills")
    
    # Default root
    cfg.skills_root = ""
    root = cfg.resolved_skills_root()
    assert root.name == "skills"
    assert "shane-skills" in str(root)

def test_remove_db_connection_exception(mock_keyring):
    mock_keyring.delete_password.side_effect = Exception("keyring error")
    cfg = Config()
    cfg.add_db_connection("test", "h", 1, "u", "d")
    # Should not raise
    cfg.remove_db_connection("test")
    assert "test" not in cfg.db_connections
