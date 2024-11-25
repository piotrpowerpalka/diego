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
DT = "2024-01-31 00:30:00"

class DummyBalancer(Agent):
    datet = DT
    devs = {}
    

    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        print("1...")
        self.inp, self.bounds, self.roles = read_data()
        print("10...")
        forecast_date = str(pd.to_datetime(DT) - Timedelta('15min'))
        currdate = str(self.datet)
        print("fd = {}, cd = {}".format(forecast_date, currdate))
        self.forecast = self.inp[self.inp['Datetime'] == forecast_date]
        self.offers_list = self.inp[self.inp['Datetime'] == currdate]
        
    async def setup(self):
        print("Agent {} started".format(self.name))

        c = self.Clear()
        self.add_behaviour(c)

    class Clear(OneShotBehaviour):
        async def run(self):
            # insert code for clearing the offers
            (state_comp_frame, blocked_devs, res_supp_devs, wp) = self.agent.balance()
            
            self.agent.output_frame = self.agent.inp.copy()

            wanted_date = DT
            print(type(DT))
            print(type(self.agent.inp[self.agent.inp['Datetime'] == wanted_date]))
            print(self.agent.inp[self.agent.inp['Datetime'] == wanted_date])
            wanted_ind = self.agent.inp[self.agent.inp['Datetime'] == wanted_date].index.values[0]

            
            self.agent.inp.loc[DT, 'SOC_Ep'] = state_comp_frame.loc['new', 'SOC_Ep']
            self.agent.inp.loc[DT, 'SOC']    = state_comp_frame.loc['new', 'SOC']



#            out = merge_data(
#                state_comp_frame,
#                pd.DataFrame(self.agent.output_frame.loc[wanted_ind-1, :]).T,
#                pd.DataFrame(self.agent.inp.loc[wanted_ind-1, ['Datetime', 'SOC', 'SOC_Ep']]).T
#                                )

            out = merge_data(
                state_comp_frame,
                self.agent.forecast,
                pd.DataFrame(self.agent.inp.loc[wanted_ind-1, ['Datetime', 'SOC', 'SOC_Ep']]).T
                                )

            print("SOC")
            print(pd.DataFrame(self.agent.inp.loc[wanted_ind-1, ['Datetime', 'SOC', 'SOC_Ep']]).T)
            #print(pd.DataFrame(self.agent.forecast[wanted_ind-1, ['Datetime', 'SOC', 'SOC_Ep']]))
            

            new_data_dict, new_out_devs = reconstruct(out, blocked_devs, res_supp_devs, wp)


    def balance(self):
        print("self offers list {}".format(self.offers_list))
        print(self.forecast)
        print(self.bounds)
        print(self.roles)

        per_balancer = Balancer(self.offers_list, self.bounds, self.roles, self.forecast)
        per_balancer.calc_fix_dem()
        (old_states, Ems_new_obs, Ems_new_pred, en_deltas,
        wp, autocons, tgs, blocked_devs, res_supp_devs) = per_balancer.balancing()

        num_cols_mask1 = ~Ems_new_pred.columns.str.contains("Datetime")
        num_cols_mask2 = ~old_states.columns.str.contains("Datetime")
        Ems_new_pred.loc[:, num_cols_mask1] = Ems_new_pred.loc[:, num_cols_mask1].astype(float)
        old_states.loc[:, num_cols_mask2] = old_states.loc[:, num_cols_mask2].astype(float)
        Ems_new_pred['Datetime'] = pd.to_datetime(Ems_new_pred['Datetime']) 
        old_states['Datetime'] = pd.to_datetime(old_states['Datetime'])        
        
        state_comp_frame = pd.concat([old_states, Ems_new_pred,  Ems_new_pred-old_states])
        state_comp_frame.index = ['old', 'new', 'diff']

        state_comp_frame['tg'] = [tgs['old'], tgs['new'], tgs['new']-tgs['old']]
        for col in ['Ep', 'Eq']:
            state_comp_frame['pv_'+col+'_auto'] = [autocons['old_pv_'+col+'_auto'].values[0],
                                                autocons['pv_'+col+'_auto'].values[0],
                                                (autocons['pv_'+col+'_auto'] - autocons['old_pv_'+col+'_auto']).values[0]]
        return state_comp_frame, blocked_devs, res_supp_devs, wp

    def merge_data(out_data, output_frame, inps):
        output_frame = output_frame.drop(columns=['SOC', 'SOC_Ep'])
        new_data = pd.DataFrame(out_data.loc['new', :]).T
        new_data = new_data.rename(columns={col: col + '_new' for col in new_data.columns if col != 'Datetime'})

        for col in ['MS_observ_Ep', 'MS_observ_Eq', 'tg', 'pv_Ep_auto', 'pv_Eq_auto']:
            new_data[col] = out_data.loc['old', col]

        new_data = new_data.reset_index(drop=True)

        output_frame = output_frame.merge(inps, how='left', on=['Datetime'])
        output_frame = output_frame.merge(new_data, how='left', on=['Datetime'])
        output_frame['fcast_date'] = output_frame['Datetime']
        output_frame['Datetime'] += pd.Timedelta('15min')

        field_list1 = [field + en for field in ['MS_observ_', 'pv_', 'eh_', 'evcs_'] for en in ['Ep', 'Eq']]
        field_list2 = ['SOC_Ep', 'inv1_Eq', 'pv_Ep_auto', 'pv_Eq_auto', 'tg']
        field_list = field_list1 + field_list2
        for col in field_list:
            output_frame['del_' + col] = output_frame[col + '_new'] - output_frame[col]

        return output_frame.copy()