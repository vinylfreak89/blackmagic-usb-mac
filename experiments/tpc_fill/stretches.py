# The planner's stretches: the live sidecar's event rows (anything that is not a plain unit, or carries an audio step),
# grouped when within 400 rows of each other, and the byte range of the capture each group is read from.
# plan.py builds its fills from these; seam_check_output.py re-derives them to find each fill in a finished output.
def event_groups(sidecar):
    """(groups of event row numbers, total rows)"""
    marks = []; nrows = 0; hdr = None
    with open(sidecar) as f:
        for line in f:
            if line.startswith('#'): continue
            if hdr is None: hdr = line.rstrip('\n').split(','); iD = hdr.index('drop_reason'); iS = hdr.index('audio_step_samples'); continue
            r = line.split(',', iS + 2)
            if r[iD] != 'None' or r[iS] not in ('', '0'): marks.append(nrows)
            nrows += 1
    groups = []
    for i in marks:
        if groups and i - groups[-1][-1] <= 400: groups[-1].append(i)
        else: groups.append([i])
    return groups, nrows
def stretch_range(grp, per, size):
    """[lo, hi) of the capture read for one group (lo is then aligned forward to a record boundary)"""
    return max(0, int(grp[0] * per) - 45_000_000), min(size, int(grp[-1] * per) + 300_000_000)
