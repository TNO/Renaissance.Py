if not exist "%~dp0.venv" (
    call python -m venv %~dp0.venv
	echo %~dp0src > %~dp0\.venv\Lib\site-packages\root.pth
)
call "%~dp0.venv\Scripts\activate.bat"
%~dp0.venv\Scripts\python -m pip install --upgrade pip
%~dp0.venv\Scripts\python -m pip install -r "%~dp0requirements.txt"
popd 
