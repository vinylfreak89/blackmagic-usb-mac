#!/usr/bin/env python3
"""check_capture.py RECORDING [--full] [--obs-logs DIR]

Checks one OBS + Shuttle recording without re-reading the capture, from:
  1. its sidecar(s), <recording>.registration.csv (+ .registration.partN.csv after a mid-recording
     restart): one row per unit the frameserver observed, with `published`, `drop_reason`,
     `preceding_ring_drops` and the device counter;
  2. OBS's own log: the plugin's `raw .tpc started/closed` lines (tee loss, control records dropped,
     spill read-back loss, write stalls), sidecar publication, USB host-loss lines and OBS's
     lagged/skipped frame counts.
With --full it also streams every .raw.tpc part (bounded memory, 8 MiB reads) and proves transport:
record chain intact, no transfer sequence gaps, no HostLoss / TransferError records, every picture
unit exactly 756,048 B, device counter +1 between adjacent picture units. --full reads every byte,
so it costs the file's size in reads (and downloads, on a cloud volume whose cache does not hold it).

RECORDING may be the .mov, the .mov.raw.tpc, the .mov.registration.csv, or a bare .tpc from
shuttle-capture; the others are found beside it. Prints what it checked and a verdict: PROBLEM lines
are loss or missing evidence, notes are normal device behaviour or presentation-only effects.
Exit status 0 = nothing wrong found, 1 = problems found, 2 = nothing to check.
"""
import argparse, collections, csv, glob, os, re, struct, sys, time

UNIT = 756048
MARK = b"\x00\x00\xff\xff"
MAGIC = 0x31504143
REC = struct.Struct("<IBBHIIII")
HOST_LOSS = {"PoolFull", "PublisherFull", "RingFullTail", "Hole"}   # frameserver.c: the host lost or shed it
problems, notes = [], []


def unit_format(fmt):
    """A unit header the parser accepts: the 0xe1xx/0xe8xx picture families, or 0x0800 no signal."""
    return fmt is not None and (fmt & 0xFF00 in (0xE800, 0xE100) or fmt == 0x0800)


# ---------------- 1. sidecar ----------------
def check_sidecar(path, expect):
    print(f"\n== Sidecar: {path}")
    if not os.path.exists(path):
        print("  not found")
        (problems if expect else notes).append(f"sidecar missing: {os.path.basename(path)}")
        return
    csv.field_size_limit(1 << 24)
    rows = pub = 0; unpub = collections.Counter(); ring = 0; epochs = set(); schemas = set()
    resets = audio_steps = 0; first = last = None
    prev = None; between = 0; covered = 0; gaps = []; missing = 0
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows += 1
            reason = r.get("drop_reason") or ""
            ring_here = int(r.get("preceding_ring_drops") or 0); ring += ring_here
            if reason == "RingFullTail":          # a range marker, not a unit: its epoch/counter cells are zero
                between += 1; continue
            epochs.add(r.get("epoch")); schemas.add(r.get("schema_version"))
            if r.get("reset_before") == "1": resets += 1
            if (r.get("audio_step_samples") or "0") not in ("0", ""): audio_steps += 1
            if r.get("published") != "1":
                unpub[reason or "(none given)"] += 1; between += 1; continue
            pub += 1
            c = int(r["counter_extended"]) if (r.get("counter_extended") or "").lstrip("-").isdigit() else None
            if c is None or c < 0: continue
            first = c if first is None else first; last = c
            if prev is not None and c != prev + 1:
                if between or ring_here: covered += 1     # the units in between are in the sidecar or counted as ring drops
                else: gaps.append((prev, c)); missing += max(0, c - prev - 1)
            prev = c; between = 0
    print(f"  rows {rows:,} (schema {','.join(sorted(s for s in schemas if s))}, epochs {','.join(sorted(e for e in epochs if e))}); "
          f"published picture counters {first}..{last}")
    print(f"  published {pub:,}; not published {sum(unpub.values()):,} {dict(unpub) if unpub else ''}")
    print(f"  ring-overflow drops {ring:,}; counter jumps covered by unpublished rows {covered}; "
          f"unexplained counter gaps {len(gaps)} ({missing:,} counters){' first ' + str(gaps[:5]) if gaps else ''}")
    print(f"  classifier resets {resets:,}; audio clock steps {audio_steps:,}")
    lost = {k: v for k, v in unpub.items() if k in HOST_LOSS}
    device = {k: v for k, v in unpub.items() if k not in HOST_LOSS}
    if lost: problems.append(f"sidecar: {sum(lost.values()):,} units lost by the host {lost}")
    if ring: problems.append(f"sidecar: {ring:,} units lost to ring overflow")
    if gaps: problems.append(f"sidecar: {len(gaps)} counter gaps with nothing logged in between, {missing:,} counters missing {gaps[:5]}")
    real_epochs = [e for e in epochs if e and e != "0"]
    if len(real_epochs) > 1: problems.append(f"sidecar: {len(real_epochs)} capture epochs (the device restarted mid-recording)")
    if device: notes.append(f"sidecar: {sum(device.values()):,} units not published as pictures because of how the device framed them {device} "
                            "(Short/ShortShown = short unit, Unframed/OtherShown = no marker, Complete = whole unit of a non-picture format "
                            "such as no-signal; expected around start-up, relock, a stopped deck and tape end)")
    if audio_steps: notes.append(f"sidecar: {audio_steps} audio clock steps (device audio discontinuities)")


