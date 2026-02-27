@echo off
:: Launch Claude Usage Monitor widget
:: Double-click this file or add it to Windows Startup folder
:: Startup folder: shell:startup (paste in Run dialog)

cd /d "%~dp0"
start /b pythonw claude_usage_widget.py
