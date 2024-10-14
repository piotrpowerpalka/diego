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

class AuctionOperator(Agent):
    datetime = DT
    

    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        #self.auctionee_list = self.config['auctionees']
        self.auctionee_list = ['pv_auctionee', 'bysprint_auctionee', 'bystar1_auctionee', 'bystar2_auctionee', 'mazak_auctionee', 'eh_auctionee', 'inv1_auctionee', 'inv2_auctionee', 'sg1_auctionee', 'sg2_auctionee', 'sg3_auctionee', 'sg4_auctionee', 'evcs_auctionee', 'soc_auctionee', 'sg1prim_auctionee', 'ms_auctionee', 'network_auctionee']

        self.offers_list = pd.DataFrame()
        self.forecast    = pd.DataFrame()
        self.roles       = pd.DataFrame(columns=['flow', 'role', 'energy', 'price', 'device'])
        self.bounds      = pd.DataFrame(columns=["energy", "min", "max"])
        self.agentsAns   = []        

    async def setup(self):
        print("Agent {} started".format(self.name))

        start_at1 = datetime.datetime.now()
        cfp = self.CallForProposal(period=600, start_at=start_at1)
        self.add_behaviour(cfp)

    async def balance(self):
        print("balancing 0111")
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

    class CallForProposal(PeriodicBehaviour):
        async def run(self):
#            print("[{}] CallForProposal beh running".format(self.agent.name))
            
            # behaviour ReceiveOffers added before sending offers, to avoid missing offers
            ro = self.agent.ReceiveOffers()
            self.agent.add_behaviour(ro)

            self.agent.offers_list = pd.DataFrame(data={'Datetime': [self.agent.datetime]})
            self.agent.forecast    = pd.DataFrame(data={'Datetime': [self.agent.datetime]})

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
            msg = await self.receive(timeout=300)  # wait for a message for 300 seconds
            if msg:
#                print("[{}] Message received with content: {}".format(self.agent.jid, msg.body))
                if (msg.get_metadata("language") == "json"):
                    msg_json = json.loads(msg.body)

                    self.agent.agentsAns.append(msg_json["device"])

                    print("AO, otrzymano: {}".format(msg_json))

                    for wpk in msg_json["workpoint"]:
                        if wpk != 'Datetime':
                            self.agent.offers_list.insert(1, wpk, msg_json["workpoint"][wpk])

                    for fck in msg_json["forecast"]:
                        if fck != 'Datetime':
                            self.agent.forecast.insert(1, fck, msg_json["forecast"][fck])

                    flow = []
                    role = []
                    energy = []
                    price = []
                    device = []

                    for pk in msg_json["prices"]["flow"]:   flow.append(pk)
                    for pk in msg_json["prices"]["role"]:   role.append(pk)
                    for pk in msg_json["prices"]["energy"]: energy.append(pk)
                    for pk in msg_json["prices"]["price"]:  price.append(pk)
                    for pk in msg_json["prices"]["device"]: device.append(pk)

                    for i in range(len(flow)):
                        self.agent.roles.loc[self.agent.roles.shape[0]] = [flow[i], role[i], energy[i], price[i], device[i]]

                    en = []
                    min = []
                    max = []
                    
                    for pk in msg_json["bounds"]["Unnamed: 0"]:   en.append(pk)
                    for pk in msg_json["bounds"]["min"]:          min.append(pk)
                    for pk in msg_json["bounds"]["max"]:          max.append(pk)

                    for i in range(len(en)):
                        self.agent.bounds.loc[self.agent.bounds.shape[0]] = [en[i], min[i], max[i]]

                    #print("AO offers list: {}".format(self.agent.offers_list))
                    #print("AO roles  list: {}".format(self.agent.roles))
                    #print("AO bounds list: {}".format(self.agent.bounds))
                    #print("AO forecast list: {}".format(self.agent.forecast))

                else:
                    raise TypeError 

                if (len(self.agent.agentsAns) == len(self.agent.auctionee_list)):
                    print("balancing 000")
                    self.kill()

            else:
                print("[{}] ReceiveOffers: did not received any message after 10 seconds".format(self.agent.name))
                self.kill()
            
        async def on_end(self):
#            cl = self.agent.Clear()
#            self.agent.add_behaviour(cl)
            print("[{}]Clear beh running".format(self.agent.name))
            (state_comp_frame, blocked_devs, res_supp_devs, wp) = await self.agent.balance()

    class Clear(OneShotBehaviour):
        async def run(self):
            print("[{}]Clear beh running".format(self.agent.name))
            # insert code for clearing the offers

            (state_comp_frame, blocked_devs, res_supp_devs, wp) = self.agent.balance(self.agent.offers_list, self.agent.bounds, self.agent.roles. self.agent.forecast)

            sci = self.agent.SendClearingInfo()
            self.agent.add_behaviour(sci)

            # clear data after balancing
            self.offers_list = pd.DataFrame()
            self.forecast    = pd.DataFrame()
            self.roles       = pd.DataFrame(columns=['flow', 'role', 'energy', 'price', 'device'])
            self.bounds      = pd.DataFrame(columns=["energy", "min", "max"])
    
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




            

