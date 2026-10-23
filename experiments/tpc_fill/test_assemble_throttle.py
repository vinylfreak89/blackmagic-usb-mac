#!/usr/bin/env python3
"""The assembler's upload brake, against a stand-in for JuiceFS's metrics: while the backlog it reports is over the limit
the copy holds, then resumes; the copy is byte-identical; an unreadable counter stops the run. usage: test_assemble_throttle.py SOURCE.tpc"""
import hashlib, http.server, json, os, subprocess, sys, tempfile, threading
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = sys.argv[1]; LIMIT = 600 << 20
answers = [8 << 30, 8 << 30, 1 << 30]; asked = []
class M(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        v = answers[min(len(asked), len(answers) - 1)]; asked.append(v)
        body = ('# HELP x\njuicefs_staging_block_bytes{vol_name="captures"} %d\n' % v).encode()
        self.send_response(200); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
srv = http.server.HTTPServer(('127.0.0.1', 0), M); threading.Thread(target=srv.serve_forever, daemon=True).start()
d = tempfile.mkdtemp(); work = os.path.join(d, 'work'); os.makedirs(work); json.dump({}, open(os.path.join(work, 'plan.json'), 'w'))
def run(dst, url):
    env = dict(os.environ, ASSEMBLE_THROTTLE='always', JUICEFS_METRICS=url, LIMIT_BYTES=str(LIMIT), ASSEMBLY_JSON=os.path.join(d, 'a.json'))
    return subprocess.run([sys.executable, os.path.join(HERE, 'assemble.py'), SRC, dst, work], env=env, capture_output=True, text=True, cwd=HERE)
r = run(os.path.join(d, 'out.tpc'), 'http://127.0.0.1:%d/metrics' % srv.server_port)
assert r.returncode == 0, r.stderr[-800:]
assert 'holding the copy' in r.stderr and 'writing again' in r.stderr, r.stderr[-800:]
a = json.load(open(os.path.join(d, 'a.json'))); n = a['bytes']
with open(SRC, 'rb') as f: want = hashlib.sha256(f.read(n)).hexdigest()
assert a['sha256'] == want and os.path.getsize(os.path.join(d, 'out.tpc')) == n, (a['sha256'], want)
r = run(os.path.join(d, 'out2.tpc'), 'http://127.0.0.1:1/metrics')
assert r.returncode != 0 and 'cannot be read' in r.stderr, r.stderr[-400:]
srv.shutdown(); import shutil; shutil.rmtree(d)
print('assemble throttle: all tests passed (held for %d readings, copy of %d bytes identical)' % (sum(1 for x in asked if x > 6 << 30), n))
