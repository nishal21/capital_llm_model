import json
from pathlib import Path

from config import DB_ROOT

try:
    from wikidata import fetch_state_capital
except ImportError:
    fetch_state_capital = None


class GeoDatabase:
    """In-memory index over the countries-states-cities JSON exports."""

    COUNTRY_FIELDS = (
        "capital",
        "currency",
        "currency_name",
        "currency_symbol",
        "phonecode",
        "iso2",
        "iso3",
        "numeric_code",
        "region",
        "subregion",
        "nationality",
        "population",
        "gdp",
        "tld",
        "native",
        "latitude",
        "longitude",
        "emoji",
    )

    STATE_FIELDS = (
        "country_name",
        "country_code",
        "iso2",
        "iso3166_2",
        "type",
        "native",
        "latitude",
        "longitude",
        "timezone",
        "population",
    )

    def __init__(self, db_root: Path | None = None):
        self.db_root = db_root or DB_ROOT
        self._loaded = False
        self.countries_by_name: dict[str, dict] = {}
        self.states_by_name: dict[str, list[dict]] = {}
        self.cities_by_name: dict[str, list[dict]] = {}
        self.regions_by_name: dict[str, dict] = {}
        self.subregions_by_name: dict[str, dict] = {}
        self.states_by_country: dict[str, list[dict]] = {}

    @staticmethod
    def _key(name: str) -> str:
        return name.strip().lower()

    def _load_json(self, filename: str):
        path = self.db_root / filename
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def load(self):
        if self._loaded:
            return

        for region in self._load_json("regions.json"):
            self.regions_by_name[self._key(region["name"])] = region

        for subregion in self._load_json("subregions.json"):
            self.subregions_by_name[self._key(subregion["name"])] = subregion

        for country in self._load_json("countries.json"):
            self.countries_by_name[self._key(country["name"])] = country

        states_by_id: dict[int, dict] = {}
        for state in self._load_json("states.json"):
            states_by_id[state["id"]] = state
            key = self._key(state["name"])
            self.states_by_name.setdefault(key, []).append(state)
            country_key = self._key(state["country_name"])
            self.states_by_country.setdefault(country_key, []).append(state)

        nested = self._load_json("countries+states+cities.json")
        for country in nested:
            country_name = country["name"]
            country_key = self._key(country_name)
            if country_key in self.countries_by_name:
                self.countries_by_name[country_key]["states_detail"] = country.get(
                    "states", []
                )

            for state in country.get("states", []):
                state_id = state.get("id")
                if state_id in states_by_id:
                    states_by_id[state_id]["cities"] = state.get("cities", [])

                state_name = state["name"]
                for city in state.get("cities", []):
                    city_record = {
                        "name": city["name"],
                        "country": country_name,
                        "state": state_name,
                        "latitude": city.get("latitude"),
                        "longitude": city.get("longitude"),
                        "timezone": city.get("timezone"),
                    }
                    self.cities_by_name.setdefault(self._key(city["name"]), []).append(
                        city_record
                    )

        self._loaded = True

    def get_country(self, name: str) -> dict | None:
        self.load()
        return self.countries_by_name.get(self._key(name))

    def get_states(self, name: str) -> list[dict]:
        self.load()
        matches = self.states_by_name.get(self._key(name), [])
        if matches:
            return matches
        return self.states_by_country.get(self._key(name), [])

    def get_cities(self, name: str) -> list[dict]:
        self.load()
        return self.cities_by_name.get(self._key(name), [])

    def resolve(self, name: str) -> tuple[str, dict | list[dict]] | None:
        """Return entity type and record(s) for a place name."""
        self.load()
        key = self._key(name)
        if key in self.countries_by_name:
            return ("country", self.countries_by_name[key])

        state_matches = self.states_by_name.get(key, [])
        if state_matches:
            return ("state", state_matches[0] if len(state_matches) == 1 else state_matches)

        city_matches = self.cities_by_name.get(key, [])
        if city_matches:
            return ("city", city_matches[0] if len(city_matches) == 1 else city_matches)

        if key in self.regions_by_name:
            return ("region", self.regions_by_name[key])

        if key in self.subregions_by_name:
            return ("subregion", self.subregions_by_name[key])

        return None

    def infer_state_capital(self, state: dict) -> str | None:
        """Best-effort capital when the dataset has no state capital field."""
        state_name = state["name"]
        cities = state.get("cities") or []
        state_key = self._key(state_name)

        for city in cities:
            if self._key(city["name"]) == state_key:
                return city["name"]

        country = self.get_country(state["country_name"])
        if country and country.get("capital"):
            capital_key = self._key(country["capital"])
            for city in cities:
                if self._key(city["name"]) == capital_key:
                    return city["name"]

        return None

    def country_capital(self, name: str) -> str | None:
        country = self.get_country(name)
        if not country:
            return None
        capital = country.get("capital")
        return capital if capital else None

    def place_capital(self, name: str) -> tuple[str | None, str]:
        """Return capital and source note for any place name."""
        resolved = self.resolve(name)
        if not resolved:
            return None, "not found"

        entity_type, record = resolved

        if entity_type == "country":
            capital = record.get("capital")
            if capital:
                return capital, "country record"
            return None, "country has no capital in dataset"

        if entity_type == "state":
            states = record if isinstance(record, list) else [record]
            for state in states:
                inferred = self.infer_state_capital(state)
                if inferred:
                    return inferred, f"inferred for {state['name']} ({state['country_name']})"
                if fetch_state_capital:
                    wiki_capital = fetch_state_capital(state.get("wikiDataId"))
                    if wiki_capital:
                        return wiki_capital, f"wikidata (via dataset wikiDataId) for {state['name']}"
            return (
                None,
                "state capital not found in dataset or wikidata",
            )

        if entity_type == "city":
            cities = record if isinstance(record, list) else [record]
            if len(cities) == 1:
                city = cities[0]
                return (
                    city["name"],
                    f"{city['name']} is a city in {city['state']}, {city['country']}",
                )
            return None, "ambiguous city name — ask which country or state it is in"

        return None, f"{entity_type} entities do not have capitals in this dataset"

    def format_country(self, country: dict) -> str:
        lines = [f"Country: {country['name']}"]
        for field in self.COUNTRY_FIELDS:
            value = country.get(field)
            if value not in (None, ""):
                label = field.replace("_", " ").title()
                lines.append(f"{label}: {value}")
        states = self.states_by_country.get(self._key(country["name"]), [])
        lines.append(f"States/Regions: {len(states)}")
        return "\n".join(lines)

    def format_state(self, state: dict) -> str:
        lines = [f"State/Region: {state['name']}"]
        for field in self.STATE_FIELDS:
            value = state.get(field)
            if value not in (None, ""):
                label = field.replace("_", " ").title()
                lines.append(f"{label}: {value}")
        cities = state.get("cities") or []
        lines.append(f"Cities in dataset: {len(cities)}")
        inferred = self.infer_state_capital(state)
        if inferred:
            lines.append(f"Inferred capital (name match): {inferred}")
        elif fetch_state_capital:
            wiki_capital = fetch_state_capital(state.get("wikiDataId"))
            if wiki_capital:
                lines.append(f"Capital (Wikidata via wikiDataId): {wiki_capital}")
            else:
                lines.append("Capital: not stored in dataset")
        else:
            lines.append("Capital: not stored in dataset")
        return "\n".join(lines)

    def format_city(self, city: dict) -> str:
        return (
            f"City: {city['name']}\n"
            f"State/Region: {city['state']}\n"
            f"Country: {city['country']}\n"
            f"Latitude: {city.get('latitude')}\n"
            f"Longitude: {city.get('longitude')}\n"
            f"Timezone: {city.get('timezone')}"
        )

    def iter_training_examples(self):
        """Generate Q&A strings from everything stored in the dataset."""
        self.load()

        for country in self.countries_by_name.values():
            name = country["name"]
            if country.get("capital"):
                yield (
                    f"Question: What is the capital of {name}? "
                    f"Answer: The capital of {name} is {country['capital']}."
                )
            for field in (
                "currency",
                "currency_name",
                "phonecode",
                "iso2",
                "iso3",
                "region",
                "subregion",
                "nationality",
                "population",
                "tld",
                "native",
            ):
                value = country.get(field)
                if value not in (None, ""):
                    label = field.replace("_", " ")
                    yield (
                        f"Question: What is the {label} of {name}? "
                        f"Answer: The {label} of {name} is {value}."
                    )

        for states in self.states_by_name.values():
            for state in states:
                name = state["name"]
                country = state["country_name"]
                yield (
                    f"Question: What country is {name} in? "
                    f"Answer: {name} is in {country}."
                )
                for field in ("type", "iso2", "timezone", "native", "population"):
                    value = state.get(field)
                    if value not in (None, ""):
                        label = field.replace("_", " ")
                        yield (
                            f"Question: What is the {label} of {name}? "
                            f"Answer: The {label} of {name} is {value}."
                        )
                inferred = self.infer_state_capital(state)
                if inferred:
                    yield (
                        f"Question: What is the capital of {name}? "
                        f"Answer: The capital of {name} is {inferred}."
                    )
                elif fetch_state_capital:
                    wiki_capital = fetch_state_capital(state.get("wikiDataId"))
                    if wiki_capital:
                        yield (
                            f"Question: What is the capital of {name}? "
                            f"Answer: The capital of {name} is {wiki_capital}."
                        )

        for cities in self.cities_by_name.values():
            city = cities[0]
            if len(cities) > 1:
                continue
            name = city["name"]
            yield (
                f"Question: What country is {name} in? "
                f"Answer: {name} is in {city['country']}."
            )
            yield (
                f"Question: What state is {name} in? "
                f"Answer: {name} is in {city['state']}, {city['country']}."
            )
