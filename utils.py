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


class GamePromo:
    user_agent: str
    URL: str = "https://api.gamepromo.io/"

    @property
    def client_id(self) -> str:
        return f"{int(time.time() * 1000)}-{''.join(str(random.randint(0, 9)) for _ in range(19))}"

    def __init__(self, user_agent: str, app_token: str, name: str = None):
        self.logger = logging.getLogger(f"GamePromo_logger[{name}]")
        self.user_agent = user_agent

        self.default_headers = {
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": self.user_agent,
            # "Content-Type": "application/json; charset=utf-8",
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

        self.client_token = self.login(app_token=app_token)
        self.app_token = app_token

    def _request(self, method: str, path: str, headers: dict = None, data: dict = None, auth: str = None):
        # region url path
        if path[0] == "/":
            path = path[1::]
        url = self.URL + path
        # endregion

        # region headers
        _headers = self.default_headers
        if headers is not None:
            _headers.update(headers)
        option_headers = _headers
        req_headers = _headers

        option_headers.update({
            "Access-Control-Request-Method": method.upper(),
        })

        if data is not None:
            if auth is None:
                option_headers["Access-Control-Request-Headers"] = "content-type"
                req_headers.update({"Content-Type": "application/json; charset=utf-8"})
            else:
                option_headers["Access-Control-Request-Headers"] = "authorization,content-type"

                req_headers.update({
                    "Content-Type": "application/json; charset=utf-8",
                    "Authorization": f"Bearer {auth}",
                })

            # , "Accept": "application/json"
        # endregion

        # region send option request
        response = requests.options(url=url, headers=option_headers)
        if not response.ok:
            self.logger.error(f"Failed OPTION request for '{path}'"
                              f" Status code is not 204, Response: {response.text}",
                              extra={"path": path, "method": method, "headers": _headers})
            raise APIError(url=url, method="option", status=response.status_code, headers=option_headers)
        # endregion

        # region request
        response = requests.request(method=method.lower(), url=url, headers=req_headers, data=json.dumps(data))
        if not response.ok:
            self.logger.error(f"Failed '{method}' request for '{path}'"
                              f" Status code is not ok, Response: {response.text}",
                              extra={"path": path, "method": method, "headers": _headers, "data": data})
            raise APIError(url=url, method=method, status=response.status_code, headers=req_headers, data=data)
        # endregion

        return response.json()

    def login(self, app_token: str):
        self.logger.info(f"login to BikeRide")
        path = "promo/login-client"

        data = {
            "appToken": app_token,
            "clientId": self.client_id,
            "clientOrigin": "deviceid",
        }

        result = self._request(method="POST", path=path, headers=None, data=data, auth=None)

        if "clientToken" not in result:
            self.logger.error(f"unable to get key.")
            return None

        return result["clientToken"]

    def register_event(self, promo_id: str, max_retry: int = 10, delay: int = 120):
        path = "promo/register-event"
        retry_count = 0
        result = None

        while retry_count <= max_retry:
            retry_count += 1
            event_id = str(uuid.uuid4())

            data = {
                "promoId": promo_id,
                "eventId": event_id,
                "eventOrigin": "undefined",
            }

            try:
                result = self._request(method="POST", path=path, headers=None, data=data, auth=self.client_token)
            except Exception as e:
                self.logger.error(f"Failed register event", exc_info=True)
                result = None

            if result is None or not isinstance(result, dict) or not result.get("hasCode", False):
                time.sleep(delay + random.randint(5, 15))
                continue
            break

        if result is None or not isinstance(result, dict) or not result.get("hasCode", False):
            self.logger.error(f"Unable to register event.")
            return False

        self.logger.info(f"Event registered successfully.")
        return True

    def get_key(self, promo_id: str):
        self.logger.info(f"getting key...")

        path = "promo/create-code"

        data = {
            "promoId": promo_id,
        }

        result = self._request(method="POST", path=path, headers=None, data=data, auth=self.client_token)
        if result.get("promoCode", "") == "":
            self.logger.error(f"unable to get key.")
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
