import base64
import gzip
import logging
import quopri
import random
import re
import string
from email import policy
from email.parser import BytesParser
from html import unescape
from html.parser import HTMLParser

import bleach
from bleach.css_sanitizer import CSSSanitizer
from bleach.sanitizer import ALLOWED_PROTOCOLS
from django.conf import settings
from django.core.files.base import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.timezone import now

logger = logging.getLogger(__name__)

css_sanitizer = CSSSanitizer(
    allowed_css_properties=settings.BLEACH_ALLOWED_CSS_PROPERTIES
)

# bleach's strip=True drops the tag but keeps its text, which for these elements
# would print raw CSS into the letter. Not a security control: bleach runs after.
# The \Z branch makes an unclosed tag one match, keeping this linear.
UNRENDERED_ELEMENT_RE = re.compile(
    r"<(style|script|title)\b.*?(?:</\1\s*>|\Z)", re.IGNORECASE | re.DOTALL
)

# Same noise bleach removes before it reads a URI's scheme.
URI_NOISE_RE = re.compile(r"[`\x00-\x20\x7f-\xa0�]+")
# No SVG: it is the one image format that can carry script.
DATA_IMAGE_RE = re.compile(r"data:image/(?:png|jpe?g|gif);base64,[a-z0-9+/=]*", re.I)


class HTMLFilter(HTMLParser):
    text = ""

    def handle_data(self, data):
        self.text += data


def allow_html_attribute(tag, name, value):
    if name == "style":
        return True
    if name not in settings.BLEACH_ALLOWED_ATTRIBUTES.get(tag, ()):
        return False
    if name not in ("href", "src"):
        return True
    # bleach's protocols apply to every tag, so "data" being allowed for pasted
    # images has to be narrowed back down here.
    uri = URI_NOISE_RE.sub("", "".join(unescape(value).split()))
    if "data:" not in uri.lower():
        return True
    return (tag, name) == ("img", "src") and bool(DATA_IMAGE_RE.fullmatch(uri))


def sanitize_html(html):
    return bleach.clean(
        UNRENDERED_ELEMENT_RE.sub("", html),
        tags=settings.BLEACH_ALLOWED_TAGS,
        attributes=allow_html_attribute,
        protocols=ALLOWED_PROTOCOLS | {"data"},
        css_sanitizer=css_sanitizer,
        strip=True,
    )


def prefix_gen(
    size=10, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase
):
    return "".join(random.choice(chars) for _ in range(size))


def date_random_path(instance, filename):
    return "letters/{y}/{m}/{d}/{r}/{f}".format(
        y=now().year, m=now().month, d=now().day, r=prefix_gen(), f=filename[-75:]
    )


def get_clean_email(email: str) -> str:
    email = str(email)
    if "," in email:
        email = email.split(",")[0]
    email = email[-99:]
    if "<" in email:
        email = email.split("<")[1]
    if ">" in email:
        email = email.split(">")[0]
    return email


def get_bytes_from_file(file):
    if isinstance(file, InMemoryUploadedFile):
        file_bytes = file.read()
    elif isinstance(file, File):
        with file.open(mode="rb") as f:
            file_bytes = f.read()
    else:
        logger.error(f"Invalid file type: {type(file)} of {file.name}")
        return b""
    eml_elements = [b"From:", b"To:", b"Subject:"]
    if any(element in file_bytes for element in eml_elements):
        return file_bytes
    try:
        decompressed_file_bytes = gzip.decompress(file_bytes)
        logger.info(f"Decompressed {file.name} using gzip.")
        return decompressed_file_bytes
    except Exception:
        logger.error(
            f"Skipping {file.name} due to eml decompression error.",
            f" {Exception}",
        )
    return b""


def get_html_from_eml_file(eml_file=None):
    if eml_file is None:
        logger.error("Skipping due to missing eml file.")
        return ""
    eml_bytes = get_bytes_from_file(eml_file)
    if eml_bytes == b"":
        logger.error(f"Skipping due to empty eml file: {eml_file.name}.")
        return ""
    msg = BytesParser(policy=policy.default).parsebytes(eml_bytes)
    html_content = ""
    for part in msg.walk():
        content_type = part.get_content_type()
        content_transfer_encoding = part.get("Content-Transfer-Encoding")
        charset = part.get_content_charset()

        # If the part is not "text/html" ("text/plain" or "multipart"), skip it
        if part.get_content_maintype() == "multipart" or content_type != "text/html":
            continue

        # Decode the part based on the encoding
        if content_transfer_encoding == "quoted-printable":
            decoded_part = quopri.decodestring(part.get_payload())
        elif content_transfer_encoding == "base64":
            decoded_part = base64.b64decode(part.get_payload())
        else:
            decoded_part = part.get_payload()

        # Decode the part based on the content type and add it to the content
        if type(decoded_part) is bytes:
            codec_map = {
                None: "utf-8",
                "windows-1252": "cp1252",
                "cp-850": "cp850",
            }
            if charset in codec_map.keys():
                charset = codec_map[charset]
            decoded_part = decoded_part.decode(charset)
        html_content += decoded_part

    # TODO - remove html cleanup after db migration to postgress or mysql8
    #        supporting natively utf8mb4 encoding
    html_content_cleaned = re.sub(r"[\U00010000-\U0010FFFF]", "(?)", html_content)
    return html_content_cleaned
