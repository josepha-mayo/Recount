# Recount: current submission draft

**Not yet submitted.** The repository and application are independent. Team creation, human holdout scoring and the final event-form requirements are separate remaining steps.

## Links

- Source: https://github.com/josepha-mayo/Recount
- App: https://recount-voice-joseph.netlify.app/
- Event: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon
- Current software receipt: [migration/REGRESSION_RECEIPT.json](migration/REGRESSION_RECEIPT.json)

## Title

Recount: Correction-Aware Voice Stocktaking

## Summary

A voice stocktaking assistant that keeps corrections on one draft, asks for explicit units, and saves only after quantity confirmation. Includes review holds, CSV export and replayable session history.

## Description

A spoken stock count becomes difficult when someone changes their mind. “Twelve, no, thirteen” should produce one checked record, not two inventory movements.

Recount uses AssemblyAI streaming transcription to stage an absolute count for one catalogue item. It asks for missing units, applies corrections to the pending draft, and requires an explicit quantity echo such as “confirm thirteen” before saving. Vague confirmations and unsupported unit conversions do not create stock records. Duplicate, missing or conflicting transcript events have explicit handling, including a review hold when the input cannot be trusted.

The independent web app exports confirmed stock as CSV and can reopen a saved action history. In its recorded provider test, five finalized turns produced one Rice / 13 / bags record; a later cartons request did not change it. CSV content and session reopening were checked. This test used a disclosed synthetic voice through the actual provider, not a prewritten transcription response.

The standalone repository's fresh import passed 86 Node tests, eight HTTP tests and 18 Chromium checks. Human speech and shopkeeper usability evaluation remain pending. The catalogue is small, and the app does not write into a production stock system, place orders or make payments.

## Media prepared

A 140.32-second, 1920-by-1080 narrated MP4 was delivered in the conversation as `Recount-Standalone-Narrated-Demo.mp4`. SHA-256: `890965557c3d0b1b1a29713cfe17988b9663b8b873a4bfd42462d953d710e972`.

It contains the actual recorded independent-site provider sequence at its original speed, plus stock neural narration around it. The original synthetic microphone fixture is restored using the recorded capture offset. Browser speech synthesis output was not recorded. There is no human microphone holdout in this video. The MP4 and cover are available in the conversation's media packet; no public watch URL is asserted here.

## Team setup

Team name: **Recount**. Member and leader: **Joseph Ayanda**, solo, Nigeria. Do not recruit or invite teammates.

Team idea: “We are building Recount, a voice stocktaking assistant that keeps corrections on one draft and saves only after the quantity is confirmed. It uses AssemblyAI streaming transcription, explicit units and a replayable count history. Built solo by Joseph Ayanda.”

LabLab's public guide documents profile completion, Discord connection and the Create or Join a team route. The exact logged-in form must still be read. Do not fabricate team creation or a final submission receipt.

## Remaining gates

1. Create and verify the one-person Recount team.
2. Score the existing frozen human holdout once when its recording is provided. Keep failures; a changed system needs a fresh holdout before a new human-performance claim.
3. Finalize the required PDF presentation and any event-specific fields; upload the MP4 or supply its actual watch URL as required by the live form.
4. Provide the private judge code only through a field explicitly private to judges. Do not publish it in source, media or team descriptions.
5. Submit through the actual event form and read back a submission receipt.

The separate Netlify site's current variables remain in place. Its deployment was uploaded directly; automatic Git-to-Netlify linkage is not yet claimed. Future provider CI needs a separately configured secret in this new repository; the no-cost regression pipeline does not.

Public form guide: https://lablab.ai/ai-articles/hackathon-guidelines
