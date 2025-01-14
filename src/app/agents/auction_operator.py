import os
import traceback
import sys
from spade.agent import Agent
from spade.behaviour import (
    OneShotBehaviour,
    PeriodicBehaviour,
    CyclicBehaviour,
)
from spade.message import Message
from datetime import datetime
import json
import pandas as pd

from balancer import Balancer
from helpers import convert_numeric, get_current_round_datetime, save_data_to_file
from settings import (
    CSV_DATA_PATH,
    DELAY_SEC,
    SERVER_HOST,
    AGENT_PASSWORD,
    VERIFY_SECURITY,
    BEHAVIOUR_TIMEOUT,
    DEBUG,
    PERIOD_MIN,
    STEP_MIN,
    BALANCING_DATETIME,
    USE_CSV,
)


class AuctionOperator(Agent):

    def __init__(self, auction_operator_name: str, device_list: list[str]):

        jid: str = f"{auction_operator_name}@{SERVER_HOST}"
        password: str = AGENT_PASSWORD
        verify_security: bool = VERIFY_SECURITY

        super().__init__(jid, password, verify_security)

        self.auctionee_name_list = [
            f"{device_name}_auctionee" for device_name in device_list
        ]
        self.offers_list = pd.DataFrame()
        self.forecast = pd.DataFrame()
        self.roles = pd.DataFrame(columns=["flow", "role", "energy", "price", "device"])
        self.bounds = pd.DataFrame(columns=["energy", "min", "max"])
        self.result_data = dict()
        self.result_data_devices = dict()
        self.clear_temp_data()

    def clear_temp_data(self):
        if self.offers_list.empty == False:
            self.offers_list = self.offers_list.iloc[0:0]
        if self.forecast.empty == False:
            self.forecast = self.forecast.iloc[0:0]
        if self.roles.empty == False:
            self.roles = self.roles.iloc[0:0]
        if self.bounds.empty == False:
            self.bounds = self.bounds.iloc[0:0]
        self.agentsAns = []
        self.flow = []
        self.role = []
        self.energy = []
        self.price = []
        self.device = []
        self.en = []
        self.min = []
        self.max = []

    async def setup(self):
        self.balancing_datetime = BALANCING_DATETIME
        print(
            f"AuctionOperator Agent [{self.name}] started with balancing datetime: {self.balancing_datetime}"
        )
        start_at1 = (
            datetime.now()
            if USE_CSV
            else datetime.fromisoformat(
                get_current_round_datetime(PERIOD_MIN, int(DELAY_SEC))
            )
        )
        cfp = self.CallForProposal(period=STEP_MIN * 60, start_at=start_at1)
        self.add_behaviour(cfp)

    async def balance(self):
        # fix the data types
        self.offers_list["Datetime"] = pd.to_datetime(self.offers_list["Datetime"])
        for col in self.offers_list.columns[1:]:
            self.offers_list[col] = self.offers_list[col].astype(float)
        self.forecast["Datetime"] = pd.to_datetime(self.forecast["Datetime"])
        for col in self.forecast.columns[1:]:
            self.forecast[col] = self.forecast[col].astype(float)
        for col in ["min", "max"]:
            self.bounds[col] = self.bounds[col].apply(
                lambda x: float(x) if x != "circ" else x
            )
        self.roles["price"] = self.roles["price"].astype(float)

        # call the balancer
        per_balancer = Balancer(
            self.offers_list, self.bounds, self.roles, self.forecast
        )

        per_balancer.calc_fix_dem()
        (
            old_states,
            Ems_new_obs,
            Ems_new_pred,
            en_deltas,
            wp,
            autocons,
            tgs,
            blocked_devs,
            res_supp_devs,
        ) = per_balancer.balancing()

        state_comp_frame = pd.concat(
            [old_states, Ems_new_pred, Ems_new_pred - old_states]
        )
        state_comp_frame.index = ["old", "new", "diff"]

        state_comp_frame["tg"] = [tgs["old"], tgs["new"], tgs["new"] - tgs["old"]]
        for col in ["Ep", "Eq"]:
            state_comp_frame["pv_" + col + "_auto"] = [
                autocons["old_pv_" + col + "_auto"].values[0],
                autocons["pv_" + col + "_auto"].values[0],
                (
                    autocons["pv_" + col + "_auto"]
                    - autocons["old_pv_" + col + "_auto"]
                ).values[0],
            ]

        return state_comp_frame, blocked_devs, res_supp_devs, wp

    class CallForProposal(PeriodicBehaviour):
        """
        ...
        """

        _log_prefix_name = "CallForProposal"

        async def run(self):

            agent: AuctionOperator = self.agent

            # behaviour ReceiveOffers added before sending offers, to avoid missing offers
            ro = agent.ReceiveOffers()
            agent.add_behaviour(ro)

            agent.balancing_datetime = str(
                pd.to_datetime(agent.balancing_datetime)
                + pd.Timedelta("{}min".format(PERIOD_MIN))
            )

            forecast_date = str(
                pd.to_datetime(agent.balancing_datetime) - pd.Timedelta("15min")
            )

            # clear inputs data
            agent.clear_temp_data()

            agent.offers_list = pd.DataFrame(
                data={"Datetime": [agent.balancing_datetime]}
            )
            agent.forecast = pd.DataFrame(data={"Datetime": [forecast_date]})

            for auctionee in agent.auctionee_name_list:

                tojid = auctionee
                msg = Message(to=f"{tojid}@{SERVER_HOST}")
                msg.set_metadata("performative", "CFP")
                msg.set_metadata("language", "json")
                msg.set_metadata("sender", agent.name)
                msg.body = json.dumps({"timestamp": agent.balancing_datetime})

                await self.send(msg)
                if DEBUG:
                    print(
                        f"{self._log_prefix_name} sent [{msg.get_metadata('performative')}] from [{agent.name}] to [{tojid}] with body:[{msg.body}]"
                    )

    class ReceiveOffers(CyclicBehaviour):

        _log_prefix_name: str = "ReceiveOffers"

        async def run(self):
            agent: AuctionOperator = self.agent
            try:

                msg = await self.receive(timeout=BEHAVIOUR_TIMEOUT)
                if msg:
                    if msg.get_metadata("language") == "json":
                        msg_json = json.loads(msg.body)

                        agent.agentsAns.append(msg_json["device"])
                        for wpk in msg_json["workpoint"]:
                            if wpk != "Datetime":
                                agent.offers_list.insert(
                                    1, wpk, msg_json["workpoint"][wpk]
                                )

                        for fck in msg_json["forecast"]:
                            if fck != "Datetime":
                                agent.forecast.insert(1, fck, msg_json["forecast"][fck])

                        for pk in msg_json["prices"]["flow"]:
                            agent.flow.append(pk)
                        for pk in msg_json["prices"]["role"]:
                            agent.role.append(pk)
                        for pk in msg_json["prices"]["energy"]:
                            agent.energy.append(pk)
                        for pk in msg_json["prices"]["price"]:
                            agent.price.append(pk)
                        for pk in msg_json["prices"]["device"]:
                            agent.device.append(pk)
                        for pk in msg_json["bounds"]["Unnamed: 0"]:
                            agent.en.append(pk)
                        for pk in msg_json["bounds"]["min"]:
                            agent.min.append(pk)
                        for pk in msg_json["bounds"]["max"]:
                            agent.max.append(pk)
                    else:
                        raise TypeError

                    if len(agent.agentsAns) == len(agent.auctionee_name_list):
                        self.kill()

                else:
                    print(
                        f"{self._log_prefix_name} did not received any message before timeout."
                    )
                    self.kill(exit_code=998)
            except Exception:
                print(traceback.format_exc())  # This line is for getting traceback.
                print(sys.exc_info()[2])  # This line is getting for the error type.
                self.kill(exit_code=999)

        async def on_end(self):
            if not self.exit_code:
                agent: AuctionOperator = self.agent

                agent.bounds = pd.DataFrame(
                    {"min": agent.min, "max": agent.max}, index=agent.en
                )

                agent.roles = pd.DataFrame(
                    {
                        "flow": agent.flow,
                        "role": agent.role,
                        "energy": agent.energy,
                        "price": agent.price,
                        "device": agent.device,
                    }
                )
                balance = agent.Balance()
                agent.add_behaviour(balance)

    class Balance(OneShotBehaviour):

        _log_prefix_name = "Balance"

        async def run(self):

            agent: AuctionOperator = self.agent
            print(f"{self._log_prefix_name} is running")
            # insert code for clearing the offers

            (state_comp_frame, blocked_devs, res_supp_devs, wp) = await agent.balance()

            agent.offers_list.loc[agent.balancing_datetime, "soc_Ep"] = (
                state_comp_frame.loc["new", "soc_Ep"]
            )
            agent.offers_list.loc[agent.balancing_datetime, "soc"] = (
                state_comp_frame.loc["new", "soc"]
            )

            forecast = agent.forecast.copy()
            # change to str as further is using string representation of datetime
            forecast["Datetime"] = forecast["Datetime"].astype(str)
            state_comp_frame["Datetime"] = state_comp_frame["Datetime"].astype(str)
            if DEBUG:
                print(f"Balancing datetime: {agent.balancing_datetime}")
                print(f"Forecast datetime: {forecast['Datetime']}")

            soc_data = pd.DataFrame(
                agent.forecast.loc[0, ["Datetime", "soc", "soc_Ep"]]
            ).T
            out = agent.merge_data(state_comp_frame, forecast, soc_data)
            agent.result_data, agent.result_data_devices = agent.reconstruct(
                out, blocked_devs, res_supp_devs, wp
            )

            print("1merge")
            print(state_comp_frame)

            print("2merge")
            print(forecast)

            print("3merge")
            print(soc_data)

            print("OUT")
            print(out)

            print("new data dict")
            print(agent.result_data)

            print("new out devs")
            print(agent.result_data_devices)

            sbi = agent.SendBalanceInfo()
            agent.add_behaviour(sbi)

    class SendBalanceInfo(OneShotBehaviour):

        _log_prefix_name = "SendBalanceInfo"

        async def run(self):

            agent: AuctionOperator = self.agent

            for auctionee in agent.auctionee_name_list:
                short_name = auctionee.split("_")[0]
                if short_name in agent.result_data_devices:
                    tojid = auctionee
                    # Instantiate the message
                    msg = Message(to=f"{tojid}@{SERVER_HOST}")
                    msg.set_metadata("performative", "inform")
                    msg.set_metadata("sender", agent.name)
                    msg.body = json.dumps(agent.result_data_devices[short_name])

                    await self.send(msg)
                    if DEBUG:
                        print(
                            f"{self._log_prefix_name} sent [{msg.get_metadata('performative')}] from [{agent.name}] to [{tojid}] with body [{msg.body}]"
                        )
            if USE_CSV:
                # write to csv
                file_path = os.path.join(CSV_DATA_PATH, "output/balance.json")
                save_data_to_file(file_path, json.dumps(agent.result_data))
            # agent.balancing_datetime = str(
            #     pd.to_datetime(agent.balancing_datetime)
            #     + pd.Timedelta("{}min".format(PERIOD_MIN))
            # )

    @staticmethod
    def merge_data(
        out_data: pd.DataFrame, output_frame: pd.DataFrame, inps: pd.DataFrame
    ) -> pd.DataFrame:
        # Drop unnecessary columns
        output_frame = output_frame.drop(columns=["soc", "soc_Ep"])

        # Prepare new data with renamed columns
        new_data = out_data.loc["new"].add_suffix("_new").to_frame().T
        new_data["Datetime"] = out_data.loc["new", "Datetime"]

        # Add old data columns to new data
        for col in ["ms_observ_Ep", "ms_observ_Eq", "tg", "pv_Ep_auto", "pv_Eq_auto"]:
            new_data[col] = out_data.loc["old", col]

        # Merge dataframes
        output_frame = output_frame.merge(inps, on="Datetime", how="left")
        output_frame = output_frame.merge(new_data, on="Datetime", how="left")

        # Update datetime and add forecast date
        output_frame["fcast_date"] = output_frame["Datetime"]
        output_frame["Datetime"] = pd.to_datetime(
            output_frame["Datetime"]
        ) + pd.Timedelta("15min")

        # Calculate deltas for specified fields
        fields = ["ms_observ_", "pv_", "eh_", "evcs_"]
        energies = ["Ep", "Eq"]
        additional_fields = ["soc_Ep", "inv1_Eq", "pv_Ep_auto", "pv_Eq_auto", "tg"]

        for field in fields:
            for energy in energies:
                col = field + energy
                output_frame["del_" + col] = (
                    output_frame[col + "_new"] - output_frame[col]
                )

        for col in additional_fields:
            output_frame["del_" + col] = output_frame[col + "_new"] - output_frame[col]

        return output_frame.copy()

    @staticmethod
    def reconstruct(
        df: pd.DataFrame, block_devs: dict, res_supp_devs: dict, wp: pd.DataFrame
    ) -> tuple[dict, dict]:
        # Initialize output dictionaries
        out_all_dict = {
            "datetime": pd.Timestamp(df["Datetime"].values[0]).strftime(
                "%Y-%m-%d %H:%M"
            ),
            "working_points": {},
            "energies": {},
            "statuses": {},
            "pv_energy_effect": {},
            "saved_net_energy": {},
            "ms_workpoint": {},
        }

        out_devices_dict = {
            dev: {
                "datetime": pd.Timestamp(df["Datetime"].values[0]).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "wp": {
                    "P": convert_numeric(wp.loc["new", f"{dev}_P"]),
                    "Q": convert_numeric(wp.loc["new", f"{dev}_Q"]),
                },
                "energies": {
                    "Ep": convert_numeric(df[f"{dev}_Ep_new"].values[0]),
                    "Eq": convert_numeric(df[f"{dev}_Eq_new"].values[0]),
                },
                "statuses": {},
            }
            for dev in [
                "pv",
                "eh",
                "evcs",
                "inv1",
                "bystar1",
                "bysprint",
                "bystar2",
                "mazak",
            ]
        }

        # Update statuses for blocked and resupply devices
        for key, item in {**block_devs, **res_supp_devs}.items():
            if key in out_devices_dict:
                if key not in ["eh", "evcs"]:
                    out_devices_dict[key]["statuses"].update(
                        {
                            "Q_problem": block_devs.get(key, False),
                            "lamp_color": (
                                "red" if block_devs.get(key, False) else "green"
                            ),
                            "res_supp": res_supp_devs.get(key, False),
                        }
                    )
                else:
                    out_devices_dict[key]["statuses"].update(
                        {
                            "Q_block": block_devs.get(key, False),
                            "res_supp": res_supp_devs.get(key, False),
                        }
                    )

        # Populate out_all_dict with working points, energies, and statuses
        for dev in out_devices_dict.keys():
            out_all_dict["working_points"][dev] = out_devices_dict[dev]["wp"]
            out_all_dict["energies"][dev] = out_devices_dict[dev]["energies"]
            out_all_dict["statuses"][dev] = out_devices_dict[dev]["statuses"]

        # Populate out_all_dict with PV energy effect and saved net energy
        for energy in ["Ep", "Eq"]:
            out_all_dict["pv_energy_effect"][energy] = convert_numeric(
                df[f"pv_{energy}_auto_new"].values[0]
            )
            out_all_dict["saved_net_energy"][energy] = convert_numeric(
                -df[f"del_ms_observ_{energy}"].values[0]
            )

        # Populate out_all_dict with ms workpoint
        for power in ["P", "Q"]:
            out_all_dict["ms_workpoint"][power] = convert_numeric(
                df[f"ms_observ_{power}_new"].values[0]
            )
        out_all_dict["ms_workpoint"]["tg"] = convert_numeric(df["tg_new"].values[0])

        return out_all_dict, out_devices_dict
