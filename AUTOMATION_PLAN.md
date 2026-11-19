# Nova Shorts Automation

## Goal
Build a low-cost pipeline that creates English-language YouTube Shorts and publishes them through Metricool.

## Current status
- Repository: `nova-api-del/nova`
- Default branch: `main`
- Video engine under evaluation: [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)
- Publishing destination: Metricool (YouTube Shorts; TikTok optional)

## Implementation rules
1. Start with a manual GitHub Actions run; enable a schedule only after a successful end-to-end test.
2. Never commit API keys, access tokens, or account credentials. Store them as GitHub Actions secrets.
3. Do not assume third-party APIs are free. Check quotas and costs before enabling them.
4. Generate English scripts, narration, titles, and descriptions.
5. Validate that the rendered video is vertical (9:16), has a valid duration, and is playable before publishing.
6. Publish only after a real video file exists and the Metricool publishing path is verified.

## Known constraints
GitHub Actions runners are temporary, not an always-on server. The runner may be free within GitHub's usage limits, but external LLM, stock-footage, and publishing services can have separate limits or costs.

## Next steps
- Verify MoneyPrinterTurbo's current install and CLI commands.
- Select genuinely no-cost sources for scripts, narration, and visuals where possible.
- Add a manual workflow and test video generation.
- Verify Metricool media upload/scheduling requirements.
- Enable daily automation only after the manual test succeeds.
