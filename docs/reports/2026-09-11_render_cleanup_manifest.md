# Scratch render cleanup, 2026-09-11

Owner: "why is it in `/private/tmp` and not `/private/tmp/hw-session/v10/cap1_review.mp4`?
how many scratch and garbage renders are laying around" then "have it move the capture into
the proper place and clean up its garbage".

Contents captured BEFORE deletion. Nothing here is a `.tpc`: the acceptance captures and every
diagnostic slice are untouched.

## Deleted

| file | size | why it is spent |
|---|---:|---|
| `smoke.mp4` | 176K | smoke test of the render path, 06:40-06:42, superseded within the hour |
| `smoke2.mp4` | 188K | smoke test of the render path, 06:40-06:42, superseded within the hour |
| `locked_capture1_SUPERSEDED_no_switch_markings.mp4` |  19M | full duplicate of a superseded render whose replacement is at the owner-named path |
| `SP_raw_vstab_on_vs_off_4panel.mp4` |  93M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `SP_raw_vstab_on_vs_off_4panel_repaired.mp4` |  93M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `SP_vstab_on_vs_off_4panel.mp4` |  92M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `codex_ref_EP_w_2100s_stab.mp4` |  20M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `codex_ref_SP_vstab_off_stab.mp4` |  48M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `codex_ref_SP_w_300s_stab.mp4` |  48M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `engine_EP_stab.mp4` |  20M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `engine_SP_stab.mp4` |  48M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `engine_SP_vstab_on_vs_off_4panel.mp4` |  92M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `engine_composite_stab.mp4` |  22M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `engine_off_stab.mp4` |  48M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `raw_SP_vstab_off.mp4` |  48M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `raw_SP_vstab_off_repaired.mp4` |  48M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `raw_SP_vstab_on.mp4` |  48M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |
| `v3_composite_stab.mp4` |  22M | Sep 7 V-stabilize/three-tree comparison; conclusions recorded in the accepted post-mortem 2026-09-07_three_tree_comparison.md, and re-derivable from the preserved captures on the frozen branches |

## KEPT, and why

| file | size | why |
|---|---:|---|
| `hw-session/v10/cap1_review.mp4` |  19M | the deliverable, at his named path |
| `hw-session/v10/cap1_review_2026-09-10_prelock_1000x676.mp4` |  15M | NOT re-derivable -- made by a pre-lock engine that no longer exists, and it is the review artifact he may have seen on Sep 10. Re-derivable things were deleted; this is not one |
| every `*.tpc` | 7.2 GB | acceptance captures and diagnostic slices; CLAUDE.md says re-cut or re-take from the deck if lost |
