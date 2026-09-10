# Frozen contract review

## Context supplied before the document was opened

This was not a context-free review. Before opening the frozen contract, I had automatically received the user's extensive AGENTS.md instructions for `/private/tmp/blackmagic-v10`. They described the Blackmagic Intensity Shuttle analog VHS capture project, its archival and downstream-rendering goals, hardware and USB protocol, measured capture results, transport provenance and damage handling, field-registration history and estimator limitations, and the owner's decisions about levels. In particular, I had already been exposed to project-specific distinctions between transport completeness and device-short units, raw preservation and corrected review output, and registration decisions and measured physical events. Those supplied instructions also included protocol and licensing history, replay information, and measurements that could influence expectations about this contract.

I also received general system/developer instructions, tool and agent descriptions, a skill catalog and permission rules, the workspace path and environment information, the user's recommended-plugin list, and the parent's bounded review task. No other reviewer's findings or review report were supplied in the task. I did not open any of the listed skills or repository instruction files. The AGENTS.md exposure was supplied in the conversation, not obtained by opening a file; absence of a file read or citation does not negate that exposure.

Procedural limitation: this formal exposure ledger was written after the first document read, rather than recorded separately before opening it as requested. It reports the context that was already present before that read; it is not a contemporaneous pre-read record. I cannot undo that sequencing deviation.

The only input artifact I opened for this review was `/private/tmp/contract-freeze-codex-20260911.TfdNRt/contract.md`. I read all 1,383 lines, including rereading portions after an initially truncated tool response. I did not inspect repository files, other instructions, reports, source code, Git state/history, web sources, or referenced artifacts. No subagents were dispatched. Thus the review is independent of other reviewers' answers and restricted in artifact access, but not isolated from prior project context. Findings below rely on the frozen document's own statements, not independent validation of its measurements, standards claims, implementation descriptions, or historical quotations.

## Result

Five consequential issues are supported: two expressly acknowledged unresolved decisions, two competing technical readings, and one competing review-disposition rule. These are not five proven implementation defects. Severity is described by what can differ in an implementation or acceptance workflow; there is no pass/fail verdict.

### 1. The second invalid-raster condition has no settled post-lock output or recovery disposition

**Locations:** lines 795–811, especially 800–806; lines 823–827; rule 13 at 1207–1214. The distinctions between retaining a placement, bypassing correction, and resetting learned state are explicitly established at 503–511.

The invalid class says the engine does not register or correct (797–798). Its second entry condition is a sufficiently long terminal black run with positively established absence of the head-switch region (807–811). However, the contract explicitly leaves that condition's disposition after an existing lock unsettled (800–806). Rule 13 specifies full reset for `0x0800` or absent regenerated rows, not for this terminal-black condition.

For an already applied `+2` correction, one implementer could retain that placement while declining new decisions; another could bypass correction and deliver the standard placement. The text itself identifies these as different pictures. Retained references, lock survival, and whether the next ordinary unit can resume correction or must reacquire are likewise undecided. The general phrase “does not correct” cannot supply all of those missing state transitions, and omission from the full-reset rule supplies no positive authorization to retain them.

**Consequence:** the same positively classified raster sequence can produce different visible output and different recovery behavior. This is an acknowledged incomplete disposition, not a newly discovered contradiction or an inference that absence can never be measured. It applies when the condition is positively established; uncertainty about whether it is established is a separate issue.

### 2. Caption-only acquisition is permitted, but the required field interleave is not determined for that route

**Locations:** Source lock at 724–743 and 767–781; Comb at 873–882; rule 8 at 1018–1030; acceptance at 1288 and 1362–1364; cadence statement at 1370–1372.

The contract permits geometry confirmed by qualified captions/VBI, and explicitly preserves caption confirmation when the comb cannot settle a candidate (880–882). A lock asserts stable geometry and aligned fields (751–756), while field precedence must be settled once per lock (1018–1019). Rule 8 then distinguishes three meanings of precedence and explicitly withdraws the claim that caption-only precedence follows from placed geometry. It asks what evidence determines the interleave and whether a lock without it may exist (1022–1030).

