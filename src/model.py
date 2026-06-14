from database import GeoDatabase


class CountryModel:
    """Backward-compatible wrapper around GeoDatabase."""

    def __init__(self, country_data=None):
        self.db = GeoDatabase()
        self.country_data = country_data or {}

    def lookup_capital(self, place):
        capital, _ = self.db.place_capital(place)
        return capital

    def get_capital(self, country):
        return self.db.country_capital(country) or "Capital not found"

    def get_state_capital(self, country, state):
        states = self.db.get_states(state)
        for item in states:
            if item["country_name"].lower() == country.lower():
                inferred = self.db.infer_state_capital(item)
                if inferred:
                    return inferred
        return "State capital not found"
