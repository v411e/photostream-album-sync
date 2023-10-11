import datetime, os, logging
from PIL import Image
import exiftool


def _iso_to_yyyymmddhhmmss(iso_string: str):
    # date_time_obj = datetime.datetime.fromisoformat(iso_string)
    try:
        date_time_obj = datetime.datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        date_time_obj = datetime.datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    new_date_str = date_time_obj.strftime("%Y:%m:%d %H:%M:%S")
    log.info(f"Converted {iso_string} to {new_date_str}")
    return new_date_str

def _convert_to_jpg_discard_exif(filename: str) -> str:
    if os.path.splitext(filename)[1].lower() != ".jpg":
        log.info(f"Converting {filename} to jpg.")
        new_filename = os.path.splitext(filename)[0] + ".jpg"
        with Image.open(filename) as im:
            im = im.convert("RGB")
            im.save(new_filename)
        os.remove(filename)
        return new_filename
    else:
        return filename

# Resize image with PIL to fit inside max_size
def resize_image(filename: str, max_size: int) -> None:
    im = Image.open(filename)
    exif = im.info["exif"]
    width, height = im.size
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int(max_size * height / width)
        else:
            new_height = max_size
            new_width = int(max_size * width / height)
        log.info(f"Resizing {filename} to {new_width}x{new_height}")
        im = im.resize((new_width, new_height), Image.LANCZOS)
        im.save(filename, exif=exif)

# Repair exif data
def repair_exif(filename: str) -> str:
    with exiftool.ExifTool() as et:
        et.execute(
                    "-overwrite_original",
                    "-all=",
                    "-tagsfromfile",
                    "@",
                    "-all:all",
                    "-unsafe",
                    "-icc_profile",
                    filename,
                )
    return filename

# Check file for exif date and update if necessary
def update_exif(filename: str, taken_at_from_server: str) -> str:
    with exiftool.ExifToolHelper() as et:
        metadata = et.get_metadata(filename)[0]
        if not metadata.get("EXIF:DateTimeOriginal"):
            log.info(f"No exif date found for {filename}.")
            filename = _convert_to_jpg_discard_exif(filename)
            if taken_at_from_server:
                log.info(f"Updating exif date for {filename}.")
                et.execute(
                    "-overwrite_original",
                    "-P",
                    "-AllDates="
                    + _iso_to_yyyymmddhhmmss(taken_at_from_server),
                    filename,
                )
                return filename
            else:
                log.warn(f"Could not find any date information for {filename}.")
                os.remove(filename)
    return filename

log = logging.getLogger()
