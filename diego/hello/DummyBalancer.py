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
from classes import *


DEFAULT_HOST = "server_hello"
DT = "2024-01-02 00:00:00"

class DummyBalancer(Agent):
    datet = DT
    

    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)

        self.inp, self.bounds, self.roles = read_data()
        forecast_date = str(pd.to_datetime(DT) - Timedelta('15min'))
        currdate = str(self.datet)
        print("fd = {}, cd = {}".format(forecast_date, currdate))
        self.forecast   = self.inp[self.inp['Datetime'] == forecast_date]
        self.offers_list  = self.inp[self.inp['Datetime'] == currdate]
        
    async def setup(self):
        print("Agent {} started".format(self.name))

        c = self.Clear()
        self.add_behaviour(c)

    class Clear(OneShotBehaviour):
        async def run(self):
            print("[{}]Clear beh running".format(self.agent.name))
            # insert code for clearing the offers
            (state_comp_frame, blocked_devs, res_supp_devs, wp) = self.agent.balance()

    def balance(self):
        print(self.offers_list)
        print(self.forecast)
        print(self.bounds)
        print(self.roles)

        per_balancer = Balancer(self.offers_list, self.bounds, self.roles, self.forecast)
        per_balancer.calc_fix_dem()
        (old_states, Ems_new_obs, Ems_new_pred, en_deltas,
        wp, autocons, tgs, blocked_devs, res_supp_devs) = per_balancer.balancing()

        print("balancing 111")

        state_comp_frame = pd.concat([old_states, Ems_new_pred,  Ems_new_pred-old_states])
        state_comp_frame.index = ['old', 'new', 'diff']

        state_comp_frame['tg'] = [tgs['old'], tgs['new'], tgs['new']-tgs['old']]
        for col in ['Ep', 'Eq']:
            state_comp_frame['pv_'+col+'_auto'] = [autocons['old_pv_'+col+'_auto'].values[0],
                                                autocons['pv_'+col+'_auto'].values[0],
                                                (autocons['pv_'+col+'_auto'] - autocons['old_pv_'+col+'_auto']).values[0]]

        return state_comp_frame, blocked_devs, res_supp_devs, wp

