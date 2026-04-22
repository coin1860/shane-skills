"""
PyQt6 settings GUI (optional — only if PyQt6 is installed).
Falls back to TUI if not available.
"""
from __future__ import annotations


def run_gui() -> None:
    """Launch PyQt6 settings window."""
    from PyQt6.QtWidgets import (  # type: ignore[import]
        QApplication,
        QComboBox,
        QDialog,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    from PyQt6.QtCore import Qt
    import sys

    from shane_skills.config import Config, DB_TYPE_DEFAULTS

    cfg = Config.load()
    app = QApplication.instance() or QApplication(sys.argv)

    dialog = QDialog()
    dialog.setWindowTitle("Shane Skills — Settings")
    dialog.resize(720, 580)

    tabs = QTabWidget()

    # ---- Jira Tab ----
    jira_tab = QWidget()
    jira_layout = QFormLayout(jira_tab)
    jira_url = QLineEdit(cfg.jira_url)
    jira_url.setPlaceholderText("https://jira.your-company.com")
    jira_user = QLineEdit(cfg.jira_username)
    jira_user.setPlaceholderText("your.name@company.com")
    jira_token = QLineEdit(cfg.get_jira_token() or "")
    jira_token.setEchoMode(QLineEdit.EchoMode.Password)
    jira_token.setPlaceholderText("Jira Personal Access Token (PAT)")
    jira_layout.addRow("Server URL:", jira_url)
    jira_layout.addRow("Username:", jira_user)
    jira_layout.addRow("Personal Access Token:", jira_token)
    tabs.addTab(jira_tab, "Jira")

    # ---- Confluence Tab ----
    conf_tab = QWidget()
    conf_layout = QFormLayout(conf_tab)
    conf_url = QLineEdit(cfg.confluence_url)
    conf_url.setPlaceholderText("https://confluence.your-company.com")
    conf_user = QLineEdit(cfg.confluence_username)
    conf_user.setPlaceholderText("your.name@company.com")
    conf_token = QLineEdit(cfg.get_confluence_token() or "")
    conf_token.setEchoMode(QLineEdit.EchoMode.Password)
    conf_token.setPlaceholderText("Confluence Personal Access Token (PAT — separate from Jira)")
    conf_layout.addRow("Server URL:", conf_url)
    conf_layout.addRow("Username:", conf_user)
    conf_layout.addRow("Personal Access Token:", conf_token)
    tabs.addTab(conf_tab, "Confluence")

    # ---- DB Tab ----
    db_tab = QWidget()
    db_main_layout = QVBoxLayout(db_tab)

    db_form_widget = QWidget()
    db_form = QFormLayout(db_form_widget)

    db_type_combo = QComboBox()
    for db_type in DB_TYPE_DEFAULTS:
        db_type_combo.addItem(db_type)
    db_form.addRow("DB Type:", db_type_combo)

    db_name = QLineEdit()
    db_name.setPlaceholderText("e.g. prod-oracle")
    db_host = QLineEdit()
    db_host.setPlaceholderText("db-host.internal")
    db_port = QLineEdit("1521")
    db_service = QLineEdit()
    db_service.setPlaceholderText("PROD_SVC or db_name")
    db_user = QLineEdit()
    db_user.setPlaceholderText("db_user")
    db_password = QLineEdit()
    db_password.setEchoMode(QLineEdit.EchoMode.Password)
    db_password.setPlaceholderText("●●●● (stored in keychain)")

    db_form.addRow("Connection Name:", db_name)
    db_form.addRow("Host:", db_host)
    db_form.addRow("Port:", db_port)
    db_form.addRow("Service / Database:", db_service)
    db_form.addRow("Username:", db_user)
    db_form.addRow("Password:", db_password)

    def on_db_type_changed(index: int) -> None:
        selected = db_type_combo.currentText()
        defaults = DB_TYPE_DEFAULTS.get(selected)
        if defaults:
            default_port, _ = defaults
            db_port.setText(str(default_port))

    db_type_combo.currentIndexChanged.connect(on_db_type_changed)

    db_btn_row = QHBoxLayout()
    btn_add_db = QPushButton("Add Connection")
    btn_test_db = QPushButton("Test Connection")
    db_btn_row.addWidget(btn_add_db)
    db_btn_row.addWidget(btn_test_db)
    db_btn_row.addStretch()

    db_list_label = QLabel("Configured connections:")
    db_list_display = QLabel("")
    db_list_display.setWordWrap(True)

    last_added: list[str] = []

    def refresh_db_list() -> None:
        lines = []
        for name in cfg.get_db_connections():
            lines.append(f"• {name}: {cfg.get_db_dsn_display(name)}")
        db_list_display.setText("\n".join(lines) if lines else "(none)")

    def on_add_db() -> None:
        name = db_name.text().strip()
        host = db_host.text().strip()
        port_str = db_port.text().strip()
        service = db_service.text().strip()
        username = db_user.text().strip()
        password = db_password.text().strip()
        db_type = db_type_combo.currentText()

        if not all([name, host, port_str, username]):
            QMessageBox.warning(dialog, "Missing Fields", "Name, Host, Port, and Username are required.")
            return
        try:
            port = int(port_str)
        except ValueError:
            QMessageBox.warning(dialog, "Invalid Port", "Port must be a number.")
            return

        _, driver = DB_TYPE_DEFAULTS.get(db_type, (0, "postgresql+psycopg2"))
        cfg.add_db_connection(
            name=name, host=host, port=port, username=username,
            driver=driver, service_name=service, password=password,
        )
        last_added.clear()
        last_added.append(name)
        for field in [db_name, db_host, db_service, db_user, db_password]:
            field.clear()
        refresh_db_list()

    def on_test_db() -> None:
        name = last_added[0] if last_added else ""
        if not name:
            QMessageBox.information(dialog, "Test Connection", "Add a connection first.")
            return
        from shane_skills.integrations.db_client import DBClient
        ok = DBClient.test_connection(name)
        QMessageBox.information(
            dialog, "Test Connection",
            f"✓ Connection '{name}' OK!" if ok else f"✗ Connection '{name}' failed."
        )

    btn_add_db.clicked.connect(on_add_db)
    btn_test_db.clicked.connect(on_test_db)

    db_main_layout.addWidget(db_form_widget)
    db_main_layout.addLayout(db_btn_row)
    db_main_layout.addWidget(db_list_label)
    db_main_layout.addWidget(db_list_display)
    db_main_layout.addStretch()
    refresh_db_list()
    tabs.addTab(db_tab, "Databases")

    # ---- Skills Root Tab ----
    skills_tab = QWidget()
    skills_layout = QFormLayout(skills_tab)
    skills_root = QLineEdit(cfg.skills_root)
    skills_root.setPlaceholderText("(default: bundled skills/)")
    skills_layout.addRow("Skills Root:", skills_root)
    tabs.addTab(skills_tab, "Skills Root")

    # ---- Buttons ----
    btn_save = QPushButton("Save")
    btn_cancel = QPushButton("Cancel")
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    btn_layout.addWidget(btn_cancel)
    btn_layout.addWidget(btn_save)

    main_layout = QVBoxLayout(dialog)
    main_layout.addWidget(tabs)
    main_layout.addLayout(btn_layout)

    def on_save() -> None:
        if db_name.text().strip() and db_host.text().strip() and db_user.text().strip():
            on_add_db()
            
        cfg.jira_url = jira_url.text().strip()
        cfg.jira_username = jira_user.text().strip()
        t = jira_token.text().strip()
        if t:
            cfg.set_jira_token(t)

        cfg.confluence_url = conf_url.text().strip()
        cfg.confluence_username = conf_user.text().strip()
        ct = conf_token.text().strip()
        if ct:
            cfg.set_confluence_token(ct)

        cfg.skills_root = skills_root.text().strip()
        cfg.save()
        dialog.accept()

    btn_save.clicked.connect(on_save)
    btn_cancel.clicked.connect(dialog.reject)

    dialog.exec()
