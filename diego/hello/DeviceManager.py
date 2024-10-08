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


    def getBounds(self):
        json_bounds = {}

        for c in range(self.bounds.shape[1]): # cols
            attr = []
            for r in range(self.bounds.shape[0]): # rows
                attr.append(str(self.bounds.iat[r,c]))
            json_bounds[self.bounds.columns[c]] = attr

        return json_bounds

    def getRoles(self):
        json_roles = {}

        for c in range(self.roles.shape[1]): # cols
            attr = []
            for r in range(self.roles.shape[0]): # rows
                attr.append(str(self.roles.iat[r,c]))
            json_roles[self.roles.columns[c]] = attr

        print(json_roles)

        return json_roles

    class WaitForRequest(CyclicBehaviour):
        async def run(self):
            # print("[{}]WaitForRequest beh running".format(self.agent.name))
            msg = await self.receive(timeout=120)  # wait for a message for 1 seconds
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

                    json_prices = self.agent.getRoles()
                    json_bounds = self.agent.getBounds()
                    
                    rply_body_json = {"device": body_json["device"], "workpoint": body_json["workpoint"], "forecast": body_json["forecast"], "prices": json_prices, "bounds": json_bounds}
                    
                    msg_rply.body = json.dumps(rply_body_json)

                    await self.send(msg_rply)
                    print("send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: Auctionee".format(msg_rply.get_metadata("performative"), self.agent.name, tojid, msg_rply.body))

        


                
        