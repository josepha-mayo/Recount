# Recount: submission copy, 21 September 2026

The live authorization failure is fixed and a complete generated-speech interaction passes on the public application. Submission files are prepared separately in the conversation. This is not a claim that the final LabLab form has been submitted or that human microphone validation has passed.

## Title

Recount: Correction-Aware Voice Stocktaking

## Short description

A voice stocktaking prototype that keeps corrections on one draft, reads back the quantity, and saves only after explicit confirmation. Uncertain counts stay available for review; confirmed stock exports to CSV.

## Long description

### A count is more than a transcript

“Twelve, no, thirteen” should update one pending count, not create two inventory movements. Recount explores a hands-busy stocktaking workflow in which corrections remain attached to the item being counted and confirmation refers to the current quantity.

### How Recount works

AssemblyAI streaming transcription supplies finalized speech turns. Recount's revision-aware ledger keeps the item, quantity and unit explicit. Corrections replace the pending quantity. Spoken confirmation must echo that quantity: “confirm thirteen” can save a draft of thirteen; “confirm twelve” cannot. A generic yes is not permission to write stock.

A bundled neural voice reads back the draft. Microphone capture pauses during the reply and resumes in the same provider session. Unfinished drafts can be parked in a separate Needs review tray. They do not enter the stock sheet until reviewed and confirmed. Confirmed counts export as CSV, and a versioned session file preserves local actions for reopening.

The application uses a constrained command grammar, not a general-purpose dialogue model. Unsupported unit conversions are refused rather than guessed. Connection loss and ambiguous instructions hold work for review rather than silently confirming it.

### What the current demonstration establishes

On 21 September, an automated browser used the public deployment and real AssemblyAI calls to stage Rice 12 bags, correct the same draft to 13, reject “confirm twelve,” and save exactly one Rice / 13 / bags row after “confirm thirteen.” The downloaded CSV was checked exactly. The test also exercised a rejected access code followed by an accepted-code retry. Four finalized turns and four completed read-backs occurred in one provider session.

Only microphone input was generated using a stock neural voice. HTTP responses, recognition events, confidence values, read-back playback, ledger transitions and export were not mocked. A second successful run supplies the current recorded footage. Its narrated walkthrough combines explanatory slides with cropped real-time footage. The soundtrack is added stock narration, not the original browser audio or the builder's voice.

### Scope and next validation

Recount is a prototype with four illustrative catalogue items. It does not place orders, make payments or write to a shop's production inventory. Two earlier frozen human recording tests failed and remain documented. The new generated-input integration does not establish physical-microphone reliability, accent-wide recognition accuracy or customer productivity. Interactive human use, noisy environments and time to a correct count remain the next validation tasks.

Built solo by Joseph Ayanda.

## Technology and suggested category tags

Technology: AssemblyAI, Streaming Speech-to-Text, JavaScript, TypeScript, Web Audio, AudioWorklet, Netlify Functions, Kokoro, Playwright.

Suggested categories: Voice AI, Inventory, Productivity, Retail Operations. Use matching options actually offered by the submission form.

Platform: Web application.

## Links

- Application: https://recount-voice.netlify.app/
- Source: https://github.com/josepha-mayo/Recount
- Existing team: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/recount
- Current acceptance receipt: [verification/LIVE_ACCEPTANCE_20260921.json](verification/LIVE_ACCEPTANCE_20260921.json)
- Deployment and actual authorization: https://github.com/josepha-mayo/Recount/actions/runs/35630443331
- Initial live voice acceptance: https://github.com/josepha-mayo/Recount/actions/runs/35630591053
- Second capture and stock narration: https://github.com/josepha-mayo/Recount/actions/runs/35631975985

## Current media

The September 21 package contains `Recount-Cover.jpg`, `Recount-Presentation.pdf`, editable `Recount-Presentation.pptx`, `Recount-Walkthrough.mp4`, captions and supporting evidence. These files replace older recovery-only media. The walkthrough explicitly identifies generated test input and added stock narration. An unedited browser recording and the exact CSV are retained in the package's evidence folder.

The current slide deck describes the deployed correction/confirmation workflow and the verified integration, while retaining the two failed human holdouts. The video is a presentation of observed integration behavior, not a new human trial. No public video-host watch URL or completed media upload is asserted.

## Private judge handling

Text/review mode is open. Voice requires the existing private judge code and explicit microphone consent. Supply the code only through a field explicitly private to judges or an organizer-approved private channel. Never put the code in public descriptions, screenshots, source or recordings.

The sample interaction is Rice twelve bags, a correction to thirteen, deliberately wrong confirmation of twelve, then confirmation of thirteen. Wait for each read-back before continuing. The fixed deployment uses the same code previously supplied privately; no additional credential setup or rotation is required.

## Remaining submission checks

Review the files; check the actual form's media and field limits; complete the existing team's form and required uploads; provide judge access privately; and read back the final submission confirmation. Neither a prepared asset bundle, green test run nor team creation is a final submission receipt. Interactive physical-device human acceptance remains unverified.

The older September 20 credential-setup blockers are superseded by the passing September 21 deployment and live receipts above. Historical failed attempts and human results are preserved, not reclassified.
