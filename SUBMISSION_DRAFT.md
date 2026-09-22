# Recount submission draft: 22 September 2026

This copy replaces the earlier single-correction framing. It describes the shipped closeout workflow and the successful public-site multi-item test. It is not a final LabLab submission receipt.

## Title

Recount: Finish the Stocktake

## Short description

Voice stocktaking with unfinished-work recovery. Park uncertain counts, return to exceptions, and hand over a sheet that separates confirmed stock from unresolved or uncounted items. Built on AssemblyAI.

## Long description

Recount helps a stockroom operator finish a count, not just transcribe it. Its unit of work is the whole scoped stocktake: what is confirmed, what needs review, and what has not been counted.

AssemblyAI streams finalized speech into a revision-aware ledger. Counts stay in a draft until the quantity is explicitly confirmed. Switching items parks unfinished work in Needs review. Neural read-back pauses microphone capture, then listening resumes in the same provider session.

The closeout view distinguishes a confirmed zero from an uncounted item. Partial exports remain available, but a complete-stocktake export is blocked while scoped work is unresolved. A transcript-free handoff records status and confirmation method. Explicit Save session and Open session actions let the operator resume unfinished work after reloading.

The new public-site demonstration covers four items, not one rehearsed correction. It parks beans, rejects a mismatched oil confirmation, distinguishes zero soap from uncounted rice, restores a saved session, resolves beans on screen, and finishes rice by voice. Two real AssemblyAI sessions produced nine final turns, nine read-backs and four exact exported rows. Three counts were speech-confirmed; one was screen-assisted. Only microphone input was generated.

The initial buyer hypothesis is a small-stockroom manager already using spreadsheets. Planned per-location software would add a voice-and-review layer without replacing their stock system. The next pilot compares exact final counts, assistance and time against the existing workflow.

This is a four-item prototype, not a customer deployment. Two earlier human recording tests failed and remain documented. Human reliability and productivity are not yet established. Catalogue import and stock-system integrations are next-stage work.

Built solo by Joseph Ayanda.

## Actual form fields

- Repository: https://github.com/josepha-mayo/Recount
- Application: https://recount-voice.netlify.app/
- Demo platform: Other (Netlify)
- Category: Productivity
- Technology: rest api. AssemblyAI was not available in the observed selector; it remains explicit in the description and architecture.

Title: 29 characters. Short description: 203 characters. Long description: 1861 characters and 264 whitespace-delimited words.

## Current proof

[Live closeout acceptance](verification/CLOSEOUT_LIVE_ACCEPTANCE_20260922.json), [actual run 35771644932](https://github.com/josepha-mayo/Recount/actions/runs/35771644932).

The session was deliberately saved and reopened. Do not imply automatic autosave/crash recovery. Three final rows used spoken confirmation and Beans used the on-screen control. Do not label the run voice-only or human-validated. The earlier human holdouts and failed checks remain preserved.

## Current media and judge access

The new eight-slide presentation and narrated multi-item walkthrough replace the previous 'twelve/no/thirteen' media. The edited footage is from the actual public-site test. Microphone input and added narration use stock synthesis; the soundtrack is not the original browser audio or Joseph's voice. The unedited recording and handoff/CSV evidence accompany the package.

Keep old uploaded media intact until replacements are available. Final submission must use matching current media and copy. The existing private judge code must only be entered in a field explicitly private to judges or another organizer-approved private channel, never in this document or public media. Additional-information labels alone do not prove privacy.
