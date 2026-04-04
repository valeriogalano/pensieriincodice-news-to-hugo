from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_reader", "utm_name",
    "fbclid", "gclid", "gclsrc", "dclid", "gbraid", "wbraid",
    "ref", "ref_", "referer",
    "mc_cid", "mc_eid",
    "_ga", "_gl", "_gac",
    "msclkid", "twclid",
    "igshid",
    "yclid",
    "s_cid",
    "_hsenc", "_hsmi", "hsCtaTracking",
}


def clean_url(url):
    if not url:
        return url
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    cleaned = {k: v for k, v in params.items() if k.lower() not in TRACKING_PARAMS}
    new_query = urlencode(cleaned, doseq=True)
    return urlunparse(parsed._replace(query=new_query))
