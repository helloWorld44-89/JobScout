from typing import Any


def score_job(
    title: str,
    company: str,
    location: str,
    description: str,
    criteria: dict[str, Any],
) -> float:
    """Score a job 0–100 against the user's scoring criteria.

    Scoring breakdown:
      keywords (include list): 0–60 pts, proportional to fraction matched
        (30 pts neutral when no keywords configured)
      location / remote:       0–40 pts

    Any excluded keyword in title+company+description immediately returns 0.
    """
    searchable = f"{title} {company} {description}".lower()

    # --- exclude check ---
    for kw in criteria.get("exclude_keywords", []):
        if kw.strip().lower() in searchable:
            return 0.0

    # --- keyword score (0–60) ---
    keywords: list[str] = criteria.get("keywords", [])
    if keywords:
        matched = sum(1 for kw in keywords if kw.strip().lower() in searchable)
        kw_score = (matched / len(keywords)) * 60.0
    else:
        kw_score = 30.0  # neutral when no keywords configured

    # --- location score (0–40) ---
    remote_pref: bool = bool(criteria.get("remote_preference", False))
    pref_loc: str = (criteria.get("location") or "").strip()
    is_remote = "remote" in f"{location} {title}".lower()

    if is_remote and remote_pref:
        loc_score = 40.0
    elif pref_loc and pref_loc.lower() in location.lower():
        loc_score = 40.0
    elif is_remote:
        loc_score = 20.0  # remote option even when not preferred
    elif not pref_loc:
        loc_score = 20.0  # no location filter → neutral
    else:
        loc_score = 0.0  # preference set but no match

    return round(kw_score + loc_score, 1)
