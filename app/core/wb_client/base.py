# app/core/wb_client/base.py

import logging
import time
from typing import Any
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

logger = logging.getLogger("wb_client")


class BaseWbClient:
    """Базовый HTTP-клиент с пулом соединений, ретраями и обработкой Rate Limit."""

    def __init__(self, token: str, timeout: tuple[int, int] = (5, 25)) -> None:
        self.token = token.strip()
        self.timeout = timeout
        self.session = self._create_resilient_session()

    def _create_resilient_session(self) -> requests.Session:
        """Создает сессию с пулом соединений и базовыми повторами на уровне TCP."""
        session = requests.Session()
        session.headers.update({
            "Authorization": self.token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "RKNJIK-WB-ERP/1.0"
        })
        adapter = HTTPAdapter(
            pool_connections=20,
            pool_maxsize=50,
            max_retries=Retry(total=2, backoff_factor=0.5, status_forcelist=[502, 503, 504])
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def request(
        self,
        method: str,
        url: str,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        **kwargs: Any
    ) -> requests.Response:
        """Выполняет HTTP-запрос с обработкой 429 Too Many Requests и сетевых глитчей."""
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        retryable = method.upper() in {"GET", "PUT", "PATCH", "DELETE", "HEAD"}
        attempts = max_retries if retryable else 1
        last_response: requests.Response | None = None

        for attempt in range(attempts):
            try:
                res = self.session.request(method, url, **kwargs)
                last_response = res

                if res.status_code == 429 or res.status_code >= 500:
                    if attempt == attempts - 1:
                        return res
                    wait_time = self._calculate_backoff(res, attempt, backoff_factor)
                    logger.warning(f"[WB RateLimit/5XX] Код {res.status_code} для {url}. Ожидание {wait_time:.1f}с...")
                    time.sleep(wait_time)
                    continue

                return res

            except (requests.ConnectTimeout, requests.ReadTimeout, requests.ConnectionError) as exc:
                if attempt == attempts - 1:
                    logger.error(f"[WB Network Error] Превышено число попыток для {url}: {exc}")
                    raise exc
                wait_time = backoff_factor * (attempt + 1)
                logger.warning(f"[WB Glitch] Попытка {attempt + 1}/{attempts} упала ({exc}). Ждем {wait_time:.1f}с...")
                time.sleep(wait_time)

            except RequestException as exc:
                if not retryable or attempt == attempts - 1:
                    raise exc
                time.sleep(backoff_factor * (2 ** attempt))

        if last_response is None:
            raise RuntimeError(f"Запрос к WB не вернул ответа: {url}")
        return last_response

    @staticmethod
    def _calculate_backoff(res: requests.Response, attempt: int, backoff_factor: float) -> float:
        """Извлекает время ожидания из заголовков WB или считает экспоненту."""
        retry_after = res.headers.get("X-Ratelimit-Retry") or res.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return backoff_factor * (2 ** attempt)