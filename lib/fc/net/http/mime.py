import logging
log = logging.getLogger("fc.net.http.mime")

mime_types = {
    # Text and Document Formats
    ".txt": "text/plain",
    ".html": "text/html",
    ".htm": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".json": "application/json",
    ".xml": "application/xml",
    ".csv": "text/csv",
    ".md": "text/markdown",

    # Image Formats
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".ico": "image/x-icon",

    # Audio Formats
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",

    # Video Formats
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",

    # Archive and Compressed Formats
    ".zip": "application/zip",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
    ".7z": "application/x-7z-compressed",
    ".rar": "application/vnd.rar",

    # Application and Binary Formats
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".odp": "application/vnd.oasis.opendocument.presentation",

    # Fonts
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".woff": "font/woff",
    ".woff2": "font/woff2",

    # Other
    ".exe": "application/octet-stream",
    ".bin": "application/octet-stream",
    ".iso": "application/octet-stream",
}

def is_jpeg(byte_array):
    # Check if the byte array starts with the JPEG SOI marker
    if len(byte_array) < 2:
        return False
    if byte_array[0] != 0xFF or byte_array[1] != 0xD8:
        return False

    # Optionally, check if the byte array ends with the JPEG EOI marker
    if len(byte_array) >= 2:
        if byte_array[-2] != 0xFF or byte_array[-1] != 0xD9:
            return False

    return True

def is_gif(byte_array):
    # Check if the byte array is long enough to contain the GIF signature
    if len(byte_array) < 6:
        return False

    # Define the valid GIF signatures
    gif87a_signature = b"GIF87a"
    gif89a_signature = b"GIF89a"

    # Check if the byte array starts with either GIF signature
    if byte_array[:6] == gif87a_signature or byte_array[:6] == gif89a_signature:
        return True

    return False

def is_png(byte_array):
    # Check if the byte array is long enough to contain the PNG signature
    if len(byte_array) < 8:
        return False

    # Define the PNG signature
    png_signature = b"\x89PNG\r\n\x1A\n"

    # Check if the byte array starts with the PNG signature
    if byte_array[:8] == png_signature:
        return True

    return False

def is_ico(byte_array):
    # Check if the byte array is long enough to contain the ICO signature
    if len(byte_array) < 6:
        return False

    # Check the first 4 bytes (reserved and type)
    if byte_array[0] != 0x00 or byte_array[1] != 0x00:
        return False
    if byte_array[2] != 0x01 or byte_array[3] != 0x00:
        return False

    # The last 2 bytes (number of images) can vary, so we don't check them
    return True

def get_mime_type_from_content(content):
    """requires someting to identify the content in the first 200 bytes.  'html' or '{' in a string
    or image type bytes

    Args:
        content (str | bytes): content to look at

    Returns:
        str: a mime type
    """
    try:
        if content is None or len(content)<10:
            log.info("Content is empty")
            return mime_types['.txt']
        log.info(f"get mime type for {type(content)} {content[0:200]}")
        # look at beginning 200 chars
        scontent = None
        bcontent = None
        content = content[0:200]

        try:
            scontent = content.decode('utf-8')  if isinstance(content,bytes) else content 
            scontent = begin.strip(' \r\n\t')
        except Exception:
            pass
                
        try:
            bcontent = memoryview(content.encode('utf-8') if isinstance(str) else content)
        except Exception:
            pass
            
        if scontent is not None and '<html>' in scontent:
            return mime_types['.html']
        elif scontent is not None and  (scontent[0] == '{' or scontent[0] == '['):
            return mime_types['.json']
        elif isinstance(bcontent,bytes):
            if is_jpeg(bcontent):
                return mime_types['.jpeg']
            elif is_gif(bcontent):
                return mime_types['.gif']
            elif is_png(bcontent):
                return mime_types['.png']
            elif is_ico(bcontent):
                return mime_types['.ico']
    except Exception as ex: 
        log.debug("cannot get mime type",exc_info=ex)
    return mime_types['.txt']

def get_mime_type_from_ext(ext, default_type = None):
    return mime_types[ext] if ext in mime_types else default_type