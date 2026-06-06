from google.protobuf.message import Message

class DispatchStepRequest(Message):
    run_id: str
    step_id: str
    agent_id: str
    organization_id: str
    input: bytes

    def __init__(
        self,
        run_id: str = ...,
        step_id: str = ...,
        agent_id: str = ...,
        organization_id: str = ...,
        input: bytes = ...,
    ) -> None: ...

class StepEventProto(Message):
    step_id: str
    event_type: str
    payload: bytes
    timestamp: int

    def __init__(
        self,
        step_id: str = ...,
        event_type: str = ...,
        payload: bytes = ...,
        timestamp: int = ...,
    ) -> None: ...

class HealthCheckRequest(Message):
    def __init__(self) -> None: ...

class HealthCheckResponse(Message):
    healthy: bool

    def __init__(self, healthy: bool = ...) -> None: ...
