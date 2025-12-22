"""
API routes for Workflow Patch Agent.
Provides endpoints for workflow analysis, patch management, and deployment.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.deps.auth import require_role
from src.hooks.audit import AuditLogger
from src.models.models import WorkflowAnalysis, WorkflowPatch
from src.schemas.schemas import (PatchDeploymentReport, WorkflowAnalysisCreate,
                                 WorkflowAnalysisResponse,
                                 WorkflowHealthReport, WorkflowPatchCreate,
                                 WorkflowPatchResponse, WorkflowPatchUpdate)
from src.services.workflow_patch_agent import WorkflowPatchAgent

router = APIRouter(prefix="/workflow-patch-agent", tags=["Workflow Patch Agent"])


@router.post("/analyze", response_model=WorkflowAnalysisResponse)
def trigger_workflow_analysis(
    workflow_name: str,
    analysis_type: str = "quality",
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("guardian")),
):
    """
    Trigger automated workflow analysis.

    Requires: Guardian role

    Args:
        workflow_name: Name of the workflow to analyze
        analysis_type: Type of analysis (security, performance, efficiency, compatibility, quality)

    Returns:
        WorkflowAnalysisResponse with findings
    """
    agent = WorkflowPatchAgent(db)

    try:
        analysis = agent.analyze_workflow(workflow_name, analysis_type)

        # Log the analysis
        AuditLogger.log_create(
            db=db,
            entity_type="WorkflowAnalysis",
            entity_id=analysis.id,
            entity_data={
                "workflow_name": workflow_name,
                "analysis_type": analysis_type,
                "severity": analysis.severity,
            },
            user_id=current_user.get("sub"),
        )

        return analysis
    except Exception as analysis_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(analysis_error)}",
        )


@router.get("/analyses", response_model=List[WorkflowAnalysisResponse])
def list_workflow_analyses(
    workflow_name: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("guardian")),
):
    """
    List workflow analyses.

    Requires: Guardian role

    Args:
        workflow_name: Optional filter by workflow name
        status_filter: Optional filter by status
        limit: Maximum number of results

    Returns:
        List of WorkflowAnalysisResponse
    """
    query = db.query(WorkflowAnalysis)

    if workflow_name:
        query = query.filter(WorkflowAnalysis.workflow_name == workflow_name)

    if status_filter:
        query = query.filter(WorkflowAnalysis.status == status_filter)

    analyses = query.order_by(WorkflowAnalysis.created_at.desc()).limit(limit).all()
    return analyses


@router.get("/analyses/{analysis_id}", response_model=WorkflowAnalysisResponse)
def get_workflow_analysis(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("guardian")),
):
    """
    Get a specific workflow analysis.

    Requires: Guardian role
    """
    analysis = (
        db.query(WorkflowAnalysis).filter(WorkflowAnalysis.id == analysis_id).first()
    )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found",
        )

    return analysis


@router.post("/patches", response_model=WorkflowPatchResponse)
def create_patch(
    analysis_id: UUID,
    patch_data: WorkflowPatchCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("guardian")),
):
    """
    Create a new patch based on analysis findings.

    Requires: Guardian role

    Args:
        analysis_id: UUID of the analysis that identified the issue
        patch_data: Patch creation data

    Returns:
        WorkflowPatchResponse
    """
    agent = WorkflowPatchAgent(db)

    try:
        patch = agent.create_patch(analysis_id, patch_data)

        # Log the patch creation
        AuditLogger.log_create(
            db=db,
            entity_type="WorkflowPatch",
            entity_id=patch.id,
            entity_data={
                "patch_name": patch.patch_name,
                "patch_type": patch.patch_type,
                "severity": patch.severity,
                "target_workflow": patch.target_workflow,
            },
            user_id=current_user.get("sub"),
        )

        return patch
    except ValueError as value_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(value_error)
        )
    except Exception as patch_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Patch creation failed: {str(patch_error)}",
        )


@router.get("/patches", response_model=List[WorkflowPatchResponse])
def list_patches(
    workflow_name: Optional[str] = None,
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("guardian")),
):
    """
    List workflow patches.

    Requires: Guardian role

    Args:
        workflow_name: Optional filter by workflow name
        status_filter: Optional filter by status
        severity_filter: Optional filter by severity
        limit: Maximum number of results

    Returns:
        List of WorkflowPatchResponse
    """
    query = db.query(WorkflowPatch)

    if workflow_name:
        query = query.filter(WorkflowPatch.target_workflow == workflow_name)

    if status_filter:
        query = query.filter(WorkflowPatch.status == status_filter)

    if severity_filter:
        query = query.filter(WorkflowPatch.severity == severity_filter)

    patches = query.order_by(WorkflowPatch.created_at.desc()).limit(limit).all()
    return patches


@router.get("/patches/{patch_id}", response_model=WorkflowPatchResponse)
def get_patch(
    patch_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("guardian")),
):
    """
    Get a specific patch.

    Requires: Guardian role
    """
    patch = db.query(WorkflowPatch).filter(WorkflowPatch.id == patch_id).first()

    if not patch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Patch {patch_id} not found"
        )

    return patch


@router.post("/patches/{patch_id}/test", response_model=dict)
def test_patch(
    patch_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("guardian")),
):
    """
    Test a patch in isolation and with integration tests.

    Requires: Guardian role

    Returns:
        Test results dictionary
    """
    agent = WorkflowPatchAgent(db)

    try:
        test_results = agent.test_patch(patch_id)

        # Log the testing
        AuditLogger.log_action(
            db=db,
            entity_type="WorkflowPatch",
            entity_id=patch_id,
            action="update",
            user_id=current_user.get("sub"),
            changes={"action": "tested", "results": test_results},
        )

        return test_results
    except ValueError as value_error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(value_error)
        )
    except Exception as test_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Testing failed: {str(test_error)}",
        )


@router.post("/patches/{patch_id}/deploy", response_model=PatchDeploymentReport)
def deploy_patch(
    patch_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("guardian")),
):
    """
    Deploy a tested and approved patch.

    Requires: Guardian role

    Returns:
        PatchDeploymentReport with deployment details
    """
    agent = WorkflowPatchAgent(db)

    try:
        report = agent.deploy_patch(
            patch_id=patch_id, approved_by=current_user.get("sub")
        )

        # Log the deployment
        AuditLogger.log_action(
            db=db,
            entity_type="WorkflowPatch",
            entity_id=patch_id,
            action="update",
            user_id=current_user.get("sub"),
            changes={"action": "deployed", "report": report.model_dump()},
        )

        return report
    except ValueError as value_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(value_error)
        )
    except Exception as deployment_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(deployment_error)}",
        )


@router.patch("/patches/{patch_id}", response_model=WorkflowPatchResponse)
def update_patch(
    patch_id: UUID,
    update_data: WorkflowPatchUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("guardian")),
):
    """
    Update a patch (e.g., approve, review).

    Requires: Guardian role
    """
    patch = db.query(WorkflowPatch).filter(WorkflowPatch.id == patch_id).first()

    if not patch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Patch {patch_id} not found"
        )

    # Store old data for audit
    old_data = {
        "status": patch.status,
        "reviewed_by": patch.reviewed_by,
        "approved_by": patch.approved_by,
    }

    # Update fields
    if update_data.status is not None:
        patch.status = update_data.status
    if update_data.reviewed_by is not None:
        patch.reviewed_by = update_data.reviewed_by
    if update_data.approved_by is not None:
        patch.approved_by = update_data.approved_by
    if update_data.test_results is not None:
        patch.test_results = update_data.test_results
    if update_data.impact_report is not None:
        patch.impact_report = update_data.impact_report

    db.commit()
    db.refresh(patch)

    # Log the update
    new_data = {
        "status": patch.status,
        "reviewed_by": patch.reviewed_by,
        "approved_by": patch.approved_by,
    }

    AuditLogger.log_update(
        db=db,
        entity_type="WorkflowPatch",
        entity_id=patch.id,
        old_data=old_data,
        new_data=new_data,
        user_id=current_user.get("sub"),
    )

    return patch


@router.get("/health/{workflow_name}", response_model=WorkflowHealthReport)
def get_workflow_health(
    workflow_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("guardian")),
):
    """
    Get comprehensive health report for a workflow.

    Requires: Guardian role

    Returns:
        WorkflowHealthReport with health metrics
    """
    agent = WorkflowPatchAgent(db)

    try:
        health_report = agent.get_workflow_health(workflow_name)
        return health_report
    except Exception as health_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate health report: {str(health_error)}",
        )


@router.delete("/patches/{patch_id}/rollback")
def rollback_patch(
    patch_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("guardian")),
):
    """
    Rollback a deployed patch.

    Requires: Guardian role

    Returns:
        Success message
    """
    agent = WorkflowPatchAgent(db)

    patch = db.query(WorkflowPatch).filter(WorkflowPatch.id == patch_id).first()

    if not patch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Patch {patch_id} not found"
        )

    if patch.status != "deployed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only deployed patches can be rolled back. Current status: {patch.status}",
        )

    try:
        agent._rollback_patch(patch)

        # Log the rollback
        AuditLogger.log_action(
            db=db,
            entity_type="WorkflowPatch",
            entity_id=patch.id,
            action="update",
            user_id=current_user.get("sub"),
            changes={"action": "rolled_back"},
        )

        return {
            "message": "Patch rolled back successfully",
            "patch_id": str(patch_id),
            "status": patch.status,
        }
    except Exception as rollback_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback failed: {str(rollback_error)}",
        )
