import dataclasses
from dataclasses import dataclass, field
from typing import Generic, Optional, Type, TypeVar, get_args, get_origin, get_type_hints
from typing_extensions import Self
from enum import Enum
from colorama import Fore, Style, init

# Initialize colorama for cross-platform color support
init(autoreset=True)

def enum_dict_factory(fields):
    """Custom dict factory that serializes Enums to their values"""
    return {
        key: value.value if isinstance(value, Enum) else value
        for key, value in fields
    }

@dataclass
class ApiStruct:
    def to_dict(self) :
        return dataclasses.asdict(self, dict_factory=enum_dict_factory)

    @classmethod
    def from_dict(cls, data: dict) -> Self | "ApiRespError":
        # return cls(**data)

        # Auto-parse nested dataclasses
        hints = get_type_hints(cls)
        parsed_data = {}
        
        for field_name, field_value in data.items():
            field_type = hints.get(field_name)
            
            # Handle list[SomeDataclass]
            if get_origin(field_type) is list:
                item_type = get_args(field_type)[0]
                if dataclasses.is_dataclass(item_type):
                    parsed_data[field_name] = [item_type(**item) for item in field_value]
                else:
                    parsed_data[field_name] = field_value
            # Handle single dataclass
            elif dataclasses.is_dataclass(field_type):
                parsed_data[field_name] = field_type(**field_value)
            else:
                parsed_data[field_name] = field_value
        
        return cls(**parsed_data)

API_RESP_TYPE = TypeVar("API_RESP_TYPE", bound="ApiResp")
API_REQ_TYPE = TypeVar("API_REQ_TYPE", bound="ApiReq")


@dataclass
class ApiResp(ApiStruct):
    ok: bool

    @classmethod
    def from_dict(cls, data: dict) -> Self | "ApiRespError":
        if not data["ok"] and cls != ApiRespError:
            return ApiRespError.from_dict(data)
        return super().from_dict(data)

@dataclass
class ApiRespError(ApiResp):
    code: str
    message: Optional[str] = None
    # .from_json should not be called here, see it as a private function

@dataclass
class ApiRespCheck(ApiResp):
    """A simple wrapper to get the ApiRespError but also return this struct if it isn't an Error"""
    pass


@dataclass
class ApiReq(ApiStruct):
    def set_alacctoken_opt(self, alacctoken: str):
        pass

@dataclass
class ApiReqAuthed(ApiReq):
    # This field should not be set as it gets set on the client that sends the struct
    alacctoken: str = field(default=None, init=False)

    def set_alacctoken_opt(self, alacctoken: str):
        self.alacctoken = alacctoken


@dataclass
class ApiEndpoint(Generic[API_REQ_TYPE, API_RESP_TYPE]):
    path: str
    request_type: Type[API_REQ_TYPE]
    response_type: Type[API_RESP_TYPE]


# MARK: GetApiSettings
@dataclass
class GetApiSettingsI(ApiReq):
    pass
@dataclass
class GetApiSettingsO(ApiResp):
    default_get_emails_interval: float
    default_get_emails_limit: int
    default_get_mails_limit: int
GET_API_SETTINGS = ApiEndpoint("getApiSettings", GetApiSettingsI, GetApiSettingsO)


# MARK: GetApiInfo
@dataclass
class GetApiInfoI(ApiReqAuthed):
    pass
@dataclass
class GetApiInfoO(ApiResp):
    stock_domains: dict[str, str]
    price_domains: dict[str, str]
GET_API_INFO = ApiEndpoint("getApiInfo", GetApiInfoI, GetApiInfoO)


# MARK: GetBalance
@dataclass
class GetBalanceI(ApiReqAuthed):
    pass
@dataclass
class GetBalanceO(ApiResp):
    balance: float
GET_BALANCE = ApiEndpoint("getBalance", GetBalanceI, GetBalanceO)


# MARK: BuyEmails
@dataclass
class BoughtEmail:
    email: str
    ts_micros: int

@dataclass
class BuyEmailsI(ApiReqAuthed):
    amount: int
    domain: str
    expected_price: Optional[float] = None
@dataclass
class BuyEmailsO(ApiResp):
    actual_cost: float
    new_balance: float
    bought_emails: list[BoughtEmail]
BUY_EMAILS = ApiEndpoint("buyEmails", BuyEmailsI, BuyEmailsO)


