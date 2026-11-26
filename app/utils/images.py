"""Avatar processing: validate, square-crop, resize and re-encode as WebP.

Re-encoding through Pillow also strips EXIF/GPS data and any payload hidden in
the original file, so what we store is always a clean 256x256 WebP.
"""
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

AVATAR_SIZE = 256
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_INPUT_PIXELS = 25_000_000
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class AvatarError(ValueError):
    """Raised with a message that is safe to show to the user."""


def process_avatar(stream) -> bytes:
    raw = stream.read(MAX_UPLOAD_BYTES + 1)
    if not raw:
        raise AvatarError("Choose an image first.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise AvatarError("Image is too large (max 2 MB).")

    try:
        img = Image.open(BytesIO(raw))
        if img.format not in ALLOWED_FORMATS:
            raise AvatarError("Use a JPG, PNG or WebP image.")
        if img.width * img.height > MAX_INPUT_PIXELS:
            raise AvatarError("Image dimensions are too large.")
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise AvatarError("That file isn't a valid image.") from exc

    img = ImageOps.exif_transpose(img)
    img = ImageOps.fit(img.convert("RGBA"), (AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)

    out = BytesIO()
    img.save(out, "WEBP", quality=85, method=4)
    return out.getvalue()
