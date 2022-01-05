#!/usr/bin/env python


'''
Script to extract profiles from the xwakes flight data.

Based on the scipy.signal.find_peak algorithm.
Calculate the highest peaks and lowest valleys.

Peaks should be above 800 meters
Valley should be below 100 meters
Neighouring peaks or Valleys should be 50 meters appart

Responsible parameters:
    plow = 800
    vhig = 100
    prom = 50

Input: --ifile /path/to/matlab/file/with/extension/.mat
       --obase /path/to/outputfile/base (no extension)

Output: Two files are created:
    a plot to check the found profiles
    a text file containing the following information:
    start and finish systime of each profile segment,
    the mean lats, lons, wspd and wdir over the profiles
'''


import argparse
import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import scipy.io
import scipy.signal
import sys


def format_date(x, pos=None):
    return ':'.join(str(datetime.timedelta(seconds=x)).split(':')[:2])


if __name__ == '__main__':
    # Input Matlab files *.mat
    parser = argparse.ArgumentParser()
    parser.add_argument('--ifile')
    parser.add_argument('--obase')
    args = parser.parse_args()

    # Calculate the highest peaks and lowest valleys
    # Peaks should be above 800 meters
    # Valls should be below 100 meters
    # Neighours should be 50 meters appart
    plow = 800
    vhig = 100
    prom = 50

    figsize = (11.6, 8.2)
    fig, ax = plt.subplots(figsize=figsize)

    # Load and extract altitude data
    mat = scipy.io.loadmat(args.ifile)

    alt = np.squeeze(mat['Alt'])
    lat = np.squeeze(mat['Lat'])
    lon = np.squeeze(mat['Lon'])

    time = np.squeeze(mat['sys_time'])
    wdir = np.squeeze(mat['DD'])
    wspd = np.squeeze(mat['FF'])

    # Filter Data for NANs
    alt_mask = np.isfinite(alt)
    lat_mask = np.isfinite(lat)
    lon_mask = np.isfinite(lon)
    time_mask = np.isfinite(time)
    wdir_mask = np.isfinite(wdir)
    wspd_mask = np.isfinite(wspd)

    mask = alt_mask & lat_mask & lon_mask & time_mask & wdir_mask & wspd_mask

    # Apply Infinite Mask
    alt = alt[mask]
    lat = lat[mask]
    lon = lon[mask]
    time = time[mask]
    wdir = wdir[mask]
    wspd = wspd[mask]

    # Calculate the highest peaks and lowest valleys
    # Peaks should be above 800 meters
    # Valls should be below 100 meters
    # Neighours should be 50 meters appart
    peaks = scipy.signal.find_peaks(alt, height=plow, prominence=prom)
    vally = scipy.signal.find_peaks(-alt, height=-vhig, prominence=prom)

    # Create Tuples with indicators:
    # 1->maximum, 0->minimum
    ma = [(p, 1) for p in peaks[0]]
    mi = [(p, 0) for p in vally[0]]
    mami = sorted(ma+mi, key=lambda tup: tup[0])

    # Take only the ma(x) which are followed by a mi(n)
    # And vice versa
    all_points = []
    for i, j in zip(mami[:-1], mami[1:]):
        if i[1] != j[1]:
            all_points.append((i, j))

    # Filter out points that are to separated
    ax.plot(time, alt)
    colors={(0,1):'y', (1,0):'c'}
    i = 0
    alt_min = np.min(alt) - 0.02 * np.min(alt)
    alt_max = np.max(alt) + 0.02 * np.max(alt)

    # Keep only valid points
    mean = np.mean([j[0]-i[0] for i,j in all_points])
    points = [o for o in all_points if o[1][0]-o[0][0]<mean]

    # Plot
    lats = []
    lons = []
    wspds = []
    wdirs = []
    for o in points:
        v1, m1 = o[0]
        v2, m2 = o[1]
        mask = np.zeros(np.shape(alt), dtype=bool)
        vslice = slice(v1, v2)
        mask[vslice] = True

        lats.append(np.mean(lat[vslice]))
        lons.append(np.mean(lon[vslice]))

        wspds.append(np.mean(wspd[vslice]))
        wdirs.append(np.mean(wdir[vslice]))

        color = colors[(m1,m2)]
        ax.plot(time[mask], alt[mask], c=color)
        fs = 'xx-large'
        if (m1, m2) == (0, 1):
            ax.text(time[v1], alt_min, str(i), bbox=dict(facecolor=color, alpha=0.5, boxstyle='round,pad=0.2', lw=0), fontsize=fs)
        elif (m1, m2) == (1, 0):
            ax.text(time[v1], alt_max, str(i), bbox=dict(facecolor=color, alpha=0.5, boxstyle='round,pad=0.1', lw=0), fontsize=fs)
        i += 1

    ax.set_ylabel('height [m]')
    ax.set_xlabel('time')
    ax.xaxis.set_major_formatter(format_date)
    fig.autofmt_xdate()

    title_parts = os.path.basename(args.ifile).split('_')
    date = [t for t in title_parts if len(t) == 8 and '20' in t]
    date = 'Date?' if not date else '.'.join([date[0][:4], date[0][4:6], date[0][6:]])
    flight = [t for t in title_parts if 'flug' in t]
    flight = '' if not flight else flight[0]

    fig.suptitle(date+' '+flight, fontsize='xx-large', transform=plt.gcf().transFigure, fontweight='bold')

    ylim = ax.get_ylim()
    ax.set_ylim(ylim[0], ylim[1]+50)
    fig.savefig(args.obase+'_cart.pdf')

    # Save Extracted Data
    out = [(time[p[0][0]], time[p[1][0]], la, lo, w, d) for p, la, lo, w, d in zip(points, lats, lons, wspds, wdirs)]
    header = 'sys_time:start and finish of each data segment, mean lats, lons, wspd, wdir'
    np.savetxt(args.obase+'.txt', out, delimiter='\t', header=header)
    
    # Return mean angle
    a_mean=np.mean([a for a in wdir if not np.isnan(a)])
    print('{:03d}'.format(int(a_mean)))
