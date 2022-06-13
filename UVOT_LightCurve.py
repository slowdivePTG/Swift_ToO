'''
A script to generate multi-band light curves from existing data
'''

from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
import argparse
import glob

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = '25'
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
for flt in filt:
    # 3 rows - Mean MJD, AB mag, AB mag err
    phot[flt] = np.ones((3, len(obsids))) * np.nan

for k, obsid in enumerate(obsids):
    ims = glob.glob(obsid + 'uvot/image/*out')
    for im in ims:
        flt = im.split('/')[-1][:-4]  # filter name
        data = fits.getdata(im)
        snr = data['AB_FLUX_AA'] / data['AB_FLUX_AA_ERR']
        phot[flt][0, k] = data['MET'] / 24 / 3600 + 51910  # mission time + Jan 1.0, 2001
        if snr >= data['AB_MAG_LIM_SIG']:
            phot[flt][1, k] = data['AB_MAG']
            phot[flt][2, k] = data['AB_MAG_ERR']
        else:
            # provide upper limit
            phot[flt][1, k] = data['AB_MAG_LIM']
            phot[flt][2, k] = -999

f, ax = plt.subplots(figsize=(12, 8))
for flt in filt:
    dat = phot[flt]
    if (~np.isnan(dat[0])).sum() == 0:
        continue
    arg = np.argwhere(dat[2] > 0).ravel()
    upper = np.argwhere(dat[2] <= 0).ravel()
    # plot light curve
    ax.errorbar(dat[0][arg],
                dat[1][arg],
                yerr=dat[2][arg],
                fmt='o',
                capsize=5,
                label=rf'${flt}$',
                markersize=10,
                markeredgecolor='k',
                markeredgewidth=.8,
                elinewidth=1.1)
    # plot upper limit
    ax.scatter(dat[0][upper], dat[1][upper], marker='v')
ax.invert_yaxis()
ax.set_xlabel(r'$\mathrm{MJD}$')
ax.set_ylabel(r'$m$')
ax.legend()
f.tight_layout()
plt.show()