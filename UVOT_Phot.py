'''
A script for UVOT photometry
'''

import subprocess, os, re, sys
import argparse
import numpy as np
from astropy.io import fits

parser = argparse.ArgumentParser(
    description='Do photometry for Swift UVOT data.')
parser.add_argument('-n', '--name', help='The name of the target.')
args = parser.parse_args()

env_var = {}
with open('HEAsoft_env', 'r') as f:
    lines = f.readlines()
for line in lines:
    l = line.lstrip().rstrip('\n')
    if len(l) == 0:
        continue
    if l[0] == '#':
        continue
    var = l.split('=')[0]
    string = l.split('=')[1]
    env_var[var] = string
try:       
    # Setting up the environment for HEAsoft
    os.environ['HEADAS'] = env_var['HEADAS']
    headas_shell = env_var['headas_shell']
    pipe = subprocess.Popen(f". {headas_shell}; env",
                            stdout=subprocess.PIPE,
                            shell=True)
    output = pipe.communicate()[0]
    env = dict(
        (line.decode('utf-8').split("=", 1) for line in output.splitlines()))
    os.environ.update(env)

    # Setting up the environment for CALDB (calibration database)
    os.environ['CALDB'] = env_var['CALDB']
    caldb_shell = env_var['caldb_shell']
    pipe = subprocess.Popen(f". {caldb_shell}; env",
                            stdout=subprocess.PIPE,
                            shell=True)
    output = pipe.communicate()[0]
    env = dict(
        (line.decode('utf-8').split("=", 1) for line in output.splitlines()))
    os.environ.update(env)

    # Setting the HEADASPROMPT variable to "/dev/null" 
    os.environ['HEADASPROMPT'] = env_var['HEADASPROMPT']
except KeyError as err:
    sys.exit(f"Please define {err} in HEAsoft_env")

# photometry script
filtdict = {
    "vv": "V",
    "bb": "B",
    "uu": "U",
    "w1": "UW1",
    "m2": "UM2",
    "w2": "UW2",
    "wh": "W"
}
datadir = f"data/{args.name}/"
obsids = os.listdir(datadir)

#TODO write a script to generate region files interactively
for d in obsids:
    if re.match("\d{11}", d):
        imdir = datadir + f"{d}/uvot/image/"
        ims = os.listdir(imdir)
        ims.sort()
        for image in ims:
            if re.search("_sk.img", image):
                print(image)
                filt = filtdict[image[14:16]]

                # uvotmaghist - make a light curve from the exposures in a UVOT image file
                # run uvotmaghist to quickly get SNR
                pipe0 = subprocess.Popen(
                    f"uvotmaghist infile={imdir + image} outfile={imdir + filt}_maghist.out plotfile=None\
                        srcreg={datadir}src.reg bkgreg={datadir}bkg.reg",
                    shell=True,
                    stdout=subprocess.PIPE)
                pipe0.communicate()
                try:
                    lc = fits.getdata(f'{imdir + filt}_maghist.out')
                    SNR = lc['AB_FLUX_HZ'] / lc['AB_FLUX_HZ_ERR']
                except FileNotFoundError:
                    SNR = 0

                # if more than one exposures were made, all of which have SNR < 5
                # run uvotimsum to stack the images
                if np.all(SNR < 5) and len(np.atleast_1d(SNR)) > 1:
                    weightedtime = np.average(
                        lc["MET"],  #Mission Elapsed Time (MET)
                        weights=lc["EXPOSURE"])
                    # swifttime - Swift Time Converter - from seconds since 2001 to MJD
                    pipe1 = subprocess.Popen(
                        f'swifttime intime={weightedtime} insystem=m informat=s outsystem=m outformat=m',
                        shell=True,
                        stdout=subprocess.PIPE)
                    res = pipe1.communicate()[0].decode("utf-8")
                    try:
                        MJD = float(res.split('\n')[1].split(' ')[-1])
                    except:
                        MJD = float(res.split('\n')[2].split(' ')[-1])

                    # uvotimsum - sum UVOT sky images or exposure maps
                    pipe2 = subprocess.Popen(
                        f'uvotimsum infile={imdir + image} outfile={imdir + filt}.fits clobber=True',
                        shell=True,
                        stdout=subprocess.PIPE)
                    pipe2.communicate()

                    # uvotsource - instrumental source magnitude derived from image
                    # need to generate two region files - src.reg and bkg.reg - in which
                    #     fk5; circle(RA [deg], Dec [deg], radius'' [arcsec])
                    # write the calibrated mags to filter_stacked.out
                    pipe3 = subprocess.Popen(
                        f"uvotsource image={imdir + filt}.fits srcreg={datadir}src.reg bkgreg={datadir}bkg.reg\
                            sigma=3.0 outfile={imdir + filt}_stacked.out\
                            syserr=yes output=ALL apercorr=CURVEOFGROWTH clobber=True\
                            > {imdir + filt}.dat",
                        shell=True,
                        stdout=subprocess.PIPE)
                    pipe3.communicate()
                    # In case of
                    #     CALDBCONFIG environment variable not properly set (at HDgtcalf.c: 609)
                    #     Problem getting CALDB index file (at HDgtcalf.c: 77)
                    # May need to change the definition of $CALDBCONFIG and $CALDBALIAS to match the local installation
