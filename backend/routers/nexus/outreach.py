"""Nexus outreach router — cold outreach: industry targeting, pitch generation."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.nexus.outreach import (
    get_available_industries,
    get_available_regions,
    get_case_studies,
    get_solutions,
    get_target_companies,
    get_contacts_for_client,
    get_batch_summary,
    generate_pitch,
    generate_visit_plan,
)
from services.nexus.knowledge import search_knowledge

router = APIRouter()


@router.get("/industries")
def list_industries():
    """List industries with case study and solution counts."""
    return get_available_industries()


@router.get("/regions")
def list_regions():
    """List distinct regions from nx_client with counts."""
    return get_available_regions()


@router.get("/case-studies")
def list_case_studies(industry: str | None = None):
    return get_case_studies(industry)


@router.get("/solutions")
def list_solutions(industry: str | None = None):
    return get_solutions(industry)


@router.get("/targets")
def list_targets(industry: str | None = None, region: str | None = None):
    return get_target_companies(industry, region)


@router.get("/targets/{client_id}/contacts")
def target_contacts(client_id: int):
    return get_contacts_for_client(client_id)


class BatchSummaryRequest(BaseModel):
    client_ids: list[int]


@router.post("/batch-summary")
def batch_summary(body: BatchSummaryRequest):
    """Get enriched info for multiple clients."""
    return get_batch_summary(body.client_ids)


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


class VisitPlanRequest(BaseModel):
    client_ids: list[int]
    region: str | None = None
    industry: str | None = None


@router.post("/generate-visit-plan")
def create_visit_plan(body: VisitPlanRequest):
    """Generate an AI visit plan for batch outreach."""
    targets = get_batch_summary(body.client_ids)
    if not targets:
        raise HTTPException(400, "No valid clients found")

    case_studies = get_case_studies(body.industry) if body.industry else []
    solutions = get_solutions(body.industry) if body.industry else []

    result = generate_visit_plan(
        targets=targets,
        region=body.region,
        industry=body.industry,
        case_studies=case_studies,
        solutions=solutions,
    )

    if result["error"] and not result["plan"]:
        raise HTTPException(500, result["error"])

    return result
