from dataclasses import dataclass


@dataclass(frozen=True)
class MetroArea:
    slug: str
    name: str
    aliases: tuple[str, ...]


METRO_LIST = [
    MetroArea("atlanta", "Atlanta", ("atlanta", "sandy springs", "alpharetta")),
    MetroArea("austin", "Austin", ("austin", "round rock")),
    MetroArea("boston", "Boston", ("boston", "cambridge", "somerville")),
    MetroArea("chicago", "Chicago", ("chicago", "naperville")),
    MetroArea("dallas", "Dallas-Fort Worth", ("dallas", "fort worth", "plano", "irving")),
    MetroArea("denver", "Denver", ("denver", "aurora", "lakewood")),
    MetroArea("houston", "Houston", ("houston", "sugar land", "the woodlands")),
    MetroArea("los-angeles", "Los Angeles", ("los angeles", "santa monica", "pasadena", "burbank")),
    MetroArea("miami", "Miami", ("miami", "fort lauderdale", "west palm beach")),
    MetroArea("new-york", "New York City", ("new york", "manhattan", "brooklyn", "queens", "jersey city")),
    MetroArea("philadelphia", "Philadelphia", ("philadelphia", "camden", "wilmington")),
    MetroArea("phoenix", "Phoenix", ("phoenix", "mesa", "scottsdale", "tempe")),
    MetroArea("raleigh", "Raleigh-Durham", ("raleigh", "durham", "cary", "chapel hill")),
    MetroArea("san-francisco", "San Francisco Bay Area", ("san francisco", "oakland", "berkeley", "san jose", "palo alto")),
    MetroArea("seattle", "Seattle", ("seattle", "bellevue", "redmond", "tacoma")),
    MetroArea("washington-dc", "Washington, DC", ("washington", "dc", "arlington", "alexandria", "bethesda")),
]

METRO_AREAS = {metro.slug: metro for metro in METRO_LIST}
