# Stop OBS's recording once OBS itself reports the recording has run for the target duration.
# Talks to OBS's built-in WebSocket server (v5 protocol, no authentication configured). Standard library only.
# usage: obs_stop_after.py <seconds> <logfile> [--probe]
import sys, os, socket, base64, json, struct, time

def log(path, msg):
    with open(path, 'a') as f: f.write(time.strftime('%H:%M:%S ') + msg + '\n')

class WS:
    def __init__(self, host='127.0.0.1', port=4455):
        self.s = socket.create_connection((host, port), timeout=10); self.buf = b''
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(('GET / HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n' % (host, port, key)).encode())
        while b'\r\n\r\n' not in self.buf: self.buf += self._recv()
        head, self.buf = self.buf.split(b'\r\n\r\n', 1)
        if b' 101 ' not in head.split(b'\r\n')[0]: raise RuntimeError('handshake refused: %r' % head[:80])
        hello = self.read()
        if hello.get('op') != 0: raise RuntimeError('no hello: %r' % hello)
        if 'authentication' in hello['d']: raise RuntimeError('server wants a password; not handled here')
        self.send({'op': 1, 'd': {'rpcVersion': 1, 'eventSubscriptions': 0}})
        ident = self.read()
        if ident.get('op') != 2: raise RuntimeError('not identified: %r' % ident)
        self.n = 0
    def _recv(self):
        d = self.s.recv(65536)
        if not d: raise ConnectionError('OBS closed the connection')
        return d
    def _need(self, n):
        while len(self.buf) < n: self.buf += self._recv()
        d, self.buf = self.buf[:n], self.buf[n:]; return d
    def send(self, obj, opcode=1):
        p = json.dumps(obj).encode() if not isinstance(obj, bytes) else obj
        mask = os.urandom(4); n = len(p)
        h = bytes([0x80 | opcode]) + (bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack('>H', n) if n < 65536 else bytes([0x80 | 127]) + struct.pack('>Q', n))
        self.s.sendall(h + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(p)))
    def read(self):
        while True:
            b0, b1 = self._need(2); op = b0 & 15; n = b1 & 127
            if n == 126: n = struct.unpack('>H', self._need(2))[0]
            elif n == 127: n = struct.unpack('>Q', self._need(8))[0]
            p = self._need(n)
            if op == 9: self.send(p, opcode=10); continue
            if op == 8: raise ConnectionError('OBS closed the connection')
            if op == 1: return json.loads(p)
    def request(self, kind):
        self.n += 1; rid = 'r%d' % self.n
        self.send({'op': 6, 'd': {'requestType': kind, 'requestId': rid}})
        while True:
            m = self.read()
            if m.get('op') == 7 and m['d'].get('requestId') == rid: return m['d']

def main():
    target = float(sys.argv[1]); lg = sys.argv[2]
    if '--probe' in sys.argv:
        w = WS(); st = w.request('GetRecordStatus'); print('status', st['requestStatus'], st.get('responseData'))
        sp = w.request('StopRecord'); print('stop while idle ->', sp['requestStatus']); return 0
    log(lg, 'armed: stop the recording at %.0f s of OBS record time' % target)
    seen = False; t_end = time.time() + 4 * 3600; fails = 0; w = None
    while time.time() < t_end:
        try:
            if w is None: w = WS()
            st = w.request('GetRecordStatus')['responseData']; fails = 0
            ms = st['outputDuration']
            if st['outputActive']:
                if not seen: log(lg, 'recording seen running, %.1f s in' % (ms / 1000)); seen = True
                if ms >= target * 1000:
                    r = w.request('StopRecord'); log(lg, 'StopRecord sent at %.1f s: %r' % (ms / 1000, r['requestStatus']))
                    for _ in range(60):
                        time.sleep(1)
                        if not w.request('GetRecordStatus')['responseData']['outputActive']: log(lg, 'CONFIRMED stopped'); return 0
                    log(lg, 'FAILED: still recording 60 s after StopRecord'); return 2
            elif seen:
                log(lg, 'recording ended before the target (stopped by someone else); nothing to do'); return 0
            time.sleep(1 if ms >= (target - 30) * 1000 else 5)
        except Exception as e:
            fails += 1; w = None; log(lg, 'connection problem %d: %r' % (fails, e))
            if fails > 120: log(lg, 'GAVE UP: OBS unreachable'); return 3
            time.sleep(5)
    log(lg, 'GAVE UP: no recording reached the target within 4 hours'); return 4
sys.exit(main())
