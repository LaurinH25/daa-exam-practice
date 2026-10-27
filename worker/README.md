# AI feedback Worker

A small Cloudflare Worker that gives AI feedback on the **written regression interpretations**.
The website stays a static site on GitHub Pages; only this one request goes to a server, because the
Anthropic API key must stay secret.

* The page sends only `{questionId, answer}`. The question, model answer and checklist come from
  `src/regression.json` (written by `build/build.py`), so the Worker cannot be used as a general chatbot.
* Claude (`claude-opus-5-5`) compares the answer with the model answer and checklist and returns
  JSON: which checklist points are covered, wrong statements, and two to four sentences of feedback.
* Only the origins in `ALLOWED_ORIGINS` (wrangler.toml) may call it; each visitor gets at most
  10 requests per minute; answers are limited to 3,000 characters.
* The Excel and SQL checks never use AI: they are computed from the data in the browser.

## Cost

The Anthropic API is paid per token from prepaid credits. With Claude Opus 5.5 one feedback request
costs roughly 2–5 cents. To make it about 40× cheaper, change `MODEL` in `src/index.js` to
`claude-haiku-5-5` and remove the `betas` and `fallbacks` lines (Haiku has no server-side fallback).
Set a monthly spend limit for the API key's workspace in the Anthropic Console.

## Set up (once)

1. **Anthropic API key.** In the Anthropic Console create an API key and add credits; set a spend limit.
2. **Cloudflare account** (free plan is enough). Note your *Account ID* (Workers & Pages overview) and
   create an *API token* with the template "Edit Cloudflare Workers".
3. **GitHub secrets.** In the repository: Settings → Secrets and variables → Actions → New repository
   secret. Add `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` and `ANTHROPIC_API_KEY`.
4. **Deploy.** Actions → "Deploy AI feedback Worker" → Run workflow. The log prints the Worker address,
   e.g. `https://daa-feedback.<your-subdomain>.workers.dev`.
5. **Connect the site.** Put that address in `site/assets/config.js` (`feedbackUrl`) and push.
   The "Get AI feedback" button then appears on the interpretation exams.

Until the secrets exist, the workflow skips the deploy and the button stays hidden.
