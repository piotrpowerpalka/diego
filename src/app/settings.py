import os
from helpers import get_current_round_datetime

# change to time zone Warsaw
TZ = os.getenv("TZ", "Europe/Warsaw")

# XMPP
SERVER_HOST = os.getenv("SERVER_HOST", "server")
AGENT_PASSWORD = "electrum1@3"
VERIFY_SECURITY = False

# CSV
CSV_DATA_PATH = os.getenv("CSV_DATA_PATH", "../data/")
CSV = os.getenv("CSV", "false")  # use csv files for data
USE_CSV = CSV.lower() == "true"

# BALANCER
PERIOD_MIN = 15  # period of balancing [minutes]
# STEP_MIN = PERIOD_MIN   # uncomment in final version
STEP_MIN = PERIOD_MIN  # step of running the balancing [minutes], for testing, comment in production
DELAY_SEC = os.getenv("DELAY_SEC", 0)  # delay of balancing [seconds]

# START DATE
START_DATE = os.getenv("START_DATE")
BALANCING_DATETIME = (
    START_DATE
    if START_DATE
    else ("2024-01-30 00:30:00" if USE_CSV else get_current_round_datetime(PERIOD_MIN))
)

# SPADE
BEHAVIOUR_TIMEOUT = 120  # timeout for behaviours [seconds]
DEBUG = True  # debug mode

# API
API_HOST = os.getenv("API_HOST", "http://host.docker.internal:5022")
# API_HOST = os.getenv("API_HOST", "http://localhost:5022")
API_AUTH = os.getenv("API_AUTH", "Basic bGx1cGluc2tpOkFiY2QxMjM0")
