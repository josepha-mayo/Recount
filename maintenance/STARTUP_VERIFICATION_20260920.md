# Recount startup continuation: 2026-09-20

## Deployed state

Public app: https://recount-voice.netlify.app/

Application source: `e1e47d6b5969055382f96b671b9a53c62e267ce2` (merged PR #9).
Netlify site: `df8d4f20-8294-4f70-820a-731fa440156b`.
New deployment: `6aaf23be193c477b8f80fa24`, published 2026-09-20T00:07:36.523Z.
The previous current deployment `6aaee2eb563b51a215214046` predated PR #9. A GitHub merge had not automatically published the startup fixes.

The deployed revision refreshes `/api/config` immediately before starting voice, adds allowlisted microphone/worklet/token/socket startup traces, and preserves numeric WebSocket close details. The server nonce cookie lasts 600 seconds. Refreshing config addresses a genuine stale-page failure path; it does not prove the cause of the user's earlier sessions. The previously merged change from 400 to 640 ms max-turn silence is included, but see the control result below.

## Executed evidence

Deployment run: https://github.com/josepha-mayo/Recount/actions/runs/35477912891
Artifact: `recount-startup-deployment`, ID `10594812868`.

- 203 Node tests passed, zero failures.
- 8 HTTP tests passed.
- Deployment helper exited zero. Netlify confirmed the new production deployment ready.
- 179 non-HTML public assets matched the pinned source exactly.
- Unauthorized production `/api/token` request returned 403.
- Initial strict identity gate failed on `/` HTML alone. Preserve that failed run. Its later provider/browser steps were skipped, not passed.

Independent verification: https://github.com/josepha-mayo/Recount/actions/runs/35478161129
Artifact: `recount-independent-startup`, ID `10595366036`.

- Fresh HTML fetch matched the pinned source exactly; expected and actual SHA-256: `49e4171c5d0ff5ac1f5bd086fb465a0f047edb69eae8e6c80dccdf5da7cf6c0c`. The earlier different response was not captured, so its cause is not established.
- Real AssemblyAI 400 ms control: token HTTP 200, WebSocket open, Begin, Termination. Therefore 400 ms was accepted and is NOT established as a startup rejection cause.
- Real AssemblyAI 640 ms probe: token HTTP 200, WebSocket open, Begin, 16,000 bytes of generated PCM silence sent, Termination. No human audio used.
- 13 browser recovery checks passed, with generated capture and mocked provider/speech events.
- 18 live-site bundled-audio browser checks passed, using actual MP3 decoding/Web Audio with mocked input and recognition. Desktop and mobile output RMS was 0.24865194907796614. Both screenshots were inspected.
- Independent verification job completed successfully.

## Limits and exact next step

The real-provider probe used the existing GitHub provider secret. It did NOT exercise the production judge-code token route, the user's microphone, or real speech recognition. Public browser checks mocked config/token/recognition. Do not describe these as an end-to-end human pass, or change previous failed human holdouts.

Next user-side check: hard-refresh the existing app, run Test speaker and acknowledge actual hearing, use the existing judge code and consent, then start voice. Say `Rice twelve bags`, wait for its reply, say `No, thirteen bags`, wait, then `Confirm thirteen`. Expected: one confirmed Rice row containing 13 bags. A failed start should be investigated from the new Download voice report; do not request repeated blind attempts.

If continuing diagnostic work: code inspection also shows some non-readback failure paths call onError before fail/onHold, while app act clears the visible error. This is an unpatched follow-up to reproduce and test; stage traces are still exported. Do not assume this UI error-order issue caused provider startup failure.
