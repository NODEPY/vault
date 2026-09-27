from urllib.parse import urlsplit
import ipaddress
import re


def canonical_origin(value: str) -> str:
    """Exact HTTPS origin; fail closed on ambiguous host spellings.

    Use the browser's ASCII/punycode address for internationalized domains.
    Python's built-in IDNA 2003 codec can map a different site than browsers.
    """
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError('Invalid website address')
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError('Control characters are not allowed in a website address')
    parsed = urlsplit(value.strip())
    if parsed.scheme != 'https' or not parsed.hostname or '@' in parsed.netloc:
        raise ValueError('Use an HTTPS website address without embedded credentials')
    host = parsed.hostname.lower()
    if not host.isascii():
        raise ValueError('Use the browser ASCII/punycode address for this domain')
    try:
        host = str(ipaddress.ip_address(host))
    except ValueError:
        if len(host)>253 or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part) for part in host.split('.')):
            raise ValueError('Invalid host')
    if ':' in host: host = '[' + host + ']'
    port = parsed.port
    if port == 0:
        raise ValueError('Port zero is not supported')
    return 'https://' + host + (f':{port}' if port is not None and port != 443 else '')
