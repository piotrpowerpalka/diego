import os
from spade.agent import Agent
from spade.behaviour import (
    CyclicBehaviour,
)
from spade.message import Message
import json
import pandas as pd
from datetime import datetime

from api.requests import fetch_properties, post_balance
from helpers import save_data_to_file
from entities.device import DeviceProperties
from settings import (
    SERVER_HOST,
    AGENT_PASSWORD,
    VERIFY_SECURITY,
    BEHAVIOUR_TIMEOUT,
    DEBUG,
    USE_CSV,
    CSV_DATA_PATH,
)


class DeviceManager(Agent):
    def __init__(self, device_name: str):
        jid: str = f"{device_name}_manager@{SERVER_HOST}"
        password: str = AGENT_PASSWORD
        verify_security: bool = VERIFY_SECURITY
        super().__init__(jid, password, verify_security)

        self.device_name = device_name
        self.predictor_name = f"{device_name}_predictor"
        self.auctionee_name = f"{device_name}_auctionee"

    async def initialize_device_properties(self):

        self.roles_dict = {}
        self.bounds_dict = {}
        if USE_CSV:
            self._initialize_device_from_csv()
        else:
            await self._initialize_device_from_api()

    async def _initialize_device_from_api(self) -> None:

        properties_json = await fetch_properties(self.device_name)
        if DEBUG:
            print(f"Device properties JSON for [{self.device_name}]: {properties_json}")
        device_properties = DeviceProperties.from_json(properties_json)
        self.roles_dict = device_properties.roles_to_spade_message()
        self.bounds_dict = device_properties.bounds_to_spade_message()

    def _initialize_device_from_csv(self) -> None:

        # roles
        roles_file_path = os.path.join(
            CSV_DATA_PATH, "roles_{}.csv".format(self.device_name)
        )
        roles = pd.read_csv(roles_file_path, sep=";")
        roles["price"] = roles["price"].astype(float)

        for c in range(roles.shape[1]):  # cols
            attr = []
            for r in range(roles.shape[0]):  # rows
                attr.append(str(roles.iat[r, c]))
            self.roles_dict[roles.columns[c]] = attr

        # bounds
        bounds_file_path = os.path.join(
            CSV_DATA_PATH, "bounds_{}.csv".format(self.device_name)
        )
        bounds = pd.read_csv(bounds_file_path, sep=";")
        for col in ["min", "max"]:
            bounds[col] = bounds[col].apply(lambda x: float(x) if x != "circ" else x)

        for c in range(bounds.shape[1]):  # cols
            attr = []
            for r in range(bounds.shape[0]):  # rows
                attr.append(str(bounds.iat[r, c]))
            self.bounds_dict[bounds.columns[c]] = attr

    async def setup(self):
        await self.initialize_device_properties()
        print(f"DeviceManager Agent [{self.name}] started")
        wfr = self.WaitForRequest()
        self.add_behaviour(wfr)

    async def set_balance(self, message):

        input = json.dumps(
            {
                "datetime": datetime.fromisoformat(message["datetime"]).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "power": message["wp"],
                "energy": {
                    k: (v if pd.notna(v) else None)
                    for k, v in message.get("energies", {}).items()
                },
                "status": message["statuses"] if "statuses" in message else None,
            }
        )

        if DEBUG:
            print(f"DeviceManager [{self.name}] set_balance input: {input}")
        if USE_CSV:
            # write to csv
            file_path = os.path.join(
                CSV_DATA_PATH, "output/{}.json".format(self.device_name)
            )
            save_data_to_file(file_path, input)
        else:
            await post_balance(self.device_name, input)

    class WaitForRequest(CyclicBehaviour):

        _log_prefix_name = "WaitForRequest"

        async def run(self):

            agent: DeviceManager = self.agent

            msg = await self.receive(timeout=BEHAVIOUR_TIMEOUT)
            if msg:

                if msg.get_metadata("performative") == "query":

                    tojid = agent.predictor_name
                    msg_rply = Message(to=f"{tojid}@{SERVER_HOST}")
                    msg_rply.set_metadata("performative", "query")
                    msg_rply.set_metadata("sender", agent.name)
                    msg_rply.set_metadata("language", "json")

                    msg_rply.body = msg.body

                    await self.send(msg_rply)
                    if DEBUG:
                        print(
                            f"{self._log_prefix_name} sent [{msg_rply.get_metadata('performative')}] from [{agent.name}] to [{tojid}] with body [{msg_rply.body}]"
                        )

                elif msg.get_metadata("performative") == "inform":

                    tojid = agent.auctionee_name
                    msg_rply = Message(to=f"{tojid}@{SERVER_HOST}")
                    msg_rply.set_metadata("performative", "inform")
                    msg_rply.set_metadata("sender", agent.name)
                    msg_rply.set_metadata("language", "json")

                    body_json = json.loads(msg.body)

                    rply_body_json = {
                        "device": body_json["device"],
                        "workpoint": body_json["workpoint"],
                        "forecast": body_json["forecast"],
                        "prices": agent.roles_dict,
                        "bounds": agent.bounds_dict,
                    }

                    msg_rply.body = json.dumps(rply_body_json)

                    await self.send(msg_rply)
                    if DEBUG:
                        print(
                            f"{self._log_prefix_name} sent [{msg_rply.get_metadata('performative')}] from [{agent.name}] to [{tojid}] with body [{msg_rply.body}]"
                        )

                elif msg.get_metadata("performative") == "accept_offer":
                    if DEBUG:
                        print(
                            f"{self._log_prefix_name} received [{msg.get_metadata('performative')}] from [{msg.get_metadata('sender')}] to [{msg.to}] with body [{msg.body}]"
                        )

                    await agent.set_balance(json.loads(msg.body))
