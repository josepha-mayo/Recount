# Recount

Count it. Correct it. Confirm it.

Independent voice stocktaking prototype by Joseph Ayanda. AssemblyAI transcribes speech; a deterministic ledger stages one absolute count, applies corrections to the same draft, and requires a quantity-echo confirmation before saving.

Standalone deployment: https://recount-voice-joseph.netlify.app

## Local use
Python 3.11+: `python server.py`, then open the printed loopback URL. Try `rice twelve`, `bags`, `no thirteen`, `confirm thirteen`. Export CSV or save and reopen the action history. Unsaved work is lost on refresh. Session files contain transcripts.

## Verification
Run `node --test tests/*.test.mjs` and `python -m unittest discover -s tests -p 'test_*.py' -v`. Browser tests require the pinned development requirements and Playwright Chromium. The migration adds a regression for continuing audio capture after a read-back: a terminal worklet flush previously stopped all later samples. A distinct non-terminal drain now preserves them. Earlier green mocked-transport tests did not exercise this real-worklet failure.

Earlier provider evidence: four authored synthetic-speech sessions using real AssemblyAI Streaming v3, original run 35269641978. That is integration evidence, not human/accent accuracy or a shopkeeper pilot. New deployment evidence is recorded separately. The original human holdout protocol and source identity are preserved in ORIGIN.json; no human recording has been received.

## Hosting
Netlify publishes `web` and bundles `netlify/functions`. Configure the four environment-variable names from `.env.example` privately, never in source. The permanent provider key stays server-side. A private judge code, same-origin check, CSRF cookie and short-lived streaming tokens gate voice access. The shared judge code is not individual-user authentication or a global billing cap. Individual sessions are capped at 90 seconds. No public unauthenticated token vending is intended.

## Current scope
Four illustrative catalogue entries, narrow English count commands, explicit units and no inferred pack conversions. CSV/session export only: no orders, payments, supplier messages or external stock-system writes. Browser speech quality depends on its installed voice. Count confirmation does not prove that the operator physically counted correctly.

## Provenance
This is a clean source export of Recount only, not a fork containing the portfolio or other projects. The old development commit remains linked in ORIGIN.json. Original code is MIT. AssemblyAI API contracts: https://www.assemblyai.com/docs/streaming/api-spec/streaming-websocket and https://www.assemblyai.com/docs/streaming/api-spec/generate-streaming-token.

Native browser APIs are now bound to their global receiver. The first standalone microphone test stopped with Illegal invocation before creating an AssemblyAI socket; that failed attempt is preserved rather than counted as a provider session. The added native-receiver regression accompanies the fix.

AssemblyAI documents a 50 ms minimum PCM packet. A continuing drain now retains a smaller tail until it can join the next valid packet; terminal flush preserves its samples and adds zero-valued trailing silence up to 50 ms. No transcript, quantity or confidence rule was changed. The preceding real provider attempt stopped after two finalized turns and is retained as a failed development run. Official contract: https://www.assemblyai.com/docs/streaming/common-session-errors-and-closures
