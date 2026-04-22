import pytest
from unittest.mock import patch, MagicMock
from shane_skills.integrations.confluence_client import ConfluenceClient

@patch("shane_skills.integrations.confluence_client.Config")
@patch("shane_skills.integrations.confluence_client.console")
def test_from_config_missing(mock_console, mock_config):
    mock_cfg = MagicMock()
    mock_cfg.confluence_url = ""
    mock_cfg.get_confluence_token.return_value = ""
    mock_config.load.return_value = mock_cfg
    with pytest.raises(SystemExit):
        ConfluenceClient.from_config()
    mock_console.print.assert_called()

@patch("shane_skills.integrations.confluence_client.Config")
def test_from_config_success(mock_config):
    mock_cfg = MagicMock()
    mock_cfg.confluence_url = "http://conf"
    mock_cfg.get_confluence_token.return_value = "token"
    mock_config.load.return_value = mock_cfg
    client = ConfluenceClient.from_config()
    assert client.url == "http://conf"

@patch("atlassian.Confluence")
def test_get_confluence(mock_conf_class):
    client = ConfluenceClient("http://conf", "token")
    conf = client._get_confluence()
    mock_conf_class.assert_called_once_with(url="http://conf", token="token", verify_ssl=False)
    assert conf == mock_conf_class.return_value
    client._get_confluence()
    assert mock_conf_class.call_count == 1

def test_format_page():
    client = ConfluenceClient("http://conf", "token")
    data = {
        "id": "123",
        "title": "Test Page",
        "space": {"name": "Test Space"},
        "version": {"number": 2, "when": "2023-01-01T12:00:00Z", "by": {"displayName": "User"}},
        "ancestors": [{"title": "Parent"}],
        "_links": {"webui": "/pages/123"},
        "body": {"storage": {"value": "<p>Content</p>"}}
    }
    md = client._format_page(data)
    assert "# Test Page" in md
    assert "**Space:** Test Space" in md
    assert "**Version:** 2" in md
    assert "**Last Modified:** 2023-01-01" in md
    assert "**Page ID:** 123" in md
    assert "**URL:** http://conf/pages/123" in md
    assert "**Path:** Parent > Test Page" in md
    assert "Content" in md

def test_format_page_empty():
    client = ConfluenceClient("http://conf", "token")
    md = client._format_page({})
    assert "# Untitled" in md
    assert "(No content)" in md

@patch("shane_skills.integrations.confluence_client.ConfluenceClient._get_confluence")
def test_get_page(mock_get_conf):
    client = ConfluenceClient("http://conf", "token")
    mock_api = MagicMock()
    mock_api.get_page_by_id.return_value = {"id": "1"}
    mock_get_conf.return_value = mock_api
    
    assert client.get_page("1") == {"id": "1"}
    mock_api.get_page_by_id.assert_called_with("1", expand="body.storage,space,version,ancestors,_links")

@patch("shane_skills.integrations.confluence_client.console")
@patch("shane_skills.integrations.confluence_client.ConfluenceClient.get_page")
def test_print_page_not_found(mock_get_page, mock_console):
    client = ConfluenceClient("http://conf", "token")
    mock_get_page.return_value = {}
    client.print_page("1")
    mock_console.print.assert_called_with("[red]Page 1 not found or access denied.[/red]")

@patch("shane_skills.integrations.confluence_client.console")
@patch("shane_skills.integrations.confluence_client.ConfluenceClient.get_page")
def test_print_page_success(mock_get_page, mock_console):
    client = ConfluenceClient("http://conf", "token")
    mock_get_page.return_value = {"id": "1"}
    client.print_page("1")
    mock_console.print.assert_called()

@patch("shane_skills.integrations.confluence_client.ConfluenceClient._get_confluence")
@patch("shane_skills.integrations.confluence_client.console")
def test_search_and_print_no_results(mock_console, mock_get_conf):
    client = ConfluenceClient("http://conf", "token")
    mock_api = MagicMock()
    mock_api.cql.return_value = {"results": []}
    mock_get_conf.return_value = mock_api
    client.search_and_print("q")
    mock_console.print.assert_called_with("[yellow]No results for: q[/yellow]")

@patch("shane_skills.integrations.confluence_client.Table")
@patch("shane_skills.integrations.confluence_client.ConfluenceClient._get_confluence")
@patch("shane_skills.integrations.confluence_client.console")
def test_search_and_print_success(mock_console, mock_get_conf, mock_table):
    client = ConfluenceClient("http://conf", "token")
    mock_api = MagicMock()
    mock_api.cql.return_value = {"results": [{"id": "1", "title": "T", "resultGlobalContainer": {"title": "S"}, "url": "/u"}]}
    mock_get_conf.return_value = mock_api
    
    mock_tbl_inst = MagicMock()
    mock_table.return_value = mock_tbl_inst
    
    client.search_and_print("q", space="S")
    mock_tbl_inst.add_row.assert_called_with("1", "T", "S", "http://conf/u")
    mock_console.print.assert_any_call(mock_tbl_inst)

@patch("shane_skills.integrations.confluence_client.ConfluenceClient._get_confluence")
def test_create_page(mock_get_conf):
    client = ConfluenceClient("http://conf", "token")
    mock_api = MagicMock()
    
    # Test parent not found
    mock_api.get_page_by_id.return_value = None
    mock_get_conf.return_value = mock_api
    assert client.create_page("1", "T", "C")["error"] is True
    
    # Test space not found
    mock_api.get_page_by_id.return_value = {"space": {}}
    assert client.create_page("1", "T", "C")["error"] is True
    
    # Test create success
    mock_api.get_page_by_id.return_value = {"space": {"key": "SP"}}
    mock_api.create_page.return_value = {"id": "2", "_links": {"webui": "/new"}}
    res = client.create_page("1", "T", "C")
    assert res["id"] == "2"
    assert res["space"] == "SP"
    assert res["url"] == "http://conf/new"
    
    # Test create fails (returns empty)
    mock_api.create_page.return_value = None
    assert client.create_page("1", "T", "C")["error"] is True

@patch("shane_skills.integrations.confluence_client.console")
def test_print_created_page(mock_console):
    client = ConfluenceClient("http://conf", "token")
    client.print_created_page({"error": True, "content": "err"})
    mock_console.print.assert_called_with("[red]Error: err[/red]")
    
    client.print_created_page({"title": "T", "space": "S", "id": "1", "url": "U"})
    mock_console.print.assert_called()
