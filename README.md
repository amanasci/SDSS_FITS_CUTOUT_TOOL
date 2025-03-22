# SDSS FITS Cutout Tool

This tool downloads a FITS image from the SDSS survey using SIAP, extracts an image cutout centered on given RA and Dec coordinates, and saves the cutout as a new FITS file.

## Features

- Downloads FITS images from SDSS.
- Extracts a 128x128 pixel cutout centered on specified coordinates.
- Saves the cutout to a user-defined folder.
- Validates input parameters before processing.

## Requirements

- Python 3.x
- requests
- astropy
- bz2 (standard library)

## Usage

Import the script and call the function:

```python
from SDSS_FITS_CUTOUT_TOOL import download_and_cutout

# Example usage:
download_and_cutout("object_name", 150.0, 2.0, "/path/to/save/cutout")
```

Ensure the RA is in the range [0, 360) and Dec is in the range [-90, 90]. The script creates the output folder if it does not exist.

## Tweaks

There are multiple things that can be tweaked in this basic script such as size of the cutout, band of the cutout, etc.
