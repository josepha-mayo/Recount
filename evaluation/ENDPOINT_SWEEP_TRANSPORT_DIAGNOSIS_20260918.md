# Endpoint sweep: transport diagnosis, 18 September 2026

## Actual received result

The development sweep returned three rows, each containing only `error: provider error`, and `best_observed: null`. These are execution errors, not three measured transcription scores. The old `sessions: 3` field counts attempted configurations; it does not prove three successful provider sessions or a particular quantity of billed audio. Both prior human holdouts remain failures.

## Verified defects in the supplied diagnostic

Inspection of the actual supplied `Recount-Private-Endpoint-Sweep.zip` found:

1. The WebSocket URL used `q.append('keyterms_prompt', term)` repeatedly. AssemblyAI's JavaScript example requires one parameter containing `JSON.stringify([...])`.
2. Its event allowlist omitted `error` and `message`, and the handler replaced the server's description with the constant `provider error`. The catch path also discarded the event collection and did not retain the close code/reason.
3. The outer loop continued to every configuration after a technical failure, without reliably closing each failed socket.

The malformed keyterms parameter is a concrete request-format defect and a plausible explanation for the rejection, not a retrospectively proven server diagnosis. The original error description was not retained, so it cannot be recovered from the supplied summary. Neither the speaker's pauses nor speech-recognition quality can be diagnosed from these three generic errors.

## Repair delivered privately

`Recount-Endpoint-Repair.zip` changes the diagnostic request serialization and failure handling, not the application ledger or frozen scoring policy. It preserves the six original audio/protocol/scorer/frozen-code inputs byte for byte, retains the same three configurations and context, sends audio only after a Begin receipt, and stops the entire comparison on the first technical error. Error.error, error_code and the WebSocket close reason are saved with known secrets redacted. Attempted connections, acknowledged Begin events, completed sessions and submitted audio bytes are reported separately. Every exit closes its socket; intermediate evidence is checkpointed.

The packet contains the existing private audio and access file. It must not be published. It is not attached to this public repository. Output to return privately: `private-diagnostic-results/Recount-Endpoint-Diagnostic.json`.

## Executed verification, and limits

- 16 offline serialization, error-handling, cleanup, PCM-packet and selection tests passed.
- ZIP integrity and preservation of all six immutable inputs passed.
- An actual execution in the ChatGPT container stopped at the Recount config DNS lookup with `EAI_AGAIN`: zero provider sessions began and zero audio bytes were submitted.
- Therefore the repair is offline-tested but not yet validated against the live provider. No endpointing winner, speech improvement, new holdout pass, deployment or submission is claimed.
- No further human recording is requested at this stage.

## Official contracts checked

- https://www.assemblyai.com/docs/streaming/prompting-and-keyterms (one JSON-encoded keyterms array in connection query)
- https://www.assemblyai.com/docs/streaming/common-session-errors-and-closures (Error.error, error_code, and close-reason semantics)
- https://www.assemblyai.com/docs/streaming/api-spec/streaming-websocket

The common-word vocabulary list was retained only to isolate the serialization defect in this debugging comparison; it is not a recommendation for final production vocabulary boosting. The live provider documentation cautions against unnecessary common-word boosting.
