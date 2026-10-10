# What each member should be able to show and explain (checklist, not a script)

Say it in your own words. The brief penalises read-out scripts and AI help during the demonstration.

**Member 1 (IT24103045) - Platform & architecture**: `docker-compose.yml` services/networks/limits; `deploy.sh` from scratch; built vs approved diagram; ports table; CTFd flag submit/hints/dependencies; `isolation.sh` + `isolation_test.sh` output; `resources.sh`; `reset.sh`; own scripts: `deploy.sh`, `isolation.sh`, `setup_ctfd.py`.

**Member 2 (IT24102161) - Stages 1-3**: for each stage show the builder (`challenges/cnr-0X/build.py`), the generated files, where the flag/clue is placed, live solve with browser/exiftool/steghide/CyberChef, hints, reset (`reset.sh files`); own solver `solvers/m2_solve_stage1_3.py` - explain every function.

**Member 3 (IT24101451) - Stages 4-6**: Flask portal code and the exact flaw, Burp/ZAP request tampering live; evidence builder + timezone traps + Autopsy/CLI timeline; PCAP builder + Wireshark filters + SSH container (Dockerfile, entrypoint, permissions) live solve; hints; resets; own solvers `m3_solve_stage4/5/6.py`.

**Member 4 (IT24102239) - Integration/testing**: end-to-end flag chain (what each stage hands to the next); run `tests/m4_e2e_test.py` and explain TC groups; unintended-solution checks; reset/recovery test (tamper a file, run `reset.sh files`; recreate stage 4/6); risk-register outcomes; `docs/design_changes.md` with justifications.

Before recording: run everything on the real VM, fix any failures, blind-test with a non-author, note real solve times, commit under your own names (commit history is part of your evidence), mention tools/references in the video.
