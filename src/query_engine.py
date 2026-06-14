import re

from database import GeoDatabase
from normalize import normalize_question, parse_place_hint, title_place, wrap_bidi


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
                r"^(?:what(?:'s| is) the )?(currency|phone\s*code|iso2?|iso3|population|region|subregion|nationality|time\s*zone|timezone|latitude|longitude|currency name|tld|native language|native name|native) of (.+?)\??$",
                re.I,
            ),
            "field",
        ),
        (
            re.compile(r"^native language of (.+?)\??$", re.I),
            "field_languages",
        ),
        (
            re.compile(r"^native(?: name)? of (.+?)\??$", re.I),
            "field_native",
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
            re.compile(r"^where(?:'s| is) (.+?)\??$", re.I),
            "where",
        ),
        (
            re.compile(r"^location of (.+?)\??$", re.I),
            "where",
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
            re.compile(r"^what is (?!the )([^?]+?)\??$", re.I),
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
        "time zone": "timezone",
        "timezone": "timezone",
        "latitude": "latitude",
        "longitude": "longitude",
        "currency name": "currency_name",
        "tld": "tld",
        "native name": "native",
        "native": "native",
    }

    LANGUAGE_LABELS = {
        "native language",
        "language",
        "official language",
        "languages",
        "official languages",
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
                field_label = match.group(1).strip()
                place = match.group(2).strip()
                if field_label.lower() in self.LANGUAGE_LABELS:
                    return self._answer_languages(place)
                return self._answer_field(field_label, place)
            if kind == "field_languages":
                return self._answer_languages(match.group(1).strip())
            if kind == "field_native":
                return self._answer_field("native", match.group(1).strip())
            if kind == "city_country":
                return self._answer_city_country(match.group(1).strip())
            if kind == "city_state":
                return self._answer_city_state(match.group(1).strip())
            if kind == "where":
                return self._answer_where(match.group(1).strip())
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
            "I could not find '{question}' in the dataset. "
            "Try: capital of India | currency of Japan | what country is Paris in | "
            "what country is Kerala in | list states in India | tell me about Kerala"
        ).format(question=question)

    def _answer_capital(self, place: str) -> str:
        place = normalize_question(place)
        capital, note = self.db.place_capital(place)
        if capital:
            return f"The capital of {place} is {capital}."
        return (
            f"I could not find a capital for '{place}' in the dataset. ({note})"
        )

    def _answer_languages(self, place: str) -> str:
        from wikidata import fetch_country_languages

        place = normalize_question(place)
        country = self.db.find_country(place)
        if not country:
            return f"'{place}' was not found in the dataset."

        display = title_place(place)
        languages = fetch_country_languages(country.get("wikiDataId"))
        if languages:
            if len(languages) == 1:
                return f"The official language of {display} is {languages[0]}."
            return f"The official languages of {display} are {', '.join(languages)}."

        native = country.get("native")
        if native:
            return (
                f"No official language list found for {display}. "
                f"The endonym (native country name) is {wrap_bidi(native)}."
            )
        return f"No language data found for {display}."

    def _format_country_timezones(self, display: str, country: dict) -> str:
        timezones = country.get("timezones") or []
        if not timezones:
            return f"The dataset has no timezone for {display}."
        parts = []
        for tz in timezones:
            zone = tz.get("zoneName") or tz.get("tzName") or "unknown"
            offset = tz.get("gmtOffsetName")
            abbr = tz.get("abbreviation")
            detail = zone
            if offset:
                detail = f"{zone} ({offset}"
                if abbr:
                    detail += f", {abbr}"
                detail += ")"
            parts.append(detail)
        if len(parts) == 1:
            return f"The timezone of {display} is {parts[0]}."
        lines = [f"The timezones of {display} are:"]
        lines.extend(f"  - {part}" for part in parts)
        return "\n".join(lines)

    def _answer_field(self, field_label: str, place: str) -> str:
        field = self.FIELD_MAP.get(field_label.lower(), field_label.lower())
        place = normalize_question(place)
        display = title_place(place)

        cities = self.db.get_cities(place)
        if cities:
            if len(cities) == 1:
                city = cities[0]
                if field in ("latitude", "longitude", "timezone"):
                    value = city.get(field)
                    if value not in (None, ""):
                        return f"The {field_label} of {display} is {value}."
                if field == "timezone":
                    return f"The dataset has no timezone for {display}."
            elif field in ("latitude", "longitude", "timezone"):
                return (
                    f"'{display}' exists in multiple places — specify state/country. "
                    f"Try: where is {display}"
                )

        country = self.db.find_country(place)
        if country:
            return self._answer_country_field(field, field_label, display, country)

        resolved = self.db.resolve(place)
        if not resolved:
            return f"'{place}' was not found in the dataset."

        entity_type, record = resolved
        if entity_type == "country":
            return self._answer_country_field(field, field_label, display, record)

        if entity_type == "state":
            states = record if isinstance(record, list) else [record]
            state = states[0]
            if field == "timezone":
                value = state.get("timezone")
                if value:
                    return f"The timezone of {display} is {value}."
            for key in ("population", "native", "iso2", "type", "latitude", "longitude"):
                if field == key:
                    value = state.get(key)
                    if value not in (None, ""):
                        return f"The {field_label} of {display} is {value}."
            return f"'{field_label}' for states is limited in the dataset. Try: tell me about {place}"

        if entity_type == "city":
            cities = record if isinstance(record, list) else [record]
            if len(cities) == 1 and field in ("latitude", "longitude", "timezone"):
                value = cities[0].get(field)
                if value not in (None, ""):
                    return f"The {field_label} of {display} is {value}."
            return f"'{field_label}' is only stored for countries in this dataset."

        return f"I cannot answer {field_label} for {entity_type} entities."

    def _answer_where(self, place: str) -> str:
        place = normalize_question(place)
        name, country_hint = parse_place_hint(place)
        display = title_place(name)

        if country_hint:
            cities = self.db.get_cities(name, country_hint)
            if cities:
                if len(cities) == 1:
                    return self.db.format_city(cities[0])
                lines = [f"'{display}' in {country_hint}:"]
                for city in cities[:10]:
                    lines.append(
                        f"- {city['state']}, {city['country']} "
                        f"(lat {city.get('latitude')}, lon {city.get('longitude')})"
                    )
                return "\n".join(lines)

        if self.db.is_country_alias(name) and not country_hint:
            country = self.db.find_country(name)
            if country:
                return self.db.format_country(country)

        cities = self.db.get_cities(name)
        if cities:
            if len(cities) == 1:
                return self.db.format_city(cities[0])
            lines = [f"'{display}' appears in multiple places:"]
            for city in cities[:10]:
                lines.append(
                    f"- {city['name']}, {city['state']}, {city['country']} "
                    f"(lat {city.get('latitude')}, lon {city.get('longitude')})"
                )
            if len(cities) > 10:
                lines.append(f"... and {len(cities) - 10} more")
            lines.append("Tip: add a country, e.g. where is Usa in Japan")
            return "\n".join(lines)

        states = self.db.get_states(name)
        if states:
            if len(states) == 1:
                return self.db.format_state(states[0])
            lines = [f"'{display}' is a state/region in multiple countries:"]
            for state in states[:10]:
                lines.append(f"- {state['name']}, {state['country_name']}")
            return "\n".join(lines)

        country = self.db.find_country(name)
        if country:
            return self.db.format_country(country)

        resolved = self.db.resolve(name)
        if resolved:
            return self._answer_info(name)

        return f"'{place}' was not found in the dataset."

    def _answer_country_field(
        self, field: str, field_label: str, display: str, country: dict
    ) -> str:
        if field == "timezone":
            return self._format_country_timezones(display, country)
        value = country.get(field)
        if value not in (None, ""):
            if field == "native":
                return f"The endonym (native name) of {display} is {wrap_bidi(value)}."
            return f"The {field_label} of {display} is {value}."
        return f"The dataset has no {field_label} for {display}."

    def _answer_city_country(self, place_name: str) -> str:
        place_name = normalize_question(place_name)
        cities = self.db.get_cities(place_name)
        if cities:
            if len(cities) == 1:
                city = cities[0]
                return f"{place_name} is in {city['country']}."
            lines = [f"'{place_name}' appears in multiple places:"]
            for city in cities[:10]:
                lines.append(f"- {city['state']}, {city['country']}")
            if len(cities) > 10:
                lines.append(f"... and {len(cities) - 10} more")
            return "\n".join(lines)

        states = self.db.get_states(place_name)
        if states:
            if len(states) == 1:
                state = states[0]
                return f"{place_name} is in {state['country_name']}."
            countries = sorted({state["country_name"] for state in states})
            if len(countries) == 1:
                return f"{place_name} is in {countries[0]}."
            lines = [f"'{place_name}' is a state/region in multiple countries:"]
            for state in states[:10]:
                lines.append(f"- {state['country_name']}")
            return "\n".join(lines)

        return f"'{place_name}' was not found in the dataset."

    def _answer_city_state(self, city_name: str) -> str:
        city_name = normalize_question(city_name)
        cities = self.db.get_cities(city_name)
        if not cities:
            return f"'{city_name}' was not found in the city index."
        if len(cities) == 1:
            city = cities[0]
            display = city["name"] if city["name"].lower() != city_name.lower() else city_name
            return f"{display} is in {city['state']}, {city['country']}."
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
        if len(names) <= 15:
            return f"States/regions in {country_name} ({len(names)}): {', '.join(names)}"
        lines = [f"States/regions in {country_name} ({len(names)}):"]
        lines.extend(f"  - {name}" for name in names)
        return "\n".join(lines)

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
