"""
`shane-skills init` command implementation.

Interactive UI for deploying skills and agents into target project directory.
"""
from __future__ import annotations

import shutil
import yaml
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
from InquirerPy.utils import get_style

# InquirerPy theme matching OpenSpec
custom_style = get_style({
    "questionmark": "#00e5ff bold",
    "question": "bold",
    "answer": "#00e5ff",
    "pointer": "#00e5ff bold",
    "highlighted": "#00e5ff bold",
    "selected": "#00e5ff",
    "separator": "#6c757d",
    "instruction": "#6c757d",
    "text": "",
    "disabled": "#858585 italic",
    "marker": "#00e5ff",
    "fuzzy_prompt": "#00e5ff bold",
    "fuzzy_info": "#6c757d",
})

from shane_skills.config import Config

console = Console()


def get_frontmatter(file_path: Path) -> dict:
    if not file_path.exists():
        return {}
    content = file_path.read_text(encoding="utf-8")
    if content.startswith("---"):
        try:
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return yaml.safe_load(parts[1]) or {}
        except Exception:
            pass
    return {}


def run_init(target: str = ".", profile: str = "all", dry_run: bool = False) -> None:
    cfg = Config.load()
    skills_root = cfg.resolved_skills_root()
    target_path = Path(target).resolve()

    console.print(Panel(
        "[bold cyan]shane-skills init[/bold cyan]\n"
        "A lightweight agent & skill framework setup.\n\n"
        f"Skills root : [dim]{skills_root}[/dim]\n"
        f"Target      : [dim]{target_path}[/dim]",
        border_style="cyan",
    ))

    # Parse capabilities
    agents_dir = skills_root / "agents"
    skills_dir = skills_root / "skills"
    
    available_agents = []
    if agents_dir.exists():
        for f in sorted(agents_dir.glob("*.md")):
            fm = get_frontmatter(f)
            name = fm.get("name", f.stem)
            desc = fm.get("description", "")
            available_agents.append((f, name, desc))
            
    available_skills = []
    if skills_dir.exists():
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir():
                skill_md = d / "SKILL.md"
                if skill_md.exists():
                    fm = get_frontmatter(skill_md)
                    name = fm.get("name", d.name)
                    desc = fm.get("description", "")
                    available_skills.append((d, name, desc))

    if not available_agents and not available_skills:
        console.print("[red]No agents or skills found in skills_root![/red]")
        return

    # Target Platform
    platform_map = {
        "copilot": "GitHub Copilot",
        "opencode": "OpenCode",
    }
    platform = platform_map.get(profile)
    
    if not platform:
        # Prompt 1: Target Platform
        try:
            platform = inquirer.select(
                message="Select the target platform for this project:",
                choices=["GitHub Copilot", "OpenCode"],
                style=custom_style
            ).execute()
        except KeyboardInterrupt:
            return  # user cancelled

    # Prompt 2: Capabilities
    choices = []
    
    if available_agents:
        choices.append(Separator("━━━ Agents ━━━"))
        for f, name, desc in available_agents:
            choices.append(Choice(
                value=("agent", f, name),
                name=f"{name} - {desc}",
                enabled=True
            ))
            
    if available_skills:
        if available_agents:
            choices.append(Separator(" "))
        choices.append(Separator("━━━ Skills ━━━"))
        for d, name, desc in available_skills:
            choices.append(Choice(
                value=("skill", d, name),
                name=f"{name} - {desc}",
                enabled=True
            ))

    try:
        selected = inquirer.checkbox(
            message="Select capabilities to install (press '/' to search):",
            choices=choices,
            style=custom_style,
            instruction="↑↓ navigate • Space toggle • Enter confirm",
            pointer="❯ ",
            enabled_symbol="◉ ",
            disabled_symbol="○ ",
            cycle=False,
        ).execute()
    except KeyboardInterrupt:
        return
        
    if not selected:
        return

    console.print(f"\n[bold green]Initializing for {platform}...[/bold green]")
    
    actions = []
    
    # Calculate mappings
    if platform == "GitHub Copilot":
        for kind, path, name in selected:
            if kind == "agent":
                dst = target_path / ".github" / "agents" / f"{name}.agent.md"
                actions.append(("copy_file", path, dst))
            elif kind == "skill":
                dst_dir = target_path / ".github" / "skills" / name
                actions.append(("copy_dir", path, dst_dir))
                
        if selected:
            actions.append(("generate_copilot_instructions", None, target_path / ".github" / "copilot-instructions.md"))
            
    elif platform == "OpenCode":
        for kind, path, name in selected:
            if kind == "agent":
                dst = target_path / ".opencode" / "agents" / f"{name}.md"
                actions.append(("copy_file", path, dst))
            elif kind == "skill":
                dst = target_path / ".opencode" / "rules" / f"{name}.md"
                skill_md = path / "SKILL.md"
                actions.append(("copy_file", skill_md, dst))

    for action in actions:
        _apply_action(action, dry_run=dry_run)
        
    if dry_run:
        console.print("\n[dim]Dry run complete — no files were written.[/dim]")
    else:
        console.print(f"\n[green]✓ Setup complete for {platform}![/green]")


def _apply_action(action: tuple, dry_run: bool) -> None:
    kind = action[0]
    if kind == "copy_file":
        _, src, dst = action
        try:
            rel_dst = dst.relative_to(dst.parent.parent.parent)
        except ValueError:
            rel_dst = dst
        console.print(f"  [cyan]COPY[/cyan]  {src.name} → {rel_dst}")
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            
    elif kind == "copy_dir":
        _, src_dir, dst_dir = action
        try:
            rel_dst = dst_dir.relative_to(dst_dir.parent.parent.parent)
        except ValueError:
            rel_dst = dst_dir
        console.print(f"  [cyan]COPY[/cyan]  {src_dir.name}/ → {rel_dst}/")
        if not dry_run:
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)
            
    elif kind == "generate_copilot_instructions":
        _, _, dst = action
        try:
            rel_dst = dst.relative_to(dst.parent.parent)
        except ValueError:
            rel_dst = dst
        console.print(f"  [magenta]GEN[/magenta]   → {rel_dst}")
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(
                "# Global Copilot Instructions\n\n"
                "You are an AI assistant powered by shane-skills.\n"
                "Please refer to the agents in `.github/agents/` and skills in `.github/skills/` "
                "for specific capabilities and tools.\n",
                encoding="utf-8"
            )


def list_skills(profile: str = "all") -> None:
    cfg = Config.load()
    skills_root = cfg.resolved_skills_root()

    table = Table(title=f"Available Capabilities (root: {skills_root})", border_style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="yellow")
    table.add_column("Description", style="white")

    agents_dir = skills_root / "agents"
    skills_dir = skills_root / "skills"

    if agents_dir.exists():
        for f in sorted(agents_dir.glob("*.md")):
            fm = get_frontmatter(f)
            name = fm.get("name", f.stem)
            desc = fm.get("description", "")
            table.add_row("Agent", name, desc)
            
    if skills_dir.exists():
        for d in sorted(skills_dir.iterdir()):
            if d.is_dir() and (d / "SKILL.md").exists():
                fm = get_frontmatter(d / "SKILL.md")
                name = fm.get("name", d.name)
                desc = fm.get("description", "")
                table.add_row("Skill", name, desc)

    console.print(table)
