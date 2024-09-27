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

class Predictor(Agent):
    inp = 0
    limits = 0
    roles = 0
    output_frame = 0
    prefix = ""

    def __init__(self, jid: str, password: str, prefix: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self.prefix = prefix
        
    async def setup(self):
        print("[{}] started".format(self.name))
        wfr = self.WaitForPredictOrder()
        self.add_behaviour(wfr)

    ''' funkcja getPrediction - do przepisania przez Electrum'''
    def getPrediction(self, datetime):
        # read data from xlsx - to substitute
        self.inp, self.limits, self.roles = read_input_data(self.prefix+"_P", self.prefix+"_Q")
        # Calculate prediction here...
        wanted_date = pd.to_datetime(datetime)
        wanted_ind = self.inp[self.inp['Datetime'] == datetime]
#        row = self.inp.loc[wanted_ind, :]
#        act_time = row.loc['Datetime']
#        print("acttime: {}".format(act_time) )

#        forecast = self.inp[self.inp['Datetime'] == (pd.to_datetime(act_time) - Timedelta('15min'))]
#        return json.dumps({DATETIME: [forecast[self.name + "_P"], forecast[self.name + "_Q"]]})
        return {datetime: [wanted_ind.iat[0, 1], wanted_ind.iat[0, 2] ]}


    class WaitForPredictOrder(CyclicBehaviour):
        async def run(self):
            
            # print("[{}]WaitForRequest beh running".format(self.agent.name))
            msg = await self.receive(timeout=10)  # wait for a message for 1 seconds
            if msg:
                msg_json = json.loads(msg.body)
                datetime = msg_json["timestamp"]
                print("[{}] datetime: {}".format(self.agent.name, datetime))

                # [ProvidePrediction] from DeviceManager
                forecast = self.agent.getPrediction(datetime)
            
                tojid = msg.get_metadata("sender")
                msg_rply = Message(to=f"{tojid}@{DEFAULT_HOST}")
                msg_rply.set_metadata("performative", "inform")
                msg_rply.set_metadata("sender", self.agent.name)
                msg_rply.set_metadata("language", "json")
                
                # and put it into the message body
                msg_rply.body = json.dumps(forecast)

                await self.send(msg_rply)
                print("send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: DeviceManager".format(msg_rply.get_metadata("performative"), self.agent.name, tojid, msg_rply.body))

    

        