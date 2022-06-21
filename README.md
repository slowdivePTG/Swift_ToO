# Swift_ToO

Triggering and analyzing Swift UVOT follow-ups for ZTF sources of interest.

## Software prerequisites

- [HEASoft](https://heasarc.gsfc.nasa.gov/lheasoft/)

- [The HEASARC Calibration Database (CALDB)](https://heasarc.gsfc.nasa.gov/docs/heasarc/caldb/caldb_intro.html)

## Usage

### Submit a ToO request

```shell
python UVOT_ToO.py
```

to enter the interactive environment and fill in the request form.

### Query data

```shell
python UVOT_Fetch.py --name "SN_NAME" --targetid "TARGET_ID"
```

Data from each observation will be stored in `./data/SN_NAME/`.

### Photometry

```shell
python UVOT_Phot.py --name "SN_NAME"
```

The Python script will automatically sum UVOT sky images/exposure maps and generate a `FITS` image for each filter in `./data/SN_NAME/OBS_ID/uvot/image/`.

After the first run, you will need to visually inspect the image and decide the source and sky background regions to be used in the aperture photometry. The two regions should be stored in `src.reg` and `bkg.reg` under the `./data/SN_NAME/` directory, in the syntax of

```
fk5;circle(RA [deg], dec [deg], radius'' [arcsec])
```

Then with a second run, the multi-band aperture photometry results will be stored in `./data/SN_NAME/OBS_ID/uvot/image/FILTER.out`.

> Not a good idea to let an expection stop us before we create the `reg` files - to be fixed in the future.

### Light curves

```shell
python UVOT_LightCurve.py --name "SN_NAME"
```

## Known issues

1. In `UVOT_Fetch.py`, in case of
   
   ```python
   tqdm.std.TqdmKeyError: "Unknown argument(s): {'display': False}"
   ```
   
   you may need to comment out the following lines in `tqdm/std.py`
   
   ```python
   raise (
       TqdmDeprecationWarning(
           "`nested` is deprecated and automated.\n"
           "Use `position` instead for manual control.\n",
           fp_write=getattr(file, 'write', sys.stderr.write))
       if "nested" in kwargs else
       TqdmKeyError("Unknown argument(s): " + str(kwargs)))
   ```

2. In `UVOT_Phot.py`, in case of
   
   ```
   CALDBCONFIG environment variable not properly set (at HDgtcalf.c: 609)
   Problem getting CALDB index file (at HDgtcalf.c: 77)
   ```
   
   you may need to change the definition of `$CALDBCONFIG` and `$CALDBALIAS` in `$CALDB/software/tools/caldbinit.sh` or `$CALDB/caldbinit.sh` to match the local installation. As you see, the path to `caldbinit.sh` can also vary from machines to machines.
