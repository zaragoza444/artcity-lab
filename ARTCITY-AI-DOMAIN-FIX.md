# Art City — `ai.artcity.group` domain fix

Railway custom domain is already attached to **frontend**.
CORS / `PUBLIC_APP_URL` already include `https://ai.artcity.group`.
Remaining step: fix Cloudflare DNS on zone **artcity.group** (clears HTTP 521).

## Cloudflare DNS (add / update in the account that owns artcity.group)

| Type  | Name                 | Content                                                                  | Proxy    |
|-------|----------------------|--------------------------------------------------------------------------|----------|
| CNAME | `ai`                 | `uzddkjs6.up.railway.app`                                                | Proxied  |
| TXT   | `_railway-verify.ai` | `railway-verify=d438cc6d54fa7fc2c6721f3ccd2f09990730d80621c913b2a3e764d4a0322fdb` | DNS only |

SSL mode for the zone: **Full (strict)** once Railway cert issues.

## Railway (already done — do not delete)

| Service  | URL |
|----------|-----|
| Frontend | https://frontend-production-6380.up.railway.app |
| Backend  | https://backend-production-9533.up.railway.app |
| Custom   | https://ai.artcity.group → frontend |

Project: `art-city-ai-studio` (`ffd2bf67-d078-4679-9ba1-641b5a1cfe54`)

## Apply via API (optional)

1. Create a Cloudflare API token with **Zone → DNS → Edit** on `artcity.group` (no IP allowlist).
2. Save as `.cloudflare.artcity.local` next to this file:

```
CLOUDFLARE_API_TOKEN=your_token_here
```

3. Run:

```powershell
python apply-ai-artcity-dns.py
```

## Verify

```powershell
# old URLs must stay up
curl -sI https://frontend-production-6380.up.railway.app
curl -sI https://backend-production-9533.up.railway.app/health

# new domain (expect 200, not 521)
curl -sI https://ai.artcity.group
```
