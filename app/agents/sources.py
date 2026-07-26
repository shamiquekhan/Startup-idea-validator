"""Source quality scoring and domain whitelist/blacklist."""

import re
from urllib.parse import urlparse

TIER_1 = {  # Primary research / official data
    "nature.com", "science.org", "cell.com", "pnas.org",
    "arxiv.org", "chemrxiv.org", "medrxiv.org",
    "doe.gov", "nrel.gov", "ornl.gov", "lbl.gov", "anl.gov", "pnnl.gov",
    "nist.gov", "nsf.gov", "nih.gov",
    "materialsproject.org", "oecd.org", "worldbank.org",
    "sequoiacap.com", "a16z.com", "ycombinator.com",
    "pitchbook.com", "cbinsights.com", "crunchbase.com",
    "techcrunch.com", "venturebeat.com",
}

TIER_2 = {  # Quality journalism / institutional
    "reuters.com", "bloomberg.com", "wsj.com", "ft.com",
    "nytimes.com", "economist.com", "technologyreview.com",
    "wired.com", "nature.com", "science.org",
    "forbes.com", "inc.com", "fastcompany.com",
    "hbr.org", "bcg.com", "mckinsey.com",
    "ieee.org", "acm.org",
    "spglobal.com", "statista.com", "grandviewresearch.com",
    "marketsandmarkets.com", "alliedmarketresearch.com",
    "gartner.com", "forrester.com", "idc.com",
}

TIER_3 = {  # Company pages / credible blogs
    "github.com", "gitlab.com", "medium.com",
    "substack.com", "producthunt.com",
}

BLOCKLIST_DOMAINS = {
    "rense.com", "naturalnews.com", "infowars.com", "breitbart.com",
    "microsoft.com/sign-in", "login", "account.microsoft.com",
}

BLOCKLIST_PATTERNS = [
    r"sign[-\s]?in",
    r"log[-\s]?in",
    r"create account",
    r"reset password",
    r"my account",
]


def score_source(url: str) -> tuple[int, str]:
    parsed = urlparse(url)
    domain = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.lower()

    for pat in BLOCKLIST_PATTERNS:
        if re.search(pat, url.lower()):
            return (0, "blocked pattern matched")

    if any(b in url.lower() for b in BLOCKLIST_DOMAINS):
        return (0, "blocklisted domain")

    if domain in TIER_1:
        return (10, "tier-1: primary research")
    if domain in TIER_2:
        return (7, "tier-2: quality journalism")
    if domain in TIER_3:
        return (4, "tier-3: company page")

    return (3, "unverified source")
