import requests
import bz2
import re
from astropy.io.votable import parse_single_table
from astropy.io import fits
from astropy.wcs import WCS
from io import BytesIO
import os

def download_and_cutout(name,ra,dec,folder_location):
    """"Download a FITS image from SDSS and create a cutout."
    """
    # Check if the folder exists, if not create it
    
    if not os.path.exists(folder_location):
        os.makedirs(folder_location)
    # Check if the file already exists
    output_filename = f"{folder_location}/{name}.fits"
    if os.path.exists(output_filename):
        print(f"[{name}] File already exists: {output_filename}")
        return
    # Check if the input coordinates are valid
    if not (-90 <= dec <= 90) or not (0 <= ra < 360):
        print(f"[{name}] Invalid coordinates: RA={ra}, Dec={dec}")
        return
    # Check if the input name is valid
    if not name or not isinstance(name, str):
        print(f"[{name}] Invalid object name: {name}")
        return
    # Check if the input folder location is valid
    if not folder_location or not isinstance(folder_location, str):
        print(f"[{name}] Invalid folder location: {folder_location}")
        return

    # Extract object parameters
    objid = name
    center_ra = ra
    center_dec = dec
    print(f"[{objid}] Processing RA: {center_ra}, Dec: {center_dec}")
    
    # Compute the SIZE parameter for SIAP:
    # 0.4 arcsec/pixel = 0.4/3600 degrees/pixel, so 128 pixels = 128*0.4/3600 degrees
    size_deg = 128 * (0.4 / 3600.0)
    
    # Construct the SIAP URL. (Note: using dr17 here; adjust if needed.)
    siap_url = (f"https://skyserver.sdss.org/dr17/SkyServerWS/SIAP/getSIAP?"
                f"POS={center_ra},{center_dec}&SIZE={size_deg}&FORMAT=image/fits")
    
    try:
        response = requests.get(siap_url)
    except Exception as e:
        print(f"[{objid}] Error in SIAP request: {e}")
        return
    
    # Fix potential encoding issues in the VOTABLE XML
    votable_str = response.content.decode("utf-8", errors="replace")
    votable_str_fixed = re.sub(r'encoding=["\'][^"\']+["\']', 'encoding="utf-8"', votable_str)
    votable_data = BytesIO(votable_str_fixed.encode("utf-8"))
    
    try:
        table = parse_single_table(votable_data).to_table()
    except Exception as e:
        print(f"[{objid}] Error parsing VOTABLE: {e}")
        return
    
    # Select the row corresponding to the r‑band image
    r_row = None
    for row2 in table:
        if "Filter r" in row2["Title"]:
            r_row = row2
            break
    if r_row is None:
        print(f"[{objid}] No r‑band entry found.")
        return
    
    fits_url = r_row["url"]
    print(f"[{objid}] Using FITS URL: {fits_url}")
    
    try:
        fits_response = requests.get(fits_url)
    except Exception as e:
        print(f"[{objid}] Error downloading FITS file: {e}")
        return

    try:
        decompressed_data = bz2.decompress(fits_response.content)
    except Exception as e:
        print(f"[{objid}] Error decompressing FITS file: {e}")
        return

    try:
        hdul = fits.open(BytesIO(decompressed_data))
    except Exception as e:
        print(f"[{objid}] Error opening FITS file: {e}")
        return

    # Use the primary HDU and its WCS to compute the cutout
    hdu = hdul[0]
    data = hdu.data
    header = hdu.header
    w = WCS(header)
    # Convert RA,Dec to pixel coordinates
    px, py = w.all_world2pix(center_ra, center_dec, 0)
    px, py = int(px), int(py)
    
    cutout_size = 128
    half_size = cutout_size // 2
    
    ny, nx = data.shape
    # Ensure indices are within bounds
    x0 = max(px - half_size, 0)
    x1 = min(px + half_size, nx)
    y0 = max(py - half_size, 0)
    y1 = min(py + half_size, ny)
    
    if (x1 - x0) < cutout_size or (y1 - y0) < cutout_size:
        print(f"[{objid}] Warning: cutout size is smaller than expected.")
    
    subimage = data[y0:y1, x0:x1]
    
    # Create a new WCS for the cutout
    w_cut = w.slice((slice(y0, y1), slice(x0, x1)))
    cutout_header = w_cut.to_header()
    
    hdu_cut = fits.PrimaryHDU(data=subimage, header=cutout_header)
    output_filename = f"{folder_location}/{objid}.fits"
    hdu_cut.writeto(output_filename, overwrite=True)
    
    print(f"[{objid}] Cutout saved as {output_filename}")
    hdul.close()


