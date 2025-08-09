from environs import Env

env = Env()

INREACH_API_URL = env.str("INREACH_API_URL", "https://eur-enterprise.inreach.garmin.com")
TRACING_ENABLED = env.bool("TRACING_ENABLED", True)
