import json
import urllib.request
from pathlib import Path

from config import PROJECT_ROOT

CACHE_PATH = PROJECT_ROOT / ".cache" / "state_capitals.json"
LANGUAGES_CACHE_PATH = PROJECT_ROOT / ".cache" / "country_languages.json"
USER_AGENT = "country-llm-app/1.0 (geo Q&A; educational project)"


def _load_cache() -> dict[str, str]:
    if not CACHE_PATH.exists():
        return {}
    with open(CACHE_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_cache(cache: dict[str, str]):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as handle:
        json.dump(cache, handle, ensure_ascii=False, indent=2)


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _entity_label(entity_id: str) -> str | None:
    payload = _fetch_json(
        f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
    )
    entity = payload["entities"][entity_id]
    return entity.get("labels", {}).get("en", {}).get("value")


def fetch_state_capital(wiki_data_id: str | None, force: bool = False) -> str | None:
    """Resolve state capital via Wikidata P36 using wikiDataId from the dataset."""
    if not wiki_data_id:
        return None

    cache = _load_cache()
    if not force and wiki_data_id in cache and cache[wiki_data_id]:
        return cache[wiki_data_id]

    capital = None
    try:
        payload = _fetch_json(
            f"https://www.wikidata.org/wiki/Special:EntityData/{wiki_data_id}.json"
        )
        claims = payload["entities"][wiki_data_id].get("claims", {}).get("P36", [])
        if claims:
            capital_id = claims[0]["mainsnak"]["datavalue"]["value"]["id"]
            capital = _entity_label(capital_id)
    except Exception:
        capital = None

    cache[wiki_data_id] = capital or ""
    _save_cache(cache)
    return capital


def prefetch_all_state_capitals(states: list[dict], show_progress: bool = True) -> dict[str, str]:
    """Fetch Wikidata capitals for all states; returns wikiDataId -> capital."""
    cache = _load_cache()
    total = len(states)
    found = 0

    for index, state in enumerate(states, start=1):
        wiki_id = state.get("wikiDataId")
        if not wiki_id:
            continue
        if cache.get(wiki_id):
            found += 1
            continue
        capital = fetch_state_capital(wiki_id, force=True)
        if capital:
            found += 1
        if show_progress and index % 100 == 0:
            print(f"  Wikidata progress: {index}/{total} ({found} capitals found)")

    if show_progress:
        cached = sum(1 for value in _load_cache().values() if value)
        print(f"  State capitals in cache: {cached}")
    return _load_cache()


def _load_languages_cache() -> dict[str, list[str]]:
    if not LANGUAGES_CACHE_PATH.exists():
        return {}
    with open(LANGUAGES_CACHE_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_languages_cache(cache: dict[str, list[str]]):
    LANGUAGES_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LANGUAGES_CACHE_PATH, "w", encoding="utf-8") as handle:
        json.dump(cache, handle, ensure_ascii=False, indent=2)


def fetch_country_languages(wiki_data_id: str | None, force: bool = False) -> list[str]:
    """Official languages via Wikidata P37."""
    if not wiki_data_id:
        return []

    cache = _load_languages_cache()
    if not force and wiki_data_id in cache:
        return cache[wiki_data_id]

    languages: list[str] = []
    try:
        payload = _fetch_json(
            f"https://www.wikidata.org/wiki/Special:EntityData/{wiki_data_id}.json"
        )
        claims = payload["entities"][wiki_data_id].get("claims", {}).get("P37", [])
        for claim in claims:
            try:
                lang_id = claim["mainsnak"]["datavalue"]["value"]["id"]
                label = _entity_label(lang_id)
                if label and label not in languages:
                    languages.append(label)
            except (KeyError, TypeError):
                continue
    except Exception:
        languages = []

    cache[wiki_data_id] = languages
    _save_languages_cache(cache)
    return languages
