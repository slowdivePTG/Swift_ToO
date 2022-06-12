'''
A script to query and download UVOT data.
'''

from swifttools.swift_too import Data
from swifttools.swift_too import ObsQuery
import argparse
import os

parser = argparse.ArgumentParser(
    description='Query and download Swift UVOT data.')
parser.add_argument('-n', '--name', help='The name of the target.')
parser.add_argument('-t',
                    '--targetid',
                    type=int,
                    help='The ID of the target ToO.')
parser.add_argument('-f',
                    '--force',
                    help='Whether to overwrite existing data.',
                    action='store_true')
args = parser.parse_args()

oqs = ObsQuery(targetid=args.targetid)
print('Found {} observations.'.format(len(oqs)))
print(oqs)
obsids = [oq.obsid for oq in oqs]

name = args.name.replace(' ', '')  # remove spaces in the directory title
if not name in os.listdir('data'):
    os.system(f'mkdir data/{name}')

for oq in oqs:
    # may need to comment out lines 1012-1018 in $PATH/tqdm/std.py if the exception below is raised:
    #     tqdm.std.TqdmKeyError: "Unknown argument(s): {'display': False}"
    data = Data(obsid=oq.obsid,
                uvot=True,
                outdir=f'data/{name}',
                clobber=args.force)
