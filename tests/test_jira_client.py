import pytest
from unittest.mock import patch, MagicMock
from shane_skills.integrations.jira_client import JiraClient, _extract_text

@patch("shane_skills.integrations.jira_client.Config")
@patch("shane_skills.integrations.jira_client.console")
def test_from_config_missing(mock_console, mock_config):
    mock_cfg = MagicMock()
    mock_cfg.jira_url = ""
    mock_cfg.get_jira_token.return_value = ""
    mock_config.load.return_value = mock_cfg
    with pytest.raises(SystemExit):
        JiraClient.from_config()
    mock_console.print.assert_called()

@patch("shane_skills.integrations.jira_client.Config")
def test_from_config_success(mock_config):
    mock_cfg = MagicMock()
    mock_cfg.jira_url = "http://jira"
    mock_cfg.get_jira_token.return_value = "token"
    mock_config.load.return_value = mock_cfg
    client = JiraClient.from_config()
    assert client.url == "http://jira"

@patch("atlassian.Jira")
def test_get_jira(mock_jira_class):
    client = JiraClient("http://jira", "token")
    jira = client._get_jira()
    mock_jira_class.assert_called_once_with(url="http://jira", token="token", verify_ssl=False)
    assert jira == mock_jira_class.return_value
    client._get_jira()
    assert mock_jira_class.call_count == 1

def test_extract_text():
    assert _extract_text(None) == ""
    assert _extract_text("text") == "text"
    assert _extract_text({"type": "text", "text": "hello"}) == "hello"
    assert _extract_text({"type": "doc", "content": [{"type": "text", "text": "hello"}, {"type": "text", "text": " world"}]}) == "hello  world"
    assert _extract_text(123) == "123"

def test_format_issue():
    client = JiraClient("http://jira", "token")
    data = {
        "key": "TEST-1",
        "fields": {
            "summary": "Sum",
            "status": {"name": "Open"},
            "priority": {"name": "High"},
            "issuetype": {"name": "Bug"},
            "assignee": {"displayName": "User A"},
            "reporter": {"displayName": "User B"},
            "labels": ["L1"],
            "components": [{"name": "C1"}],
            "description": "Desc"
        },
        "renderedFields": {
            "description": "<p>Desc</p>"
        }
    }
    comments = [
        {"author": {"displayName": "User C"}, "created": "2023-01-01T00:00:00Z", "body": "Comment 1"}
    ]
    md = client._format_issue(data, comments)
    assert "# TEST-1 — Sum" in md
    assert "**Type:** Bug | **Status:** Open | **Priority:** High" in md
    assert "**Assignee:** User A | **Reporter:** User B" in md
    assert "**Labels:** L1" in md
    assert "**Components:** C1" in md
    assert "**URL:** http://jira/browse/TEST-1" in md
    assert "Desc" in md
    assert "**User C (2023-01-01):**" in md
    assert "Comment 1" in md

    # dict body for comment/desc
    data["renderedFields"]["description"] = {"type": "text", "text": "dict desc"}
    comments[0]["body"] = {"type": "text", "text": "dict comm"}
    md2 = client._format_issue(data, comments)
    assert "dict desc" in md2
    assert "dict comm" in md2

@patch("shane_skills.integrations.jira_client.JiraClient._get_jira")
def test_get_issue(mock_get_jira):
    client = JiraClient("http://jira", "token")
    mock_api = MagicMock()
    mock_api.issue.return_value = {"key": "1"}
    mock_get_jira.return_value = mock_api
    assert client.get_issue("1") == {"key": "1"}
    mock_api.issue.assert_called_with("1", expand="renderedFields")

@patch("shane_skills.integrations.jira_client.console")
@patch("shane_skills.integrations.jira_client.JiraClient.get_issue")
@patch("shane_skills.integrations.jira_client.JiraClient._get_jira")
def test_print_issue(mock_get_jira, mock_get_issue, mock_console):
    client = JiraClient("http://jira", "token")
    mock_get_issue.return_value = {"key": "1"}
    mock_api = MagicMock()
    mock_api.issue_get_comments.return_value = {"comments": []}
    mock_get_jira.return_value = mock_api
    
    client.print_issue("1", as_json=True)
    mock_console.print_json.assert_called()
    
    client.print_issue("1")
    mock_console.print.assert_called()

