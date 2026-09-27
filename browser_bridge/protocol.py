import json
import struct
from browser_bridge.config import MAX_MESSAGE


def read_exact(stream, count):
    result = bytearray()
    while len(result) < count:
        chunk = stream.read(count - len(result))
        if not chunk:
            raise EOFError('Incomplete message')
        result.extend(chunk)
    return bytes(result)


def read_message(stream):
    header = stream.read(4)
    if not header:
        return None
    if len(header) < 4: header += read_exact(stream, 4-len(header))
    length = struct.unpack('=I', header)[0]
    if not 0 < length <= MAX_MESSAGE: raise ValueError('Message too large')
    value = json.loads(read_exact(stream, length))
    if not isinstance(value, dict): raise ValueError('Expected object')
    return value


def write_message(stream, value):
    data = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if len(data) > MAX_MESSAGE: raise ValueError('Response too large')
    stream.write(struct.pack('=I', len(data)) + data)
    stream.flush()
