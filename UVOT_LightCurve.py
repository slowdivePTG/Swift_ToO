"""
A script to generate multi-band light curves from existing data
"""

from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
import argparse
import glob

mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.size"] = "25"
mpl.rcParams["text.usetex"] = True
mpl.rcParams["xtick.labelsize"] = "25"
mpl.rcParams["ytick.labelsize"] = "25"

parser = argparse.ArgumentParser(
    description="Generate multi-band light curves from existing data."
)
parser.add_argument("-n", "--name", help="The name of the target.")
parser.add_argument("--snr_limit", help="The required S/N.", default=-1, type=float)
args = parser.parse_args()

filt = ["V", "B", "U", "UW1", "UM2", "UW2", "W"]
obsids = glob.glob(f"data/{args.name}/*/")
obsids.sort()

# initialize a dictionary for photometric results
phot = {}
phot_output = []
for k, obsid in enumerate(obsids):
    # check if there is stacked file
    ims_stacked = glob.glob(obsid + "uvot/image/*stacked.out")
    ims = glob.glob(obsid + "uvot/image/*maghist.out")
    # print(obsid)
    for flt in filt:
        stacked = False
        for im in ims_stacked:
            if im.split("/")[-1][:-12] == flt:
                stacked = True
                break
        hist = False
        if not stacked:
            for im in ims:
                if im.split("/")[-1][:-12] == flt:
                    hist = True
                    break
        if not (hist or stacked):
            # print(f'Cannot find {flt} band outputs.')
            continue
        data = fits.getdata(im)
        snr = data["AB_FLUX_HZ"] / data["AB_FLUX_HZ_ERR"]
        mjd = np.array([])
        mag_Vega, mag_unc, mag_Vega_lim = (
            np.array([]),
            np.array([]),
            np.array([]),
        )
        mag, mag_ulim, mag_llim = (
            np.array([]),
            np.array([]),
            np.array([]),
        )
        fl, fl_unc = np.array([]), np.array([])
        lolim = np.array([])
        mjd = np.append(
            mjd, data["MET"] / 24 / 3600 + 51910
        )  # mission time + Jan 1.0, 2001
        for k in range(len(snr)):
            AB_mag = data["AB_MAG"][k]
            Vega_mag = data["MAG"][k]
            Vega_mag_unc = data["MAG_ERR"][k]
            mag = np.append(mag, AB_mag)
            mag_Vega = np.append(mag_Vega, Vega_mag)
            mag_unc = np.append(mag_unc, Vega_mag_unc)
            if args.snr_limit < 0:
                snr_limit = data["AB_MAG_LIM_SIG"]
            else:
                snr_limit = args.snr_limit
            fl = np.append(fl, data["AB_FLUX_HZ"][k] * 1e3)  # mJy --> muJy
            fl_unc = np.append(fl_unc, data["AB_FLUX_HZ_ERR"][k] * 1e3)  # mJy --> muJy
            if (snr[k] >= snr_limit).any():
                AB_mag_up = -2.5 * np.log10(
                    1 + data["AB_FLUX_HZ_ERR"][k] / data["AB_FLUX_HZ"][k]
                )
                AB_mag_lo = 2.5 * np.log10(
                    1 - data["AB_FLUX_HZ_ERR"][k] / data["AB_FLUX_HZ"][k]
                )
                # pass the snr threshold
                mag_ulim = np.append(mag_ulim, AB_mag_up)
                mag_llim = np.append(mag_llim, AB_mag_lo)
                lolim = np.append(lolim, np.zeros_like(AB_mag))
            else:
                # low snr, provide limit
                AB_mag_lim = data["AB_MAG_LIM"][k]
                Vega_mag_lim = data["MAG_LIM"][k]
                mag_ulim = np.append(mag_ulim, AB_mag - AB_mag_lim)
                mag_llim = np.append(mag_llim, 0)
                lolim = np.append(lolim, np.ones_like(AB_mag))
        if not flt in phot.keys():
            phot[flt] = np.array([mjd, mag, mag_ulim, mag_llim, lolim])
        else:
            phot[flt] = np.append(
                phot[flt], np.array([mjd, mag, mag_ulim, mag_llim, lolim]), axis=1
            )

        if len(phot_output) == 0:
            phot_output = np.array(
                [
                    mjd,
                    mag_Vega,
                    mag_unc,
                    fl,
                    fl_unc,
                    mag,
                    mag_ulim,
                    mag_llim,
                    lolim,
                    [flt],
                ],
                dtype=object,
            )
        else:
            phot_output = np.append(
                phot_output,
                np.array(
                    [
                        mjd,
                        mag_Vega,
                        mag_unc,
                        fl,
                        fl_unc,
                        mag,
                        mag_ulim,
                        mag_llim,
                        lolim,
                        [flt],
                    ],
                    dtype=object,
                ),
                axis=1,
            )

np.savetxt(
    f"./data/{args.name}/UVOT_light_curve.dat",
    phot_output.T,
    fmt="%.6f %.6f %.6f %.6e %.6e %.6f %.6f %.6f %.0f %s",
)

f, ax = plt.subplots(figsize=(12, 8))
for flt in phot.keys():
    dat = phot[flt]
    if (~np.isnan(dat[0])).sum() == 0:
        continue
    # plot light curve
    ax.errorbar(
        dat[0],
        dat[1],
        yerr=(dat[2], dat[3]),
        uplims=dat[4],
        fmt="o",
        capsize=4,
        label=rf"${flt}$",
        markersize=8,
        markeredgecolor="k",
        markeredgewidth=0.8,
        elinewidth=1.1,
    )
ax.invert_yaxis()
ax.set_xlabel(r"$\mathrm{MJD}$")
ax.set_ylabel(r"$m$")
ax.legend(prop={"size": 20})
f.tight_layout()
plt.show()
