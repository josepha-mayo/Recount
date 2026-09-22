# Recount: Finish the Stocktake

**A saved row is not a finished stocktake.**

Recount is an AssemblyAI-powered voice stocktaking prototype that keeps unfinished work visible. Count an item, move to another, return to a review queue, and hand over a sheet that separates confirmed stock from unresolved or uncounted items.

[Open the application](https://recount-voice.netlify.app/) · [Current live acceptance](verification/CLOSEOUT_LIVE_ACCEPTANCE_20260922.json) · [Existing LabLab team](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/recount)

Built solo by Joseph Ayanda, Nigeria, for the AssemblyAI Voice Agent Hackathon.

## The workflow

1. Speak one catalogue item, whole-number count and explicit unit. A neural voice reads back the draft.
2. Confirm by repeating the current quantity. A mismatched confirmation does not save it. Outside capture, an explicit on-screen confirmation is also available.
3. Name the next item on its own to park an unfinished draft in **Needs review**. Parked work is not confirmed stock.
4. Use **Save session** and **Open session** to resume exported work after a page reload. Opening a review does not confirm it.
5. Inspect **Stocktake closeout**. A confirmed zero is different from **Not counted**. The complete-stocktake CSV remains blocked while any scoped item is unresolved. A regular partial CSV is still available and is not presented as a completed stocktake.

The review handoff lists status, confirmed quantity, open drafts and confirmation method without transcript text, audio or credentials. Session exports, in contrast, contain transcript/action history and should be shared deliberately.

## Current demonstration: an interrupted multi-item task

The September 22 public-site run staged Beans 27 bags, parked that draft, counted Cooking oil 16 bottles, rejected a confirmation of 15, and confirmed Soap 0 bars. Rice remained uncounted.

At that checkpoint, the handoff reported **2 confirmed / 1 needs review / 1 not counted**. The session was explicitly saved, the page reloaded, and the saved session reopened. Beans was restored and deliberately confirmed on screen. A second voice session counted and confirmed Rice 41 bags. Only then did closeout reach **4 / 4 resolved** and enable complete export.

The exact CSV contained:

```csv
item,quantity,unit
Beans,27,bags
Cooking oil,16,bottles
Soap,0,bars
Rice,41,bags
```

The test checked row contents independently of ordering. [Receipt and source identifiers](verification/CLOSEOUT_LIVE_ACCEPTANCE_20260922.json); [run 35771644932](https://github.com/josepha-mayo/Recount/actions/runs/35771644932).

**What was real:** the public deployment, two token authorizations, two AssemblyAI sessions, nine finalized turns, nine read-backs, ledger transitions, session reopening and exact downloads. **What was generated:** the microphone input used stock Kokoro speech. Three counts were speech-confirmed; Beans used the on-screen control. This was one scripted integration task, not a human usability trial or an entirely hands-free run.

## How it works

Browser AudioWorklet capture sends PCM audio through a short-lived AssemblyAI streaming session. Finalized turns become actions in a deterministic, revision-aware ledger. The grammar keeps item, quantity and unit explicit; unsupported conversions are not guessed. Capture pauses during neural read-back and resumes in the same provider session. Startup or transport failures retain a visible explanation and hold uncertain work for review.

`web/closeout.mjs` derives completion from the ledger without changing recognition or count values. It exposes omissions and unresolved drafts rather than treating every nonempty CSV as a finished task. There is no extra general-purpose language model deciding inventory writes.

Permanent provider credentials stay server-side. Deployment generates a server-only one-way judge-code verifier from the existing Actions secret. Do not put the code, generated verifier or provider credentials in public descriptions, source, screenshots or media.

## Scope and limits

The catalogue currently contains **four illustrative items**: rice, beans, cooking oil and soap. Counts are whole numbers; supported units are fixed for those items. Arbitrary catalogue import, stock-on-hand variance comparisons and direct inventory-system writes are not implemented.

Confirmed means explicitly accepted in this local session, not independently verified physical stock. The history and handoff are not tamper-proof. Recovery requires an explicit saved session: unsaved work can be lost on refresh. There are no orders, payments or production inventory writes.

Two earlier frozen human recordings failed their four-count task and remain failed. Generated-input success does not establish physical-microphone, accent, noise or customer-productivity performance. The confidence floors are development heuristics, not calibrated probabilities. Historical failures and development replays remain in `evaluation/`, `diagnostics/`, `migration/` and `verification/`.

## First buyer and next validation

The initial buyer hypothesis is a small-stockroom manager already using a spreadsheet. The proposed per-location product adds a voice-and-review layer rather than replacing a warehouse system. Neither revenue nor willingness to pay has been established.

A first operator pilot must compare exact final counts, unresolved items, voice-only versus assisted completion, and time against the current workflow. Catalogue import and integrations follow demonstrated dialogue usefulness, not the other way around. Voice inventory and confirmation already exist in commercial products; the claim here is a focused, inspectable implementation of resumable stocktaking, not a category-first invention.

## Run locally

Python 3.11+ is enough for text/review mode:

```sh
python server.py
```

Use the printed loopback URL. Try `beans 27 bags`, then `oil`, then `16 bottles`. Review the parked Beans draft and inspect the closeout states. The example commands run the real parser; they do not force a successful result.

```sh
node --test --test-concurrency=1 tests/*.test.mjs
python -m unittest discover -s tests -p 'test_*.py' -v
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python tests/browser_closeout.py
```

Local browser closeout tests use typed commands, not live speech. `diagnostics/browser_stocktake_voice.py` is the separate provider-backed test and requires deliberate provider authorization. Do not confuse mocked protocol checks with live or human evidence.

## Submission

[Submission draft](SUBMISSION_DRAFT.md) and [narration script](submission/CLOSEOUT_NARRATION_20260922.json) describe the current multi-item workflow. Presentation media is supplied separately. A prepared package, team page, saved form or successful test is not final LabLab submission confirmation.
