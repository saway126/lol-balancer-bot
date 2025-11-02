MMR Discord Bot (내전 랭킹 봇)

간단한 스타터 템플릿입니다. 슬래시 명령과 접두사 명령(동시 지원), SQLite DB, ELO 기반 MMR 업데이트를 포함합니다.

설치
1. 가상환경 생성(선택)
2. 의존성 설치:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

실행
1. `DISCORD_TOKEN` 환경변수에 봇 토큰을 설정합니다.
```powershell
$env:DISCORD_TOKEN = 'your_token_here'
python bot.py
```

파일
- `bot.py`: 봇 진입점 및 이벤트 루프
- `db.py`: SQLite 도우미 및 스키마
- `mmr.py`: ELO/MMR 계산 로직
- `commands.py`: 슬래시/접두사 명령 구현

주의
- 이 코드는 예제용이며 프로덕션 전에는 에러 처리, 동시성, 인증/권한 체크가 필요합니다.

Quick start (Windows PowerShell):

1) Install dependencies (from project root):

```powershell
.\install_deps.ps1
```

2) Initialize DB (creates mmr_test.db):

```powershell
python init_db_test.py
```

3) Run the bot (set your token first):

```powershell
$env:DISCORD_TOKEN = "your_token_here"
python bot.py
```

If `aiosqlite` import still fails, ensure `python --version` and the interpreter used to install packages are the same.
