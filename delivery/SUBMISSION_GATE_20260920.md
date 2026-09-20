# Recount release and submission gate

Status checked 20 September 2026: NOT submission-ready. Code verification is not live deployment verification.

## Completed in this continuation

The startup error display is fixed: the hold reducer no longer erases the authorization error after microphone cleanup. Reports now include a bounded, non-secret failure class. Socket failures, startup timeouts and malformed events retain their explanation. The new module is served by the local server. Parser and confidence thresholds are unchanged.

Verified application commit: 789f9fd11ee78a3472f63a65f5a77b284085ea58. Run: https://github.com/josepha-mayo/Recount/actions/runs/35538609871

Actual checks: 214 Node tests, 8 HTTP tests, 8 startup/retry browser checks, 13 recovery browser checks, 18 bundled-audio browser checks and 32 general browser checks passed. The browser tests use synthetic capture and mocked authorization/ASR; real MP3 decoding is exercised where stated. A rejected mock authorization followed by an accepted mock retry produced exactly one Rice / 13 / bags row and that exact CSV. Mobile failed-authorization and desktop successful-retry screenshots were inspected. No new human or real-provider audio was sent in this continuation.

The first integration run 35538393733 failed on a missing local route for the new module. That failure is preserved. It was corrected, not waived.

## Live blocker and permanent release path

Last observed production deploy: 6aaf23be193c477b8f80fa24. It still contains application source e1e47d6b5969055382f96b671b9a53c62e267ce2, not this fix. The user report has two token HTTP 403 failures after microphone/worklet setup. The old report does not retain the exact server rejection reason.

The Netlify connector can read the project and return an expiring upload command, but this working runtime cannot reach Netlify to execute it. The browser has no authenticated Netlify session. GitHub Actions has ASSEMBLYAI_API_KEY configured, but its NETLIFY_AUTH_TOKEN and RECOUNT_DEMO_PASS secrets are absent. Secret values were not printed or committed. The existing passcode was not changed in this continuation.

A standard, manual-only publish job is provided in `.github/workflows/production-release.yml`. Its regression job also runs on relevant pushes and pull requests. Publishing is permitted only by workflow_dispatch on master. It requires two repository Actions secrets:

- NETLIFY_AUTH_TOKEN: a Netlify personal access token authorized for the existing Recount site.
- RECOUNT_DEMO_PASS: the same current judge code already supplied privately, not a newly generated code.

Owner setup: Netlify User settings > Applications > Personal access tokens > New access token. Save it directly in Recount > Settings > Secrets and variables > Actions as NETLIFY_AUTH_TOKEN. Save the current judge code there as RECOUNT_DEMO_PASS. Do not put either value in an issue, commit, public submission, screenshot, or chat. Then Actions > Recount production release > Run workflow > master.

The job first runs regressions, applies the supplied existing judge code to production Functions, and uploads this source to the existing site. Its final verification calls the real public config and token endpoints with a fresh cookie and CSRF value, checks a deliberately invalid-code rejection, checks the supplied valid code, checks served source hashes, and sends half a second of generated silence through a real bounded provider connection. A Begin event alone does not pass. The receipt records no passcode, token, cookie, CSRF, audio or transcript. This workflow has not yet published or passed its live checks. Do not call its prepared state a deployed fix.

References: https://docs.netlify.com/api-and-cli-guides/cli-guides/get-started-with-cli/ ; https://cli.netlify.com/commands/deploy/ ; https://cli.netlify.com/commands/env/ ; https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets

## Official submission requirements

Official source fetched on 20 September: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon

The event metadata and timeline specify the submission deadline as 30 September 2026 at 15:00 UTC, or 16:00 WAT. Recheck the submission form for later changes before submission.

The public guidelines request: project title, short description, long description, technology and category tags; cover image, video presentation, slide presentation; public GitHub repository, demo application platform and application URL. The retrieved public page did not establish file-size limits or a maximum video duration.

The two supported architecture paths are Voice Agent API and Realtime Speech-to-Text API with custom orchestration. Recount uses the latter; the page does not require replacing this architecture with Voice Agent API. Judging categories are Application of Technology, Presentation, Business Value and Originality.

Existing team: Recount. Team URL: https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon/recount
Repository: https://github.com/josepha-mayo/Recount
Application: https://recount-voice.netlify.app/

Suggested current title: Recount: Correction-Aware Voice Stocktaking

Suggested short description: A voice stocktaking prototype that keeps corrections in one draft, checks spoken quantity confirmation, and exports only confirmed stock. Unfinished or uncertain counts stay available for review rather than silently entering inventory.

## What remains before submission

1. Obtain a passing real production authorization/source/provider receipt from the new release workflow.
2. Verify the deployed microphone/read-back/correction/confirmation interaction without pretending simulated ASR is human evidence. Preserve both earlier failed one-speaker holdouts; do not overwrite them with development results.
3. Record an actual current-build demonstration and update cover/slides/descriptions to match it. The existing narrated slide walkthrough is not a new live microphone demonstration.
4. Complete the existing team's required fields and media. Provide the judge code only in an explicitly private judge field. Do not create another team or expose credentials in public descriptions.
5. Read back the actual final submission confirmation. No submission was performed in this continuation.
