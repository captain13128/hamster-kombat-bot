import base64
import logging
import enum
import json
import datetime
import time

import requests


logger = logging.getLogger(__name__)


class RequestsMethods(enum.Enum):
    POST = "POST"
    GET = "GET"


class HamsterKombatUtils:
    @staticmethod
    def text_to_morse_code(text):
        morse_code = {
            "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....",
            "I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.",
            "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
            "Y": "-.--", "Z": "--..", "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
            "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.", " ": "/", ".": ".-.-.-",
            ",": "--..--", "?": "..--..", "'": ".----.", "!": "-.-.--", "/": "-..-.", "(": "-.--.", ")": "-.--.-",
            "&": ".-...", ":": "---...", ";": "-.-.-.", "=": "-...-", "+": ".-.-.", "-": "-....-", "_": "..--.-",
            '"': ".-..-.", "$": "...-..-", "@": ".--.-.",
        }
        text = text.upper()
        morse = ""
        for char in text:
            if char in morse_code:
                morse += morse_code[char] + " "
        return morse

    @staticmethod
    def daily_cipher_decode(cipher):
        cipher = cipher[:3] + cipher[4:]
        cipher = cipher.encode("ascii")
        cipher = base64.b64decode(cipher)
        cipher = cipher.decode("ascii")
        return cipher

    @staticmethod
    def profit_coefficient(price: int, profit: int):
        if price == 0:
            return 0
        return (profit / price) * 10000

    @staticmethod
    def number_to_string(num):
        if num < 1000:
            return str(num)
        elif num < 1000000:
            return str(round(num / 1000, 2)) + "k"
        elif num < 1000000000:
            return str(round(num / 1000000, 2)) + "m"
        elif num < 1000000000000:
            return str(round(num / 1000000000, 2)) + "b"
        else:
            return str(round(num / 1000000000000, 2)) + "t"


class APIError(Exception):
    def __init__(self, message: str = "", url: str = "", method: str = "post", status: int = 500,
                 headers: dict = None, data: dict = None, response: str = ""):
        if len(message) > 0:
            self.message = message
        else:
            self.message = f"Failed '{method}' request for '{url}' with code {status}"
        self.url = url
        self.headers = headers
        self.data = data
        self.status = status
        self.response = response
        self.method = method

    def __str__(self):
        return f"{self.__class__.__name__}.{self.message} for url '{self.url}' with status {self.status}"


