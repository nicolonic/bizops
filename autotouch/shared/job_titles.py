from typing import Iterable, List

SDR_TITLES = [
    "bdr",
    "business development representative",
    "inside sales",
    "inside sales account executive",
    "inside sales account manager",
    "inside sales assistant",
    "inside sales associate",
    "inside sales consultant",
    "inside sales coordinator",
    "inside sales customer service",
    "inside sales engineer",
    "inside sales executive",
    "inside sales manager",
    "inside sales rep",
    "inside sales rep.",
    "inside sales representative",
    "inside sales specialist",
    "inside sales supervisor",
    "inside sales support",
    "sales developer",
    "sales development",
    "sales development executive",
    "sales development manager",
    "sales development representative",
    "sales development specialist",
    "sales representative",
    "sales representatives",
]

AE_TITLES = [
    "account executive",
    "account executive assistant",
    "account executive ii",
    "account executive intern",
    "account executive manager",
    "account executive officer",
    "account executive sales",
    "account manager",
    "account manager assistant",
    "account manager business development",
    "account manager emea",
    "account manager ii",
    "account manager project manager",
    "account manager recruiter",
    "account manager sales",
    "ae",
    "enterprise account executive",
    "sales executive",
    "sales executives",
]


def to_or_query(titles: Iterable[str]) -> str:
    quoted: List[str] = []
    for title in titles:
        title = title.strip()
        if not title:
            continue
        if " " in title:
            quoted.append(f'"{title}"')
        else:
            quoted.append(title)
    return " OR ".join(quoted)