One reading permits caption-only acquisition and applies a conventional interleave, perhaps reading the acceptance output's “top field first” as that convention. Another withholds acquisition or corrective rendering until spatial interleave is independently established. The document does not authorize equating a render cadence/parity convention with the independent evidence that rule 8 says is missing. Requiring a successful comb in every such case would also narrow the explicitly permitted caption route.

**Consequence:** implementations can differ on whether and how to acquire and render the same caption-confirmed candidate. This is an expressly acknowledged unresolved interface between acquisition and rendering. It is not a claim that captions could never participate in an independently justified interleave determination.

### 3. “Last recorded row” does not uniquely identify the deck clip under the document's recorded-row definition

**Locations:** lines 463–467 and 475–476; Recorded row at 491–502; Offset d/clip at 683–704; the distinction between delivery window and picture quantity at 395–399; output padding at 1014–1017.

The measured description says that pass-through rows below the deck's clip contain near-blank remainder and decoder chroma noise (463–464), and that a chroma-noise row can lie below the band (475–476). “Recorded row” means a pass-through row that came through the analog decoder, distinguished from generated rows using qualified chroma noise or luma above blanking (491–494). By those words, an analog-decoded post-clip remainder can be recorded even though the deck no longer delivers picture there.

The clip definition nevertheless identifies two things as one: “the last row the deck delivers” and “the last recorded row's constant” (700–702). A reader following analog-decoder provenance can include the post-clip remainder when locating the last recorded row. A reader following the deck-content cutoff can exclude it. The text does not define the further distinction by which a row can satisfy the recorded-row provenance definition yet be excluded from the recorded-row endpoint used for the clip.

Qualification of noise populations alone does not resolve this semantic difference: distinguishing recorded material from device fill is not the same decision as identifying the end of deck-delivered material within the recorded region. This is not an assertion that the two endpoints are impossible to distinguish empirically.

**Consequence:** choosing different `C` values changes `E = C − T + 1` and `P = C − 22 − N` (683–697), and changes which output rows are replaced by legal black (1017). The ambiguity can therefore affect both geometry accounting and retained visible rows, rather than merely the label attached to a diagnostic measurement.

### 4. Optional switch evidence and the box-contact acquisition test give different readings when a switch is known to exist but its boundary is unresolved

**Locations:** lines 731–734 and 767–774; rule 8a at 1033–1038; rule 8b at 1064–1077; rule 8c at 1080–1086.

The source-lock definition makes head-switch evidence optional and says there is “no route-dependent switch requirement of any kind” (770–772). A count that was not measured stays Unknown without prohibiting source-lock acquisition (731–734, 773–774).

The boxed-source rule requires the box's lower outer boundary to meet a present switch region with no intervening source blanking (1065–1072). Contact permits acquisition, demonstrated separation prevents it, and an unresolved boundary does not establish contact (1073–1075). The stated exemption is a genuinely switch-free source, with failure to measure a switch explicitly insufficient to establish that exemption (1075–1077).

Consider an initial boxed candidate with independently qualified geometry and comb or caption confirmation, a source known to have a switch region, and insufficient current or retained evidence to establish the box-to-switch contact. The general lock rule permits the route without switch evidence. Reading contact as a necessary condition for boxed acquisition with a present switch prohibits it. Alternatively, reading “unresolved ... is not a failure of the test” as permission to acquire makes contact optional in precisely the cases where it cannot be established. These readings have different evidential requirements, and the explicit “no route-dependent” language does not state a box exception.

**Consequence:** the same candidate can acquire under one reading and remain uncorrected under another. This finding concerns the priority and scope of two acquisition requirements. It does not equate an unmeasurable switch with an absent switch, or claim that a numeric current switch line is the only possible way to establish contact. Previously qualified contact evidence could settle some cases; it does not settle the stated initial case with no such evidence.

### 5. Instrument disagreement has two competing adjudication dispositions

**Locations:** acceptance at 1271–1277 and the final disagreement procedure at 1358–1364.

The first acceptance passage separates disagreement about what a row is from disagreement about geometry. The former is decided on raw rows by both agents and listed; the latter goes to the owner and is not adjudicated by either agent (1275–1277).