# ---------------- 2. OBS log ----------------
def session_recording_name(tpc):
    """The recording name the plugin wrote into the .tpc's SESSION note (survives a rename)."""
    try:
        with open(tpc, "rb") as f: head = f.read(64 << 10)
    except OSError: return None
    off = 0
    while off + 24 <= len(head):
        m, t, ep, pi, seq, st, req, al = REC.unpack_from(head, off)
        if m != MAGIC: return None
        if t == 3:
            note = head[off + 24:off + 24 + al].decode("utf-8", "replace")
            m2 = re.search(r"recording=(.*?\.(?:mov|mkv|mp4|m4v|flv|ts|mpg))(?=\s|$)", note) or re.search(r"recording=(\S+)", note)
            return m2.group(1).strip() if m2 else None
        off += 24 + (al if t in (0, 3) else 0)
    return None


def check_obs_log(rec, logdir, name=None):
    name = name or os.path.basename(rec)
    print(f"\n== OBS log (recording name {name})")
    logs = sorted(glob.glob(os.path.join(logdir, "*.txt")), key=os.path.getmtime, reverse=True)
    for lp in logs:
        with open(lp, errors="replace") as f: lines = f.read().splitlines()
        hits = [i for i, l in enumerate(lines) if name in l and "[shuttle-source]" in l]
        if not hits: continue
        start, end = hits[0], hits[-1]
        mine = lines[start:end + 1]
        print(f"  {os.path.basename(lp)}: lines {start + 1}-{end + 1}")
        for l in mine:
            if name in l and any(k in l for k in ("stream started", "recording", "raw .tpc started", "sidecar")):
                print("  " + l[:240])
        started = [l for l in mine if "raw .tpc started:" in l and name in l]
        closed = [l for l in mine if re.search(r"raw \.tpc closed( WITH A WRITE ERROR)?:", l) and name in l]
        if started and not closed:
            problems.append("OBS log: the raw .tpc was started but never closed (recording still running, or OBS quit before closing it)")
        if not started: notes.append("OBS log: no raw .tpc for this recording (the plugin's raw-file option was off)")
        for l in closed:
            print("  " + l[:400])
            if "WITH A WRITE ERROR" in l: problems.append("raw .tpc: closed WITH A WRITE ERROR")
            m = re.search(r"tee loss video (\d+) pkts / (\d+) B, audio (\d+) pkts / (\d+) B, control records dropped (\d+)", l)
            if m:
                v, vb, a, ab, c = map(int, m.groups())
                if v or a: problems.append(f"raw .tpc: tee loss video {v} pkts / {vb} B, audio {a} pkts / {ab} B")
                if c: problems.append(f"raw .tpc: {c} control records dropped")
            m = re.search(r"loss episodes (\d+)", l)
            if m and int(m.group(1)): problems.append(f"raw .tpc: {m.group(1)} write-loss episodes")
            m = re.search(r"longest ([\d.]+) ms, (\d+) over 100 ms", l)
            if m and float(m.group(1)) > 1000: notes.append(f"raw .tpc writer: longest write {float(m.group(1)) / 1000:.1f} s ({m.group(2)} over 100 ms); absorbed, since tee loss is reported separately")
        for l in mine:
            if "the local spill could not give back" in l: problems.append("raw .tpc: " + l[l.find("the local spill"):][:200])
            if "HOST LOSS" in l: problems.append("USB: " + l[l.find("HOST LOSS"):][:180])
            if "sidecar" in l and re.search(r"INCOMPLETE|left unpublished|complete sidecar left at|not attached at recording stop|could not be opened|publish failed", l):
                problems.append("sidecar publication: " + l[l.find("[shuttle-source]") + 17:][:220])
        late = [l for l in mine if "delivery timing: counter" in l]
        if late: notes.append(f"OBS delivery: {len(late)} late handoffs logged during the recording (presentation only; capture unaffected)")
        # OBS's output summary sits around the plugin's closing lines; stop at the next session's start
        for i in range(start, min(len(lines), end + 40)):
            l = lines[i]
            if i > end and "[shuttle-source]" in l and ("stream started" in l or "raw .tpc started" in l): break
            m = re.search(r"Number of lagged frames due to rendering lag/stalls: (\d+) \(([\d.]+)%\)", l)
            if m and int(m.group(1)): notes.append(f"OBS output: {m.group(1)} frames lagged by rendering ({m.group(2)}%) - presentation only")
            m = re.search(r"skipped frames due to encoding lag: (\d+)/(\d+) \(([\d.]+)%\)", l)
            if m and int(m.group(1)): notes.append(f"OBS output: {m.group(1)} of {m.group(2)} frames skipped by encoding lag ({m.group(3)}%) - presentation only")
        return True
    print("  no OBS log mentions this recording (OBS keeps only its last 10 logs)")
    notes.append("no OBS log found for this recording (OBS keeps only its last 10 logs); the sidecar and --full still apply")
    return False


