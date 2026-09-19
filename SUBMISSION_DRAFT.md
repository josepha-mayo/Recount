# Recount: current submission draft

**Team exists. Project is not submitted.** This draft describes the deployed recovery release, not just the earlier synthetic-voice demonstration. The public team page was read again on 18 September 2026 and still stated that no submission had been made.

## Links

- Team: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/recount
- Source: https://github.com/josepha-mayo/Recount
- Application: https://recount-voice.netlify.app/
- Deployed-release receipt: [verification/INTERACTIVE_RECOVERY_RELEASE_20260918.json](verification/INTERACTIVE_RECOVERY_RELEASE_20260918.json)
- New public screenshot and narration build: https://github.com/josepha-mayo/Recount/actions/runs/35388255349

## Title

Recount: Correction-Aware Voice Stocktaking

## Short description

A voice stocktaking prototype with correction-aware drafts, quantity-echo confirmation and a separate Needs review tray. Recover unfinished counts without silently saving them; export only confirmed stock.

## Description

A stock count is more than a transcript. “Twelve, no, thirteen” should update one pending count, not create two inventory movements. An unclear confirmation should not destroy otherwise useful work or freeze the rest of the stocktake.

Recount uses AssemblyAI streaming transcription with a deterministic, revision-aware count ledger. It asks for explicit units, keeps corrections attached to their draft and requires an exact quantity echo for spoken confirmation. An operator can also inspect the visual read-back and explicitly confirm it. Unsupported pack conversions and vague confirmations do not silently become stock records.

The recovery release adds a Needs review tray. Moving to another named item parks an unfinished draft rather than discarding it or treating it as stock. Resuming it is a separate action, followed by review and confirmation. Confirmed records can be downloaded as CSV; a versioned session export preserves the action history for reopening.

The microphone is muted during the local spoken read-back. A timeout or speech-output error cancels speech and holds the session for review instead of resuming capture while the application is still talking. Browser tests exercise these transitions with simulated speech events. They are not a replacement for human speech validation.

The application is an independent Netlify project, with server-side provider credentials and short-lived streaming tokens. The catalogue currently contains four illustrative items. Recount does not place orders, make payments, message suppliers or modify a shop's production inventory.

## Evidence and limits

Two frozen, one-speaker human recording replays failed: each produced zero of four expected final counts and zero saves. They remain recorded failures. Zero writes alone is not proof of a useful or reliably safe product. Reuse of exposed recordings for recovery development is not held-out evidence, and unconfirmed review drafts are not completed counts.

Earlier authored synthetic-speech runs demonstrated actual AssemblyAI integration, including quantity correction and confirmation. They belong to earlier revisions and do not establish that the current release passes a human task.

The current release receipt identifies application commit `b82c262cd962415721c5654541ec5c82bc49223b` and Netlify deploy `6aad870e4dae12c26dae08e9`. Its checks comprise 146 code tests, eight HTTP tests, 32 standard browser checks, 13 interactive-recovery browser checks using mocked provider/speech events, and 20 actual public-site checks. Nine deployed assets matched their expected source bytes. These different checks are not independent human trials and must not be relabelled as recognition accuracy.

A later media capture exercised nine asserted public-site behaviors using typed commands and checked actual CSV/session downloads. It made no provider audio calls and uploaded no human recording.

## Current media

`Recount-Recovery-Presentation.pdf` and its editable PowerPoint describe the deployed recovery workflow, its failure handling, and the two failed human recording tests. The accompanying `Recount-Recovery-Walkthrough.mp4` is a narrated slide walkthrough built from real public-site screenshots and typed-input actions. Narration uses a stock neural voice. It is **not** a real-time screen recording, a new microphone test or a human validation result.

The older `Recount-Standalone-Narrated-Demo.mp4` remains historical provider-integration media using synthetic input. Do not silently present it as a demonstration of the new recovery release. Current assets are provided in the conversation; no LabLab upload or public YouTube watch URL is asserted here.

## Remaining path

1. Validate the current deployed microphone/read-back interaction in a genuine interactive session. Keep automatic voice completion, operator-assisted completion, wrong writes and unresolved items separate. Do not consume another unseen recording merely to tune known failures.
2. Finalize a current-release voice demonstration and accurate submission assets from what that session actually establishes.
3. Complete the existing LabLab team's form and asset uploads. Do not create another team or describe team creation as submission.
4. Supply the judge code only in a field explicitly private to judges; never publish it in screenshots, source or descriptions.
5. Read back the actual final submission confirmation.

Runtime variables are already configured on the independent site. This work does not require recreating the repository, setting up another account, or copying provider keys into chat. Automatic Git-to-Netlify linkage remains separate from the verified direct deployment.