The final procedure defines “every true disagreement” to include “the two instruments against each other on a unit,” requires owner review with a rendered frame, and concludes “Neither agent adjudicates these” (1360–1364). It does not preserve the earlier exception for row-identity measurement disagreements. A disagreement over whether the partial row is switch or picture is both a row-identity disagreement and a disagreement between the two instruments on a unit.

One reading sends that case to the agents for raw-row adjudication; another requires owner adjudication and forbids the agents from deciding it. Restricting the later phrase to geometry disagreements could reconcile them, but that restriction is not what its explicit enumeration says.

**Consequence:** acceptance can require different decision makers and artifacts for the same discrepancy, affecting whether a reference correction or an acceptance stage may be completed by the instruments' authors. This is a workflow consequence, not a claim of pixel corruption.

## Material limitations and tensions not counted as additional findings

- **Unbuilt discriminators are not impossibility proofs.** The document explicitly withholds an edge-identification method (128–136), requires independently identified calibration material (107–150), specifies Unknown when switch motion and picture motion cannot be separated (902–933), and limits the meaning of the box detector's errors (1189–1206). Those are empirical dependencies with conservative outcomes already specified. No text-only review can establish that an adequate method exists or cannot exist. I do not count every use of “qualified” as a separate missing algorithm.

- **Qualification can prevent application of an otherwise correct identity.** The `P`, `E`, `N`, and `d` relations are expressly conditional (689–697, 911–916, 946–953). A head-catch event does not by itself refute their algebra, and an observed extent must not automatically be treated as qualified displacement evidence. The separate displacement and switch-state decisions at 896–910 substantially address that trap. The accepted count expansion in rule 8c is also expressly carried into rule 4 and the acceptance invariant (963–966, 1278–1280), so I do not report “the count is fixed” versus that named exception as an independent contradiction.

- **Rendered picture position differs from crop-origin metadata.** Rule 8's stable-output requirement can coexist with per-unit crop-origin tracking: acceptance explicitly defines output as the stabilized visible picture (1277), and the OSD explanation describes the correction window moving to hold picture still (1353–1356). Merely placing the tracking and stable-output sentences side by side would not establish a conflict.

- **Historical quotations do not override express supersession.** Section 1's status statement (22–26), the later Source lock definition (724–743), and the withdrawn insert-based mechanism (785–788, 878–879) prevent the earlier “comb or head switch” and regenerated-caption statements from independently defining current confirmation routes. Similarly, removing procedural gates is not a claim that the promised technical correction was delivered (186–197), and implementation permission is distinct from the expressly retained acceptance order (1247–1257).

- **Cadence and comb coverage are distinguished.** The engine's absence of comb evaluation under a maintained lock is reconciled with the harness's independent evaluation and reporting coverage by 836–856. I do not treat every per-unit record as a demand for a new per-unit measurement, since 1218–1220 expressly says otherwise. Finding 2 is about the evidence for caption-only field interleave, not a demand for continuous comb evaluation.

- **Several dependencies are deliberately external.** The authoritative row header (15), pending-work tracker (520–521, 1368–1369), signal-state inputs (243–244, 982–987, 1136–1137), and capture logistics (1257–1258) were not inspected. I cannot certify their interfaces, whether they resolve an implementation detail, or whether the document accurately describes current code. The phrase that the engine “reads the raster only” sits beside an explicit signal-state architecture boundary; I read it as a responsibility distinction rather than enough evidence, by itself, of an impossible API.

- **The numerical policy has broad wording and explicit local choices.** The blanket rule at 17–18 coexists with a chosen pilot size explicitly not claimed as a sufficiency threshold (116–120), a memory-capacity comparator (716–723), owner-specified rules, and display choices. I do not infer an operational defect merely from the presence of a number without first establishing that it functions as an unauthorized decision threshold.

- **No empirical, source-code, or standards validation was performed.** In particular, I have not checked the actual clip populations, field order, filter behavior, measurement separability, or any claimed capture result. Findings 3–5 concern the competing readings the prose permits; they are not evidence that the implemented system currently takes either reading. The two explicitly open decisions in findings 1–2 are reported as known unresolved requirements, not concealed defects or proof of a failed design.
