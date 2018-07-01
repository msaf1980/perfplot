#!/usr/bin/python

# Plot Widows perfomance graph
# Export csv from Windows Perfomance Monitor blg file with relog command
# relog perf.blg -f csv -o perf.csv

import sys
import os
import numpy as np
import time
from datetime import datetime
import math
import csv

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.axes as axes
import matplotlib.ticker as ticker
import matplotlib



remap_obj = {
    'Физический диск': 'Physical Disk',
    'Процессор': 'CPU',
    'Система': 'Sys',
    'Файл подкачки': 'Swap'
}
remap_field = {
    #'Физический диск': 'Physical Disk',
    'Скорость чтения с диска (байт/с)': 'Read Bytes/s',
    'Обращений чтения с диска/с': 'Read/s',
    'Скорость записи на диск (байт/с)': 'Write Bytes/s',
    'Обращений записи на диск/с': 'Write/s',
    'Среднее время обращения к диску (с)': 'Avg req time(s)',
    'Средний размер одного обмена с диском (байт)': 'Avg BSize(bytes)',
    'Процент времени бездействия': 'Idle%',
    'Текущая длина очереди диска': 'RunQ',
    
    #'Файл подкачки'
    '% использования': 'Use%',
    
    #'Процессор'
    '% загруженности процессора': 'Busy%',
    '% работы в привилегированном режиме': 'Sys%',
    '% работы в пользовательском режиме': 'User%',
    
    #'Система'
    'Длина очереди процессора': 'RunQ'
}

remap_symbol = {
    ':': '',
    '%': '',
    '/': '_',
    ' ': '_'
}
    
def replace_str(s, repl_dict):
    for k in repl_dict:
        s = s.replace(k, repl_dict[k])
    return s
    
def win_perf_csv(csv_file):
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        next(reader)
        dlist = []
        values = dict()
        for line in reader:
           line[0] = datetime.strptime(line[0], '%m/%d/%Y %H:%M:%S.%f')
           #line[0] = dates.date2num(datetime.strptime(line[0], '%m/%d/%Y %H:%M:%S.%f'))
           #line[0] = np.datetime64(line[0])
           for i in range(1, len(line)):
               line[i] = float(line[i])
           dlist.append(line)
        data = np.asarray(dlist).transpose()
        it = iter(header)
        for i in range(1, len(header)):
            #print(i)
            hs = header[i].lstrip('\\').split('\\')
            #print(hs)
            hs[1] = replace_str(hs[1], remap_obj)
            hs[2] = replace_str(hs[2], remap_field)
            host_data = values.get(hs[0])
            if host_data is None:
                host_data = dict()
                values[hs[0]] = host_data
                
            obj_data = host_data.get(hs[1])
            if obj_data is None:
                obj_data = dict()
                host_data[hs[1]] = obj_data
            
            ts = data[0]
            obj_data[hs[2]] = data[i]
            
        return (ts, values)

        
def np_max_value(*args):
    m = 0
    #print(args)
    for arg in args:
        if arg is None or arg[1] is None:
            continue
              
        m1 = np.max(arg[1])
        if m1 > m: m = m1
            
    return m

    
def np_kb(*args):
    m = 0
    for arg in args:
        if arg is None:
            continue
        for i in range(0, len(arg)): arg[i] = arg[i] / 1024
    
def np_pcnt_rev(a):
    if a is None: return a
    return np.subtract(100, a)

        
def plot_arrays(file, title, ts, tsfmt, *args):
    n = 0
    fig, ax = plt.subplots()
    plt.title(title)
    ax.set_xlabel("Time (%m-%d %H:%M)")
    ax.xaxis.set_major_formatter(tsfmt)
    plt.xticks(rotation='vertical')
    m = np_max_value(*args)
    if n > 0:
        yticks = np.arange(0, math.ceil(m), m // 10)
    else:
        yticks = None
        
    prop_cycle = plt.rcParams['axes.prop_cycle']
    colors = prop_cycle.by_key()['color']
    cc = iter(colors)               
    for arg in args:
        if arg is None or arg[1] is None:
            continue
        n += 1
        ax.plot(ts, arg[1], next(cc), label=arg[0])
    
    if n > 0:
        plt.grid()
        ax.legend(loc='upper left', frameon=False)
        plt.savefig(file,bbox_inches='tight',dpi=100)
    #plt.show()
    plt.close()
                
def plot_disks(data, ts, tsfmt, dir):
    for ok in data: # obj
        if ok.startswith('Physical Disk'):

            r = 'Read/s'
            w = 'Write/s'
            file = os.path.join(dir, "IOPS_%s.png" % replace_str(ok, remap_symbol))
            plot_arrays(file, ok, ts, tsfmt, 
                [ r, data[ok].get(r) ],
                [ w, data[ok].get(w) ],
            )
            
            rv = data[ok].get('Read Bytes/s')
            wv = data[ok].get('Write Bytes/s')
            np_kb(rv, wv)
            file = os.path.join(dir, "Bytes_s_%s.png" % replace_str(ok, remap_symbol))
            plot_arrays(file, ok, ts, tsfmt, 
                [ 'Read KBytes/s', rv ],
                [ 'Write KBytes/s', wv ],
            )
                
            runq = 'RunQ'
            file = os.path.join(dir, "Runq_%s.png" % replace_str(ok, remap_symbol))
            plot_arrays(file, ok, ts, tsfmt, 
                [ runq, data[ok].get(runq) ],
            )
            
            idle = 'Idle%'
            file = os.path.join(dir, "Busy_%s.png" % replace_str(ok, remap_symbol))
            plot_arrays(file, ok, ts, tsfmt, 
                [ 'Busy', np_pcnt_rev( data[ok].get(idle) ) ],
            )
            
        elif ok.startswith('CPU'):
            
            b = 'Busy%'
            bv = data[ok].get(b)
            u = 'User%'
            uv = data[ok].get(u)
            s = 'Sys%'
            sv = data[ok].get(s)
            file = os.path.join(dir, "%s.png" % replace_str(ok, remap_symbol))
            plot_arrays(file, ok, ts, tsfmt, 
                [ b, bv ],
                [ u, uv ],
                [ s, sv ],
            )
        elif ok.startswith('Sys'):
            
            r = 'RunQ'
            rv = data[ok].get(r)
            file = os.path.join(dir, "Sys_RunQ.png")
            plot_arrays(file, ok, ts, tsfmt, 
                [ r, rv ],
            )
        
        #for vk in data[ok]:
        #    print("  %s" % vk)
            
            
if __name__ == "__main__":        
    for i in range(1, len(sys.argv)):
        filename = sys.argv[i]
        (ts, data) = win_perf_csv(filename)
        #print(ts)
        #print(data)

        dir = os.path.splitext(filename)[0]
        try:
            os.mkdir(dir)
        except:
            pass

        #xfmt = mdates.DateFormatter('%Y-%m-%d %H:%M')
        xfmt = mdates.DateFormatter('%m-%d %H:%M')

        for hk in data: # hosts
            subdir = os.path.join(dir, hk)
            try:
                os.mkdir(subdir)
            except:
                pass
            plot_disks(data[hk], ts, xfmt, subdir)

            #for ok in data[hk]:
            #    for vk in data[hk][ok]:
            #        print("%s\%s\%s" % (hk, ok, vk))
