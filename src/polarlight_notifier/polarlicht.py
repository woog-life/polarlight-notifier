import re
from dataclasses import dataclass
from datetime import datetime

import httpx
from bs4 import BeautifulSoup


def get_page(url: str = "https://polarlicht-vorhersage.de") -> str:
    response = httpx.get(url, timeout=15, follow_redirects=True)
    response.raise_for_status()

    return response.text


def parse_page(page: str) -> BeautifulSoup:
    soup = BeautifulSoup(page, "html.parser")

    return soup


def get_probability() -> str:
    page = get_page()
    soup = parse_page(page)
    tag = soup.select_one(".auroraChance")
    if tag:
        chance = "".join(tag.text).strip()
        return chance

    raise MissingChanceException()


@dataclass
class Sighting:
    url: str
    date: datetime
    brightness: str
    sightings_count: int


SIGHTING_REGEX = re.compile(
    r"Datum:\s*(?P<date>.*?)\s*Helligkeit:\s*(?P<brightness>.*?)\s*Anzahl\s*der\s*Sichtungen:\s*(?P<sightings_count>.*)"
)


class MissingSightingsException(Exception):
    pass


class MissingChanceException(Exception):
    pass


def get_last_sighting() -> Sighting:
    page = get_page()
    soup = parse_page(page)

    latest_sighting = soup.select_one("a.latestAuroraSighting")
    if not latest_sighting:
        raise MissingSightingsException()

    url = latest_sighting.attrs["href"]
    text = latest_sighting.text
    if match := SIGHTING_REGEX.search(text):
        date_group = match.group("date").split("/")[0]
        date = datetime.strptime(date_group, "%Y-%m-%d")

        return Sighting(
            url,
            date=date,
            brightness=match.group("brightness"),
            sightings_count=int(match.group("sightings_count").strip()),
        )
    else:
        raise MissingSightingsException()
