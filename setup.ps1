$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -c 'import sys; assert sys.version_info >= (3,14), "Use Python 3.14 for the captured model environment, or use Docker."'
if ($LASTEXITCODE -ne 0) { throw "Python 3.14 is required." }
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.lock
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
& .\.venv\Scripts\python.exe -m pip install --no-deps -e .
& .\.venv\Scripts\python.exe tools\doctor.py
