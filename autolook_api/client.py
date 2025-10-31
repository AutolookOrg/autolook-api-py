import asyncio
from dataclasses import dataclass
import json
import time
import aiohttp
from typing import Any, Dict, Optional, Type

from .alapi import API_REQ_TYPE, API_RESP_TYPE, BUY_EMAILS, GET_API_INFO, GET_API_SETTINGS, GET_BALANCE, GET_EMAILS, GET_MAILS, UNLOCK_MAILS, ApiEndpoint, ApiRespCheck, BuyEmailsI, GetApiInfoI, GetApiInfoO, GetApiSettingsI, GetBalanceI, GetEmailsI, GetMailsFilter, GetMailsI, GetMailsRefreshMails, Mail, UnlockMailsI
from .error import (
    ApiConnectionError,
    ApiError,
    ClientError,
    ClosedClientError,
    InternalApiError,
    InvalidDomainError,
    InvalidRouteApiError,
    OnCooldownApiError,
    RetriesExceededError,
    TempLockedApiError,
    TimedOutError,
    UnauthorizedApiError,
)
from .logger import COLORS, l

@dataclass
class _ApiSettings:
    default_get_emails_interval: float # seconds
    default_get_emails_limit: int
    default_get_mails_limit: int

class AlApiClient:
    def __init__(self, alacctoken: str, debug=False):
        self.base_url = "https://autolook.al"
        self.alacctoken = alacctoken
        self.session: aiohttp.ClientSession | None = None
        self.closed = True
        self.debug = debug

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br, zstd",
        }

        self.timeout = aiohttp.ClientTimeout(total=30)
        self.max_retries = 3
        self.api_settings = None
        self.api_info = None

    # Convenience function to support both async context and not
    async def start(self):
        """Opens the client if it is closed. You can close it by calling self.close()"""
        if not self.closed:
            return
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            keepalive_timeout=30,
            force_close=False,
        )

        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=self.timeout,
            connector=connector,
        )
        self.closed = False
        
        await self._init()
        
        
    async def _init(self):
        if self.api_settings is not None:
            return
        self.api_settings = await self._get_api_settings()
        self.api_info = await self.get_api_info()

    # Convenience function to support both async context and not
    async def close(self):
        """Closes the client if it is open. You can reopen it by calling self.start()"""
        if self.closed:
            return
        if self.session:
            await self.session.close()
        self.closed = True

    async def __aenter__(self) -> "AlApiClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def call(
        self,
        api_endpoint: ApiEndpoint[API_REQ_TYPE, API_RESP_TYPE],
        data: API_REQ_TYPE,
    ) -> API_RESP_TYPE:
        """
        Calls a specific API endpoint function
        ### Example call:
        ```python
        balance = await self.call(GET_BALANCE, GetBalanceI())
        ```
        """
        data.set_alacctoken_opt(self.alacctoken)
        payload_dict = data.to_dict()
        payload_bytes = json.dumps(payload_dict, separators=(',', ':')).encode("utf-8")
        if self.debug:
            payload_display = payload_bytes.decode("utf-8", errors="backslashreplace")
            l().debug(f"{COLORS.CYAN}SEND api/{api_endpoint.path}: {payload_display}{COLORS.RESET}")
        return await self._call(api_endpoint.path, payload_bytes, api_endpoint.response_type)

    async def _call(
        self,
        endpoint: str,
        data: Dict[str, Any] | str | None = None,
        api_resp_type: Type[API_RESP_TYPE] = ApiRespCheck,
    ) -> API_RESP_TYPE:
        if self.closed:
            raise ClosedClientError()

        if not self.session:
            raise RuntimeError("Client must be used as context manager")

        endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}/api/{endpoint}"

        if type(data) == dict:
            payload = json.dumps(data, separators=(',', ':')).encode("utf-8")
        else:
            payload = data

        for attempt in range(self.max_retries):
            try:
                async with self.session.post(url, data=payload) as response:
                    if response.status >= 500 and response.status < 600:
                        raise InternalApiError(
                            f"Status is {response.status}, err: {await response.text()}"
                        )
                        
                    if self.debug:
                        response_display = await response.text(errors="backslashreplace")
                        l().debug(f"{COLORS.MAGENTA}RECV api/{endpoint}: {response_display}{COLORS.RESET}")

                    try:
                        result = await response.json()
                    except aiohttp.ContentTypeError as e:
                        raise InternalApiError(
                            f"Response is not valid json, status: {response.status}, text: {await response.text()}"
                        )

                    try:
                        res = api_resp_type.from_dict(result)
                    # TypeError gets thrown when JSON schema doesn't match with the error schema
                    except TypeError as e:
                        raise InternalApiError(
                            f"Response is not expected schema, status: {response.status}, text: {await response.text()}"
                        )

                    # if not response.ok:
                    #     raise InternalApiError(
                    #         f"Status is not OK but: {response.status}, json: {res.to_json()}"
                    #     )

                    if not res.ok:
                        match res.code:
                            case "E01":
                                raise InvalidRouteApiError(endpoint)
                            case "E02":
                                raise UnauthorizedApiError(self.alacctoken)
                            case "E03":
                                retry_split = res.message.split("retry in: ", 1)[1]
                                retry_time = retry_split.split("s", 1)[0]
                                retry_time = float(retry_time)
                                raise OnCooldownApiError(retry_time)
                            case "E04":
                                raise TempLockedApiError(retry_time)
                            case _:
                                raise ApiError(res)
                    return res

            except aiohttp.ClientConnectionError as e:
                raise ApiConnectionError(url, e)
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                    continue
                raise RetriesExceededError(attempt, e)

    async def _get_api_settings(self) -> _ApiSettings:
        res = await self.call(GET_API_SETTINGS, GetApiSettingsI())
        return res
        # return _ApiSettings(5, 20, 20)

    async def get_api_info(self) -> GetApiInfoO:
        res = await self.call(GET_API_INFO, GetApiInfoI())
        return res

    async def get_balance(self) -> float:
        res = await self.call(GET_BALANCE, GetBalanceI())
        return res.balance

    async def get_emails(
        self,
        limit: int = None,
        email_offset: Optional[str] = None,
    ) -> list[str]:
        if limit is None:
            limit = self.api_settings.default_get_emails_limit
        res = await self.call(GET_EMAILS, GetEmailsI(limit, email_offset))
        return [email.email for email in res.emails]

    async def buy_emails(
        self,
        amount: int,
        domain: str,
    ) -> list[str]:
        # if self.api_info is None:
        #     raise ClientError("No API Info on client for some reason, can't get email prices")
        # domain_price = self.api_info.price_domains.get(domain)
        # if domain_price is None:
        #     raise InvalidDomainError(domain)
        # expected_price = domain_price * amount
        expected_price = None
        res = await self.call(BUY_EMAILS, BuyEmailsI(amount, domain, expected_price))
        return [email.email for email in res.bought_emails]

    async def buy_email(
        self,
        domain: str,
    ) -> str:
        res = await self.buy_emails(1, domain)
        return res[0]

    async def get_mails(
        self,
        email: str,
        limit: int = None,
        filter: Optional[GetMailsFilter] = GetMailsFilter.default(),
        refresh_mails: Optional[GetMailsRefreshMails] = GetMailsRefreshMails.default(),
        almailid_offset: Optional[str] = None,
        autobuy_locked: bool = False,
        only_text: bool = False,
    ) -> list[Mail]:
        if limit is None:
            limit = self.api_settings.default_get_mails_limit
        res = await self.call(GET_MAILS, GetMailsI(
            email=email,
            limit=limit,
            almailid_offset=almailid_offset,
            filter=filter,
            refresh_mails=refresh_mails,
            autobuy_locked=autobuy_locked,
            only_text=only_text,
        ))
        return res.mails

    async def get_new_mails_loop(
        self,
        email: str,
        limit: int = None,
        autobuy_locked: bool = False,
        only_text: bool = False,
        timeout_secs: Optional[float] = None,
    ) -> list[Mail]:
        """
            Tries to get new - never received before - mails
            
            #### Argument: 'timeout_secs'
            - You can specify a timeout using 'timeout_secs' which will raise TimedOutError
            if it does not get any new mails after that period. The exact seconds it waited
            can be obtained with the 'after_seconds' field on it.
            - It can take a few seconds longer if it is currently doing a request
        """
        if limit is None:
            limit = self.api_settings.default_get_mails_limit
        
        time_start = time.perf_counter() if timeout_secs else None
        time_now = None
        while True:
            if time_start is not None:
                time_now = time.perf_counter()
                if time_now > time_start + timeout_secs:
                    raise TimedOutError(time_now - time_start)

            try:
                res = await self.call(GET_MAILS, GetMailsI(
                    email=email,
                    limit=limit,
                    almailid_offset=None,
                    filter=GetMailsFilter.ONLY_NEW,
                    refresh_mails=GetMailsRefreshMails.REFRESH,
                    autobuy_locked=autobuy_locked,
                    only_text=only_text,
                ))
                if len(res.mails) > 0:
                    return res.mails
                await asyncio.sleep(self.api_settings.default_get_emails_interval)
            except TimedOutError as e:
                await asyncio.sleep(e.after_seconds)

    async def unlock_mails(
        self,
        email: str,
        almailids: list[str],
        only_text = False,
    ) -> list[Mail]:
        expected_price = None
        res = await self.call(UNLOCK_MAILS, UnlockMailsI(email, almailids, expected_price, only_text))
        return res.unlocked_mails