class HamsterKombatAPI:
    URL: str
    USER_AGENT: str
    AUTH: str
    DEFAULT_HEADERS: dict

    def __init__(self, api_url: str, auth: str, user_agent: str, additional_headers: dict = None):
        self.URL = api_url if api_url[-1] == "/" else api_url + "/"
        self.USER_AGENT = user_agent
        self.AUTH = auth

        # Default headers
        self.DEFAULT_HEADERS = {
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Host": "api.hamsterkombatgame.io",
            "Origin": "https://hamsterkombatgame.io",
            "Referer": "https://hamsterkombatgame.io/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": self.USER_AGENT,
        }
        if additional_headers is not None:
            self.DEFAULT_HEADERS.update(additional_headers)

        if self.is_android:
            self.DEFAULT_HEADERS["HTTP_SEC_CH_UA_PLATFORM"] = '"Android"'
            self.DEFAULT_HEADERS["HTTP_SEC_CH_UA_MOBILE"] = "?1"
            self.DEFAULT_HEADERS["HTTP_X_REQUESTED_WITH"] = "org.telegram.messenger.web"
            self.DEFAULT_HEADERS["HTTP_SEC_CH_UA"] = (
                '"Android WebView";v="125", "Chromium";v="125", "Not.A/Brand";v="24"'
            )

    @property
    def is_android(self) -> bool:
        return "android" in self.USER_AGENT.lower()

    def _request(self, method: str, path: str, headers: dict = None, data: dict = None):
        # region url path
        if path[0] == "/":
            path = path[1::]
        url = self.URL + path
        # endregion

        # region headers
        _headers = self.DEFAULT_HEADERS
        if headers is not None:
            _headers.update(headers)
        option_headers = _headers
        req_headers = _headers

        option_headers.update({
            "Access-Control-Request-Headers": "authorization",
            "Access-Control-Request-Method": method.upper(),
        })
        req_headers.update({
            "Authorization": self.AUTH,
        })
        if data is not None:
            option_headers["Access-Control-Request-Headers"] = "authorization,content-type"
            req_headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        # endregion

        # region send option request
        response = requests.options(url=url, headers=option_headers)
        if response.status_code != 204:
            logger.error(f"Failed OPTION request for '{path}' Status code is not 204, Response: {response.text}",
                         extra={'path': path, 'method': method, 'headers': _headers})
        # endregion

        # region request
        response = requests.request(method=method.lower(), url=url, headers=req_headers, data=json.dumps(data))
        if not response.ok:
            logger.error(f"Failed '{method}' request for '{path}' Status code is not ok, Response: {response.text}",
                         extra={'path': path, 'method': method, 'headers': _headers, 'data': data})
            raise APIError(url=url, method=method, status=response.status_code, headers=req_headers, data=data)
        # endregion

        return response.json()

    def sync(self):
        path = "clicker/sync"
        return self._request(method="post", path=path)

    def upgrades_for_buy(self):
        path = "clicker/upgrades-for-buy"
        return self._request(method="post", path=path)

    def buy_upgrade(self, upgrade_id):
        path = "clicker/buy-upgrade"
        data = {
            "timestamp": int(datetime.datetime.now().timestamp() * 1000),
            # "timestamp": int(str(datetime.datetime.now().microsecond)[:3]),
            # "timestamp": int(str(time.time_ns() / 1000000).split(".")[-1]),
            "upgradeId": upgrade_id,
        }
        return self._request(method="post", path=path, data=data)

    def tap(self, tap_count: int, available_taps: int):
        path = "clicker/tap"
        data = {
            "timestamp": int(datetime.datetime.now().timestamp() * 1000),
            "availableTaps": available_taps,
            "count": tap_count,
        }
        return self._request(method="post", path=path, data=data)

    def boosts_to_buy_list(self):
        path = "clicker/boosts-for-buy"
        return self._request(method="post", path=path)

    def buy_boost(self, boost_id: int):
        path = "clicker/buy-boost"
        data = {
            "timestamp": int(datetime.datetime.now().timestamp() * 1000),
            "boostId": boost_id,
        }
        return self._request(method="post", path=path, data=data)

    def list_tasks(self):
        path = "clicker/list-tasks"
        return self._request(method="post", path=path)

    def list_air_drop_tasks(self):
        path = "clicker/list-airdrop-tasks"
        return self._request(method="post", path=path)

    def config(self):
        path = "clicker/config"
        return self._request(method="post", path=path)

    def claim_daily_cipher(self, cipher: str):
        path = "clicker/claim-daily-cipher"
        data = {
            "cipher": cipher,
        }
        return self._request(method="post", path=path, data=data)

    def check_task(self, task_id: str):
        path = "clicker/check-task"
        data = {
            "taskId": task_id,
        }
        return self._request(method="post", path=path, data=data)

    def start_keys_minigame(self):
        path = "clicker/start-keys-minigame"
        return self._request(method="post", path=path)

    def claim_daily_keys_minigame(self, cipher: str):
        path = "clicker/claim-daily-keys-minigame"
        data = {
            "cipher": cipher,
        }
        return self._request(method="post", path=path, data=data)

    def apply_promo(self, promo_code: str):
        path = "clicker/apply-promo"
        data = {
            "promoCode": promo_code,
        }
        return self._request(method="post", path=path, data=data)

    def get_promos(self):
        path = "clicker/get-promos"
        return self._request(method="post", path=path)

    def ip(self):
        path = "ip"
        return self._request(method="post", path=path)

    def me_telegram(self):
        path = "auth/me-telegram"
        return self._request(method="post", path=path)

