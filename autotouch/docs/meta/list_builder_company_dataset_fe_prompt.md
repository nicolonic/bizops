# Context + Task
You are fixing the Autotouch list builder UI for the company dataset. The backend is returning valid filter values, but the frontend UI stays stuck on "Loading options..." and users cannot select Country/Region/City/Industry/Company size. The live preview table does populate, so the preview API is working. Determine why the FE is not applying the filter-values response and fix it.

# Where the frontend is
Repo: `/Users/nicolo/Projects/smart_table`

Relevant frontend files (UI + service):
- `apps/web/src/shared/services/companyDataset.ts`
- `apps/web/src/systems/list-builder/components/ListBuilderCanvas.tsx`

Relevant backend proxy (smart_table API) in case you need to verify routing:
- `apps/api/routers/integrations/company_dataset_proxy.py`
- `apps/api/routers/integrations/__init__.py`
- `apps/api/main.py`

Upstream list-builder service (separate repo) for reference only:
- `app.py` (endpoints)
- `services/company_dataset/store.py` (query logic)

# Problem summary
- UI shows "Loading options..." for Country/Region/City/Industry/Company size.
- Browser Network shows `GET /api/company-dataset/filter-values?limit=200` returns 200 with valid JSON.
- Preview is working (`POST /api/company-dataset/preview`), so dataset is accessible.
- This indicates FE state is not updating, or the loaded data isn’t being used to populate options.

# Backend response shapes (as currently returned)
GET `/api/company-dataset/filter-values?limit=200`
Response example:
{
  "values": {
    "country": [{ "value": "united states", "count": 8705680 }, ...],
    "industry": [{ "value": "construction", "count": 1346080 }, ...],
    "size": [{ "value": "1-10", "count": 26565098 }, ...],
    "region": [{ "value": "england", "count": 2675559 }, ...],
    "locality": [{ "value": "london", "count": 825332 }, ...]
  },
  "ranges": {
    "founded": { "min": 1001, "max": 2025 }
  },
  "generated_at": "2026-01-22T14:30:22.986656"
}

POST `/api/company-dataset/preview`
Response example:
{
  "total_count": null,
  "preview": [
    {
      "country": "azerbaijan",
      "founded": "2013",
      "id": "0NiyFK1H1XyGVWCYnUHN0QOuVo53",
      "industry": "civic & social organization",
      "linkedin_url": "linkedin.com/company/asan-volunteers-organization",
      "locality": null,
      "name": "asan volunteers\" organization | \"asan könüllüləri\" təşkilatı",
      "region": "bakı",
      "size": "10001+",
      "website": "asanvolunteers.az"
    }
  ],
  "limit": 25
}

Notes:
- `total_count` is currently `null` by design to avoid slow full-table counts.
- All filter values are lowercased; FE formats via `formatDatasetLabel`.

# Expected FE behavior
- `companyDatasetApi.getFilterValues()` should populate options for:
  - Country
  - Region/State
  - City/Locality
  - Industry
  - Company size
- After loading, dropdowns should be interactive (not disabled).
- If the response is valid, `companyFilters` state should be set and `companyFiltersLoading` should flip to false.

# What to check
1) Confirm FE uses correct base URL and is calling `/api/company-dataset/filter-values` (not `/company-dataset/...` without `/api`).
2) Ensure response is being parsed and stored in `companyFilters` state.
3) Confirm `companyFilterOptions` is derived from `companyFilters` and is non-empty.
4) Confirm dropdowns are not stuck disabled due to `companyFilters` still `null`.
5) Check for runtime errors in console (JSON parse, undefined access, etc).

# Goal
Make Country/Region/Locality/Industry/Size filter dropdowns populate and become selectable in the list builder UI.
