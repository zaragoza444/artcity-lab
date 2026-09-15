# Art City AI Studio (private)

Private Art City project. Standalone ownership.

**Never integrate with:**

- Nova (any Nova product, repo, API, SDK, wallet, or `.nova` config)
- Alltra (chain, tokens, reports, DEX, checkout, or related repos)

Work only inside this repository: `C:\Users\novac\Documents\art-city-ai-studio`

## Branch policy

`feature/*` → `development` → `staging` → `main`

- Production deploys only from `main` after approval
- Protect `main`: PR required, at least one reviewer, no force push
- Never commit `.env`, datasets, or model weights

## AI Core directive

See [docs/ART_CITY_AI_CORE_DIRECTIVE.md](docs/ART_CITY_AI_CORE_DIRECTIVE.md).

## Art City Edit

Product PRD: [docs/ART_CITY_EDIT_PRD.md](docs/ART_CITY_EDIT_PRD.md). Edit is part of Art City AI Studio (Cinema · Studio · Edit · Publish · Hub · Vertical Drama · **Graphic Motion**).

MSG contracts: [contracts/ac-graphic-motion/](contracts/ac-graphic-motion/). Spec: [docs/AC_GRAPHIC_MOTION_MSG_SPEC.md](docs/AC_GRAPHIC_MOTION_MSG_SPEC.md).
