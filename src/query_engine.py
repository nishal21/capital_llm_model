import re

from database import GeoDatabase
from normalize import normalize_question


class QueryEngine:
    PATTERNS = [
        (
            re.compile(
                r"^what(?:'s| is) the capital of (.+?)\??$",
                re.I,
            ),
            "capital",
        ),
        (
            re.compile(
                r"^(?:what(?:'s| is) the )?capital of (.+?)\??$",
                re.I,
            ),
            "capital",
        ),
        (
            re.compile(
                r"^(?:what(?:'s| is) the )?(currency|phone\s*code|iso2?|iso3|population|region|subregion|nationality|timezone|currency name|tld|native name) of (.+?)\??$",
                re.I,
            ),
            "field",
        ),
        (
            re.compile(r"^what country is (.+?) in\??$", re.I),
            "city_country",
        ),
        (
            re.compile(r"^what state is (.+?) in\??$", re.I),
            "city_state",
        ),
        (
            re.compile(r"^list (?:all )?states (?:in|of) (.+?)\??$", re.I),
            "list_states",
        ),
        (
            re.compile(
                r"^list cities (?:in|of) (.+?)(?: in (.+?))?\??$",
                re.I,
            ),
            "list_cities",
        ),
        (
            re.compile(r"^(?:tell me about|info(?:rmation)? on|about) (.+?)\??$", re.I),
            "info",
        ),
        (
            re.compile(r"^(.+?) capital\??$", re.I),
            "capital",
        ),
    ]

    FIELD_MAP = {
        "currency": "currency",
        "phone code": "phonecode",
        "phonecode": "phonecode",
        "iso2": "iso2",
        "iso": "iso2",
        "iso3": "iso3",
        "population": "population",
        "region": "region",
        "subregion": "subregion",
        "nationality": "nationality",
        "timezone": "timezone",
        "currency name": "currency_name",
        "tld": "tld",
        "native name": "native",
        "native": "native",
    }

    def __init__(self, db: GeoDatabase | None = None):
        self.db = db or GeoDatabase()

    def answer(self, question: str) -> str:
        question = normalize_question(question)
        if not question:
            return "Please ask a question."

        for pattern, kind in self.PATTERNS:
            match = pattern.match(question)
            if not match:
                continue

            if kind == "capital":
                return self._answer_capital(match.group(1).strip())
            if kind == "field":
                return self._answer_field(match.group(1).strip(), match.group(2).strip())
            if kind == "city_country":
                return self._answer_city_country(match.group(1).strip())
            if kind == "city_state":
                return self._answer_city_state(match.group(1).strip())
            if kind == "list_states":
                return self._answer_list_states(match.group(1).strip())
            if kind == "list_cities":
                place = match.group(1).strip()
                country = match.group(2).strip() if match.lastindex and match.lastindex >= 2 and match.group(2) else None
                return self._answer_list_cities(place, country)
            if kind == "info":
                return self._answer_info(match.group(1).strip())

        capital, note = self.db.place_capital(question)
        if capital:
            return f"The capital of {question} is {capital}. ({note})"

        resolved = self.db.resolve(question)
        if resolved:
            return self._answer_info(question)

        return (
            f"I could not find '{question}' in the dataset. "
            "Try: capital of India | currency of Japan | what country is Paris in | "
            "list states in India | tell me about Kerala"
        )

    def _answer_capital(self, place: str) -> str:
        place = normalize_question(place)
        capital, note = self.db.place_capital(place)
        if capital:
            return f"The capital of {place} is {capital}."
        return (
            f"I could not find a capital for '{place}' in the dataset. ({note})"
        )

    def _answer_field(self, field_label: str, place: str) -> str:
        field = self.FIELD_MAP.get(field_label.lower(), field_label.lower())
        resolved = self.db.resolve(place)
        if not resolved:
            return f"'{place}' was not found in the dataset."

        entity_type, record = resolved
        if entity_type == "country":
            value = record.get(field)
            if value not in (None, ""):
                return f"The {field_label} of {place} is {value}."
            return f"The dataset has no {field_label} for {place}."

        if entity_type == "state":
            states = record if isinstance(record, list) else [record]
            state = states[0]
            if field == "timezone":
                value = state.get("timezone")
                if value:
                    return f"The timezone of {place} is {value}."
            for key in ("population", "native", "iso2", "type"):
                if field == key:
                    value = state.get(key)
                    if value not in (None, ""):
                        return f"The {field_label} of {place} is {value}."
            return f"'{field_label}' for states is limited in the dataset. Try: tell me about {place}"

        if entity_type == "city":
            cities = record if isinstance(record, list) else [record]
            if field == "timezone" and cities:
                return f"The timezone of {place} is {cities[0].get('timezone')}."
            return f"'{field_label}' is only stored for countries in this dataset."

        return f"I cannot answer {field_label} for {entity_type} entities."

    def _answer_city_country(self, city_name: str) -> str:
        cities = self.db.get_cities(city_name)
        if not cities:
            return f"'{city_name}' was not found in the city index."
        if len(cities) == 1:
            city = cities[0]
            return f"{city_name} is in {city['country']}."
        lines = [f"'{city_name}' appears in multiple places:"]
        for city in cities[:10]:
            lines.append(f"- {city['state']}, {city['country']}")
        if len(cities) > 10:
            lines.append(f"... and {len(cities) - 10} more")
        return "\n".join(lines)

    def _answer_city_state(self, city_name: str) -> str:
        cities = self.db.get_cities(city_name)
        if not cities:
            return f"'{city_name}' was not found in the city index."
        if len(cities) == 1:
            city = cities[0]
            return f"{city_name} is in {city['state']}, {city['country']}."
        lines = [f"'{city_name}' appears in multiple states:"]
        for city in cities[:10]:
            lines.append(f"- {city['state']}, {city['country']}")
        if len(cities) > 10:
            lines.append(f"... and {len(cities) - 10} more")
        return "\n".join(lines)

    def _answer_list_states(self, country_name: str) -> str:
        states = self.db.get_states(country_name)
        if not states:
            return f"No states found for '{country_name}'."
        names = sorted({state["name"] for state in states})
        preview = ", ".join(names[:20])
        suffix = f" ... ({len(names)} total)" if len(names) > 20 else f" ({len(names)} total)"
        return f"States/regions in {country_name}: {preview}{suffix}"

    def _answer_list_cities(self, place: str, country: str | None) -> str:
        states = self.db.get_states(place)
        if states:
            target_states = states
            if country:
                target_states = [
                    state
                    for state in states
                    if state["country_name"].lower() == country.lower()
                ]
            if not target_states:
                return f"No state '{place}' found in {country}."
            state = target_states[0]
            cities = state.get("cities") or []
            names = [city["name"] for city in cities[:25]]
            suffix = f" ... ({len(cities)} total)" if len(cities) > 25 else f" ({len(cities)} total)"
            return f"Cities in {state['name']}, {state['country_name']}: {', '.join(names)}{suffix}"

        country = self.db.get_country(place)
        if country:
            states = self.db.get_states(place)
            city_names = []
            for state in states[:5]:
                for city in (state.get("cities") or [])[:5]:
                    city_names.append(city["name"])
            return (
                f"{place} has {len(states)} states/regions in the dataset. "
                f"Sample cities: {', '.join(city_names) or 'none loaded'}. "
                f"Ask: list cities in <state>"
            )

        return f"'{place}' is not a country or state in the dataset."

    def _answer_info(self, place: str) -> str:
        resolved = self.db.resolve(place)
        if not resolved:
            return f"'{place}' was not found in the dataset."

        entity_type, record = resolved
        if entity_type == "country":
            return self.db.format_country(record)
        if entity_type == "state":
            states = record if isinstance(record, list) else [record]
            if len(states) > 1:
                blocks = [self.db.format_state(state) for state in states[:5]]
                extra = f"\n... and {len(states) - 5} more matches" if len(states) > 5 else ""
                return "\n\n".join(blocks) + extra
            return self.db.format_state(states[0])
        if entity_type == "city":
            cities = record if isinstance(record, list) else [record]
            if len(cities) > 1:
                blocks = [self.db.format_city(city) for city in cities[:5]]
                extra = f"\n... and {len(cities) - 5} more matches" if len(cities) > 5 else ""
                return "\n\n".join(blocks) + extra
            return self.db.format_city(cities[0])
        if entity_type == "region":
            return f"Region: {record['name']}"
        if entity_type == "subregion":
            return f"Subregion: {record['name']}"
        return str(record)
