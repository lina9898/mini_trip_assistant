import os

from fastapi import APIRouter, HTTPException

from api.schemas import (
    AdoptTripRequest,
    EditTripRequest,
    ExportTripRequest,
    FeedbackTripRequest,
    GenerateTripRequest,
    RestoreTripRequest,
)
from evaluation_manager import record_reopen, update_project_evaluation
from memory_manager import get_memory_text
from storage import (
    list_saved_projects,
    load_project_by_filepath,
    save_project,
    save_project_snapshot,
)
from trip_service import (
    adopt_project,
    create_project_by_requirements,
    edit_project_by_request,
    export_current_project,
    restore_project_previous_version,
    submit_project_feedback,
)


router = APIRouter(prefix="/api/trips", tags=["trips"])


def build_download_url(filepath):
    if not filepath:
        return None
    return f"/{filepath.replace(os.sep, '/')}"


def group_projects_by_base_id(projects):
    grouped = {}

    for project in projects:
        base_project_id = project.get("base_project_id") or project.get("project_id") or project.get("filepath")
        if base_project_id not in grouped:
            grouped[base_project_id] = {
                "base_project_id": base_project_id,
                "project_id": project.get("project_id") or base_project_id,
                "destination": project.get("destination", "未知目的地"),
                "origin": project.get("origin", "未填写"),
                "travel_dates": project.get("travel_dates", {}),
                "created_at": project.get("created_at", "未知"),
                "updated_at": project.get("updated_at", "未知"),
                "latest_snapshot_version": project.get("snapshot_version", 1),
                "snapshot_count": 0,
                "latest_project_filepath": project.get("project_filepath") or project.get("filepath"),
                "snapshots": []
            }

        grouped[base_project_id]["snapshots"].append(project)

    groups = []
    total_snapshots = 0

    for group in grouped.values():
        snapshots = group["snapshots"]
        snapshots.sort(
            key=lambda item: (
                item.get("snapshot_version", 1),
                item.get("updated_at", ""),
                item.get("modified_time", "")
            )
        )

        latest = max(
            snapshots,
            key=lambda item: (
                item.get("snapshot_version", 1),
                item.get("updated_at", ""),
                item.get("modified_time", "")
            )
        )

        group["snapshots"] = snapshots
        group["snapshot_count"] = len(snapshots)
        group["latest_snapshot_version"] = latest.get("snapshot_version", 1)
        group["latest_project_filepath"] = latest.get("project_filepath") or latest.get("filepath")
        group["updated_at"] = latest.get("updated_at", latest.get("modified_time", "未知"))
        group["travel_dates"] = latest.get("travel_dates", group.get("travel_dates", {}))
        total_snapshots += len(snapshots)
        groups.append(group)

    groups.sort(key=lambda item: item.get("updated_at", ""), reverse=True)

    return {
        "groups": groups,
        "summary": {
            "project_count": len(groups),
            "snapshot_count": total_snapshots
        }
    }


@router.post("/generate")
def generate_trip(request: GenerateTripRequest):
    try:
        project_data = create_project_by_requirements(request.model_dump())
        filepath = save_project(project_data)

        return {
            "success": True,
            "message": "行程生成成功",
            "project_filepath": filepath,
            "project_data": project_data
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("")
def list_trips():
    try:
        projects = list_saved_projects()
        grouped = group_projects_by_base_id(projects)

        return {
            "success": True,
            "projects": grouped["groups"],
            "summary": grouped["summary"]
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/detail")
def get_trip_detail(project_filepath: str):
    try:
        project_data = load_project_by_filepath(project_filepath)
        project_data = record_reopen(project_data)
        project_data = update_project_evaluation(project_data)
        save_project_snapshot(project_data, update_timestamp=False)

        return {
            "success": True,
            "project_data": project_data
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/edit")
def edit_trip(request: EditTripRequest):
    try:
        project_data = load_project_by_filepath(request.project_filepath)
        project_data = edit_project_by_request(
            project_data=project_data,
            user_edit_request=request.edit_request
        )
        filepath = save_project(project_data)

        return {
            "success": True,
            "message": "行程修改成功",
            "project_filepath": filepath,
            "project_data": project_data
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/restore")
def restore_trip(request: RestoreTripRequest):
    try:
        project_data = load_project_by_filepath(request.project_filepath)
        project_data, result = restore_project_previous_version(project_data)

        if not result.get("success"):
            return {
                "success": False,
                "message": result.get("message"),
                "project_data": project_data
            }

        filepath = save_project(project_data)

        return {
            "success": True,
            "message": result.get("message"),
            "project_filepath": filepath,
            "project_data": project_data
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/memory")
def get_trip_memory(project_filepath: str):
    try:
        project_data = load_project_by_filepath(project_filepath)
        return {
            "success": True,
            "memory": project_data.get("memory", {}),
            "version_history": project_data.get("version_history", []),
            "memory_text": get_memory_text(project_data)
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/export")
def export_trip(request: ExportTripRequest):
    try:
        project_data = load_project_by_filepath(request.project_filepath)
        project_data = export_current_project(
            project_data=project_data,
            export_type=request.export_type
        )

        export_history = project_data.get("export_history", [])
        latest_export = export_history[-1] if export_history else {}

        return {
            "success": True,
            "message": "导出成功",
            "export": latest_export,
            "download_url": build_download_url(latest_export.get("filepath")),
            "project_data": project_data
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/adopt")
def adopt_trip(request: AdoptTripRequest):
    try:
        project_data = load_project_by_filepath(request.project_filepath)
        project_data = adopt_project(project_data)
        save_project_snapshot(project_data)

        return {
            "success": True,
            "message": "已标记为采纳此行程",
            "project_data": project_data
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/feedback")
def submit_feedback(request: FeedbackTripRequest):
    try:
        project_data = load_project_by_filepath(request.project_filepath)
        project_data = submit_project_feedback(
            project_data=project_data,
            score=request.score,
            feedback=request.feedback
        )
        save_project_snapshot(project_data)

        return {
            "success": True,
            "message": "反馈提交成功",
            "project_data": project_data
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