# ---------------- 3. full .tpc read (optional) ----------------
def check_tpc_full(path):
    print(f"\n== Full read: {path}")
    if not os.path.exists(path):
        print("  not found"); problems.append(f"no .tpc to read: {os.path.basename(path)}"); return
    fd = os.open(path, os.O_RDONLY); size = os.fstat(fd).st_size; BLK = 8 << 20
    state = {"buf": b"", "boff": 0, "retries": 0, "short": False}; pos = 0; t0 = time.time(); next_report = 10 << 30

    def need(n):
        buf, boff = state["buf"], state["boff"]
        while len(buf) - (pos - boff) < n:
            if boff + len(buf) >= size: break
            for k in range(30):
                try: chunk = os.pread(fd, BLK, boff + len(buf)); break
                except OSError: state["retries"] += 1; time.sleep(min(2 * (k + 1), 15))
            else: raise SystemExit(f"READ FAILED at offset {boff + len(buf)}")
            if not chunk: state["short"] = True; break      # the file ended before its stated size
            buf = buf[pos - boff:] + chunk; boff = pos
        state["buf"], state["boff"] = buf, boff
        return len(buf) - (pos - boff) >= n

    last = {0x83: None, 0x84: None}; gaps = collections.Counter(); types = collections.Counter(); bad_status = 0
    vpos = 0; lastmark = lastfmt = lastctr = None; tail = b""; exact = 0; nonexact = []; ctr_bad = []; units = 0
    nosignal = 0; corrupt = None
    while need(24):
        buf, boff = state["buf"], state["boff"]
        m, t, ep, pi, seq, st, req, al = REC.unpack(buf[pos - boff:pos - boff + 24])
        if m != MAGIC: corrupt = f"bad record magic at byte {pos:,}"; break
        if t > 4 or (t == 0 and not (al <= req <= 65536)) or (t == 3 and al > 65536):   # capture_core's plausibility bounds
            corrupt = f"implausible record (type {t}, req {req}, len {al}) at byte {pos:,}"; break
        plen = al if t in (0, 3) else 0
        if not need(24 + plen): corrupt = f"truncated record at byte {pos:,}"; break
        buf, boff = state["buf"], state["boff"]
        types[t] += 1
        if t == 0:
            if st: bad_status += 1
            if ep in last and pi == 0:
                if last[ep] is not None and seq != last[ep] + 1: gaps[ep] += 1
                last[ep] = seq
            if ep == 0x83 and al:
                s = tail + buf[pos - boff + 24:pos - boff + 24 + al]; base = vpos - len(tail); i = s.find(MARK)
                while i >= 0:
                    fmt = struct.unpack_from("<H", s, i + 6)[0] if i + 8 <= len(s) else None
                    if unit_format(fmt):
                        mk = base + i; c = struct.unpack_from("<H", s, i + 4)[0]
                        if lastmark is not None:
                            if lastfmt == 0x0800: nosignal += 1
                            else:                                    # picture units: judged on exact size
                                units += 1
                                if mk - lastmark == UNIT: exact += 1
                                else: nonexact.append(mk - lastmark)
                            if lastfmt == 0xE801 and fmt == 0xE801 and (c - lastctr) & 0xFFFF != 1: ctr_bad.append((lastctr, c))
                        lastmark, lastfmt, lastctr = mk, fmt, c
                    i = s.find(MARK, i + 1)
                vpos += al; tail = s[-7:]
        pos += 24 + plen
        if pos >= next_report:
            print(f"  ... {pos / 1e9:.0f} of {size / 1e9:.0f} GB ({(time.time() - t0) / 60:.1f} min)", flush=True); next_report += 10 << 30
    print(f"  read {pos / 1e9:.3f} of {size / 1e9:.3f} GB in {(time.time() - t0) / 60:.1f} min ({state['retries']} read retries)")
    print(f"  records by type {dict((['DATA', 'HostLoss', 'TransferError', 'SESSION', 'TICK'][k] if k < 5 else k, v) for k, v in types.items())}")
    print(f"  transfer sequence gaps: video {gaps[0x83]}, audio {gaps[0x84]}; packets with error status {bad_status}")
    print(f"  picture units {units:,}: exactly {UNIT:,} B {exact:,}, other sizes {units - exact:,}{' first ' + str(nonexact[:8]) if nonexact else ''}")
    print(f"  no-signal units {nosignal:,}; counter jumps between adjacent 0xe801 units: {len(ctr_bad)}{' ' + str(ctr_bad[:5]) if ctr_bad else ''}")
    if corrupt: problems.append("tpc: " + corrupt)
    elif pos < size: problems.append(f"tpc: stopped at byte {pos:,} of {size:,}" + (" (the file read back shorter than its size)" if state["short"] else ""))
    if types[1]: problems.append(f"tpc: {types[1]} HostLoss records")
    if types[2]: problems.append(f"tpc: {types[2]} TransferError records")
    if gaps[0x83] or gaps[0x84]: problems.append(f"tpc: transfer sequence gaps video {gaps[0x83]} audio {gaps[0x84]}")
    if bad_status: problems.append(f"tpc: {bad_status} packets with error status")
    if ctr_bad: problems.append(f"tpc: {len(ctr_bad)} counter jumps between adjacent picture units {ctr_bad[:5]}")
    if units - exact: notes.append(f"tpc: {units - exact} picture units not 756,048 B (the device emits a few short units at start-up or relock; the sidecar lists them)")
    if nosignal: notes.append(f"tpc: {nosignal:,} no-signal units (not loss)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("recording")
    ap.add_argument("--full", action="store_true", help="also stream every .raw.tpc part (reads every byte)")
    ap.add_argument("--obs-logs", default=os.path.expanduser("~/Library/Application Support/obs-studio/logs"))
    a = ap.parse_args()
    given = os.path.abspath(a.recording)
    if given.endswith(".tpc") and not given.endswith(".raw.tpc") and ".raw.part" not in given:   # a bare shuttle-capture file
        rec = given[:-4]; tpcs, sides, from_obs = [given], [], False
    else:
        rec = re.sub(r"\.(raw(\.part\d+)?\.tpc|registration(\.part\d+)?\.csv)$", "", given)
        part = lambda pat: sorted(glob.glob(glob.escape(rec) + pat), key=lambda p: int(re.search(r"part(\d+)", p).group(1)))
        tpcs = [rec + ".raw.tpc"] + part(".raw.part*.tpc")
        sides = [rec + ".registration.csv"] + part(".registration.part*.csv")
        from_obs = True
    print(f"Recording {rec}")
    for p in [rec] + tpcs + sides:
        print(f"  {os.path.basename(p):<60} {('%15s B' % format(os.path.getsize(p), ',')) if os.path.exists(p) else 'missing'}")
    if not any(os.path.exists(p) for p in tpcs + sides):
        print("nothing to check: no .raw.tpc and no sidecar"); return 2
    if len(sides) > 1 or len(tpcs) > 1: notes.append(f"recording has {max(len(sides), len(tpcs))} parts (the capture restarted mid-recording)")
    for s in sides: check_sidecar(s, expect=True)
    if not sides: notes.append("bare capture: no sidecar or OBS log to check")
    if from_obs:
        orig = session_recording_name(tpcs[0])
        if orig and orig != os.path.basename(rec): print(f"  recorded as {orig}")
        check_obs_log(rec, a.obs_logs, orig)
    if a.full:
        for t in tpcs: check_tpc_full(t)
    print("\n== Verdict")
    for p in problems: print("  PROBLEM  " + p)
    for n in notes: print("  note     " + n)
    if not problems: print("  OK: nothing lost" + ("" if a.full else " (sidecar + OBS log; add --full to prove the .tpc byte by byte)"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
