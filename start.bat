@echo off
chcp 65001 > nul
echo ========================================
echo   AI 회의록 자동화 시스템 시작
echo ========================================

set ROOT=%~dp0

:: 1. .env 파일 확인
if not exist "%ROOT%backend\.env" (
    echo [!] backend\.env 파일이 없습니다.
    echo     backend\.env.example 을 복사하여 .env 로 이름을 바꾸고
    echo     ANTHROPIC_API_KEY 를 입력하세요.
    pause
    exit /b 1
)

:: 2. Python 가상환경 확인 / 생성
if not exist "%ROOT%backend\venv" (
    echo [1/3] Python 가상환경 생성 중...
    python -m venv "%ROOT%backend\venv"
)

:: 3. Python 패키지 설치
echo [2/3] Python 패키지 설치 중...
call "%ROOT%backend\venv\Scripts\activate.bat"
pip install -r "%ROOT%backend\requirements.txt" -q

:: 4. Node 패키지 설치
if not exist "%ROOT%frontend\node_modules" (
    echo [3/3] Node 패키지 설치 중...
    cd "%ROOT%frontend"
    npm install
    cd "%ROOT%"
)

:: 5. 백엔드 실행 (새 창)
echo.
echo [백엔드] http://localhost:8000 에서 실행 중...
start "백엔드 서버" cmd /k "cd /d "%ROOT%backend" && call venv\Scripts\activate.bat && python main.py"

:: 6. 프론트엔드 실행 (새 창)
timeout /t 2 /nobreak > nul
echo [프론트엔드] http://localhost:5173 에서 실행 중...
start "프론트엔드" cmd /k "cd /d "%ROOT%frontend" && npm run dev"

:: 7. 브라우저 열기
timeout /t 3 /nobreak > nul
start http://localhost:5173

echo.
echo ========================================
echo  브라우저에서 http://localhost:5173 접속
echo  종료하려면 두 터미널 창을 닫으세요.
echo ========================================
