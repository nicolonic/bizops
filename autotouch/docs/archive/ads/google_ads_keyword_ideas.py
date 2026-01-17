#!/usr/bin/env python3
import argparse
import csv
import os
import sys
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class KeywordIdeaRow:
    text: str
    avg_monthly_searches: Optional[int]
    competition: Optional[str]
    competition_index: Optional[int]
    low_top_of_page_bid: Optional[float]
    high_top_of_page_bid: Optional[float]


def _micros_to_units(micros: Optional[int]) -> Optional[float]:
    if micros is None:
        return None
    return micros / 1_000_000


def _dedupe_best(rows: Iterable[KeywordIdeaRow]) -> list[KeywordIdeaRow]:
    best: dict[str, KeywordIdeaRow] = {}
    for row in rows:
        existing = best.get(row.text)
        if existing is None:
            best[row.text] = row
            continue

        # Prefer higher search volume; if missing, keep existing unless new has it.
        if existing.avg_monthly_searches is None and row.avg_monthly_searches is not None:
            best[row.text] = row
        elif (
            existing.avg_monthly_searches is not None
            and row.avg_monthly_searches is not None
            and row.avg_monthly_searches > existing.avg_monthly_searches
        ):
            best[row.text] = row

    return list(best.values())


def _write_csv(path: str, rows: list[KeywordIdeaRow]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "text",
                "avg_monthly_searches",
                "competition",
                "competition_index",
                "low_top_of_page_bid",
                "high_top_of_page_bid",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "text": r.text,
                    "avg_monthly_searches": r.avg_monthly_searches,
                    "competition": r.competition,
                    "competition_index": r.competition_index,
                    "low_top_of_page_bid": r.low_top_of_page_bid,
                    "high_top_of_page_bid": r.high_top_of_page_bid,
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate keyword ideas + metrics via Google Ads API (ADC auth).",
    )
    parser.add_argument("--customer-id", default=os.environ.get("GOOGLE_ADS_CUSTOMER_ID"))
    parser.add_argument("--login-customer-id", default=os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID"))
    parser.add_argument(
        "--developer-token",
        default=os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"),
        help="Optional: defaults to env GOOGLE_ADS_DEVELOPER_TOKEN.",
    )
    parser.add_argument(
        "--api-version",
        default=os.environ.get("GOOGLE_ADS_API_VERSION", "v19"),
        help="google-ads client version (e.g. v19/v20/v21/v22). Default: v19.",
    )
    parser.add_argument(
        "--location",
        action="append",
        default=[],
        help="Geo target ID(s). Example: 2840 (United States). Can be repeated.",
    )
    parser.add_argument(
        "--language",
        default="1000",
        help="Language constant ID. Example: 1000 (English).",
    )
    parser.add_argument(
        "--seed",
        action="append",
        default=[],
        help="Seed keyword(s). Can be repeated.",
    )
    parser.add_argument("--seed-file", help="Newline-separated seed keywords.")
    parser.add_argument("--seed-url", help="Landing page URL seed (e.g. https://autotouch.ai/).")
    parser.add_argument("--out", default="keyword_ideas.csv")
    parser.add_argument("--max-results", type=int, default=500)
    parser.add_argument(
        "--network",
        choices=["GOOGLE_SEARCH", "GOOGLE_SEARCH_AND_PARTNERS"],
        default="GOOGLE_SEARCH",
    )
    args = parser.parse_args()

    if not args.customer_id:
        print("Missing --customer-id (or env GOOGLE_ADS_CUSTOMER_ID).", file=sys.stderr)
        sys.exit(2)
    if not args.developer_token:
        print("Missing --developer-token (or env GOOGLE_ADS_DEVELOPER_TOKEN).", file=sys.stderr)
        sys.exit(2)

    seed_keywords: list[str] = []
    if args.seed:
        seed_keywords.extend([s.strip() for s in args.seed if s.strip()])
    if args.seed_file:
        with open(args.seed_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    seed_keywords.append(line)

    if not seed_keywords and not args.seed_url:
        print("Provide at least one --seed and/or --seed-url.", file=sys.stderr)
        sys.exit(2)

    from google.ads.googleads.client import GoogleAdsClient

    config: dict[str, object] = {
        "developer_token": args.developer_token,
        "use_proto_plus": True,
        "use_application_default_credentials": True,
    }
    if args.login_customer_id:
        config["login_customer_id"] = args.login_customer_id

    client = GoogleAdsClient.load_from_dict(config, version=args.api_version)
    service = client.get_service("KeywordPlanIdeaService")

    # Locations: default to US if none provided.
    locations = args.location or ["2840"]

    def build_request(keywords_chunk: list[str]):
        req = client.get_type("GenerateKeywordIdeasRequest")
        req.customer_id = str(args.customer_id)
        req.language = f"languageConstants/{args.language}"
        req.include_adult_keywords = False
        for loc in locations:
            req.geo_target_constants.append(f"geoTargetConstants/{loc}")
        req.keyword_plan_network = client.enums.KeywordPlanNetworkEnum[args.network]

        if keywords_chunk and args.seed_url:
            req.keyword_and_url_seed.url = args.seed_url
            req.keyword_and_url_seed.keywords.extend(keywords_chunk)
        elif keywords_chunk:
            req.keyword_seed.keywords.extend(keywords_chunk)
        else:
            req.url_seed.url = args.seed_url
        return req

    rows: list[KeywordIdeaRow] = []
    keyword_chunks: list[list[str]]
    if seed_keywords:
        keyword_chunks = [seed_keywords[i : i + 20] for i in range(0, len(seed_keywords), 20)]
    else:
        keyword_chunks = [[]]

    for chunk in keyword_chunks:
        request = build_request(chunk)
        for idea in service.generate_keyword_ideas(request=request):
            metrics = getattr(idea, "keyword_idea_metrics", None)
            avg = getattr(metrics, "avg_monthly_searches", None) if metrics else None
            competition = str(getattr(metrics, "competition", "")) if metrics else None
            competition_index = getattr(metrics, "competition_index", None) if metrics else None
            low_bid = _micros_to_units(getattr(metrics, "low_top_of_page_bid_micros", None) if metrics else None)
            high_bid = _micros_to_units(getattr(metrics, "high_top_of_page_bid_micros", None) if metrics else None)
            rows.append(
                KeywordIdeaRow(
                    text=idea.text,
                    avg_monthly_searches=avg,
                    competition=competition or None,
                    competition_index=competition_index,
                    low_top_of_page_bid=low_bid,
                    high_top_of_page_bid=high_bid,
                )
            )
            if len(rows) >= args.max_results:
                break
        if len(rows) >= args.max_results:
            break

    rows = _dedupe_best(rows)
    rows.sort(key=lambda r: (r.avg_monthly_searches or 0, r.high_top_of_page_bid or 0.0), reverse=True)

    _write_csv(args.out, rows)
    print(f"Wrote {len(rows)} keyword ideas to {args.out}")


if __name__ == "__main__":
    main()
