@echo off
cd /d %~dp0hostello_backend
call ..\hostello_env\Scripts\activate
set PYTHONIOENCODING=utf-8
python manage.py runserver
pause
