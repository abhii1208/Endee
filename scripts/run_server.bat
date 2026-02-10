@echo off
set PYTHONPATH=%cd%
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

