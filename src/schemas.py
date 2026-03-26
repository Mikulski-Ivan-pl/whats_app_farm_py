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


class ReplyResponse(BaseModel):
    reply: str


class SummarizeRequest(BaseModel):
    phone: str
    messages: list[Message]


class SummarizeResponse(BaseModel):
    summary: str
