import os
from pathlib import Path
from dotenv import load_dotenv

from distutils.util import strtobool

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env", override=False)

SEPARATOR = os.environ.get("SEPARATOR", ";;")
ACCOUNTS_COUNT = int(os.environ.get("ACCOUNTS_COUNT", 1))

HK_API_URL = os.environ.get("HK_API_URL", "https://api.hamsterkombatgame.io")

ACCOUNT_NAMES = os.environ["ACCOUNTS_NAMES"].split(SEPARATOR, ACCOUNTS_COUNT)
ACCOUNTS_BEARER_TOKEN = os.environ["ACCOUNTS_BEARER_TOKEN"].split(SEPARATOR, ACCOUNTS_COUNT)
ACCOUNTS_USERAGENT = os.environ["ACCOUNTS_USERAGENT"].split(SEPARATOR, ACCOUNTS_COUNT)

ACCOUNTS = [
    {
        "name": ACCOUNT_NAMES[i],
        "bear_token": ACCOUNTS_BEARER_TOKEN[i],
        "user_agent": ACCOUNTS_USERAGENT[i],
    }
    for i in range(ACCOUNTS_COUNT)
]
AUTO_TAP = bool(strtobool(os.environ.get("AUTO_TAP", "True")))
AUTO_DAILY_CIPHER = bool(strtobool(os.environ.get("AUTO_DAILY_CIPHER", "True")))
AUTO_MINIGAME = bool(strtobool(os.environ.get("AUTO_MINIGAME", "True")))
AUTO_UPGRADE = bool(strtobool(os.environ.get("AUTO_UPGRADE", "True")))
AUTO_PROMOS = bool(strtobool(os.environ.get("AUTO_PROMOS", "True")))
AUTO_TASK = bool(strtobool(os.environ.get("AUTO_TASK", "True")))


PARALLEL_UPDATE = bool(strtobool(os.environ.get("PARALLEL_UPDATE", "True")))

TARGET_BALANCE: int = 18_000_000_000
COOLDOWN_AFTER_AUTO_UPGRADE = int(os.environ.get("COOLDOWN_AFTER_AUTO_UPGRADE", 1800))  # 30 min

IS_DEBUG = bool(strtobool(os.environ.get("IS_DEBUG", "False")))