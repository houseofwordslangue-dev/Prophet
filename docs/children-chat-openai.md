# Children chatbot — OpenAI backend

The browser calls `POST /api/children-chat`. The server implementation is `functions/api/children-chat.js` and is designed for a serverless runtime that supports Cloudflare Pages Functions-style `onRequest` handlers.

## Required secret

Set `OPENAI_API_KEY` in the deployment platform's secret/environment-variable store. Never put the key in HTML, JavaScript served to browsers, a repository file, or a public build variable.

Optional: set `OPENAI_CHAT_MODEL`. If omitted, the endpoint uses `gpt-5.6-luna` for a cost-conscious interactive child assistant.

## Request

```json
{
  "message": "...",
  "page": "/children.html",
  "language": "ar",
  "context": {"title":"...","excerpt":"..."},
  "history": [{"role":"user","text":"..."},{"role":"assistant","text":"..."}]
}
```

The endpoint caps message/context/history sizes, moderates input and output, sends only short recent history, sets `store:false` on Responses API calls, and does not persist chat replies into editorial content.

## Deployment requirement

A static-only host such as plain GitHub Pages cannot execute `/api/children-chat`. Deploy the site on a serverless host that executes the `functions/` directory, or route `/api/children-chat` to an equivalent server-side Worker/function. Keep the secret server-side in either case.

## Smoke test

After deployment and secret configuration:

```bash
curl -X POST https://YOUR_DOMAIN/api/children-chat \
  -H 'content-type: application/json' \
  --data '{"message":"ماذا نتعلم من الصدق؟","language":"ar","page":"/children.html"}'
```

Expected: HTTP 200 JSON with an `answer` field. Without the secret, the endpoint intentionally returns HTTP 503 with `CHAT_NOT_CONFIGURED`.
