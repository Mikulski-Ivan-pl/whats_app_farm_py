from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str
    timestamp: int


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict


class ToolCall(BaseModel):
    id: str
    name: str
    args: dict


class ToolResult(BaseModel):
    tool_call_id: str
    content: str


class ReplyRequest(BaseModel):
    phone: str
    messages: list[Message]
    summary: str = ""
    system_prompt: str = ""
    model: str = ""
    tools: list[ToolDefinition] = []
    previous_tool_calls: list[ToolCall] = []
    tool_results: list[ToolResult] = []


class ReplyResponse(BaseModel):
    reply: str = ""
    tool_calls: list[ToolCall] = []


class SummarizeRequest(BaseModel):
    phone: str
    messages: list[Message]
    model: str = ""
    previous_summary: str = ""


class SummarizeResponse(BaseModel):
    summary: str
