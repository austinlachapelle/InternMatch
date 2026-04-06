from fastapi import APIRouter, HTTPException, Query

from ..services.metro import METRO_AREAS
from ..services.scraper import InternshipScraper


router = APIRouter(tags=["internships"])
scraper = InternshipScraper()


@router.get("/metros")
def list_metros() -> dict[str, list[dict[str, str]]]:
    return {
        "metros": [
            {"slug": metro.slug, "name": metro.name}
            for metro in sorted(METRO_AREAS.values(), key=lambda item: item.name)
        ]
    }


@router.get("/internships")
def get_internships(
    metro: str = Query(..., description="Metro slug"),
    keyword: str = Query("", description="Optional keyword"),
) -> dict[str, object]:
    if metro not in METRO_AREAS:
        raise HTTPException(status_code=404, detail="Metro area not found.")

    roles = scraper.find_internships(metro_slug=metro, keyword=keyword)
    return {
        "metro": METRO_AREAS[metro].name,
        "count": len(roles),
        "results": roles,
        "sources": scraper.source_names,
        "diagnostics": scraper.last_diagnostics,
    }
