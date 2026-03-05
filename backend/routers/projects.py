"""Projects API router — wraps services/project.py."""

from fastapi import APIRouter, HTTPException

from services import project as project_svc

router = APIRouter()


@router.get("/")
def list_projects():
    return project_svc.get_all()


@router.get("/presale")
def list_presale():
    return project_svc.get_presale()


@router.get("/postsale")
def list_postsale():
    return project_svc.get_postsale()


@router.get("/{project_id}")
def get_project(project_id: int):
    result = project_svc.get_by_id(project_id)
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    return result
