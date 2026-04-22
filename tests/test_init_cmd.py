import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from shane_skills.init_cmd import run_init, list_skills, _apply_action

@patch("shane_skills.init_cmd.console")
@patch("shane_skills.init_cmd.Config")
def test_run_init_missing_source(mock_config, mock_console, tmp_path):
    mock_cfg = MagicMock()
    mock_cfg.resolved_skills_root.return_value = tmp_path / "missing"
    mock_config.load.return_value = mock_cfg
    
    run_init(str(tmp_path), "all", False)
    mock_console.print.assert_any_call("[red]No agents or skills found in skills_root![/red]")

@patch("shane_skills.init_cmd.inquirer")
@patch("shane_skills.init_cmd.console")
@patch("shane_skills.init_cmd.Config")
def test_run_init_success(mock_config, mock_console, mock_inquirer, tmp_path):
    source_dir = tmp_path / "source"
    agents_dir = source_dir / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "a1.md").write_text("---\nname: agent1\n---\ncontent", encoding="utf-8")
    
    skills_dir = source_dir / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "s1").mkdir(parents=True)
    (skills_dir / "s1" / "SKILL.md").write_text("---\nname: skill1\n---\ncontent", encoding="utf-8")
    
    mock_cfg = MagicMock()
    mock_cfg.resolved_skills_root.return_value = source_dir
    mock_config.load.return_value = mock_cfg
    
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    # Mock user input
    mock_checkbox = MagicMock()
    mock_checkbox.execute.return_value = [
        ("agent", agents_dir / "a1.md", "agent1"),
        ("skill", skills_dir / "s1", "skill1")
    ]
    mock_inquirer.checkbox.return_value = mock_checkbox
    
    # Dry run
    run_init(str(target_dir), "copilot", True)
    assert not (target_dir / ".github").exists()
    
    # Real run
    run_init(str(target_dir), "copilot", False)
    
    assert (target_dir / ".github" / "agents" / "agent1.agent.md").read_text() == "---\nname: agent1\n---\ncontent"
    assert (target_dir / ".github" / "skills" / "skill1" / "SKILL.md").read_text() == "---\nname: skill1\n---\ncontent"
    assert "Global Copilot Instructions" in (target_dir / ".github" / "copilot-instructions.md").read_text()
    
    # OpenCode profile
    run_init(str(target_dir), "opencode", False)
    assert (target_dir / ".opencode" / "agents" / "agent1.md").read_text() == "---\nname: agent1\n---\ncontent"
    assert (target_dir / ".opencode" / "rules" / "skill1.md").read_text() == "---\nname: skill1\n---\ncontent"

@patch("shane_skills.init_cmd.console")
@patch("shane_skills.init_cmd.Config")
def test_list_skills(mock_config, mock_console, tmp_path):
    source_dir = tmp_path / "source"
    agents_dir = source_dir / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "a1.md").write_text("---\nname: agent1\n---\ncontent")
    
    mock_cfg = MagicMock()
    mock_cfg.resolved_skills_root.return_value = source_dir
    mock_config.load.return_value = mock_cfg
    
    list_skills("all")
    mock_console.print.assert_called()

def test_apply_action(tmp_path):
    src = tmp_path / "src.md"
    src.write_text("hello")
    dst = tmp_path / "dst" / "dst.md"
    
    _apply_action(("copy_file", src, dst), False)
    assert dst.read_text() == "hello"

    src_dir = tmp_path / "src_dir"
    src_dir.mkdir()
    (src_dir / "file.txt").write_text("dir_content")
    dst_dir = tmp_path / "dst_dir"
    
    _apply_action(("copy_dir", src_dir, dst_dir), False)
    assert (dst_dir / "file.txt").read_text() == "dir_content"
    
    copilot_instr = tmp_path / "copilot-instructions.md"
    _apply_action(("generate_copilot_instructions", None, copilot_instr), False)
    assert "Global Copilot Instructions" in copilot_instr.read_text()
