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
DT = "2024-01-02 00:00:00"

class AuctionOperator(Agent):
    datetime = DT
    

    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        #self.auctionee_list = self.config['auctionees']
        self.auctionee_list = ['pv_auctionee', 'bystar1_auctionee', 'bysprint_auctionee']

        self.offers_list = pd.DataFrame()
        self.roles       = pd.DataFrame(columns=['flow', 'role', 'energy', 'price', 'device'])
        self.forecast    = pd.DataFrame()


    async def setup(self):
        print("Agent {} started".format(self.name))

        start_at1 = datetime.datetime.now()
        cfp = self.CallForProposal(period=60, start_at=start_at1)
        self.add_behaviour(cfp)

    def balance(drow, limits, roles, forecast):
        per_balancer = Balancer(drow, limits, roles, forecast)
        per_balancer.calc_fix_dem()
        (old_states, Ems_new_obs, Ems_new_pred, en_deltas,
        wp, autocons, tgs, blocked_devs, res_supp_devs) = per_balancer.balancing()

        state_comp_frame = pd.concat([old_states, Ems_new_pred,  Ems_new_pred-old_states])
        state_comp_frame.index = ['old', 'new', 'diff']

        state_comp_frame['tg'] = [tgs['old'], tgs['new'], tgs['new']-tgs['old']]
        for col in ['Ep', 'Eq']:
            state_comp_frame['pv_'+col+'_auto'] = [autocons['old_pv_'+col+'_auto'].values[0],
                                                autocons['pv_'+col+'_auto'].values[0],
                                                (autocons['pv_'+col+'_auto'] - autocons['old_pv_'+col+'_auto']).values[0]]

        return state_comp_frame, blocked_devs, res_supp_devs, wp

    class CallForProposal(PeriodicBehaviour):
        async def run(self):
#            print("[{}] CallForProposal beh running".format(self.agent.name))
            
            # behaviour ReceiveOffers added before sending offers, to avoid missing offers
            ro = self.agent.ReceiveOffers()
            self.agent.add_behaviour(ro)

            self.agent.offers_list = pd.DataFrame(data={'Datetime': [self.agent.datetime]})

            for curr_agent in self.agent.auctionee_list:

                tojid = f"{curr_agent}@{DEFAULT_HOST}"
                # Instantiate the message
                msg = Message(to=tojid)
                msg.set_metadata("performative", "CFP")
                msg.set_metadata("language", "json")
                msg.set_metadata("sender", self.agent.name)
                msg.body = json.dumps({"timestamp": self.agent.datetime})

                await self.send(msg)
                print("send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: Auctionee".format(msg.get_metadata("performative"), self.agent.name, tojid, msg.body))

    
    class ReceiveOffers(CyclicBehaviour):
        async def run(self):
            # print("[{}] ReceiveOffers beh running".format(self.agent.name))
            msg = await self.receive(timeout=20)  # wait for a message for 300 seconds
            if msg:
#                print("[{}] Message received with content: {}".format(self.agent.jid, msg.body))
                if (msg.get_metadata("language") == "json"):
                    msg_json = json.loads(msg.body)
                    print("AO, otrzymano: {}".format(msg_json))

                    
                    self.agent.offers_list.insert(1, msg_json["device"] + "_P", msg_json["active_power"]["value"])
                    self.agent.offers_list.insert(1, msg_json["device"] + "_Q", msg_json["reactive_power"]["value"])

                    self.agent.roles.loc[-1] = [msg_json["device"] + "_Ep", msg_json["active_power"]["role"], 'Ep', msg_json["active_power"]['price'], msg_json["device"]]
                    self.agent.roles.loc[-1] = [msg_json["device"] + "_Eq", msg_json["reactive_power"]["role"], 'Eq', msg_json["reactive_power"]['price'], msg_json["device"]]
                

                    print("AO offers list: {}".format(self.agent.offers_list))
                    print("AO roles list: {}".format(self.agent.roles))
                    
                    # self.agent.offers_list.append(json.loads(msg.body))

                else:
                    raise TypeError 

                if (len(self.agent.offers_list) == len(self.agent.auctionee_list)):
                    self.kill()

            else:
                print("[{}] ReceiveOffers: did not received any message after 10 seconds".format(self.agent.name))
                self.kill()
            
        async def on_end(self):
            cl = self.agent.Clear()
            self.agent.add_behaviour(cl)


    class Clear(OneShotBehaviour):
        async def run(self):
            print("[{}]Clear beh running".format(self.agent.name))
            # insert code for clearing the offers

            (state_comp_frame, blocked_devs, res_supp_devs, wp) = balance(self.offers_list, self.roles. self.forecast)

            sci = self.agent.SendClearingInfo()
            self.agent.add_behaviour(sci)

    
    class SendClearingInfo(OneShotBehaviour):
        async def run(self):
            for curr_agent in self.agent.auctionee_list:

                tojid = f"{curr_agent}@{DEFAULT_HOST}"
                # Instantiate the message
                msg = Message(to=tojid)
                msg.set_metadata("performative", "inform")
                msg.set_metadata("sender", self.agent.name)
                

                await self.send(msg)
                print("send: prf: [{}] from:[{}] to:[{}] body:[{}] tgt: Auctionee".format(msg.get_metadata("performative"), self.agent.name, tojid, msg.body))




            

