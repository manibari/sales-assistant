"""Nexus outreach router — cold outreach: industry targeting, pitch generation."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.outreach import (
    get_available_industries,
    get_case_studies,
    get_solutions,
    get_target_companies,
    get_contacts_for_client,
    generate_pitch,
)
from services.nexus.knowledge import search_knowledge

router = APIRouter()


@router.get("/industries")
def list_industries():
    """List industries with case study and solution counts."""
    return get_available_industries()


@router.get("/case-studies")
def list_case_studies(industry: str | None = None):
    return get_case_studies(industry)


@router.get("/solutions")
def list_solutions(industry: str | None = None):
    return get_solutions(industry)


@router.get("/targets")
def list_targets(industry: str | None = None):
    return get_target_companies(industry)


@router.get("/targets/{client_id}/contacts")
def target_contacts(client_id: int):
    return get_contacts_for_client(client_id)


class PitchRequest(BaseModel):
    target_company: str
    target_industry: str
    case_study_industries: list[str] | None = None
    include_knowledge: bool = True


@router.post("/generate-pitch")
def create_pitch(body: PitchRequest):
    """Generate an AI pitch for cold outreach."""
    # Gather case studies
    cases = []
    if body.case_study_industries:
        for ind in body.case_study_industries:
            cases.extend(get_case_studies(ind))
    else:
        cases = get_case_studies(body.target_industry)

    # Gather solutions
    solutions = get_solutions(body.target_industry)

    # Optionally pull knowledge context
    knowledge_context = None
    if body.include_knowledge:
        try:
            chunks = search_knowledge(body.target_industry)
            if chunks:
                knowledge_context = "\n".join(
                    c.get("summary") or c.get("content", "")[:200]
                    for c in chunks[:5]
                )
        except Exception:
            pass

    result = generate_pitch(
        target_company=body.target_company,
        target_industry=body.target_industry,
        case_studies=cases,
        solutions=solutions,
        knowledge_context=knowledge_context,
    )

    if result["error"] and not result["pitch"]:
        raise HTTPException(500, result["error"])

    return result
