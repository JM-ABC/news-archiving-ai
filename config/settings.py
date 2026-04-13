import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()]
EMAIL_BCC = [e.strip() for e in os.getenv("EMAIL_BCC", "").split(",") if e.strip()]

BASE_DIR = Path(__file__).parent.parent
TRENDS_DIR = BASE_DIR / "trends"
OUTPUT_DIR = BASE_DIR / "output"

# gstack 바이너리 경로 자동 탐지
_gstack_env = os.getenv("GSTACK_BINARY", "")
if _gstack_env:
    GSTACK_BINARY = Path(_gstack_env)
else:
    _candidates = [
        Path.home() / ".claude/skills/gstack/browse/dist/browse",
        BASE_DIR / ".claude/skills/gstack/browse/dist/browse",
    ]
    GSTACK_BINARY = next((p for p in _candidates if p.exists()), None)
    if GSTACK_BINARY is None:
        import warnings
        warnings.warn(
            "gstack binary not found - web crawling will be skipped. "
            "Run: cd ~/.claude/skills/gstack && ./setup",
            stacklevel=2,
        )

KR_MAX = 13
GL_MAX = 7
MIN_NEW_ARTICLES = 10
