# AI feedback Worker (Google Gemini)

A small Cloudflare Worker that gives AI feedback on the **written regression interpretations**.
The website stays a static site on GitHub Pages; only this one request goes to a server, because the
Gemini API key must stay secret.

* The page sends only `{questionId, answer}`. The question, model answer and checklist come from
  `src/regression.json` (written by `build/build.py`), so the Worker cannot be used as a general chatbot.
* Gemini (`gemini-3.8-flash`) compares the answer with the model answer and checklist and returns
  JSON: which checklist points are covered, wrong statements, and two to four sentences of feedback.
  The Worker checks the JSON's shape before passing it on.
* Only the origins in `ALLOWED_ORIGINS` (wrangler.toml) may call it; each visitor gets at most
  10 requests per minute; answers are limited to 3,000 characters.
* The Excel and SQL checks never use AI: they are computed from the data in the browser.

## Free tier: what to know

* The free tier costs nothing but has rate limits; see your key's limits in Google AI Studio. When the
  quota is used up, students see "The free feedback quota is used up for now."
* On the free tier Google may use the submitted text to improve its products, and human reviewers may
  read it. The page tells students this under the button.
* Google's terms require users to be 18 or older and say that apps offered to users in the EEA,
  Switzerland or the UK should use paid services. Check the current
  [Gemini API terms](https://ai.google.dev/gemini-api/terms) before using it beyond this assignment.

## Set up (once)

1. **Gemini API key.** Sign in to Google AI Studio (aistudio.google.com) and create an API key.
2. **Cloudflare account** (free plan is enough). Note your *Account ID* (Workers & Pages overview) and
   create an *API token* with the template "Edit Cloudflare Workers".
3. **GitHub secrets.** In the repository: Settings → Secrets and variables → Actions → New repository
   secret. Add `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` and `GEMINI_API_KEY`.
4. **Deploy.** Actions → "Deploy AI feedback Worker" → Run workflow. The log prints the Worker address,
   e.g. `https://daa-feedback.<your-subdomain>.workers.dev`.
5. **Connect the site.** Put that address in `site/assets/config.js` (`feedbackUrl`) and push.
   The "Get AI feedback" button then appears on the interpretation exams.

Until the secrets exist, the workflow skips the deploy and the button stays hidden.
