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
        # read data from csv
        self.inp = pd.read_csv("input_data_{}.csv".format(self.prefix), sep=";")

    async def setup(self):
        print("[{}] started".format(self.name))
        wfr = self.WaitForPredictOrder()
        self.add_behaviour(wfr)

    ''' funkcja getPrediction - do przepisania przez Electrum'''
    def getPrediction(self, datetime):
        # read data from csv - to substitute
        # Calculate prediction here...
        forecast_date = str(pd.to_datetime(datetime) - Timedelta('15min'))
        workpoint  = self.inp[self.inp['Datetime'] == datetime]
        forecast   = self.inp[self.inp['Datetime'] == forecast_date]
        
        json_wp = {}        # json z punktem pracy
        json_fc = {}        # json z predykcją

        for r in range(1, workpoint.shape[1]):
            json_wp[workpoint.columns[r]] = str(workpoint.iat[0,r])

        for rf in range(1, forecast.shape[1]):
            json_fc[forecast.columns[rf]] = str(forecast.iat[0,rf])
        
        return {"device": self.prefix, "workpoint": json_wp, "forecast": json_fc}

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
    

    

        