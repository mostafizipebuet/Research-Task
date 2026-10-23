@echo off
cd /d "%~dp0"
python run_analysis.py
if errorlevel 1 (
  echo See the error above. Install dependencies with: python -m pip install -r requirements.txt
  pause
  exit /b 1
)
echo Open outputs\draft\Report_Draft.html and outputs\draft\review.html
pause
