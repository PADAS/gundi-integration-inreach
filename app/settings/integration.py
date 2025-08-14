from environs import Env

env = Env()

TRACING_ENABLED = env.bool("TRACING_ENABLED", True)
