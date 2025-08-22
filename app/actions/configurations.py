from pydantic import Field, SecretStr
from .core import PushActionConfiguration, AuthActionConfiguration, ExecutableActionMixin
from app.services.utils import GlobalUISchemaOptions


class AuthenticateConfig(AuthActionConfiguration, ExecutableActionMixin):
    api_url: str = Field(
        "",  # Auth params made optional until we can differentiate config requirements for providers and destinations
        title="inReach Portal Connect (IPC) Inbound API",
        description="Base URL for inReach Inbound API"
    )
    username: str = Field(
        "",
        title="Username",
        description="Username for inReach account"
    )
    password: SecretStr = Field(
        "",
        title="Password",
        description="Password for inReach account",
        format="password"
    )

    ui_global_options: GlobalUISchemaOptions = GlobalUISchemaOptions(
        order=[
            "api_url",
            "username",
            "password",
        ],
    )


class PushMessageConfig(PushActionConfiguration):
    pass
