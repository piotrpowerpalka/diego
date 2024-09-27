import pandas as pd
from pandas import Timedelta, Timestamp
from numpy import sqrt, nan


class Balancer:

    def __init__(self, drow, limits, roles, forecast):
        if isinstance(drow, pd.DataFrame):
            self.date = Timestamp(drow['Datetime'].values[0])
        elif isinstance(drow, pd.Series):
            self.date = pd.DataFrame(drow).loc['Datetime'].values[0]

        self.period = int((self.date - self.date.replace(hour=0, minute=0, second=0))/Timedelta('15min'))
        self.during_peak = {period: False if (period < 24) or (period > 56) else True for period in range(96)}
        self.num_ep = 8  # number_of_export_periods
        self.bess_should_export = {period: True if 32 <= period <= 72 else False for period in range(96)}

        self.unc_dev_Eq_oper = {device: False for device in roles['device'].unique()}
        self.lim = limits.copy()
        # self.pred = forecast.copy().reset_index(drop=True)

        self.roles = roles.copy()
        self.real_data = drow.copy().reset_index(drop=True)

        self.pred = forecast.copy().reset_index(drop=True)

        self.pred['MS_observ_Ep'] = self.pred.loc[:, ['MS_Ep', 'pv_Ep']].sum(axis=1)
        self.pred.loc[:, 'MS_observ_Eq'] = self.pred.loc[:, ['MS_Eq', 'pv_Eq']].sum(axis=1)
        self.initial_state = self.pred.copy()
        self.avail_pv_energy = self.initial_state['MS_Ep'].values[0] + self.pred['pv_Ep'].values[0]

        self.curr_balance_Ep = None
        self.curr_balance_Eq = None

        self.work_points = {}
        self.dev_Eq_blocked = {'eh': False, 'evcs': False}
        self.dev_res_suppl = {'eh': False, 'evcs': False}
        self.to_turn_off = []

        self.Ep_offers = roles[roles['energy'] == 'Ep'].sort_values(by='price')
        self.Eq_offers = roles[roles['energy'] == 'Eq'].sort_values(by='price')

        self.dev_Energies = {}
        self.pv_Ep_auto_cons = None
        self.pv_Eq_auto_cons = None
        self.bess_full_state = self.get_full_state()
        self.energy_deltas = {}
        self.Ems_new = {}
        self.Ems_new_obs = {}

        self.old_pv_Ep_auto = None
        self.old_pv_Eq_auto = None
        self.auto_cons = None
        self.tg_old = None
        self.tg_new = None
        self.init_wp = None

        self.wps_frame = None
        self.to_turn_off = []

        self.calc_old_autocons()
        self.fill_init_wp()

    def fill_init_wp(self):
        self.init_wp = self.initial_state.filter(regex='_P|_Q').reset_index(drop=True)

        for col in ['MS_observ_P', 'MS_observ_Q']:
            energy = col.replace("_P", '_Ep').replace("_Q", '_Eq')
            self.init_wp[col] = self.initial_state[energy] * 4

    def calc_old_autocons(self):
        if self.initial_state['MS_Ep'].values[0] != 0.000:
            self.old_pv_Ep_auto = -(self.initial_state['pv_Ep'] / self.initial_state['MS_Ep']).values[0]
        else:
            self.old_pv_Ep_auto = nan

        if self.initial_state['MS_Eq'].values[0] != 0.000:
            self.old_pv_Eq_auto = -(self.initial_state['pv_Eq'] / self.initial_state['MS_Eq']).values[0]
        else:
            self.old_pv_Eq_auto = nan

    def get_full_state(self):
        if self.date < Timestamp(2024, 6, 24, 0, 15):
            max_capacity = 177.6
        else:
            max_capacity = 263

        return max_capacity

    def calc_fix_dem(self):

        self.curr_balance_Ep = self.pred['MS_Ep'].values[0]
        self.curr_balance_Eq = self.pred['MS_Eq'].values[0]

    def make_autocons_df(self):
        self.auto_cons = pd.DataFrame(data=[self.pv_Ep_auto_cons, self.pv_Eq_auto_cons],
                                      index=['pv_Ep_auto', 'pv_Eq_auto']).T

        self.auto_cons['old_pv_Ep_auto'] = self.old_pv_Ep_auto
        self.auto_cons['old_pv_Eq_auto'] = self.old_pv_Eq_auto

    def calculate_tgs(self):
        if self.initial_state['MS_observ_Ep'].values[0] != 0:
            self.tg_old = (self.initial_state['MS_observ_Eq'] / self.initial_state['MS_observ_Ep']).values[0]
        else:
            self.tg_old = nan

        if self.Ems_new_obs['Ep'].values[0] != 0:
            self.tg_new = (self.Ems_new_obs['Eq'] / self.Ems_new_obs['Ep']).values[0]
        else:
            self.tg_new = nan

        return {'old': self.tg_old, 'new': self.tg_new}

    def scale_wp(self):
        ms_cols = ['MS_observ_P', 'MS_observ_Q']
        for col in self.initial_state.filter(regex='_P|_Q').columns.tolist()+ms_cols:
            #if col not in self.work_points:
            energy = col.replace("_P", '_Ep').replace("_Q", '_Eq')
            self.work_points[col] = self.pred[energy]*4
            self.pred[col] = self.pred[energy]*4

        col = 'inv1_P'
        energy = 'SOC_Ep'
        self.work_points[col] = self.pred[energy] * 4

        self.work_points = pd.DataFrame(data=self.work_points.values(), index=list(self.work_points.keys())).T
        self.wps_frame = pd.concat([self.init_wp, self.work_points, self.work_points-self.init_wp])
        self.wps_frame.index = ['old', 'new', 'diff']

    def update_blocks(self):
        self.dev_Eq_blocked.update({laser: False
                                    for laser in ['bystar1', 'bysprint', ' bystar2', 'mazak']})

        if len(self.to_turn_off) > 0:
            self.dev_Eq_blocked.update({laser: True for laser in self.to_turn_off})

    def balancing(self):

        while True:
            bess_import = 0
            pv_res = 0
            pv_to_bess_export = 0

            # active energy balancing
            for ind, offer in self.Ep_offers.iterrows():

                if offer['device'] == 'pv':
                    if self.avail_pv_energy < 0:
                        # overwrite load/discharge timetable
                        self.bess_should_export[self.period] = False
                        # give bess all energy pv can give

                        pv_to_bess_export = min(abs(self.avail_pv_energy),
                                                    12.5,
                                                    self.bess_full_state - self.pred['SOC_Ep'].values[0])

                        self.pred['SOC_Ep'] += pv_to_bess_export
                        self.pred['SOC'] = (self.pred['SOC_Ep']/self.bess_full_state)*100

                        # find residual Ep_pv - expected with minus (-)
                        pv_res = self.pred['pv_Ep'].values[0] + pv_to_bess_export
                        self.avail_pv_energy += pv_to_bess_export
                    else:
                        if self.pred['pv_Ep'].values[0] > 0:
                            # if PV imports energy add it to the rest of demand
                            self.curr_balance_Ep += self.pred['pv_Ep'].values[0]

                elif offer['device'] == 'inv1':
                    if self.bess_should_export[self.period]:
                        # bess has to keep at least 20 % of capacity
                        # and cannot exchange more than 12.5 kWh for each step
                        contr_bess_energy = self.pred['SOC_Ep'].values[0] - self.bess_full_state*0.2

                        if contr_bess_energy > 0:
                            bess_export = min(contr_bess_energy / self.num_ep, 12.5)
                            self.pred['SOC_Ep'] -= bess_export
                            self.pred['SOC'] = (self.pred['SOC_Ep'] / self.bess_full_state) * 100
                            self.curr_balance_Ep -= bess_export

                            if self.curr_balance_Ep < 0:
                                # in case of oversupply:
                                self.pred['SOC_Ep'] += abs(self.curr_balance_Ep)
                                self.pred['SOC'] = (self.pred['SOC_Ep'] / self.bess_full_state) * 100
                                self.curr_balance_Ep = 0
                        # else:
                            # print(self.date, '-> bess capacity <20%, not included in export')
                    else:
                        if self.pred['pv_Ep'].values[0] >= 0:
                            # if PV not generating get some energy from network
                            bess_import = 12.5*0.5
                            self.pred['SOC_Ep'] += min(bess_import,
                                                       self.bess_full_state - bess_import,
                                                       self.bess_full_state - self.pred['SOC_Ep'].values[0])

                            self.pred['SOC'] = (self.pred['SOC_Ep'] / self.bess_full_state) * 100
                            self.curr_balance_Ep += bess_import
                    self.dev_Energies['SOC_Ep'] = self.pred['SOC_Ep'].values[0]

                elif offer['device'] in ['eh', 'evcs']:
                    if not self.dev_Eq_blocked[offer['device']]:
                        dev_power_max = self.lim.loc[offer['device'] + '_P', 'max']
                        dev_energy_max = dev_power_max * 0.25

                        if ((self.pred[offer['device']+'_Ep'].values[0] > 0)
                                and (self.avail_pv_energy <= -1*dev_energy_max)):

                            self.work_points[offer['device']+'_P'] = dev_power_max
                            self.dev_Energies[offer['device']+'_Ep'] = dev_energy_max
                            # include device in Eq balancing
                            self.unc_dev_Eq_oper[offer['device']] = True
                            pv_res += dev_energy_max
                            self.pred[offer['device'] + '_Ep'] = dev_energy_max
                            self.dev_res_suppl[offer['device']] = True

                        else:
                            # if cannt supply extra load from pv turn the load off
                            self.work_points[offer['device'] + '_P'] = 0
                            self.dev_Energies[offer['device'] + '_Ep'] = 0
                            self.pred[offer['device'] + '_Ep'] = 0

                            self.work_points[offer['device'] + '_Q'] = 0
                            self.dev_Energies[offer['device'] + '_Eq'] = 0
                            self.pred[offer['device'] + '_Eq'] = 0
                            self.unc_dev_Eq_oper[offer['device']] = False
                            self.dev_res_suppl[offer['device']] = False
                    else:
                        # if device was blocked unblock it after omitting it from active energy balance
                        # and marking that it should not be used for reactive balancing
                        # unblock device and do not include it in Eq balancing
                        self.dev_Eq_blocked[offer['device']] = False
                        self.unc_dev_Eq_oper[offer['device']] = False
                        self.dev_res_suppl[offer['device']] = False

                elif offer['device'] == 'network':
                    self.curr_balance_Ep += pv_res
                    pv_res = 0
                    # in case of oversupply
                    if self.curr_balance_Ep < 0:
                        pv_res = self.curr_balance_Ep
                        self.curr_balance_Ep = 0

                    self.dev_Energies['network_Ep'] = self.curr_balance_Ep

                    if pv_res < 0:
                        self.pred['pv_Ep'] -= pv_res
                        self.dev_Energies['pv_Ep'] = self.pred['pv_Ep'].values[0]
                        # find what fraction of initial energy forecast correscted pv energy is
                        # then use it to scale original working point
                        #scaler = self.pred['pv_Ep'].values[0] / self.initial_state['pv_Ep']
                        #self.work_points['pv_P'] = scaler * self.pred['pv_P'].values[0]

            # ########## bilansowanier energii biernej

            # check if reactive energy of eh/evcs should be added to balance
            for device, is_oper in self.unc_dev_Eq_oper.items():
                if device in ['evcs', 'eh'] and is_oper:
                    dev_Eq = self.lim.loc[device + '_Q', 'max'] * 0.25
                    self.pred[device + '_Eq'] = dev_Eq
                    self.curr_balance_Eq += dev_Eq

            # set to 0 before reactive power compensation
            self.pred['pv_Eq'] = 0
            self.pred['inv1_Eq'] = 0

            Eq_fields = ['inv1_Eq', 'evcs_Eq', 'eh_Eq', 'pv_Eq']
            Eq_state = (self.initial_state['MS_Eq']
                        - self.initial_state.loc[:, Eq_fields].sum(axis=1)
                        + self.pred.loc[:, Eq_fields].sum(axis=1)).values[0]

            Ep_fields = ['SOC_Ep', 'evcs_Ep', 'eh_Ep', 'pv_Ep']
            Ep_state = (self.initial_state['MS_Ep']
                        - self.initial_state.loc[:, Ep_fields].sum(axis=1)
                        + self.pred.loc[:, Ep_fields].sum(axis=1)).values[0]

            if Eq_state >= 0:
                if Ep_state != 0:
                    tg_phi_nat = Eq_state / Ep_state
                else:
                    tg_phi_nat = nan
                    #print(self.date, '-> Ep state 0 at non-0 Eq')

                Eqk = (Ep_state * (tg_phi_nat - 0.4))

                if Eqk >= 0:
                    for ind, offer in self.Eq_offers.iterrows():
                        if offer['device'] == 'pv':
                            tg_gr = 0.75  # tan(arccos(0.8))
                            Eq_pv_perm = -abs(self.pred['pv_Ep'].values[0] * tg_gr)

                            # get max avail. power inverter for work point on
                            Eq_pv = max(Eq_pv_perm, -Eqk)
                            self.pred['pv_Eq'] = Eq_pv
                            Eqk += Eq_pv
                            self.curr_balance_Eq += Eq_pv

                        elif offer['device'] == 'inv1':
                            Eq_bess_perm = 0
                            Emax = 50 * 0.25
                            Ep_bess = (self.pred['SOC_Ep'] - self.initial_state['SOC_Ep']).values[0]

                            if (Emax ** 2 - Ep_bess ** 2) < 0:
                                print((self.date, self.pred['SOC_Ep'].values[0], self.initial_state['SOC_Ep'].values[0]))
                            else:
                                Eq_bess_perm = sqrt(Emax ** 2 - Ep_bess ** 2)

                            #Eq_bess_perm = max(Eq_bess_perm, -12.5)
                            Eq_bess = min(Eq_bess_perm, -Eqk)
                            Eqk += Eq_bess
                            self.curr_balance_Eq += Eq_bess
                            self.pred['inv1_Eq'] = Eq_bess
                            self.dev_Energies['inv1_Eq'] = Eq_bess
                            self.work_points['inv1_Q'] = Eq_bess * 4

                        elif offer['device'] in ['evcs', 'eh']:
                            if Eqk > 0:
                                # if reactive energy cannot be supported from PV + bess
                                # for non-important device, then turn it off
                                # then reaclculate their 0-influence in nexti teration
                                # of balancing algorithm

                                # do this if device imports reactive energy and device is included in balance
                                if (self.pred[offer['device'] + '_Eq'].values[0] > 0) and (self.unc_dev_Eq_oper[offer['device']]):
                                    # correct Eqk not to turn off both devices each time
                                    Eqk -= self.lim.loc[offer['device'] + '_P', 'max'].values[0]

                                    # indicate that device is to be turned off
                                    self.work_points[offer['device'] + '_P'] = 0
                                    self.pred[offer['device'] + '_Ep'] = 0
                                    self.work_points[offer['device']+'_Q'] = 0
                                    self.pred[offer['device'] + '_Eq'] = 0

                                    self.dev_Eq_blocked[offer['device']] = True

                            else:
                                self.dev_Eq_blocked[offer['device']] = False

                        elif offer['device'] == 'network':
                            # what cannot be covered by pv+bess must be supplied from network
                            self.pred['network_Eq'] = self.curr_balance_Eq

            else:
                Eqk = Eq_state
                # 'pv'
                tg_gr = 0.75  # tan(arccos(0.8))
                Eq_pv_perm = abs(self.pred['pv_Ep'].values[0] * tg_gr)

                # get max avail. power inverter for work point on
                Eq_pv = min(Eq_pv_perm, abs(Eqk))
                self.pred['pv_Eq'] = Eq_pv
                self.dev_Energies['pv_Eq'] = Eq_pv
                self.work_points['pv_Q'] = Eq_pv * 4

                Eqk += Eq_pv
                self.curr_balance_Eq += Eq_pv

                # 'inv1'
                Eq_bess_perm = 0
                Emax = 50*0.25
                Ep_bess = (self.pred['SOC_Ep'] - self.initial_state['SOC_Ep']).values[0]

                if (Emax ** 2 - Ep_bess ** 2) < 0:
                    print((self.date, self.pred['SOC_Ep'].values[0], self.initial_state['SOC_Ep'].values[0]))
                else:
                    Eq_bess_perm = sqrt(Emax ** 2 - Ep_bess ** 2)

                Eq_bess_perm = min(Eq_bess_perm, 12.5)
                Eq_bess = min(Eq_bess_perm, - Eqk)
                Eqk += Eq_bess
                self.curr_balance_Eq += Eq_bess
                self.pred['inv1_Eq'] = Eq_bess
                self.dev_Energies['inv1_Eq'] = Eq_bess
                self.work_points['inv1_Q'] = Eq_bess * 4

                self.pred['network_Eq'] = Eqk

            if not self.dev_Eq_blocked['eh'] and not self.dev_Eq_blocked['evcs']:
                break

        if Eqk > 0:

            Eq_net_new = Eqk
            # send info to turn off lasers
            sort_lasers = self.pred.loc[:,
                          ['bystar1_Eq', 'bystar2_Eq', 'bysprint_Eq', 'mazak_Eq']
                          ].reset_index(drop=True).sort_values(by=0, axis=1, ascending=False)

            for laser, laser_Eq in sort_lasers.items():
                if laser_Eq.values[0] > 0:
                    self.to_turn_off.append(laser.replace('_Eq', ''))
                    Eq_net_new -= laser_Eq
                    Eq_net_new = Eq_net_new.values[0]
                    if Eq_net_new <= 0:
                        break

        elif (Eqk < 0) and (Eq_state < 0):

            Eq_net_new = Eqk
            # send info to turn off lasers
            sort_lasers = self.pred.loc[:,
                          ['bystar1_Eq', 'bystar2_Eq', 'bysprint_Eq', 'mazak_Eq']
                          ].reset_index(drop=True).sort_values(by=0, axis=1, ascending=True)

            for laser, laser_Eq in sort_lasers.items():
                if laser_Eq.values[0] < 0:
                    self.to_turn_off.append(laser.replace('_Eq', ''))
                    Eq_net_new += laser_Eq
                    Eq_net_new = Eq_net_new.values[0]
                    if Eq_net_new >= 0:
                        break

        # determine changes for objects that can be influenced
        delta_cols = ['SOC_Ep', 'inv1_Eq', 'eh_Ep', 'eh_Eq', 'evcs_Ep', 'evcs_Eq', 'pv_Ep', 'pv_Eq']
        for col in delta_cols:
            self.energy_deltas[col] = (self.pred[col] - self.initial_state[col]).values[0]

        for energy in ['Ep', 'Eq']:
            if energy == 'Ep':
                desired_col = 'SOC_'+energy
            else:
                desired_col = 'inv1_' + energy

            self.Ems_new[energy] = (self.pred['MS_' + energy] +
                                    self.energy_deltas[desired_col] +
                                    self.energy_deltas['eh_'+energy] +
                                    self.energy_deltas['evcs_'+energy] -
                                    min(self.energy_deltas['pv_'+energy], 0)
                                    ).values[0]

            self.Ems_new_obs[energy] = self.Ems_new[energy] + self.pred['pv_'+energy]

            self.pred['MS_observ_' + energy] = self.Ems_new_obs[energy]

            self.energy_deltas[energy] = (self.Ems_new_obs[energy] - self.pred['MS_observ_'+energy]).values[0]

        if self.Ems_new['Ep'] != 0:
            self.pv_Ep_auto_cons = -self.pred['pv_Ep'].values[0] / self.Ems_new['Ep']
        else:
            self.pv_Ep_auto_cons = nan

        if self.Ems_new['Eq'] != 0:
            self.pv_Eq_auto_cons = -self.pred['pv_Eq'].values[0] / self.Ems_new['Eq']
        else:
            self.pv_Eq_auto_cons = nan

        self.make_autocons_df()
        tg_dict = self.calculate_tgs()
        self.scale_wp()

        self.update_blocks()
        return (self.initial_state, self.Ems_new_obs, self.pred, self.energy_deltas, self.wps_frame, self.auto_cons,
                tg_dict, self.dev_Eq_blocked, self.dev_res_suppl)
