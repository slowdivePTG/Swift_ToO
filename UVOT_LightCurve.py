'''
A script to generate multi-band light curves from existing data
'''

from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
import argparse
import glob

mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.size'] = '25'
mpl.rcParams['text.usetex'] = True
mpl.rcParams['xtick.labelsize'] = '25'
mpl.rcParams['ytick.labelsize'] = '25'

parser = argparse.ArgumentParser(
    description='Generate multi-band light curves from existing data.')
parser.add_argument('-n', '--name', help='The name of the target.')
args = parser.parse_args()

filt = ['V', 'B', 'U', 'UW1', 'UM2', 'UW2', 'W']
obsids = glob.glob(f'data/{args.name}/*/')
obsids.sort()

#initialize a dictionary for photometric results
phot = {}

for k, obsid in enumerate(obsids):
    # check if there is stacked file
    ims_stacked = glob.glob(obsid + 'uvot/image/*stacked.out')
    ims = glob.glob(obsid + 'uvot/image/*maghist.out')
    #print(obsid)
    for flt in filt:
        stacked = False
        for im in ims_stacked:
            if im.split('/')[-1][:-12] == flt:
                stacked = True
                break
        hist = False
        if not stacked:
            for im in ims:
                if im.split('/')[-1][:-12] == flt:
                    hist = True
                    break
        if not (hist or stacked):
            #print(f'Cannot find {flt} band outputs.')
            continue
        data = fits.getdata(im)
        snr = data['AB_FLUX_HZ'] / data['AB_FLUX_HZ_ERR']
        mjd = np.array([])
        mag, mag_ulim, mag_llim = np.array([]), np.array([]), np.array([])
        lolim = np.array([])
        mjd = np.append(mjd, data['MET'] / 24 / 3600 +
                        51910)  # mission time + Jan 1.0, 2001
        for k in range(len(snr)):
            AB_mag = -2.5 * np.log10(data['AB_FLUX_HZ'][k] / 3631e3)
            mag = np.append(mag, AB_mag)
            if (snr[k] >= data['AB_MAG_LIM_SIG']):
                AB_mag_up = -2.5 * np.log10(
                    (data['AB_FLUX_HZ'][k] - data['AB_FLUX_HZ_ERR']) / 3631e3)
                AB_mag_lo = -2.5 * np.log10(
                    (data['AB_FLUX_HZ'][k] + data['AB_FLUX_HZ_ERR']) / 3631e3)
                # pass the snr threshold
                mag_ulim = np.append(mag_ulim, AB_mag - AB_mag_up)
                mag_llim = np.append(mag_llim, AB_mag_lo - AB_mag)
                lolim = np.append(lolim, False)
            else:
                # low snr, provide lower limit
                AB_mag_lim = -2.5 * np.log10(
                    data['AB_FLUX_HZ_LIM'][k] / 3631e3)
                mag_ulim = np.append(mag_ulim, np.zeros_like(AB_mag))
                mag_llim = np.append(mag_llim, AB_mag_lim - AB_mag)
                lolim = np.append(lolim, True)
        if not flt in phot.keys():
            phot[flt] = np.array([mjd, mag, mag_ulim, mag_llim, lolim])
        else:
            phot[flt] = np.append(phot[flt],
                                  np.array(
                                      [mjd, mag, mag_ulim, mag_llim, lolim]),
                                  axis=1)

f, ax = plt.subplots(figsize=(12, 8))
for flt in phot.keys():
    dat = phot[flt]
    if (~np.isnan(dat[0])).sum() == 0:
        continue
    # plot light curve
    ax.errorbar(dat[0],
                dat[1],
                yerr=(dat[2], dat[3]),
                lolims=dat[4],
                fmt='o',
                capsize=4,
                label=rf'${flt}$',
                markersize=8,
                markeredgecolor='k',
                markeredgewidth=.8,
                elinewidth=1.1)
ax.invert_yaxis()
ax.set_xlabel(r'$\mathrm{MJD}$')
ax.set_ylabel(r'$m$')
ax.legend(prop={'size':20})
f.tight_layout()
plt.show()