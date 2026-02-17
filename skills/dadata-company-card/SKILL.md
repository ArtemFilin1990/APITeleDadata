---
name: dadata-company-card
description: Use this skill when changing how the Telegram bot renders company cards/pages from DaData fields (main card, details, founders, management, taxes, licenses/documents) and related inline navigation/tests.
---

# DaData Company Card Skill

## When to use
- User asks to change card output for company data.
- User asks to add/remove fields in detail pages (`Подробнее`, учредители, руководство, налоги, документы).
- User asks to adjust inline buttons/callback pages tied to company profile output.

## Source of truth in this repository
- `handlers.py` — text rendering and callback page routing.
- `keyboards.py` — callback constants and inline keyboard layout.
- `dadata_direct.py` — direct API data fetch and utility formatting.
- `tests/test_handlers_logic.py`, `tests/test_keyboards.py` — regression coverage for rendering and navigation.
- `API_Организация_по_ИНН_или_ОГРН.md` — known DaData fields and payload shape.

## Minimal workflow
1. Confirm target fields exist in documented DaData response shape.
2. Implement safe rendering:
   - never assume list/dict type without `isinstance` checks,
   - fallback to `—` or `данные не предоставлены`.
3. Keep callback constants in sync between `keyboards.py` and `handlers.py`.
4. Add/adjust tests for:
   - new text blocks,
   - callback routing,
   - defensive behavior on missing/invalid types.
5. Run checks:
   - `PYTHONPATH=. pytest -q`

## Guardrails
- Do not log or hardcode secrets.
- Preserve Telegram message safety (length split helpers and safe string formatting).
- Prefer minimal reversible changes; avoid changing unrelated startup/runtime behavior.
