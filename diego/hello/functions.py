import numpy as np
import pandas as pd
from pandas import read_csv, to_datetime
from classes import Balancer


def read_data():
    data = pd.read_csv('MAS_tests_input_data_red.csv', sep=";",  index_col=0)
    bounds = pd.read_csv('bounds.csv', sep=";", index_col=0)
    roles = pd.read_csv('roles.csv', sep=";", index_col=0)
    #### konwersja typów
    # data['Datetime'] = to_datetime(data['Datetime'])
    print("2...")
        
    data.iloc[:, 1:] = data.iloc[:, 1:].astype(float)

    print("3...")
        
    print(roles)
    print(bounds)
    print(data)

    print("4...")
        
    roles['price'] = roles['price'].astype(float)

    print("5...")
        

    for col in ['min', 'max']:
        bounds[col] = bounds[col].apply(lambda x: float(x) if x != 'circ' else x)

    data = data.iloc[2:, :].reset_index(drop=True)

    return data, bounds, roles


def read_input_data(name):
    print("read_input_data... preparing")
    data = read_csv("input_data_{}.csv".format(name), sep=";")
    bounds = read_csv('bounds.csv')
    print("read_input_data... bounds.xlsx")
    roles = read_csv('roles.csv')
    print("read_input_data... roles.xlsx")
    data = data.iloc[2:, :].reset_index(drop=True)
    print("read_input_data... readed")
    return data[["Datetime", "{}_P".format(name), "{}_Q".format(name)]], bounds, roles


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


def is_inst(val):
    if isinstance(val, np.floating):
        val = float(val)
    elif isinstance(val, np.integer):
        val = int(val)
    return val


def reconstruct(df, block_devs, res_supp_devs, wp):

    out_dict = {
        "datetime": {},
        "working_points": {},
        "energies": {},
        "statuses": {},
        "pv_energy_effect": {},
        "saved_net_energy": {},
        "MS_workpoint": {}
     }

    out_dict.update({"datetime": pd.Timestamp(df['Datetime'].values[0]).strftime('%Y-%m-%d %H:%M')})

    for dev in ['pv', 'eh', 'evcs', 'inv1', 'bystar1', 'bysprint', 'bystar2', 'mazak']:
        out_dict["working_points"][dev] = {}
        for power in ['P', 'Q']:
            val = is_inst(wp.loc['new', dev + '_' + power])
            out_dict["working_points"][dev].update({power: val})

    for dev in ['pv', 'eh', 'evcs', 'inv1', 'bystar1', 'bysprint', 'bystar2', 'mazak', 'MS_observ']:
        out_dict["energies"][dev] = {}
        for energy in ['Ep', 'Eq']:
            val = is_inst(df[dev + '_' + energy + '_new'].values[0])
            out_dict["energies"][dev].update({energy: val})

    for key, item in block_devs.items():
        if key not in ['eh', 'evcs']:
            out_dict['statuses'][key] = {'Q_problem': item}
            out_dict['statuses'][key].update({'lamp_color': 'red' if item else 'green'})
        else:
            out_dict['statuses'][key] = {'Q_block': item}

    for key, item in res_supp_devs.items():
        out_dict['statuses'][key].update({'res_supp': item})

    for energy in ['Ep', 'Eq']:
        val = is_inst(df['pv_' + energy + '_auto_new'].values[0])
        out_dict["pv_energy_effect"].update({energy: val})

        # ## NOTICE - here change of sign to achieve saved energy
        val = is_inst(-df['del_MS_observ_' + energy].values[0])
        out_dict["saved_net_energy"].update({energy: val})

        power = energy.replace('Ep', 'P').replace('Eq', 'Q')
        val = is_inst(df['MS_observ_' + power + '_new'].values[0])
        out_dict["MS_workpoint"].update({power: val})

    val = is_inst(df['tg_new'].values[0])
    out_dict["MS_workpoint"].update({'tg': val})

    return out_dict


def save_json(jobject):
    with open('test_sample_out.json', 'w') as f:
        f.write(jobject)
