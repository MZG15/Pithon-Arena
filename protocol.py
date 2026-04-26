import pickle

import struct



def send_msg(sock, data):

    payload = pickle.dumps(data)

    length = struct.pack('>I', len(payload))

    sock.sendall(length + payload)



def recv_msg(sock):

    raw_len = _recv_exact(sock, 4)

    if raw_len is None:

        return None

    msg_len = struct.unpack('>I', raw_len)[0]

    raw_data = _recv_exact(sock, msg_len)

    if raw_data is None:

        return None

    return pickle.loads(raw_data)



def _recv_exact(sock, n):

    data = b''

    while len(data) < n:

        chunk = sock.recv(n - len(data))

        if not chunk:

            return None

        data += chunk

    return data
