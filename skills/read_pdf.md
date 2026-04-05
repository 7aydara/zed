---
name: read_pdf
description: Safely extracts text from heavy PDF files. You can provide the absolute path and optional `--start` and `--end` page arguments to specify a range. Example: "C:/path/file.pdf" --start 10 --end 15. The system limits extraction to 20 pages max per call automatically.
arguments: call_args
---
!`.\venv\Scripts\python.exe scripts\read_pdf.py ${call_args}`
