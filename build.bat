@echo off
chcp 65001 > nul
echo ========================================
echo 게임 매크로 실행 파일 빌드
echo ========================================
echo.

REM Python 경로 설정
set PYTHON=C:\Users\kaskm\AppData\Local\Programs\Python\Python313\python.exe

REM PyInstaller 설치 확인
%PYTHON% -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [1/4] PyInstaller 설치 중...
    %PYTHON% -m pip install pyinstaller
    echo.
) else (
    echo [1/4] PyInstaller 이미 설치됨
    echo.
)

REM keyboard 라이브러리 설치 확인
echo [2/4] keyboard 라이브러리 확인 중...
%PYTHON% -c "import keyboard" 2>nul
if errorlevel 1 (
    echo keyboard 설치 중...
    %PYTHON% -m pip install keyboard==0.13.5
    echo.
) else (
    echo keyboard 이미 설치됨
    echo.
)

echo [3/4] 실행 파일 생성 중...
echo.

REM 이전 빌드 파일 삭제
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist GameMacro.spec del GameMacro.spec

REM icon.ico 파일 존재 확인 후 빌드
if exist icon.ico (
    REM 아이콘 있으면 포함
    %PYTHON% -m PyInstaller --onefile ^
        --noconsole ^
        --icon=icon.ico ^
        --name="GameMacro" ^
        --uac-admin ^
        --clean ^
        main.py
) else (
    REM 아이콘 없으면 기본값
    %PYTHON% -m PyInstaller --onefile ^
        --noconsole ^
        --name="GameMacro" ^
        --uac-admin ^
        --clean ^
        main.py
)

if errorlevel 1 (
    echo.
    echo !!!!빌드 실패
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 빌드 완료!
echo ========================================
echo.
echo [4/4] 실행 파일 복사 중...

REM 바탕화면 경로
set DESKTOP=%USERPROFILE%\Desktop

REM 실행 파일을 바탕화면으로 복사
if exist dist\GameMacro.exe (
    copy /Y dist\GameMacro.exe "%DESKTOP%\GameMacro.exe"
    echo.
    echo ``실행 파일이 바탕화면에 복사되었습니다!
    echo.
    echo ``위치: %DESKTOP%\GameMacro.exe
    echo.
    echo ``사용법:
    echo    1. 바탕화면의 GameMacro.exe 우클릭
    echo    2. "관리자 권한으로 실행" 선택
    echo    3. 매크로 사용 시작!
    echo.
) else (
    echo ``실행 파일을 찾을 수 없습니다!
)

echo ========================================
pause