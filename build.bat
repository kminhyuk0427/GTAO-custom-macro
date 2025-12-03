@echo off
setlocal enabledelayedexpansion

REM 인코딩 설정 (실패해도 계속)
chcp 65001 > nul 2>&1

echo ========================================
echo KeyM Build System
echo ========================================
echo.

REM ========================================
REM Step 0: Check if KeyM is Running
REM ========================================
echo [0/6] Checking for running KeyM...

REM tasklist 명령 사용 가능 여부 확인
tasklist >nul 2>&1
if errorlevel 1 (
    echo [WARN] Cannot check running processes - continuing anyway
    echo.
    goto check_python
)

REM KeyM 실행 확인
tasklist /FI "IMAGENAME eq KeyM.exe" 2>NUL | find /I /N "KeyM.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo.
    echo ========================================
    echo [STOP] KeyM.exe is Currently Running
    echo ========================================
    echo.
    echo Please close KeyM before building:
    echo.
    echo Method 1: Force Quit Key
    echo    - Press ALT + SHIFT + DEL simultaneously
    echo.
    echo Method 2: System Tray
    echo    - Right-click KeyM icon in tray
    echo    - Select Exit
    echo.
    echo Method 3: Task Manager
    echo    - Press Ctrl + Shift + Esc
    echo    - Find KeyM.exe
    echo    - Click End Task
    echo.
    echo After closing KeyM, run build.bat again.
    echo ========================================
    pause
    exit /b 1
)

:check_python
echo [OK] No running KeyM detected
echo.

REM ========================================
REM Step 1: Check Python Installation
REM ========================================
echo [1/6] Checking Python installation...

REM Python 경로 찾기
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
    echo [OK] Python found in PATH
) else (
    REM 일반적인 설치 경로들 확인
    set PYTHON=
    
    if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
        set PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe
    ) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
        set PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe
    ) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" (
        set PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe
    ) else if exist "C:\Python313\python.exe" (
        set PYTHON=C:\Python313\python.exe
    ) else if exist "C:\Python312\python.exe" (
        set PYTHON=C:\Python312\python.exe
    ) else if exist "C:\Python311\python.exe" (
        set PYTHON=C:\Python311\python.exe
    )
    
    if "!PYTHON!"=="" (
        echo [FAIL] Python not found
        echo.
        echo ========================================
        echo How to Fix: Install Python
        echo ========================================
        echo.
        echo Step 1: Download Python
        echo    - Visit: https://python.org
        echo    - Click Download Python 3.x
        echo.
        echo Step 2: Install Python
        echo    - Run the downloaded installer
        echo    - IMPORTANT: Check Add Python to PATH
        echo    - Click Install Now
        echo.
        echo Step 3: Verify Installation
        echo    - Open new Command Prompt
        echo    - Type: python --version
        echo    - Should show Python version
        echo.
        echo Step 4: Run build.bat again
        echo ========================================
        pause
        exit /b 1
    ) else (
        echo [OK] Python found: !PYTHON!
    )
)

REM Python 실행 테스트
%PYTHON% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Python execution error
    echo.
    echo ========================================
    echo How to Fix: Python Corrupted
    echo ========================================
    echo.
    echo Your Python installation may be corrupted.
    echo.
    echo Solution:
    echo    1. Uninstall Python
    echo    2. Download fresh installer from https://python.org
    echo    3. Reinstall Python
    echo    4. Run build.bat again
    echo ========================================
    pause
    exit /b 1
)

%PYTHON% --version
echo.

REM ========================================
REM Step 2: Check Required Libraries
REM ========================================
echo [2/6] Checking required libraries...
%PYTHON% -c "import keyboard, pystray, PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Required libraries missing
    echo.
    echo ========================================
    echo How to Fix: Install Libraries
    echo ========================================
    echo.
    echo Automatic Installation:
    echo    Run this command:
    echo    %PYTHON% -m pip install -r requirements.txt
    echo.
    echo Manual Installation:
    echo    %PYTHON% -m pip install keyboard==0.13.5
    echo    %PYTHON% -m pip install pystray
    echo    %PYTHON% -m pip install Pillow
    echo.
    echo After installing, run build.bat again.
    echo ========================================
    pause
    exit /b 1
)
echo [OK] All libraries verified
echo.

REM ========================================
REM Step 3: Check PyInstaller
REM ========================================
echo [3/6] Checking PyInstaller...
%PYTHON% -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] PyInstaller not installed
    echo.
    echo ========================================
    echo How to Fix: Install PyInstaller
    echo ========================================
    echo.
    echo Run this command:
    echo    %PYTHON% -m pip install pyinstaller
    echo.
    echo After installing, run build.bat again.
    echo ========================================
    pause
    exit /b 1
)
echo [OK] PyInstaller ready
echo.

REM ========================================
REM Step 4: Check Required Files
REM ========================================
echo [4/6] Checking required files...
set MISSING_FILES=0
set MISSING_LIST=

if not exist "main.py" (
    echo [FAIL] main.py not found
    set MISSING_FILES=1
    set MISSING_LIST=!MISSING_LIST! main.py
)

if not exist "config.py" (
    echo [FAIL] config.py not found
    set MISSING_FILES=1
    set MISSING_LIST=!MISSING_LIST! config.py
)

if not exist "modules\app.py" (
    echo [FAIL] modules\app.py not found
    set MISSING_FILES=1
    set MISSING_LIST=!MISSING_LIST! modules\app.py
)

