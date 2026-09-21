# Recount

**Count it. Correct it. Confirm it.**

Correction-aware voice stocktaking by Joseph Ayanda for the AssemblyAI Voice Agent Hackathon.

- Application: https://recount-voice.netlify.app/
- Source: https://github.com/josepha-mayo/Recount
- Team: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/recount
- Current evidence: [21 September live acceptance](verification/LIVE_ACCEPTANCE_20260921.json)

Recount has its own repository and Netlify project. It is an experimental hackathon prototype, not a validated production inventory system.

## Current verified release: 21 September 2026

Application source `3ebb05fee80a17f8e031f5f8d1ea40a1b0c7b602` plus a deployment-generated, server-only judge-code verifier is deployed as Netlify `6ab16590c8d1a808fe600807`. The frontend is unchanged from `d9841875a27c95dcb50d36c91728fdce9252ebfb`. JavaScript, styles and the voice manifest matched the tested source byte-for-byte. HTML matched after removing only two exact recorded Netlify-managed additions; raw hashes and byte-equality results are retained.

The release passed 219 application tests, 11 native authorization tests and eight Python HTTP tests. The actual public authorization path returned 403 for a deliberately invalid code and 200 for the configured code. A real AssemblyAI connection accepted generated PCM audio and terminated normally. [Deployment evidence](https://github.com/josepha-mayo/Recount/actions/runs/35630443331).

An actual browser then completed the following on the public site, without mocked HTTP responses, recognition events or confidence values:

1. `Rice twelve bags` staged 12 bags without writing stock.
2. `No, thirteen bags` changed that same draft to 13.
3. `Confirm twelve` was rejected; the stock sheet remained empty.
4. `Confirm thirteen` saved exactly one Rice / 13 / bags record.

Four finalized provider turns produced four completed neural read-backs in one provider session. The exported CSV was checked byte-for-byte. A failed-code attempt followed by an accepted-code retry was also exercised. [Live browser evidence](https://github.com/josepha-mayo/Recount/actions/runs/35630591053).

**Input was generated Kokoro speech, not a human microphone recording.** The browser's speaker acknowledgement was an automated test control, not a claim that a person heard sound. This establishes integration behavior for the tested sequence, not general speech accuracy, real-device audio reliability or operator productivity.

## The task

A count is not just a transcript. “Twelve, no, thirteen” should update one draft, not add two stock movements. Recount keeps item, quantity and unit explicit. Spoken commits require the current quantity to be echoed. A vague yes, wrong unit or mismatched number cannot save the count.

When recognition is uncertain, a usable draft is retained for another confirmation or on-screen review. A standalone correction clears the old number before a following fragment supplies its replacement. Moving to a clearly named next item parks unresolved work in **Needs review** instead of silently saving or losing it. Resuming an old review cannot silently replace a newer confirmed count. Review drafts remain outside the stock CSV.

Capture pauses during each bundled neural read-back and resumes in the same provider session. A timeout or speech-output failure cancels playback and holds the session. Startup errors remain visible after cleanup, and private report exports contain bounded diagnostic classes instead of credentials. The 160/640 ms endpointing profile is a development choice, not a claimed optimum.

## Human evaluation: not passed

Both frozen human recordings remain failed holdouts: neither produced the four expected final counts. The first had nine finalized provider turns, the second four; each produced no stock writes. Rejecting everything is not a successful voice workflow.

A corrected diagnostic on already-seen audio produced 27 final events. Reusing those events with the later recovery ledger retained complete unconfirmed review drafts, but still made zero automatic saves. Some drafts contained intermediate counts; they are not four correct final counts. Staging and spoken-commit confidence floors remain 0.75 and 0.90, respectively. They are development heuristics, not calibrated probabilities.

Historical synthetic runs, failed human results, development replays and the new automated public-site run are separate evidence. The successful generated-input integration does not change either failed human result. Physical-device and interactive human validation remain outstanding. Private human audio and raw human diagnostic transcripts are not in this repository.

## Run and test locally

Python 3.11+ runs text/review mode:

```sh
python server.py
```

Open the printed loopback URL. Try `rice twelve bags`, `no`, `thirteen bags`, then `confirm thirteen`. A stale `confirm twelve` must not save. Start another named item to inspect the review tray.

```sh
node --test tests/*.test.mjs
node --experimental-strip-types --test diagnostics/functions-env.test.mjs diagnostics/judge-auth.test.mjs
python -m unittest discover -s tests -p 'test_*.py' -v
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python tests/browser.py
python tests/browser_voice_recovery.py
python tests/browser_startup_errors.py
```

Native TypeScript diagnostics use Node.js 22.16. The local browser tests mock authorization/ASR and generate audio; no provider key is required. They are not human speech tests. Unsaved work is lost on refresh. Session exports contain transcripts and use `recount-session-2`; incompatible older histories are rejected rather than silently rescored.

## Hosting, releases and access

Netlify publishes `web` and bundles `netlify/functions`. Provider configuration stays server-side:

```text
ASSEMBLYAI_API_KEY
RECOUNT_SIGNING_SECRET
RECOUNT_ALLOWED_ORIGIN=https://recount-voice.netlify.app
```

The manual **Recount production release** workflow uses repository Actions secrets `NETLIFY_AUTH_TOKEN` and `RECOUNT_DEMO_PASS`. `delivery/build-judge-verifier.mjs` derives a one-way verifier from the existing high-entropy generated judge code. Only that verifier enters the server bundle; the raw code is not embedded in the client, repository or function bundle. This avoids dependence on the host's failed attempts to persist the raw judge-code variable. A legacy server environment code remains supported when no compiled verifier exists.

This verifier is for generated high-entropy access codes, not human-chosen passwords. Voice access still requires the correct code, explicit audio consent, same-origin request and CSRF validation. Hosted sessions are capped at 90 seconds. The shared demonstration code is not individual-user authentication or a global billing limit. Never place it in public descriptions, source or recordings.

Publishing is manual-only on `master`. The release checks source identity, a real invalid-code rejection, actual configured-code acceptance, and a bounded provider connection. A green regression job alone is not a deployed release. The checked-in empty verifier fails closed until configured during an authorized deployment.

## Scope and provenance

Four illustrative catalogue entries and a narrow English command grammar. No inferred carton conversions, payments, orders, supplier messages or external production-inventory writes. A confirmed record does not prove that the operator physically counted correctly. No measured shopkeeper productivity or general accent-performance claim is made.

Original source lineage and migration receipts remain in [ORIGIN.json](ORIGIN.json), `migration/` and historical verification records. Failed deployment attempts and earlier human holdouts remain preserved. No competition submission is claimed without an actual submission confirmation.

Provider references: [streaming contract](https://www.assemblyai.com/docs/streaming/api-spec/streaming-websocket), [temporary tokens](https://www.assemblyai.com/docs/streaming/api-spec/generate-streaming-token), [session errors](https://www.assemblyai.com/docs/streaming/common-session-errors-and-closures).

MIT license. No private human recordings, model weights or font files are bundled.