@patch("shane_skills.integrations.jira_client.JiraClient._run_jql")
def test_search_and_jql(mock_run_jql):
    client = JiraClient("http://jira", "token")
    mock_run_jql.return_value = []
    
    client.search("text", limit=5)
    mock_run_jql.assert_called_with('text ~ "text" ORDER BY updated DESC', limit=5)
    
    client.jql("query", limit=5)
    mock_run_jql.assert_called_with("query", limit=5)

@patch("shane_skills.integrations.jira_client.JiraClient._get_jira")
def test_run_jql(mock_get_jira):
    client = JiraClient("http://jira", "token")
    mock_api = MagicMock()
    mock_api.jql.return_value = {"issues": [{"key": "1"}]}
    mock_get_jira.return_value = mock_api
    
    assert client._run_jql("q") == [{"key": "1"}]

@patch("shane_skills.integrations.jira_client.Table")
@patch("shane_skills.integrations.jira_client.console")
def test_print_search_results(mock_console, mock_table):
    client = JiraClient("http://jira", "token")
    
    client.print_search_results([])
    mock_console.print.assert_called_with("[yellow]No results found.[/yellow]")
    
    mock_tbl_inst = MagicMock()
    mock_table.return_value = mock_tbl_inst
    client.print_search_results([{"key": "1", "fields": {"summary": "S", "issuetype": {"name": "T"}, "status": {"name": "O"}, "priority": {"name": "H"}}}])
    mock_tbl_inst.add_row.assert_called_with("1", "T", "O", "H", "S")
    mock_console.print.assert_any_call(mock_tbl_inst)

@patch("shane_skills.integrations.jira_client.JiraClient._get_jira")
def test_create_issue(mock_get_jira):
    client = JiraClient("http://jira", "token")
    mock_api = MagicMock()
    
    assert client.create_issue("", "Sum")["error"] is True
    assert client.create_issue("P", "")["error"] is True
    
    mock_api.create_issue.return_value = {"key": "P-1"}
    mock_get_jira.return_value = mock_api
    
    res = client.create_issue("p", "Sum", "Desc", "Bug")
    assert res["key"] == "P-1"
    assert res["url"] == "http://jira/browse/P-1"
    mock_api.create_issue.assert_called_with(fields={"project": {"key": "P"}, "summary": "Sum", "issuetype": {"name": "Bug"}, "description": "Desc"})

@patch("shane_skills.integrations.jira_client.console")
def test_print_created_issue(mock_console):
    client = JiraClient("http://jira", "token")
    client.print_created_issue({"error": True, "content": "err"})
    mock_console.print.assert_called_with("[red]Error: err[/red]")
    
    client.print_created_issue({"key": "1", "url": "U", "summary": "S"})
    mock_console.print.assert_called()

def test_format_issue_html_comment():
    client = JiraClient("http://jira", "token")
    data = {"key": "T-1", "fields": {"summary": "S"}, "renderedFields": {}}
    comments = [{"body": "<b>bold</b>"}]
    md = client._format_issue(data, comments)
    assert "bold" in md

@patch("shane_skills.integrations.jira_client.console")
@patch("shane_skills.integrations.jira_client.JiraClient.get_issue")
@patch("shane_skills.integrations.jira_client.JiraClient._get_jira")
def test_print_issue_comments_error(mock_get_jira, mock_get_issue, mock_console):
    client = JiraClient("http://jira", "token")
    mock_get_issue.return_value = {"key": "1"}
    mock_api = __import__("unittest.mock").mock.MagicMock()
    mock_api.issue_get_comments.side_effect = Exception("err")
    mock_get_jira.return_value = mock_api
    client.print_issue("1")
    mock_console.print.assert_called()
