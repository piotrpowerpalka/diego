from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, TimeoutBehaviour, PeriodicBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import time
import datetime
import json
from functions import *
from json import dumps
from pandas import Timedelta

DEFAULT_HOST = "server_hello"

class DeviceManager(Agent):
    def __init__(self, jid: str, password: str, config: dict, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.config = config
        self.predictor = self.config["predictor"]
        self.auctionee = self.config["auctionee"]
        
    async def setup(self):
        print("Agent {} started".format(self.name))
        wfr = self.WaitForRequest()
        self.add_behaviour(wfr)

    class WaitForRequest(CyclicBehaviour):
        async def run(self):
            # print("[{}]WaitForRequest beh running".format(self.agent.name))
            msg = await self.receive(timeout=10)  # wait for a message for 1 seconds
            if msg:
#                print("[{}] Message received with content: {}".format(self.agent.name, msg.body))
                if msg.get_metadata("performative") == "query":
                    # [GetWorkingPoint] - from Auctionee - send it to Predictor
                    #print("rec:  from:[{}] to: [{}] body: [{}]".format(msg.get_metadata("sender"), msg.to, msg.body))

                    tojid = self.agent.predictor
                    msg_rply = Message(to=f"{tojid}@{DEFAULT_HOST}")
                    msg_rply.set_metadata("performative", "query")
                    msg_rply.set_metadata("sender", self.agent.name)
                    msg_rply.set_metadata("language", "json")

                    msg_rply.body = msg.body

                    await self.send(msg_rply)
                    print("send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: Predictor".format(msg_rply.get_metadata("performative"), self.agent.name, tojid, msg_rply.body))

                elif msg.get_metadata("performative") == "inform":
                    # [GetPrediction] - from predictor, send it to Auctionee
#                    print("rec:  from:[{}] to: [{}] body: [{}]".format(msg_rply.get_metadata("sender"), msg.to, msg.body))

                    tojid = self.agent.auctionee
                    msg_rply = Message(to=f"{tojid}@{DEFAULT_HOST}")
                    msg_rply.set_metadata("performative", "inform")
                    msg_rply.set_metadata("sender", self.agent.name)
                    msg_rply.set_metadata("language", "json")

                    msg_rply.body = msg.body

                    await self.send(msg_rply)
                    print("send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: Auctionee".format(msg_rply.get_metadata("performative"), self.agent.name, tojid, msg_rply.body))

        


                
        