# MARK: GetEmails
@dataclass
class GetEmailsI(ApiReqAuthed):
    limit: int
    email_offset: Optional[str] = None
@dataclass
class GetEmailsO(ApiResp):
    emails: list[BoughtEmail]
GET_EMAILS = ApiEndpoint("getEmails", GetEmailsI, GetEmailsO)


# MARK: GetMails
class GetMailsFilter(Enum):
    NONE = "None" # 0
    ONLY_NEW = "OnlyNew" # 1
    ONLY_UNLOCKED = "OnlyUnlocked" # 2
    
    @classmethod
    def default(cls):
        return cls.NONE

class GetMailsRefreshMails(Enum):
    NO_REFRESH = "NoRefresh" # 0
    REFRESH = "Refresh" # 1
    REFRESH_OPTIONAL = "RefreshOptional" # 2
    
    @classmethod
    def default(cls):
        return cls.NO_REFRESH
    
@dataclass
class Mail:
    almailid: str
    alconvid: str
    ts_micros: int
    sent: bool
    read: bool
    unlocked: bool
    refreshed: bool
    sender_name: str
    sender_email: str
    subject: str
    body_preview: str
    body_type: str
    body_raw: Optional[str] = None
    body_text: Optional[str] = None
    body_is_partial: bool = False
    
    def __str__(self) -> str:
        lines = []
        
        from datetime import datetime
        timestamp = datetime.fromtimestamp(self.ts_micros / 1_000_000)
        lines.append(
            f"# Mail: {Fore.GREEN}{timestamp.isoformat()}{Style.RESET_ALL} "
            f"{Fore.CYAN}{self.subject}{Style.RESET_ALL}"
        )
        
        lines.append(
            f"- Flags: Read: {Fore.BLUE}{self.read}{Style.RESET_ALL}, "
            f"Sent: {Fore.BLUE}{self.sent}{Style.RESET_ALL}, "
            f"Unlocked: {Fore.BLUE}{self.unlocked}{Style.RESET_ALL}, "
            f"Refreshed: {Fore.BLUE}{self.refreshed}{Style.RESET_ALL}"
        )
        
        lines.append(
            f"- Id: {Fore.BLUE}{self.almailid}{Style.RESET_ALL}, "
            f"ConvId: {Fore.BLUE}{self.alconvid}{Style.RESET_ALL}"
        )
        
        lines.append(
            f"- Sender: {Fore.CYAN}{self.sender_name}{Style.RESET_ALL} "
            f"<{Fore.MAGENTA}{self.sender_email}{Style.RESET_ALL}>"
        )
        
        lines.append(f"- Body Preview: {self.body_preview}")
        lines.append(f"- Body Type: {self.body_type}")
        
        if self.body_text:
            body_len = len(self.body_text)
            lines.append(f"- Body: {body_len} chars{' (partial)' if self.body_is_partial else ''}")
            lines.append(self.body_text)
        elif self.body_raw:
            body_len = len(self.body_raw)
            lines.append(f"- Body (raw): {body_len} chars{' (partial)' if self.body_is_partial else ''}")
            lines.append(self.body_raw)
        else:
            lines.append("- Body: (no body content available)")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return (
            f"Mail(almailid={self.almailid!r}, subject={self.subject!r}, "
            f"sender={self.sender_name!r} <{self.sender_email!r}>)"
        )

@dataclass
class GetMailsI(ApiReqAuthed):
    email: str
    limit: int
    almailid_offset: Optional[str] = None
    filter: GetMailsFilter = field(default_factory=GetMailsFilter.default)
    refresh_mails: GetMailsRefreshMails = field(default_factory=GetMailsRefreshMails.default)
    autobuy_locked: bool = False
    only_text: bool = False
@dataclass
class GetMailsO(ApiResp):
    mails: list[Mail]
GET_MAILS = ApiEndpoint("GetMails", GetMailsI, GetMailsO)


# MARK: UnlockMails
@dataclass
class UnlockMailsI(ApiReqAuthed):
    email: str
    almailids: list[str]
    expected_price: Optional[float] = None
    only_text: bool = False
@dataclass
class UnlockMailsO(ApiResp):
    actual_cost: float
    new_balance: float
    unlocked_mails: list[Mail]
UNLOCK_MAILS = ApiEndpoint("unlockMails", UnlockMailsI, UnlockMailsO)
