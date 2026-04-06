from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests

from .metro import METRO_AREAS


GREENHOUSE_SOURCES = [
    {"company": "HubSpot", "board_token": "hubspot"},
    {"company": "Stripe", "board_token": "stripe"},
    {"company": "OpenAI", "board_token": "openai"},
    {"company": "Datadog", "board_token": "datadog"},
    {"company": "Vercel", "board_token": "vercel"},
]

LEVER_SOURCES = [
    {"company": "Ramp", "account": "ramp"},
    {"company": "Plaid", "account": "plaid"},
    {"company": "Figma", "account": "figma"},
    {"company": "Robinhood", "account": "robinhood"},
]

FALLBACK_INTERNSHIPS = [
    {
        "id": "fallback-openai-sf",
        "company": "OpenAI",
        "title": "Software Engineering Intern",
        "department": "Engineering",
        "location": "San Francisco, CA",
        "url": "https://openai.com/careers",
        "updatedAt": None,
        "isRemote": False,
        "source": "Fallback",
    },
    {
        "id": "fallback-vercel-remote",
        "company": "Vercel",
        "title": "Product Design Intern",
        "department": "Design",
        "location": "Remote (US)",
        "url": "https://vercel.com/careers",
        "updatedAt": None,
        "isRemote": True,
        "source": "Fallback",
    },
    {
        "id": "fallback-datadog-nyc",
        "company": "Datadog",
        "title": "Software Engineer Intern",
        "department": "Engineering",
        "location": "New York, NY",
        "url": "https://www.datadoghq.com/careers",
        "updatedAt": None,
        "isRemote": False,
        "source": "Fallback",
    },
    {
        "id": "fallback-figma-seattle",
        "company": "Figma",
        "title": "Data Science Intern",
        "department": "Data",
        "location": "Seattle, WA",
        "url": "https://www.figma.com/careers",
        "updatedAt": None,
        "isRemote": False,
        "source": "Fallback",
    },
    {
        "id": "fallback-stripe-chicago",
        "company": "Stripe",
        "title": "Product Management Intern",
        "department": "Product",
        "location": "Chicago, IL",
        "url": "https://stripe.com/jobs",
        "updatedAt": None,
        "isRemote": False,
        "source": "Fallback",
    },
]


class InternshipScraper:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "InternMatchBot/0.2 (+https://localhost) "
                    "student internship discovery tool"
                )
            }
        )
        self.source_names = [source["company"] for source in GREENHOUSE_SOURCES + LEVER_SOURCES]
        self.last_diagnostics: dict[str, Any] = {"errors": [], "usedFallback": False}

    def find_internships(self, metro_slug: str, keyword: str = "") -> list[dict[str, Any]]:
        metro = METRO_AREAS[metro_slug]
        keyword_lower = keyword.strip().lower()
        self.last_diagnostics = {"errors": [], "usedFallback": False}

        tasks: list[tuple[str, dict[str, str]]] = [
            *[("greenhouse", source) for source in GREENHOUSE_SOURCES],
            *[("lever", source) for source in LEVER_SOURCES],
        ]

        with ThreadPoolExecutor(max_workers=6) as executor:
            batches = list(executor.map(self._fetch_by_source, tasks))

        roles = [role for batch in batches for role in batch]
        if not roles:
            self.last_diagnostics["usedFallback"] = True
            roles = [dict(role) for role in FALLBACK_INTERNSHIPS]
        scored_roles: list[dict[str, Any]] = []

        for role in roles:
            title = role["title"].lower()
            location = role["location"].lower()
            department = role["department"].lower()

            if not self._looks_like_internship(title):
                continue

            if keyword_lower and not self._matches_keyword(keyword_lower, title, department, role["company"].lower()):
                continue

            if not any(alias in location or role["isRemote"] for alias in metro.aliases):
                continue

            role["score"] = self._score_role(role, keyword_lower, metro.aliases)
            scored_roles.append(role)

        deduped = self._dedupe(scored_roles)
        deduped.sort(key=lambda item: (-item["score"], item["company"], item["title"]))
        return deduped[:60]

    def _fetch_by_source(self, task: tuple[str, dict[str, str]]) -> list[dict[str, Any]]:
        kind, source = task
        if kind == "greenhouse":
            return self._fetch_greenhouse_roles(source)
        return self._fetch_lever_roles(source)

    def _fetch_greenhouse_roles(self, source: dict[str, str]) -> list[dict[str, Any]]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{source['board_token']}/jobs?content=true"
        try:
            response = self.session.get(url, timeout=12)
            response.raise_for_status()
        except requests.RequestException as exc:
            self.last_diagnostics["errors"].append(f"Greenhouse {source['company']}: {exc.__class__.__name__}")
            return []

        jobs = response.json().get("jobs", [])
        return [
            {
                "id": f"greenhouse-{source['board_token']}-{job['id']}",
                "company": source["company"],
                "title": job.get("title", "Untitled role"),
                "department": (job.get("departments") or [{"name": "General"}])[0].get("name", "General"),
                "location": job.get("location", {}).get("name", "Location unavailable"),
                "url": job.get("absolute_url", ""),
                "updatedAt": job.get("updated_at"),
                "isRemote": "remote" in job.get("location", {}).get("name", "").lower(),
                "source": "Greenhouse",
            }
            for job in jobs
        ]

    def _fetch_lever_roles(self, source: dict[str, str]) -> list[dict[str, Any]]:
        url = f"https://api.lever.co/v0/postings/{source['account']}?mode=json"
        try:
            response = self.session.get(url, timeout=12)
            response.raise_for_status()
        except requests.RequestException as exc:
            self.last_diagnostics["errors"].append(f"Lever {source['company']}: {exc.__class__.__name__}")
            return []

        jobs = response.json()
        return [
            {
                "id": f"lever-{source['account']}-{job['id']}",
                "company": source["company"],
                "title": job.get("text", "Untitled role"),
                "department": job.get("categories", {}).get("team", "General"),
                "location": job.get("categories", {}).get("location", "Location unavailable"),
                "url": job.get("hostedUrl", ""),
                "updatedAt": job.get("createdAt"),
                "isRemote": "remote" in job.get("categories", {}).get("location", "").lower(),
                "source": "Lever",
            }
            for job in jobs
        ]

    def _looks_like_internship(self, title: str) -> bool:
        internship_terms = ("intern", "internship", "co-op", "co op", "apprentice", "student")
        return any(term in title for term in internship_terms)

    def _score_role(self, role: dict[str, Any], keyword: str, aliases: tuple[str, ...]) -> int:
        score = 0
        title = role["title"].lower()
        location = role["location"].lower()
        department = role["department"].lower()

        if "software" in title or "engineer" in title:
            score += 6
        if "product" in title or "design" in title or "data" in title:
            score += 4
        if role["isRemote"]:
            score += 5
        if any(alias in location for alias in aliases):
            score += 8
        if keyword and (keyword in title or keyword in department):
            score += 7
        if "intern" in title:
            score += 10

        return score

    def _matches_keyword(self, keyword: str, title: str, department: str, company: str) -> bool:
        keywords = [part for part in keyword.split() if part]
        haystacks = (title, department, company)
        return any(part in haystack for part in keywords for haystack in haystacks)

    def _dedupe(self, roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
        for role in roles:
            key = (
                role["company"].strip().lower(),
                role["title"].strip().lower(),
                role["location"].strip().lower(),
            )
            current = deduped.get(key)
            if current is None or role["score"] > current["score"]:
                deduped[key] = role
        return list(deduped.values())
