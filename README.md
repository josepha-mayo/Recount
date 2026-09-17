# Recount

**Count it. Correct it. Confirm it.**

A correction-aware voice stocktaking prototype by **Joseph Ayanda** for the AssemblyAI Voice Agent Hackathon.

- **Application:** https://recount-voice-joseph.netlify.app/
- **Source:** https://github.com/josepha-mayo/Recount
- **Fresh import verification:** [migration/REGRESSION_RECEIPT.json](migration/REGRESSION_RECEIPT.json)
- **Frozen human evaluation:** [evaluation/HUMAN_HOLDOUT_PROTOCOL.json](evaluation/HUMAN_HOLDOUT_PROTOCOL.json)

This is Recount's own repository and its own Netlify project. It contains no portfolio application or unrelated hackathon projects. Historical source attribution remains in [ORIGIN.json](ORIGIN.json).

## The task

A stock count is not just a transcript. “Twelve ... no, thirteen” must update one draft, not add another stock movement.

```text
Rice twelve bags.      -> Draft: Rice / 12 / bags
No, thirteen bags.     -> Same draft: Rice / 13 / bags
Confirm thirteen.      -> One saved count: Rice / 13 / bags
Rice twelve cartons.   -> Unit mismatch; saved count stays unchanged
Confirm twelve.        -> Nothing new is saved
```

The prototype asks for missing units, stages absolute counts and requires an explicit quantity echo for spoken confirmation. A generic “yes” cannot commit a count. Duplicate final transcripts cannot create another entry; interrupted or conflicting input can place the session on hold. CSV contains confirmed counts. Reopening a saved session reconstructs state from its action history.

## Run locally

Python 3.11+ and a modern browser are sufficient for text mode:

```sh
python server.py
```

Open the loopback URL printed by the server. Try `rice twelve`, `bags`, `no thirteen`, then `confirm thirteen`. Refresh loses unsaved work. Exported session files contain transcripts, so share them deliberately.

## Verification

The fresh import into this repository passed **86 Node tests, 8 HTTP tests and 18 Chromium checks** in [run 35286291759](https://github.com/josepha-mayo/Recount/actions/runs/35286291759). No provider calls were made by that regression run.

```sh
node --test tests/*.test.mjs
python -m unittest discover -s tests -p 'test_*.py' -v
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python tests/browser.py
```

All 42 imported source files were checked against the standalone archive with SHA-256 `50a7c1304b7336f2674e6ac9c1ec6d3d8ceee97c30b41bd83f3ce37d2ca66536`. [IMPORT_RECEIPT.json](migration/IMPORT_RECEIPT.json) records the original bytes; later documentation changes are separate commits. Historical files under `verification/` retain their original scope and are not silently relabelled as current results.

A separate, earlier independent-site browser run used a stock synthetic voice through the actual AssemblyAI service. It received five finalized turns, preserved exactly one Rice / 13 / bags row, exported the expected CSV and reopened the saved session. Its source evidence is [historical run 35279755338](https://github.com/josepha-mayo/Joseph-Portfolio/actions/runs/35279755338). The demonstration is genuine provider integration on synthetic input, **not human/accent validation or a shopkeeper pilot**. No human holdout recording has been scored.

## Hosting and credentials

The independent Netlify project is `recount-voice-joseph`. Publish directory: `web`. Functions directory: `netlify/functions`. The existing site was deployed by an authorized upload; automatic Git-to-Netlify deployment is not claimed to be configured.

Store these values privately in that Netlify project's environment, never in repository source:

```text
ASSEMBLYAI_API_KEY
RECOUNT_SIGNING_SECRET
RECOUNT_DEMO_PASS
RECOUNT_ALLOWED_ORIGIN=https://recount-voice-joseph.netlify.app
```

The existing site's runtime variables were retained during repository import. GitHub repository secrets do not accompany a source-code import. The tests above do not require a provider key. Any later live-provider workflow must receive its own explicitly configured secret and a bounded execution budget.

The permanent provider key stays server-side. A private judge code, same-origin check, CSRF cookie and short-lived streaming token gate voice access. Individual hosted sessions are capped at 90 seconds. The shared code is not individual-user authentication or a global billing cap. Do not put the code in public team descriptions, screenshots or videos.

## Scope and development findings

Four illustrative catalogue entries; narrow English count commands; no inferred pack conversions. No payments, orders, supplier messages or production stock-system writes. Confirmation does not prove that the physical count is correct.

The microphone path separates continuing drains from terminal flushes, binds native browser APIs to their correct receiver, and keeps outgoing audio packets within the provider's minimum-duration contract. The preceding failing runs are retained in the development lineage. No confidence threshold or count-parser change was made merely to pass the migration.

Official provider references:
- https://www.assemblyai.com/docs/streaming/api-spec/streaming-websocket
- https://www.assemblyai.com/docs/streaming/api-spec/generate-streaming-token
- https://www.assemblyai.com/docs/streaming/common-session-errors-and-closures

MIT license. No credentials, private human recordings, model weights or font files are bundled.
