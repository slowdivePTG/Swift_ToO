'''
An interactive script to submit a UVOT ToO request.
'''

from swifttools.swift_too import TOO, UVOT_mode
import argparse

parser = argparse.ArgumentParser(description='Summit a UVOT ToO request.')
parser.add_argument(
    '-s',
    '--submit',
    help=
    'Whether to submit the request [default = False, trigger the debug mode].',
    action='store_true')
parser.add_argument(
    '-f',
    '--force',
    help='Whether to forcibly submit a request (usually a modified one).',
    action='store_true')
args = parser.parse_args()

# log in
import pandas as pd
df = pd.read_csv("shared_secret", delimiter=",")
username = df["username"].values[0]
shared_secret = df["shared_secret"].values[0]
too = TOO()
too.username = username
too.shared_secret = shared_secret
too.debug = not (args.submit)
print('Debug mode {}'.format('on' if too.debug else 'off'))

# source info
too.source_name = input('Source name: ')
too.source_type = input('Source type [Supernova]: ') or 'Supernova'
too.ra = float(input('Right ascension (deg): '))
too.dec = float(input('Declination (deg): '))
too.immediate_objective = input(
    'Reason to observe this object (e.g., We hope to measure the UV evolution of SN 2022xx, a newly discovered and young SN Ia. This SN, at a distance of ~xx Mpc, is a great laboratory for studying different explosion mechanisms for SNe Ia.):\n'
)

# observation info
too.exp_time_per_visit = float(
    input('Exposure time per visit (usually between 1000 and 2000s): '))
too.monitoring_freq = input('Monitoring frequency [1 day]: ') or '1 day'
too.num_of_visits = int(input('Number of observations [7]: ') or '7')
print('Observation types:')
_ = [print(f"{t[0]}: {t[1]}")
     for t in enumerate(too.obs_types)]  # print supported obs types
too.obs_type = too.obs_types[int(
    input('Observation type for this object [1]: ') or '1')]
too.opt_mag = float(input('Current magnitude in optical bands: '))
too.opt_filt = input(
    'What filter was this measured in (can be non-UVOT filters) [g]: ') or 'g'
urgency_rules = '''
Urgency Rules:
    Urgency 1: We need observations within 4 hours
    Urgency 2: Observations should start within the next 24 hours
    Urgency 3: Observations should start in the next few days
    Urgency 4: Weeks to a month
Urgency for this object [2]: 
'''
too.urgency = int(input(urgency_rules) or '2')
too.instrument = "UVOT"
too.uvot_mode = int(input('UVOT mode [0x223f]: ') or '0x223f', 16)
print(UVOT_mode(too.uvot_mode))

# Justifications
Sci_Just = 'We aim to obtain a UV light curve of this young SN Ia to see if there are signs of interaction with a nearby companion (ejecta-companion collision, which manifests as a short lived UV flash), or an early radioactive peak powered by the nucleosynthesis of radioactive material in a He shell on the exploding white dwarf.'
too.science_just = input(f'Science justification [{Sci_Just}]:\n') or Sci_Just

Exp_Just = "Our requested exposure time is based on previous experience observing young SNe and the current brightness of this target. In {:.0f} s, we expect to detect the UV flux at SNR >~ 10 in each of the UV filters.".format(
    too.exp_time_per_visit)
too.exp_time_just = input(
    f'Exposure time justification [{Exp_Just}]:\n') or Exp_Just

UVOT_Filter_Just = "For this source it is essential that we obtain a UV flight curve, and hence we need to obtain observations in each of the UV filters, but we also want the exposures weighted towards the UV filters as the SN is expected to be much brighter in the optical."
too.uvot_just = input(
    f'UVOT filter justification [{UVOT_Filter_Just}]:\n') or UVOT_Filter_Just

if too.validate():
    print('Request validated:')
    print(too)

if too.submit():
    print(f"Submitted TOO ID = {too.status.too_id}")
else:
    print(f"{too.status.status}. Errors: {too.status.errors}")

if args.force:
    if not too.status:
        if ('TOO already recently submitted.' in too.status.errors):
            too.status.clear(
            )  # Clear the 'Rejected' status of the previous attempt to submit
        if too.submit():
            print(f"Submitted TOO ID = {too.status.too_id}")
        else:
            print(f"{too.status.status}. Errors: {too.status.errors}")
    else:
        print("TOO was already accepted.")
