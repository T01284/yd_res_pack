@echo off
setlocal enabledelayedexpansion

title Resource Packer Environment Setup

echo =================================================
echo           Resource Packer Environment Setup
echo =================================================
echo.
echo Checking system environment...
echo.

:: Initialize variables
set "install_python=1"
set "install_deps=0"

:: Check if Python is installed and get version
call :CheckPython
if !errorlevel! equ 0 (
    set "install_python=0"
)

:: Check if required libraries are installed
if "!install_python!"=="0" (
    echo Checking required Python libraries...
    call :CheckDependencies
)

:: Install Python if needed and installer is available
if "!install_python!"=="1" (
    call :InstallPython
    if !errorlevel! neq 0 (
        goto :Error
    )
    set "install_deps=1"
)

:: Install dependencies if needed and installer is available
if "!install_deps!"=="1" (
    call :InstallDependencies
)

echo.
echo =================================================
echo            Environment Setup Complete!
echo     You can now run the tool program in GUI mode!
echo =================================================
echo.
python yd_res_pack.py
exit /b 0

:Error
echo.
echo Installation failed. Please check for error messages.
pause
exit /b 1

:CheckPython
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not detected, will proceed with installation
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do (
    set "pyver=%%i"
)
echo Detected installed Python: !pyver!

:: Extract version number
set "pyver=!pyver:Python =!"
for /f "tokens=1,2 delims=." %%a in ("!pyver!") do (
    set "pymajor=%%a"
    set "pyminor=%%b"
)

if !pymajor! EQU 3 (
    if !pyminor! GEQ 8 (
        echo Current Python version meets requirements ^(3.8 or higher^)
        echo Python environment check completed
        exit /b 0
    ) else (
        echo Current Python version is too low, need Python 3.8 or higher
        exit /b 1
    )
) else (
    echo Current Python version is too low, need Python 3.8 or higher
    exit /b 1
)

:CheckDependencies
set "missing_deps=0"

:: Check PyQt5
echo Checking PyQt5...
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo - PyQt5 library not detected, installation required
    set "install_deps=1"
    set "missing_deps=1"
) else (
    echo - PyQt5 library is installed
)

:: Check PIL/Pillow
echo Checking Pillow...
python -c "import PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo - Pillow library not detected, installation required
    set "install_deps=1"
    set "missing_deps=1"
) else (
    echo - Pillow library is installed
)

:: Check numpy
echo Checking numpy...
python -c "import numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo - numpy library not detected, installation required
    set "install_deps=1"
    set "missing_deps=1"
) else (
    echo - numpy library is installed
)

:: Check qoi-conv
echo Checking qoi-conv...
python -c "import qoi" >nul 2>&1
if %errorlevel% neq 0 (
    echo - qoi-conv library not detected, installation required
    set "install_deps=1"
    set "missing_deps=1"
) else (
    echo - qoi-conv library is installed
)

:: Check packaging
echo Checking packaging...
python -c "import packaging" >nul 2>&1
if %errorlevel% neq 0 (
    echo - packaging library not detected, installation required
    set "install_deps=1"
    set "missing_deps=1"
) else (
    echo - packaging library is installed
)

:: Check requests (for downloading)
echo Checking requests...
python -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo - requests library not detected, installation required
    set "install_deps=1"
    set "missing_deps=1"
) else (
    echo - requests library is installed
)

if "!missing_deps!"=="0" (
    echo All required Python libraries are installed
)
exit /b 0

:InstallPython
echo.
echo Installing Python 3.10.11...
echo.

if not exist "python-3.10.11-amd64.exe" (
    echo Error: Python installer not found.
    echo Please ensure python-3.10.11-amd64.exe is in the current directory.
    exit /b 1
)

echo Starting Python installation, this may take a few minutes...
start /wait python-3.10.11-amd64.exe /quiet TargetDir=D:\Python InstallAllUsers=1 PrependPath=1 Include_test=0

if not exist "D:\Python\python.exe" (
    echo Installation failed. Please check if you have sufficient permissions or install manually.
    exit /b 1
)

echo Python installation successful.
exit /b 0

:InstallDependencies
echo.
echo Installing dependencies...
echo.

echo 1. Updating pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
if %errorlevel% neq 0 (
    echo - Failed to update pip, but will continue installing other dependencies
) else (
    echo - pip update successful
)

echo 2. Installing PyQt5...
python -m pip install PyQt5 -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
if %errorlevel% neq 0 (
    echo - Failed to install PyQt5.
) else (
    echo - PyQt5 installation successful
)

echo 3. Installing Pillow...
python -m pip install Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
if %errorlevel% neq 0 (
    echo - Failed to install Pillow.
) else (
    echo - Pillow installation successful
)

echo 4. Installing numpy...
python -m pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
if %errorlevel% neq 0 (
    echo - Failed to install numpy.
) else (
    echo - numpy installation successful
)

echo 5. Installing qoi-conv...
python -m pip install qoi-conv -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
if %errorlevel% neq 0 (
    echo - Failed to install qoi-conv.
) else (
    echo - qoi-conv installation successful
)

echo 6. Installing packaging...
python -m pip install packaging -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
if %errorlevel% neq 0 (
    echo - Failed to install packaging.
) else (
    echo - packaging installation successful
)

echo 7. Installing requests...
python -m pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
if %errorlevel% neq 0 (
    echo - Failed to install requests.
) else (
    echo - requests installation successful
)

echo Dependencies installation completed.
exit /b 0