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
    def __init__(self, jid: str, password: str, prefix: str, config: dict, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.config = config
        self.prefix = prefix
        self.predictor = self.config["predictor"]
        self.auctionee = self.config["auctionee"]
        
        self.roles =  pd.read_csv("roles_{}.csv".format(self.prefix), sep=";")
        self.bounds = pd.read_csv("bounds_{}.csv".format(self.prefix), sep=";")
        
        
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

                    body_json = json.loads(msg.body)

                    print(self.agent.roles)
                    print(self.agent.bounds)

                    priceP = self.agent.roles.iat[0, 3]
                    priceQ = self.agent.roles.iat[1, 3]
                    roleP  = self.agent.roles.iat[0, 1]
                    roleQ  = self.agent.roles.iat[1, 1]
                    minP   = self.agent.bounds.iat[0, 1]
                    minQ   = self.agent.bounds.iat[1, 1]
                    maxP   = self.agent.bounds.iat[0, 2]
                    maxQ   = self.agent.bounds.iat[1, 2]
                    
                    
                    rply_body_json = {"device": body_json["device"], "date": body_json["date"],  "active_power": {"bounds": {"min": str(minP), "max": str(maxP)}, "value": body_json["P"], "price": str(priceP), "role": str(roleP)} , "reactive_power": {"bounds": {"min": str(minQ), "max": str(maxQ)}, "value": body_json["Q"], "price": str(priceQ), "role": str(roleQ)}}
                    
                    msg_rply.body = json.dumps(rply_body_json)

                    await self.send(msg_rply)
                    print("send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: Auctionee".format(msg_rply.get_metadata("performative"), self.agent.name, tojid, msg_rply.body))

        


                
        