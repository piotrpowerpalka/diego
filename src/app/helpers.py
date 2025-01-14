# %%
import numpy as np
import pandas as pd


def convert_numeric(val):
    if isinstance(val, np.floating):
        val = float(val)
    elif isinstance(val, np.integer):
        val = int(val)
    return val


def get_current_round_datetime(
    period_min: int = 15, deley_sec: int = 0, tz: str = "Europe/Warsaw"
) -> str:
    """
    Get the current datetime in the format 'YYYY-MM-DD HH:MM:SS' which the time is rounded to period in minutes.

    """
    current_datetime = pd.Timestamp.now(tz=tz).round(f"{period_min}min") + pd.Timedelta(
        f"{deley_sec}sec"
    )
    return current_datetime.strftime("%Y-%m-%d %H:%M:%S")


# %%


def get_devices_list():
    return [
        "pv",
        "bysprint",
        "bystar1",
        "bystar2",
        "mazak",
        "eh",
        "inv1",
        "inv2",
        "sg1",
        "sg2",
        "sg3",
        "sg4",
        "evcs",
        "soc",
        "sg1prim",
        "ms",
        "network",
    ]


def save_data_to_file(file_path: str, data: str):
    import os

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(data)
