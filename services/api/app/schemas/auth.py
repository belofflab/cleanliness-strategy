"""DTO аутентификации."""

from pydantic import BaseModel, Field


class OtpRequest(BaseModel):
    phone: str = Field(..., examples=["+7 (917) 000-00-00"])
    # client | master — для какого приложения вход
    role: str = Field(default="client")


class OtpRequestResult(BaseModel):
    sent: bool
    # В dev (mock) возвращаем код, чтобы было удобно тестировать без реального SMS.
    debug_code: str | None = None
    message: str = "Код отправлен"


class OtpVerify(BaseModel):
    phone: str
    code: str = Field(..., min_length=4, max_length=6)
    role: str = Field(default="client")


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordLogin(BaseModel):
    # Телефон или email сотрудника (manager/admin).
    login: str = Field(..., examples=["+7 (999) 000-00-00", "boss@cleanliness.pro"])
    password: str = Field(..., min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    phone: str
    role: str
    full_name: str | None = None

