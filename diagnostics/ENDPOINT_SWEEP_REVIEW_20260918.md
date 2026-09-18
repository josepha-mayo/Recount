# Endpoint sweep: request failure, not a speech score

18 September 2026.

## What the returned file supports

The user's `Recount-Endpoint-Sweep.json` reports three configuration attempts, each with only `provider error`, and `best_observed: null`. No configuration has a usable speech/ledger score. The aggregate `sessions: 3` field counts attempts, not verified provider Begin receipts. Audio sent, successful session count, original error codes and rejection descriptions cannot be recovered from that file.

Both previously scored human holdouts remain failed. This sweep is development debugging and is not a third holdout.

## Concrete defects in the supplied sweep script

1. The raw WebSocket query appends `keyterms_prompt` separately for each term. AssemblyAI's documented raw query expects one JSON-stringified array. The new diagnostic serializer uses one `keyterms_prompt=JSON.stringify(terms)` value.
2. The old `safeEvent` omitted the provider `error` text. Its handler replaced the event with the literal `provider error`; the outer catch then discarded the partial event log. Consequently the returned report cannot establish the original rejection cause.
3. Failure before Begin could exit without closing the socket. The private diagnostic runner now closes on every exit and records close code/reason, Begin count and audio bytes. It stops on the first error instead of trying three further configurations.

The malformed query is a verified local contract defect and a plausible explanation for the rejection, not a retrospectively recovered server error.

## Scope of the correction

`diagnostics/request-contract.mjs` and its offline tests validate serialization and retain sanitized diagnostic details. They do not modify the deployed app, confidence floors, parser, ledger, audio, expected answers, or holdout scoring code. Fifteen public unit checks cover the helper. The private packet additionally exercises socket lifecycle and packet handling with eleven simulated-transport checks (26 total locally passed checks). These are mocks, not new AssemblyAI success receipts.

The bounded private diagnostic repeats only the first prior candidate's 160/400 ms timing with the same contextual text and terms, correcting their encoding. It waits for a valid Begin before sending the already-exposed recording. One network attempt, no automatic retries. A successful development replay cannot establish independent human performance or select a production setting by itself.

The current working runtime's public-endpoint probe failed DNS resolution before HTTP. No human audio was uploaded from that runtime. Network-capable local execution remains necessary.

## Official contracts checked

- https://www.assemblyai.com/docs/streaming/prompting-and-keyterms (raw WebSocket JSON-array encoding)
- https://www.assemblyai.com/docs/streaming/common-session-errors-and-closures (`Error.error_code`, `Error.error`, and close-frame details)
- https://www.assemblyai.com/docs/streaming/api-spec/streaming-websocket (supported parameters and session messages)

No private recording, judge access code, permanent API key, or private transcript is committed here.
