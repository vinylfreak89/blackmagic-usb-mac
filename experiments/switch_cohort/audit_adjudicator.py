#!/usr/bin/env python3
"""Audit what an adjudicator actually read, from its own transcript.

The blind exchange for this cohort could not be made structurally isolated in time: the other
agent's verdicts live in a LINKED WORKTREE of this repository, so they are reachable from here by
`git show v10-engine:<path>` or by plain absolute path (see EXCHANGE_PROTOCOL.md, hole 2). An
adjudicator working here is therefore instructed not to look rather than prevented from looking.

Testimony would be weak. This is evidence instead: every tool call the adjudicator made is read out
of its transcript and classified. It cannot certify isolation retrospectively, but it can show
whether the reachable material was in fact reached.

  audit_adjudicator.py <transcript.jsonl> [--panels-dir DIR]
  -> tool census, files read inside and outside the panel set, and any call touching the other
     agent's verdicts, its branch, the session transcript or a repository search.
"""
import argparse, json, re, collections, os

SENSITIVE = ("VERDICTS", "v10-engine", "blackmagic-v10", ".claude/projects",
             "git show", "git log", "git cat-file", "git worktree")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("transcript")
    ap.add_argument("--panels-dir", default="experiments/switch_cohort/panels")
    a=ap.parse_args()
    panel=re.compile(re.escape(os.path.basename(a.panels_dir.rstrip('/'))) + r"/cohort_\d+\.png$")
    tools=collections.Counter(); inside=set(); outside=set(); flagged=[]
    with open(a.transcript) as f:
        for ln,line in enumerate(f):
            try: d=json.loads(line)
            except Exception: continue
            c=d.get("message",{}).get("content")
            if not isinstance(c,list): continue
            for b in c:
                if b.get("type")!="tool_use": continue
                tools[b.get("name")]+=1
                s=json.dumps(b.get("input",{}))
                fp=b.get("input",{}).get("file_path")
                if fp: (inside if panel.search(fp) else outside).add(fp)
                if any(k in s for k in SENSITIVE): flagged.append((ln,b.get("name"),s[:300]))
    print(f"tool census: {dict(tools)}")
    print(f"panel files read: {len(inside)}")
    print(f"other files read: {len(outside)}")
    roots=collections.Counter(os.path.dirname(p) for p in outside)
    for r,n in roots.most_common(): print(f"    {n:4d}  {r}")
    print(f"\ncalls touching the other agent's verdicts, its branch, the session transcript, "
          f"or a repository search: {len(flagged)}")
    for ln,n,s in flagged: print(f"    line {ln}  {n}  {s}")
    print("\n⚠️ A clean result shows the material was not reached. It does NOT show it was "
          "unreachable, and it is not a substitute for structural isolation.")

if __name__=="__main__": main()
