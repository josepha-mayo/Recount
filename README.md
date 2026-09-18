# Recount

**Count it. Correct it. Confirm it.**

Correction-aware voice stocktaking by Joseph Ayanda for the AssemblyAI Voice Agent Hackathon.

- Application: https://recount-voice-joseph.netlify.app/
- Source: https://github.com/josepha-mayo/Recount
- Team: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/recount
- Current release receipt: [verification/INTERACTIVE_RECOVERY_RELEASE_20260918.json](verification/INTERACTIVE_RECOVERY_RELEASE_20260918.json)

Recount has its own repository and Netlify project. It does not run inside the portfolio. This remains an experimental hackathon entry, not a completed or validated production stock system.

## Current release, 18 September 2026

Source `b82c262cd962415721c5654541ec5c82bc49223b` is deployed as Netlify `6aad870e4dae12c26dae08e9`. All nine deployed web assets matched the tested source. The existing server-side variables remained configured; an unauthorized token request returned 403. Deployment used a one-time authorized upload, not an automatic Git-to-Netlify connection.

The full software suite passed 146 Node checks, eight HTTP checks, 32 existing browser checks and 13 additional recovery-interaction checks. A separate public-site run passed 20 desktop/mobile checks, including the actual CSV/session downloads and review controls. See runs [35381776522](https://github.com/josepha-mayo/Recount/actions/runs/35381776522), [35382100504](https://github.com/josepha-mayo/Recount/actions/runs/35382100504) and [35382303646](https://github.com/josepha-mayo/Recount/actions/runs/35382303646).

The new browser recovery tests use a real browser, application and AudioWorklet, but generated silence and mocked provider/SpeechSynthesis events. Public-site checks use typed commands. **Neither is a human speech-recognition result.** No new provider audio requests were made for this release.

## The task

A count is not just a transcript. “Twelve, no, thirteen” should update one draft, not add two stock movements. Recount keeps item, quantity and unit explicit, and spoken commits require the same quantity to be echoed. A vague yes, wrong unit or mismatched number cannot save the count.

When recognition is uncertain, a usable draft is retained for another confirmation or on-screen review. A standalone correction clears the old number before a following fragment supplies its replacement. Moving to a clearly named next item parks unresolved work in **Needs review** instead of silently saving or losing it. Resuming an old review cannot silently replace a newer confirmed count. Review drafts remain outside the stock CSV.

Spoken read-backs are shorter than the full on-screen explanation. If speech synthesis errors or times out, it is cancelled before the microphone path is held; capture is not reopened while the reply may still be speaking. The client sends vocabulary as one JSON-array query parameter with the observed 160/400 ms development profile. That profile is not claimed optimal.

## Human evaluation: not passed

Both frozen human recordings remain failed holdouts: neither produced the four expected final counts. The first had nine finalized provider turns, the second four; each produced no stock writes. Rejecting everything is not a successful voice workflow.

A corrected diagnostic on already-seen audio produced 27 final events. Reusing those exact events with the later recovery ledger retained complete unconfirmed review drafts, but still made zero automatic saves. Those drafts include an intermediate count and must not be reported as four correct final counts. The confidence floors remain 0.75 for staging and 0.90 for spoken commits; they are development heuristics, not calibrated probabilities.

Historical synthetic-speech provider runs, failed human scores and subsequent development replays are separate evidence. Existing video/presentation assets describe earlier work, not a new human pass. An interactive live voice/retry validation and final LabLab submission remain outstanding. Private human audio and raw diagnostic transcripts are not in this repository.

## Run and test locally

Python 3.11+ is sufficient for text/review mode:

```sh
python server.py
```

Open the printed loopback URL. Try `rice twelve bags`, `no`, `thirteen bags`, then `confirm thirteen`. A stale `confirm twelve` must not save. Start another named item to see the review tray.

```sh
node --test tests/*.test.mjs
python -m unittest discover -s tests -p 'test_*.py' -v
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python tests/browser.py
python tests/browser_voice_recovery.py
```

The last command mocks the provider and generates silence; it is not a microphone/ASR test. No provider key is needed for these tests. Unsaved work is lost on refresh. Session exports contain transcripts and use `recount-session-2`; incompatible earlier histories are rejected rather than silently rescored.

## Hosting and access

Netlify publishes `web` and bundles `netlify/functions`. Store configuration only in the private environment:

```text
ASSEMBLYAI_API_KEY
RECOUNT_SIGNING_SECRET
RECOUNT_DEMO_PASS
RECOUNT_ALLOWED_ORIGIN=https://recount-voice-joseph.netlify.app
```

The permanent provider key stays server-side. Voice access requires the private judge code, explicit audio consent, a same-origin request, CSRF validation and a short-lived streaming token. Hosted sessions are capped at 90 seconds. The shared code is not individual-user authentication or a global billing limit. Never put it in public descriptions, recordings or source.

## Scope and provenance

Four illustrative catalogue entries and a narrow English command grammar. No inferred carton conversions, payments, orders, supplier messages or production inventory writes. A confirmed record does not prove that the operator physically counted correctly. No measured shopkeeper productivity or general accent-performance claim is made.

Original source lineage and migration receipts remain in [ORIGIN.json](ORIGIN.json) and `migration/`. Earlier failures remain recorded; the initial source import accidentally omitted the web directory and was corrected after clean-checkout CI detected it.

Provider references: [streaming contract](https://www.assemblyai.com/docs/streaming/api-spec/streaming-websocket), [temporary tokens](https://www.assemblyai.com/docs/streaming/api-spec/generate-streaming-token), [session errors](https://www.assemblyai.com/docs/streaming/common-session-errors-and-closures).

MIT license. No credentials, private human recordings, model weights or font files are bundled.
