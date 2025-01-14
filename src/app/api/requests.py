import aiohttp
from settings import API_HOST, API_AUTH

HEADERS = {"Authorization": API_AUTH, "Content-Type": "application/json"}


async def fetch_devices():
    """
    Output:

       [
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
       "network"
        ]
    """

    url = f"{API_HOST}/api/devices"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            return await response.json()


async def fetch_metrics(device_name: str, timestamp: str):
    """
        Output:

        {
        "datetime": "2024-12-17T09:30:00",
        "power": {
            "p": -13.375087459435624,
            "q": 0.1977098165603166
        },
        "energy": {
            "ep": -2.1589763246746396,
            "eq": 0.05662478047507942
        }
    }

    """

    timestamp = timestamp.replace(" ", "T")
    url = f"{API_HOST}/api/devices/{device_name}/metrics?timestamp={timestamp}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            return await response.json()


async def fetch_properties(device_name: str):
    """

    Output:

    {
    "deviceName": "pv",
    "bounds": [
        {
            "attribute": "P",
            "min": -317.12,
            "max": 0.2
        },
        {
            "attribute": "tg",
            "min": 0,
            "max": 0.75
        }
    ],
    "roles": [
        {
            "roleType": "UAS",
            "energyType": "Ep",
            "price": 1
        },
        {
            "roleType": "CA",
            "energyType": "Eq",
            "price": 1
        }
    ]
    }


    """
    # bounds and roles
    url = f"{API_HOST}/api/devices/{device_name}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            return await response.json()


async def post_balance(device_name: str, input: str):
    """
    Input:
        {
      "datetime": "2025-01-13T12:12:15.713Z",
      "power": {
        "p": 0,
        "q": 0
      },
      "energy": {
        "ep": 0,
        "eq": 0
      },
      "status": {
        "during_peak": true,
        "q_block": true,
        "res_supp": true,
        "q_problem": true,
        "lamp_color": "string"
      }
    }
    """
    url = f"{API_HOST}/api/devices/{device_name}"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=HEADERS, data=input) as response:
            return await response.text()
