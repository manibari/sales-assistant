"""Network API router — stakeholder relations + intel + graph data."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import network as network_svc

router = APIRouter()


class RelationCreate(BaseModel):
    from_contact_id: int
    to_contact_id: int
    relation_type: str
    notes: str | None = None
    leverage_value: str = "medium"


class IntelCreate(BaseModel):
    title: str
    summary: str | None = None
    leverage_value: str = "medium"
    source_contact_id: int | None = None
    org_ids: list[str] | None = None


# --- Relations ---


@router.get("/relations")
def list_relations():
    return network_svc.get_all_relations()


@router.get("/relations/{contact_id}")
def get_contact_relations(contact_id: int):
    return network_svc.get_relations(contact_id)


@router.post("/relations", status_code=201)
def create_relation(body: RelationCreate):
    rel_id = network_svc.create_relation(
        from_contact_id=body.from_contact_id,
        to_contact_id=body.to_contact_id,
        relation_type=body.relation_type,
        notes=body.notes,
        leverage_value=body.leverage_value,
    )
    return {"id": rel_id}


@router.delete("/relations/{relation_id}", status_code=204)
def delete_relation(relation_id: int):
    network_svc.delete_relation(relation_id)


# --- Intel ---


@router.get("/intel")
def list_intel():
    return network_svc.get_all_intel()


@router.get("/intel/{intel_id}")
def get_intel(intel_id: int):
    result = network_svc.get_intel_by_id(intel_id)
    if not result:
        raise HTTPException(status_code=404, detail="Intel not found")
    return result


@router.post("/intel", status_code=201)
def create_intel(body: IntelCreate):
    intel_id = network_svc.create_intel(
        title=body.title,
        summary=body.summary,
        leverage_value=body.leverage_value,
        source_contact_id=body.source_contact_id,
        org_ids=body.org_ids,
    )
    return {"id": intel_id}


@router.delete("/intel/{intel_id}", status_code=204)
def delete_intel(intel_id: int):
    network_svc.delete_intel(intel_id)


# --- Graph ---


@router.get("/graph")
def get_graph():
    """Full graph data for network visualization."""
    return network_svc.get_graph_data()
