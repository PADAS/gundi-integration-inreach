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

    @classmethod
    def ui_schema(cls, *args, **kwargs):
        # The heading the portal shows above the auth form. GlobalUISchemaOptions
        # has no title or description, so add them to the generated ui schema.
        return {
            **super().ui_schema(*args, **kwargs),
            "ui:title": "Connection Credentials",
            "ui:description": "Enter your credentials to authenticate.",
        }


class PushMessageConfig(PushActionConfiguration):
    pass
