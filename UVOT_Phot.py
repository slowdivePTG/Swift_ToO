'''
A script for UVOT photometry
'''

import subprocess, os, re
import argparse

parser = argparse.ArgumentParser(
    description='Do photometry for Swift UVOT data.')
parser.add_argument('-n', '--name', help='The name of the target.')
args = parser.parse_args()

# Setting up the environment for HEAsoft
#     $ export HEADAS=/path/to/your/installed/heasoft-6.30/(PLATFORM)
# In the examples above, (PLATFORM) is a placeholder for the platform-specific string denoting your machine's architecture,
# for example:x86_64-apple-darwin20.6.0
os.environ['HEADAS'] = '/Users/chang/HEASARC/heasoft-6.30.1/x86_64-apple-darwin21.5.0'

# Setting up the environment for CALDB (calibration database)
os.environ['CALDB'] = '/Users/chang/HEASARC/caldb'

headas_shell = '$HEADAS/headas-init.sh'
caldb_shell = '$CALDB/caldbinit.sh'  #'$CALDB/software/tools/caldbinit.sh'

pipe = subprocess.Popen(f". {headas_shell}; env",
                        stdout=subprocess.PIPE,
                        shell=True)
output = pipe.communicate()[0]
env = dict(
    (line.decode('utf-8').split("=", 1) for line in output.splitlines()))
os.environ.update(env)

pipe = subprocess.Popen(f". {caldb_shell}; env",
                        stdout=subprocess.PIPE,
                        shell=True)
output = pipe.communicate()[0]
env = dict(
    (line.decode('utf-8').split("=", 1) for line in output.splitlines()))
os.environ.update(env)

# Setting the HEADASPROMPT variable to "/dev/null" redirects prompts to the null stream
# and prevents tasks from trying to open the console terminal in any situation
os.environ['HEADASPROMPT'] = '/dev/null'

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
for d in obsids:
    if re.match("\d{11}", d):
        imdir = datadir + f"{d}/uvot/image/"
        ims = os.listdir(imdir)
        ims.sort()
        for image in ims:
            if re.search("_sk.img.gz", image):
                print(image)
                filt = filtdict[image[14:16]]
                
                # uvotimsum - sum UVOT sky images or exposure maps
                pipe1 = subprocess.Popen(
                    f'uvotimsum {imdir + image} {imdir + filt}.fits clobber=True',
                    shell=True,
                    stdout=subprocess.PIPE)
                pipe1.communicate()
                '''pipe2 = subprocess.Popen(f"cp {datadir}*.reg {imdir}",
                                         shell=True,
                                         stdout=subprocess.PIPE)
                pipe2.communicate()'''

                # uvotsource - instrumental source magnitude derived from image
                # need to generate two region files - src.reg and bkg.reg - in which
                #     fk5; circle(RA [deg], Dec [deg], radius'' [arcsec])
                # write the calibrated mags to filter.out
                pipe3 = subprocess.Popen(
                    f"uvotsource image={imdir + filt}.fits srcreg={datadir}src.reg bkgreg={datadir}bkg.reg\
                        sigma=3.0 outfile={imdir + filt}.out\
                        syserr=yes output=ALL apercorr=CURVEOFGROWTH clobber=True\
                        > {imdir + filt}.dat",
                    shell=True,
                    stdout=subprocess.PIPE)
                pipe3.communicate()
                # In case of
                #     CALDBCONFIG environment variable not properly set (at HDgtcalf.c: 609)
                #     Problem getting CALDB index file (at HDgtcalf.c: 77)
                # May need to change the definition of $CALDBCONFIG and $CALDBALIAS to match the local installation