from pydantic import Field, SecretStr
from .core import PushActionConfiguration, AuthActionConfiguration, ExecutableActionMixin
from app.services.utils import GlobalUISchemaOptions


class AuthenticateConfig(AuthActionConfiguration, ExecutableActionMixin):
    username: str = Field(
        ...,
        title="Username",
        description="Username for inReach account"
    )
    password: SecretStr = Field(
        ...,
        title="Password",
        description="Password for inReach account",
        format="password"
    )

    ui_global_options: GlobalUISchemaOptions = GlobalUISchemaOptions(
        order=[
            "username",
            "password",
        ],
    )


class PushMessageConfig(PushActionConfiguration):
    pass
