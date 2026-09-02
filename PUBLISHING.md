# Publishing note

This repository's history was reconstructed once, before its first public push, so that
the project has its public shape from its first commit. The sequence of commits, their
dates, authorship, and co-author trailers are the originals; what changed inside them:

- **File and symbol names** were made descriptive throughout history (a file is born with
  the name it has today): the tagged capture container is `.tpc` (Tagged USB Packet
  Capture, record magic `CAP1`), the capture library is `capture_core`, the registration
  engine is `field_registration`, the experiment programs are named for what they do.
- **Tools were parameterized in the version that introduced them.** No Makefile or CLI
  defaults to a file that only the author had; every tool documents the properties its
  input must have, and inputs are arguments.
- **Fixture generators were folded into the commit that first needed them**, so every
  test in every commit runs against a synthetic input a stranger can regenerate.
  Measurements taken on the author's own captures remain in the design doc as recorded
  results, labelled as author-fixture validation; they are not asserted by any test.
- **Personal material was removed** from every version of every file and from commit
  messages: the identity and history of the test tape's recordings, and the author's
  archive, are not engineering content. Commits that carried nothing else were dropped.
- **Session logistics were removed** from every version: the author's disk space and file
  locations, cabling and hub arrangements, dates of individual runs, and which collaborator
  did what. Measured results and the reasons behind decisions were kept.
- **Narrative commit messages were replaced** by descriptions of what the commit changed
  or found. No message was given a marker saying it was rewritten.

Validation of the reconstruction: every commit was checked out in order; every C source
present compiles, every test present passes against generated fixtures, every Python tool
parses and answers `--help`, and every repository path referenced from the design doc
exists at that commit. A term audit over the full rewritten history (file contents and
messages) returns zero hits for the removed material and the old names.
