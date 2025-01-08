from spade.agent import Agent
from spade.behaviour import (
    OneShotBehaviour,
    TimeoutBehaviour,
    PeriodicBehaviour,
    CyclicBehaviour,
)
from spade.message import Message
from spade.template import Template
import time
import datetime
import json
from functions import *
from json import dumps
from pandas import Timedelta
from classes import *
import traceback
import sys


DEFAULT_HOST = "server_hello"
DT = "2024-01-31 00:30:00"
PERIOD = 15  # period of balancing [minutes]
# STEP = PERIOD   # uncomment in final version
STEP = 2  # step of running the balancing [minutes], for testing, comment in production


class AuctionOperator(Agent):
    datetime = DT

    flow = []
    role = []
    energy = []
    price = []
    device = []

    en = []
    min = []
    max = []

    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        # self.auctionee_list = self.config['auctionees']
        self.auctionee_list = [
            "pv_auctionee",
            "bysprint_auctionee",
            "bystar1_auctionee",
            "bystar2_auctionee",
            "mazak_auctionee",
            "eh_auctionee",
            "inv1_auctionee",
            "inv2_auctionee",
            "sg1_auctionee",
            "sg2_auctionee",
            "sg3_auctionee",
            "sg4_auctionee",
            "evcs_auctionee",
            "soc_auctionee",
            "sg1prim_auctionee",
            "ms_auctionee",
            "network_auctionee",
        ]

        self.offers_list = pd.DataFrame()
        self.forecast = pd.DataFrame()
        self.roles = pd.DataFrame(columns=["flow", "role", "energy", "price", "device"])
        self.bounds = pd.DataFrame(columns=["energy", "min", "max"])
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
        print("Agent {} started".format(self.name))

        start_at1 = datetime.datetime.now()
        cfp = self.CallForProposal(period=STEP * 60, start_at=start_at1)
        self.add_behaviour(cfp)

    async def balance(self):
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
        async def run(self):
            #            print("[{}] CallForProposal beh running".format(self.agent.name))

            # behaviour ReceiveOffers added before sending offers, to avoid missing offers
            ro = self.agent.ReceiveOffers()
            self.agent.add_behaviour(ro)

            self.agent.fcst_date = str(
                pd.to_datetime(self.agent.datetime) - Timedelta("15min")
            )

            # clear inputs data
            self.agent.clear_temp_data()

            self.agent.offers_list = pd.DataFrame(
                data={"Datetime": [self.agent.datetime]}
            )
            self.agent.forecast = pd.DataFrame(
                data={"Datetime": [self.agent.fcst_date]}
            )

            for curr_agent in self.agent.auctionee_list:

                tojid = f"{curr_agent}@{DEFAULT_HOST}"
                # Instantiate the message
                msg = Message(to=tojid)
                msg.set_metadata("performative", "CFP")
                msg.set_metadata("language", "json")
                msg.set_metadata("sender", self.agent.name)
                msg.body = json.dumps({"timestamp": self.agent.datetime})

                await self.send(msg)
                print(
                    "send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: Auctionee".format(
                        msg.get_metadata("performative"),
                        self.agent.name,
                        tojid,
                        msg.body,
                    )
                )

    class ReceiveOffers(CyclicBehaviour):
        async def run(self):
            try:
                # print("[{}] ReceiveOffers beh running".format(self.agent.name))
                msg = await self.receive(
                    timeout=300
                )  # wait for a message for 300 seconds
                if msg:
                    if msg.get_metadata("language") == "json":
                        msg_json = json.loads(msg.body)

                        self.agent.agentsAns.append(msg_json["device"])
                        #                        print("AO, otrzymano: {}".format(msg_json))
                        for wpk in msg_json["workpoint"]:
                            if wpk != "Datetime":
                                self.agent.offers_list.insert(
                                    1, wpk, msg_json["workpoint"][wpk]
                                )

                        for fck in msg_json["forecast"]:
                            if fck != "Datetime":
                                self.agent.forecast.insert(
                                    1, fck, msg_json["forecast"][fck]
                                )

                        for pk in msg_json["prices"]["flow"]:
                            self.agent.flow.append(pk)
                        for pk in msg_json["prices"]["role"]:
                            self.agent.role.append(pk)
                        for pk in msg_json["prices"]["energy"]:
                            self.agent.energy.append(pk)
                        for pk in msg_json["prices"]["price"]:
                            self.agent.price.append(pk)
                        for pk in msg_json["prices"]["device"]:
                            self.agent.device.append(pk)
                        for pk in msg_json["bounds"]["Unnamed: 0"]:
                            self.agent.en.append(pk)
                        for pk in msg_json["bounds"]["min"]:
                            self.agent.min.append(pk)
                        for pk in msg_json["bounds"]["max"]:
                            self.agent.max.append(pk)
                    else:
                        raise TypeError

                    if len(self.agent.agentsAns) == len(self.agent.auctionee_list):
                        self.kill()

                else:
                    print(
                        "[{}] ReceiveOffers: did not received any message after 10 seconds".format(
                            self.agent.name
                        )
                    )
                    self.kill()
            except Exception:
                print(traceback.format_exc())  # This line is for getting traceback.
                print(sys.exc_info()[2])  # This line is getting for the error type.

        async def on_end(self):
            self.agent.bounds = pd.DataFrame(
                {"min": self.agent.min, "max": self.agent.max}, index=self.agent.en
            )
            #', 'role', 'energy', 'price', 'device'
            self.agent.roles = pd.DataFrame(
                {
                    "flow": self.agent.flow,
                    "role": self.agent.role,
                    "energy": self.agent.energy,
                    "price": self.agent.price,
                    "device": self.agent.device,
                }
            )
            cl = self.agent.Clear()
            self.agent.add_behaviour(cl)

    class Clear(OneShotBehaviour):
        async def run(self):
            print("[{}]Clear beh running".format(self.agent.name))
            # insert code for clearing the offers

            (state_comp_frame, blocked_devs, res_supp_devs, wp) = (
                await self.agent.balance()
            )
            self.agent.output_frame = self.agent.offers_list.copy()

            wanted_date = self.agent.datetime
            forecast_date = str(
                pd.to_datetime(self.agent.datetime) - Timedelta("15min")
            )

            self.agent.offers_list.loc[self.agent.datetime, "SOC_Ep"] = (
                state_comp_frame.loc["new", "SOC_Ep"]
            )
            self.agent.offers_list.loc[self.agent.datetime, "SOC"] = (
                state_comp_frame.loc["new", "SOC"]
            )

            fcst = self.agent.forecast.copy()
            fcst["Datetime"] = self.agent.fcst_date  # check!!!!!

            soc_data = pd.DataFrame(
                self.agent.forecast.loc[0, ["Datetime", "SOC", "SOC_Ep"]]
            ).T
            out = merge_data(state_comp_frame, fcst, soc_data)
            self.agent.new_data_dict, self.agent.new_out_devs = reconstruct(
                out, blocked_devs, res_supp_devs, wp
            )

            print("1merge")
            print(state_comp_frame)

            print("2merge")
            print(fcst)

            print("3merge")
            print(soc_data)

            print("OUT")
            print(out)

            print("new data dict")
            print(self.agent.new_data_dict)

            print("new out devs")
            print(self.agent.new_out_devs)

            sci = self.agent.SendClearingInfo()
            self.agent.add_behaviour(sci)

    class SendClearingInfo(OneShotBehaviour):
        async def run(self):
            for curr_agent in self.agent.auctionee_list:
                short_name = curr_agent.split("_")[0]
                if short_name in self.agent.new_out_devs:
                    tojid = f"{curr_agent}@{DEFAULT_HOST}"
                    # Instantiate the message
                    msg = Message(to=tojid)
                    msg.set_metadata("performative", "inform")
                    msg.set_metadata("sender", self.agent.name)
                    msg.body = dumps(self.agent.new_out_devs[short_name])

                    await self.send(msg)
                    print(
                        "send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: Auctionee".format(
                            msg.get_metadata("performative"),
                            self.agent.name,
                            tojid,
                            msg.body,
                        )
                    )

            self.agent.datetime = str(
                pd.to_datetime(self.agent.datetime) + Timedelta("{}min".format(PERIOD))
            )
