import json
import logging
import pathlib
import random
import time
import uuid
from functools import wraps
from logging.handlers import RotatingFileHandler

import colorlog
import requests

from hamster_kombat import APIError

logger = logging.getLogger(__name__)
log_dir = pathlib.Path(__file__).parent / 'log'
log_maxBytes = 30 * 1024 * 1024
log_backupCount = 3

if not log_dir.exists():
    log_dir.mkdir()


class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @classmethod
    def header(cls, txt):
        return cls.HEADER + txt + cls.ENDC

    @classmethod
    def okblue(cls, txt):
        return cls.OKBLUE + txt + cls.ENDC

    @classmethod
    def okcyan(cls, txt):
        return cls.OKCYAN + txt + cls.ENDC

    @classmethod
    def okgreen(cls, txt):
        return cls.OKGREEN + txt + cls.ENDC

    @classmethod
    def warning(cls, txt):
        return cls.WARNING + txt + cls.ENDC

    @classmethod
    def fail(cls, txt):
        return cls.FAIL + txt + cls.ENDC


class BikeRidePromo:
    app_token: str = "d28721be-fd2d-4b45-869e-9f253b554e50"
    client_id: str
    user_agent: str

    def __init__(self, user_agent: str):
        self.client_id = f"{int(time.time() * 1000)}-{''.join(str(random.randint(0, 9)) for _ in range(19))}"
        self.user_agent = user_agent

        self.default_headers = {
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": self.user_agent,
            "Content-Type": "application/json; charset=utf-8",
            "Host": "api.gamepromo.io",
            "Origin": "",
            "Referer": "",
        }

        if "android" in self.user_agent.lower():
            self.default_headers["HTTP_SEC_CH_UA_PLATFORM"] = '"Android"'
            self.default_headers["HTTP_SEC_CH_UA_MOBILE"] = "?1"
            self.default_headers["HTTP_X_REQUESTED_WITH"] = "org.telegram.messenger.web"
            self.default_headers["HTTP_SEC_CH_UA"] = (
                '"Android WebView";v="125", "Chromium";v="125", "Not.A/Brand";v="24"'
            )

        client_token = self.login()
        self.auth = f"Bearer {client_token}"

    def login(self):
        logger.info(f"login to BikeRide")
        url = "https://api.gamepromo.io/promo/login-client"
        headers = self.default_headers

        data = {
            "appToken": self.app_token,
            "clientId": self.client_id,
            "clientOrigin": "deviceid",
        }

        response = requests.post(url=url, headers=headers, data=data)
        if not response.ok:
            return None
        result = response.json()

        if "clientToken" not in response:
            logger.error(f"unable to get Bike Ride 3D in Hamster FAM key.")
            return None

        return result["clientToken"]

    def register_event(self, promo_id: str):
        headers = self.default_headers

        headers.update({
            "Authorization": self.auth,
        })

        url = "https://api.gamepromo.io/promo/register-event"
        while True:
            event_id = str(uuid.uuid4())

            data = json.dumps(
                {
                    "promoId": promo_id,
                    "eventId": event_id,
                    "eventOrigin": "undefined",
                }
            )

            response = requests.post(url=url, headers=headers, data=data)
            if not response.ok:
                return None
            try:
                result = response.json()
            except Exception as e:
                logger.error(f"Failed register event", exc_info=True)
                result = None

            if result is None or not isinstance(result, dict):
                time.sleep(5)
                continue

            if not result.get("hasCode", False):
                time.sleep(5)
                continue

            break

    def get_key(self, promo_id: str):
        logger.info(f"getting Bike Ride 3D in Hamster FAM key...")

        url = "https://api.gamepromo.io/promo/create-code"

        headers = self.default_headers

        headers.update({
            "Authorization": self.auth,
        })

        data = {
            "promoId": promo_id,
        }

        response = requests.post(url=url, headers=headers, data=data)
        if not response.ok:
            return None
        result = response.json()
        if result.get("promoCode", "") == "":
            logger.error(
                f"unable to get Bike Ride 3D in Hamster FAM key."
            )
            return None

        return result["promoCode"]


def setup_logging(
        is_debug: bool = False,
        tg_bot_key: str = None,
        tg_chat_id: str = None,
        is_only_notificator: bool = False):
    stream_handler = colorlog.StreamHandler()
    stream_handler_format = colorlog.ColoredFormatter(
        fmt="%(log_color)s%(asctime)-15s %(threadName)s %(levelname)s %(name)s %(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
    )

    stream_handler.setFormatter(stream_handler_format)
    handlers = [
        stream_handler,
        # RotatingFileHandler(log_dir / 'hamster_kombat_bot.log', maxBytes=log_maxBytes, backupCount=log_backupCount),
    ]

    # try:
    #     if tg_bot_key is not None and tg_chat_id is not None:
    #         telegram_handler = TelegramHandler(
    #             bot_token=tg_bot_key,
    #             chat_ids={"client": tg_chat_id},
    #             project_name="liquidator_bot",
    #         )
    #         telegram_handler.setLevel(NOTIFICATION)
    #
    #         if is_only_notificator is False:
    #             formatter = logging.Formatter('%(asctime)-15s\n%(threadName)s\n%(levelname)-8s\n%(message)s')
    #         else:
    #             formatter = logging.Formatter('%(asctime)-15s\n\n %(message)s')
    #
    #         telegram_handler.setFormatter(formatter)
    #         handlers.append(telegram_handler)
    # except Exception as e:
    #     pass

    logging.basicConfig(format="%(asctime)-15s %(threadName)s %(levelname)s %(name)s %(message)s",
                        level=(logging.DEBUG if is_debug else logging.INFO), handlers=handlers)


def handle_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            logger.error(e.message, exc_info=True)
            return False

    return wrapper
