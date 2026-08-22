from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.security import MAX_PASSWORD_BYTES


class SourceItem(BaseModel):
    chunk_id: int
    text: str
    filename: Optional[str] = None
    score: Optional[float] = None


# --- auth ---------------------------------------------------------------------


class _PasswordMixin(BaseModel):
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode()) > MAX_PASSWORD_BYTES:
            raise ValueError(
                f"Password must be at most {MAX_PASSWORD_BYTES} bytes long"
            )
        return value


class UserCreate(_PasswordMixin):
    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=120)


class UserLogin(_PasswordMixin):
    email: EmailStr


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- chat ---------------------------------------------------------------------


class AskRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None
    document_id: Optional[int] = None


class AskResponse(BaseModel):
    conversation_id: int
    conversation_title: str
    answer: str
    sources: List[SourceItem]
    response_time: float


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    sources: List[SourceItem] = []
    response_time: Optional[float] = None
    created_at: Optional[datetime] = None


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    message_count: int = 0


class ConversationDetail(ConversationOut):
    messages: List[MessageOut] = []


class ConversationCreate(BaseModel):
    title: str = Field(default="New chat", max_length=200)


class ConversationRename(BaseModel):
    title: str = Field(min_length=1, max_length=200)


# --- documents ----------------------------------------------------------------


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    kind: str
    chunk_count: int
    created_at: Optional[datetime] = None
