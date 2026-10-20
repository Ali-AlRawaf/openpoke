# v1 routing eval (archived)

These files built and ran the first version of the routing eval, which produced `results/v1/`. They're kept for reference and aren't runnable as they are: they import `evals.routing.*` paths that have since moved.

- `generate.py`: one-off Haiku generation for the distractor names, their task logs, the cards (through the production card updater), the older conversation filler and the summary
- `build_fixtures.py`: the hand-written world (core agents' histories, recent conversation, cases), plus the builder for `fixtures/state/` and `fixtures/rosters/`
- `run.py`, `score.py`: the v1 harness, which copied the interaction loop and stubbed tools by name, and the v1 scorer
- `recall.py`: offline recall@K for agent search, with four scoring methods compared
- `SPEC.md`: the full v1 spec (formats, labelling policy, harness contract)
- `fixtures/`: the v1 state, the 7 roster files, the generated JSON and the v1 `cases.json`
- `_stub_fixture/`: a tiny fixture used to test the v1 harness

The current suite needs only `fixtures/roster.json`, `fixtures/working_memory.log` and `fixtures/cases.json`. They were converted from the v1 files, and `roster.json` reproduced every v1 roster exactly before the v2 traps were added.
