from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, TimeoutBehaviour, PeriodicBehaviour, CyclicBehaviour
from spade.message import Message
from spade.template import Template
import time
import datetime
import json

DEFAULT_HOST = "server_hello"

class Predictor(Agent):
    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        
    async def setup(self):
        print("[{}] started".format(self.name))
        wfr = self.WaitForPredictOrder()
        self.add_behaviour(wfr)

    class WaitForPredictOrder(CyclicBehaviour):
        async def run(self):
            # print("[{}]WaitForRequest beh running".format(self.agent.name))
            msg = await self.receive(timeout=1)  # wait for a message for 1 seconds
            if msg:
                # [ProvidePrediction] from DeviceManager
                #print("rec:  from:[{}] to: [{}] body: [{}]".format(msg.get_metadata("sender"), msg.to, msg.body))
                tojid = msg.get_metadata("sender")
                msg_rply = Message(to=f"{tojid}@{DEFAULT_HOST}")
                msg_rply.set_metadata("performative", "inform")
                msg_rply.set_metadata("sender", self.agent.name)
                msg_rply.set_metadata("language", "json")

                # Calculate prediction here...
                # and put it into the message body
                msg_rply.body = json.dumps({'2024-08-06T10:00:00': [121, 100, 410, 430, 200, 201]})

                await self.send(msg)
                print("send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: DeviceManager".format(msg_rply.get_metadata("performative"), self.agent.name, tojid, msg_rply.body))
    
        