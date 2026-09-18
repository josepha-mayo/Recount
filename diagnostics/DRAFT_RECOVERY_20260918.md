# Recount: diagnostic-driven draft recovery

## The returned result

The private request diagnostic completed one AssemblyAI session, sent 46.5535 seconds of the previously exposed second recording, and received 27 finalized turns with no recorded provider error. The unchanged scored ledger produced zero saves and zero of four expected final counts. This was development reuse, not a third holdout. No incorrect writes were observed; a reject-everything result does not demonstrate useful reliability.

The exact returned 27 final events were replayed locally through the unchanged core blob `28b7216204254381b6411c4d777ed6e8e9ed4b31`. All 27 replies, pending states and confirmed-count states matched the supplied diagnostic. The baseline could therefore be reproduced without another API request or recording.

## Failure mechanisms visible in the trace

An early unrecognized number fragment blocked an item draft. Correction markers delivered as separate provider turns could not recover it. A subsequent isolated item name remained attached to that blocked draft rather than starting a new reviewable item. An uncertain confirmation contaminated an otherwise usable draft. Cancellation was also rejected when the action verb had high confidence but its filler noun did not.

The requested 160/400 ms setting and context produced more fragments than the scripted utterance count. It is not established as the best endpoint configuration. Changing provider turn timing alone does not solve these state-management problems. No provider settings are changed by this patch.

## Implemented candidate behavior

- A standalone correction marker keeps the known item but invalidates the old quantity and unit. A later explicit number/unit fragment can complete that draft; a unit alone cannot revive the stale number. Transport holds and disputed item identities still require a full restatement.
- An unclear matching spoken confirmation preserves the draft for repeat confirmation or explicit on-screen review. The numerical staging floor stays 0.75 and the spoken confirmation floor stays 0.90. The command word must also meet the existing staging floor.
- Exact discard/cancel commands use confidence in their action word. Discard never changes confirmed stock and does not erase other parked reviews.
- An isolated, sufficiently clear catalogue item name is now a documented focus-change action. It parks the old draft in a visible Needs review tray rather than discarding or confirming it. Multi-item compound commands remain rejected; they are not silently split into writes.
- Review selection is revision-bound. A review older than a newer confirmed count cannot silently overwrite it. CSV includes only confirmed counts, never review drafts.

Session exports use `recount-session-2` because the action interpretation now includes review state. Earlier files are rejected with an explanation, not silently rescored by a different ledger. Their original bytes and pinned earlier engine remain available.

## What the offline development replay achieved

Using the original returned transcripts and confidences, with no injected confirmations or resets, the candidate preserved four complete unconfirmed review drafts across distinct catalogue items. It also retained an incomplete wrong-unit review. The later uncertain zero count remained unconfirmed.

This is NOT four of four correct final counts. One of the complete reviews is an intermediate count that the script later attempted to replace with zero. Automatic saves remain zero and the original final-count score remains zero of four. Confidence handling and the live interaction still need evaluation; this patch removes the recovery dead end rather than declaring the voice task solved.

No new provider calls, audio uploads, or private transcript publication were performed. Only this aggregate summary, code, and authored regression fixtures are published. Both failed human holdouts remain failed. Do not request another unseen recording until development and interactive recovery testing justify it.

## Tests

The first local patch check passed all 88 available inherited ledger/transport tests plus 29 new recovery tests and eight loopback HTTP checks. The local Chromium attempt was blocked by administrator policy before navigation; that is not counted as a browser pass. The pull request runs the full repository suite, including its separate diagnostic helper tests, and an expanded desktop/mobile browser workflow in GitHub CI. Use the actual CI receipt for the final totals.

The live Netlify app is a separate direct deployment. A GitHub push or merge alone does not update it. This document does not claim production deployment or a new human-speech pass.
