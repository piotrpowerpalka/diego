from datetime import datetime
import os
from spade.agent import Agent
from spade.behaviour import (
    CyclicBehaviour,
)
from spade.message import Message
import json
from pandas import Timedelta
import pandas as pd

from api.requests import fetch_metrics
from entities.metric import Metric

from settings import (
    SERVER_HOST,
    AGENT_PASSWORD,
    VERIFY_SECURITY,
    BEHAVIOUR_TIMEOUT,
    DEBUG,
    USE_CSV,
    CSV_DATA_PATH,
)


class Predictor(Agent):
    """
    Predictor class inherits from Agent and is responsible for making predictions based on input data.
    Attributes:
        device_prefix (str): Prefix used to identify device Agent.
    Methods:
        __init__(jid: str, password: str, prefix: str, verify_security: bool = False):
            Initializes the Predictor instance with the given JID, password, prefix, and security verification flag.
        setup():
            Sets up the Predictor agent by adding the WaitForPredictOrder behaviour.
        get_prediction(datetime):
            Generates a prediction based on the input data for the given datetime.
            Args:
                datetime (str): The datetime for which the prediction is to be made.
            Returns:
                dict: A dictionary containing the device prefix, workpoint data, and forecast data.
    """

    def __init__(self, device_name: str):
        jid: str = f"{device_name}_predictor@{SERVER_HOST}"
        password: str = AGENT_PASSWORD
        verify_security: bool = VERIFY_SECURITY
        super().__init__(jid, password, verify_security)

        self.device_name: str = device_name

    def _read_data_from_csv(self):
        file_path = os.path.join(
            CSV_DATA_PATH, "input_data_{}.csv".format(self.device_name)
        )
        self._input_data: pd.DataFrame = pd.read_csv(file_path, sep=";")

    async def setup(self):
        if USE_CSV:
            self._read_data_from_csv()
        print(f"Predictor Agent [{self.name}] started")
        wfr = self.WaitForPredictOrder()
        self.add_behaviour(wfr)

    async def get_prediction(self, timestamp: str) -> dict:
        """
        Get prediction for the given datetime.
        Args:
            timestamp (str): The datetime for which the prediction is to be made.
        Returns:
            dict: A dictionary containing the device name, workpoint data, and forecast data.
        """
        try:
            pd.to_datetime(timestamp)
            if DEBUG:
                print(
                    f"[{self.name}] Received request to get prediction for datetime: {timestamp}"
                )
        except ValueError:
            raise ValueError(
                "Invalid datetime format. Please provide a valid datetime string."
            )

        if USE_CSV:
            return self._get_prediction_from_csv(timestamp)
        return await self._get_prediction_from_api(timestamp)

    async def _get_prediction_from_api(self, timestamp: str) -> dict:
        """
        Get prediction from API for the given datetime.
        Args:
            timestamp (str): The datetime for which the prediction is to be made.
        Returns:
            dict: A dictionary containing the device name, workpoint data, and forecast data.
        """
        # prediction based on previous 15 min data
        forecast_datetime = str(pd.to_datetime(timestamp) - Timedelta("15min"))

        metrics_json = await fetch_metrics(self.device_name, forecast_datetime)

        if DEBUG:
            print(f"Metrics JSON for [{self.device_name}]: {metrics_json}")

        forecast_timestamp = datetime.fromisoformat(metrics_json["datetime"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        forecast_metric = Metric(
            device_name=self.device_name,
            timestamp=forecast_timestamp,
            active_power=metrics_json["power"]["p"],
            reactive_power=metrics_json["power"]["q"],
            active_energy=metrics_json["energy"]["ep"],
            reactive_energy=metrics_json["energy"]["eq"],
        )

        workpoint_metric = Metric(
            device_name=self.device_name,
            timestamp=timestamp,
            active_power=0.0,
            reactive_power=0.0,
            active_energy=0.0,
            reactive_energy=0.0,
        )
        if self.device_name == "soc":
            return {
                "device": self.device_name,
                "workpoint": {
                    "Datetime": timestamp,
                    "soc": metrics_json["value"],
                    "soc_Ep": metrics_json["energy"]["ep"],
                },
                "forecast": {
                    "Datetime": forecast_datetime,
                    "soc": metrics_json["value"],
                    "soc_Ep": metrics_json["energy"]["ep"],
                },
            }
        return {
            "device": self.device_name,
            "workpoint": workpoint_metric.to_spade_message(),
            "forecast": forecast_metric.to_spade_message(),
        }

    def _get_prediction_from_csv(self, datetime):
        """
        Get prediction from CSV for the given datetime.
        """
        # prediction based on previous 15 min data
        forecast_date = str(pd.to_datetime(datetime) - Timedelta("15min"))
        workpoint: pd.DataFrame = self._input_data[
            self._input_data["Datetime"] == datetime
        ]
        forecast: pd.DataFrame = self._input_data[
            self._input_data["Datetime"] == forecast_date
        ]

        json_wp = {}  # json z punktem pracy
        json_fc = {}  # json z predykcją

        if workpoint.shape[1] >= 1 and workpoint.shape[0] > 0:
            for r in range(1, workpoint.shape[1]):
                json_wp[workpoint.columns[r]] = str(workpoint.iat[0, r])

        if forecast.shape[1] >= 1 and forecast.shape[0] > 0:
            for rf in range(1, forecast.shape[1]):
                json_fc[forecast.columns[rf]] = str(forecast.iat[0, rf])

        return {"device": self.device_name, "workpoint": json_wp, "forecast": json_fc}

    class WaitForPredictOrder(CyclicBehaviour):
        """
        WaitForPredictOrder class inherits from CyclicBehaviour and is responsible for waiting for a prediction order.
        Methods:
            run():
                Waits for a prediction order message and sends a prediction response message.
        """

        _log_prefix_name = "WaitForPredictOrder"

        async def run(self):

            agent: Predictor = self.agent
            msg = await self.receive(timeout=BEHAVIOUR_TIMEOUT)
            if msg:
                msg_json = json.loads(msg.body)
                timestamp = msg_json["timestamp"]

                try:
                    prediction_dict = await agent.get_prediction(timestamp)
                except Exception as e:
                    print(
                        f"{self._log_prefix_name} Error while getting prediction for [{agent.name}]: {e}"
                    )
                    return

                tojid = msg.get_metadata("sender")
                if tojid:
                    msg_rply = Message(to=f"{tojid}@{SERVER_HOST}")
                    msg_rply.set_metadata("performative", "inform")
                    msg_rply.set_metadata("sender", agent.name)
                    msg_rply.set_metadata("language", "json")

                    msg_rply.body = json.dumps(prediction_dict)

                    await self.send(msg_rply)
                    if DEBUG:
                        print(
                            f"{self._log_prefix_name} sent [{msg_rply.get_metadata('performative')}] from [{agent.name}] to [{tojid}] with body [{msg_rply.body}]"
                        )
                else:
                    print(
                        f"{self._log_prefix_name} Metadata 'sender' is missing in the received message."
                    )
            else:
                print(
                    f"{self._log_prefix_name} No message received within the timeout period."
                )
