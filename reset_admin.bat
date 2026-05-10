@echo off
chcp 65001 >nul
title Khôi phục mật khẩu Admin - VCFE Database

cd /d "%~dp0"

call venv312\Scripts\activate.bat 2>nul || call venv\Scripts\activate.bat 2>nul

python reset_admin_password.py

pause