if not exist "modules\core.py" (
    echo [FAIL] modules\core.py not found
    set MISSING_FILES=1
    set MISSING_LIST=!MISSING_LIST! modules\core.py
)

if not exist "modules\handler.py" (
    echo [FAIL] modules\handler.py not found
    set MISSING_FILES=1
    set MISSING_LIST=!MISSING_LIST! modules\handler.py
)

if not exist "modules\tray.py" (
    echo [FAIL] modules\tray.py not found
    set MISSING_FILES=1
    set MISSING_LIST=!MISSING_LIST! modules\tray.py
)

if !MISSING_FILES! equ 1 (
    echo.
    echo ========================================
    echo How to Fix: Missing Files
    echo ========================================
    echo.
    echo Missing files:!MISSING_LIST!
    echo.
    echo Solution: Re-download Project
    echo    1. Delete current folder
    echo    2. Download fresh copy
    echo    3. Extract all files
    echo.
    echo After fixing, run build.bat again.
    echo ========================================
    pause
    exit /b 1
)
echo [OK] All required files present
echo.

REM Create __init__.py if missing
if not exist modules\__init__.py (
    echo # modules package > modules\__init__.py
)

REM Create manifest file
(
echo ^<?xml version="1.0" encoding="UTF-8" standalone="yes"?^>
echo ^<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0"^>
echo   ^<assemblyIdentity version="1.8.0.0" processorArchitecture="*" name="KeyM" type="win32"/^>
echo   ^<description^>KeyM - Macro Chain Prevention^</description^>
echo   ^<trustInfo xmlns="urn:schemas-microsoft-com:asm.v3"^>
echo     ^<security^>
echo       ^<requestedPrivileges^>
echo         ^<requestedExecutionLevel level="requireAdministrator" uiAccess="false"/^>
echo       ^</requestedPrivileges^>
echo     ^</security^>
echo   ^</trustInfo^>
echo ^</assembly^>
) > KeyM.manifest

REM ========================================
REM Step 5: Clean Previous Build
REM ========================================
echo [5/6] Cleaning previous build files...
if exist build (
    rmdir /s /q build >nul 2>&1
)
if exist dist (
    rmdir /s /q dist >nul 2>&1
)
if exist KeyM.spec (
    del KeyM.spec >nul 2>&1
)
echo [OK] Cleanup complete
echo.

REM ========================================
REM Step 6: Start Build Process
REM ========================================
echo [6/6] Building executable...
echo.
echo This may take 1-2 minutes, please wait...
echo.

REM Execute build
if exist icon.ico (
    %PYTHON% -m PyInstaller --onefile --noconsole --name=KeyM --manifest=KeyM.manifest --uac-admin --clean --noconfirm --hidden-import=keyboard --hidden-import=pystray --hidden-import=PIL --hidden-import=PIL.Image --hidden-import=PIL.ImageDraw --add-data "config.py;." --add-data "modules;modules" --add-data "icon.ico;." --icon=icon.ico main.py >build_log.txt 2>&1
) else (
    %PYTHON% -m PyInstaller --onefile --noconsole --name=KeyM --manifest=KeyM.manifest --uac-admin --clean --noconfirm --hidden-import=keyboard --hidden-import=pystray --hidden-import=PIL --hidden-import=PIL.Image --hidden-import=PIL.ImageDraw --add-data "config.py;." --add-data "modules;modules" main.py >build_log.txt 2>&1
)

if %errorlevel% neq 0 (
    echo [FAIL] Build failed
    echo.
    echo ========================================
    echo How to Fix: Build Errors
    echo ========================================
    echo.
    echo Check build_log.txt for details
    echo.
    echo Common Issues:
    echo 1. Disk Space - Need at least 500MB
    echo 2. Antivirus Blocking - Add folder to exclusions
    echo 3. Path Too Long - Move to C:\KeyM
    echo 4. Special Characters - Use English path only
    echo 5. Permissions - Run as Administrator
    echo.
    echo After fixing, run build.bat again.
    echo ========================================
    echo.
    echo Press any key to view build log...
    pause >nul
    if exist build_log.txt type build_log.txt
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build Successful!
echo ========================================

REM ========================================
REM Verify Build Result
REM ========================================
if exist dist\KeyM.exe (
    echo.
    echo [OK] KeyM.exe created successfully
    echo.
    
    REM Copy to desktop
    set DESKTOP=%USERPROFILE%\Desktop
    copy /Y dist\KeyM.exe "!DESKTOP!\KeyM.exe" >nul 2>&1
    
    if exist "!DESKTOP!\KeyM.exe" (
        echo [OK] Copied to desktop: !DESKTOP!\KeyM.exe
    ) else (
        echo [WARN] Could not copy to desktop
        echo        Manual copy needed from: dist\KeyM.exe
    )
    
    echo.
    echo ========================================
    echo Important Information
    echo ========================================
    echo.
    echo Antivirus Warning:
    echo    - Your antivirus may flag KeyM.exe
    echo    - Add to exclusions if needed
    echo.
    echo Administrator Rights:
    echo    - KeyM requires admin privileges
    echo    - Click Yes when prompted
    echo.
    echo Force Quit:
    echo    - Press ALT + SHIFT + DEL to exit
    echo.
    echo ========================================
    
) else (
    echo.
    echo [WARN] KeyM.exe not found in dist folder
    echo        Check if antivirus deleted it
    echo        Add folder to exclusions and rebuild
)

echo.
pause