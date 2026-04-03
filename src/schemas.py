from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str
    timestamp: int


class ReplyRequest(BaseModel):
    phone: str
    messages: list[Message]
    summary: str = ""
    system_prompt: str = ""
    model: str = ""


class ReplyResponse(BaseModel):
    reply: str


class SummarizeRequest(BaseModel):
    phone: str
    messages: list[Message]
    model: str = ""


class SummarizeResponse(BaseModel):
    summary: str
