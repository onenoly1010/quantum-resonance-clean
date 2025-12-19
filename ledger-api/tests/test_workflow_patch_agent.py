"""
Tests for Workflow Patch Agent service.
"""
import pytest
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from src.db.session import Base
from src.models.models import WorkflowPatch, WorkflowAnalysis
from src.services.workflow_patch_agent import WorkflowPatchAgent
from src.schemas.schemas import (
    WorkflowPatchCreate, PatchContent,
    WorkflowAnalysisCreate, AnalysisFindings
)


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def patch_agent(db_session):
    """Create a WorkflowPatchAgent instance."""
    return WorkflowPatchAgent(db_session)


def test_analyze_workflow_security(patch_agent):
    """Test security analysis of a workflow."""
    workflow_name = "test-workflow-ci"
    
    analysis = patch_agent.analyze_workflow(workflow_name, "security")
    
    assert analysis is not None
    assert analysis.workflow_name == workflow_name
    assert analysis.analysis_type == "security"
    assert analysis.status == "new"
    assert analysis.analyzed_by == "WorkflowPatchAgent"
    assert analysis.severity in ["critical", "high", "medium", "low", "info"]
    assert "issues" in analysis.findings
    assert "inefficiencies" in analysis.findings
    assert "opportunities" in analysis.findings


def test_analyze_workflow_performance(patch_agent):
    """Test performance analysis of a workflow."""
    workflow_name = "test-workflow-ci"
    
    analysis = patch_agent.analyze_workflow(workflow_name, "performance")
    
    assert analysis is not None
    assert analysis.analysis_type == "performance"
    assert analysis.metrics is not None
    assert "execution_time_ms" in analysis.metrics


def test_analyze_workflow_quality(patch_agent):
    """Test quality analysis of a workflow."""
    workflow_name = "test-workflow-ci"
    
    analysis = patch_agent.analyze_workflow(workflow_name, "quality")
    
    assert analysis is not None
    assert analysis.analysis_type == "quality"
    assert analysis.recommendations is not None


def test_create_patch_valid(patch_agent):
    """Test creating a valid patch."""
    # First create an analysis
    analysis = patch_agent.analyze_workflow("test-workflow", "security")
    
    # Create patch
    patch_content = PatchContent(
        files_modified=["src/main.py", "src/config.py"],
        changes={"fix": "Updated authentication logic"},
        dependencies=["python-jose"],
        configuration={"timeout": 30}
    )
    
    patch_data = WorkflowPatchCreate(
        patch_name="Fix Authentication Issue",
        patch_version="1.0.0",
        patch_type="security",
        description="Fixes critical authentication vulnerability",
        target_workflow="test-workflow",
        issue_identified="Weak authentication mechanism",
        patch_content=patch_content,
        severity="critical"
    )
    
    patch = patch_agent.create_patch(analysis.id, patch_data)
    
    assert patch is not None
    assert patch.patch_name == "Fix Authentication Issue"
    assert patch.status == "pending"
    assert patch.severity == "critical"
    assert patch.created_by == "WorkflowPatchAgent"
    assert patch.deployment_config is not None
    assert patch.rollback_config is not None
    assert "strategy" in patch.deployment_config
    assert "rollback_steps" in patch.rollback_config


def test_create_patch_invalid_analysis(patch_agent):
    """Test creating patch with invalid analysis ID."""
    fake_analysis_id = uuid4()
    
    patch_content = PatchContent(
        files_modified=["test.py"],
        changes={},
        dependencies=[],
        configuration={}
    )
    
    patch_data = WorkflowPatchCreate(
        patch_name="Test Patch",
        patch_version="1.0.0",
        patch_type="bug_fix",
        description="Test",
        target_workflow="test",
        issue_identified="Test issue",
        patch_content=patch_content,
        severity="low"
    )
    
    with pytest.raises(ValueError) as exc_info:
        patch_agent.create_patch(fake_analysis_id, patch_data)
    
    assert "not found" in str(exc_info.value)


def test_test_patch_success(patch_agent):
    """Test successful patch testing."""
    # Create analysis and patch
    analysis = patch_agent.analyze_workflow("test-workflow", "security")
    
    patch_content = PatchContent(
        files_modified=["src/main.py"],
        changes={"fix": "Bug fix"},
        dependencies=[],
        configuration={}
    )
    
    patch_data = WorkflowPatchCreate(
        patch_name="Test Patch",
        patch_version="1.0.0",
        patch_type="bug_fix",
        description="Test patch",
        target_workflow="test-workflow",
        issue_identified="Test issue",
        patch_content=patch_content,
        severity="medium"
    )
    
    patch = patch_agent.create_patch(analysis.id, patch_data)
    
    # Test the patch
    test_results = patch_agent.test_patch(patch.id)
    
    assert test_results is not None
    assert "isolated_tests" in test_results
    assert "integration_tests" in test_results
    assert "safety_checks" in test_results
    assert "compatibility_checks" in test_results
    assert test_results["isolated_tests"]["passed"] is True
    assert test_results["integration_tests"]["passed"] is True
    assert test_results["safety_checks"]["passed"] is True
    assert test_results["compatibility_checks"]["passed"] is True
    
    # Verify patch status updated
    patch_agent.db.refresh(patch)
    assert patch.status == "tested"
    assert patch.tested_at is not None
    assert patch.test_results is not None


def test_test_patch_invalid_id(patch_agent):
    """Test testing a non-existent patch."""
    fake_patch_id = uuid4()
    
    with pytest.raises(ValueError) as exc_info:
        patch_agent.test_patch(fake_patch_id)
    
    assert "not found" in str(exc_info.value)


def test_deploy_patch_success(patch_agent):
    """Test successful patch deployment."""
    # Create, test, and deploy a patch
    analysis = patch_agent.analyze_workflow("test-workflow", "security")
    
    patch_content = PatchContent(
        files_modified=["src/main.py"],
        changes={"fix": "Security fix"},
        dependencies=[],
        configuration={}
    )
    
    patch_data = WorkflowPatchCreate(
        patch_name="Security Patch",
        patch_version="1.0.0",
        patch_type="security",
        description="Security fix",
        target_workflow="test-workflow",
        issue_identified="Security issue",
        patch_content=patch_content,
        severity="high"
    )
    
    patch = patch_agent.create_patch(analysis.id, patch_data)
    
    # Test the patch first
    patch_agent.test_patch(patch.id)
    
    # Deploy the patch
    deployment_report = patch_agent.deploy_patch(patch.id, "test-user")
    
    assert deployment_report is not None
    assert deployment_report.patch_id == patch.id
    assert deployment_report.deployment_status == "success"
    assert deployment_report.rollback_available is True
    assert len(deployment_report.issues_fixed) > 0
    
    # Verify patch status
    patch_agent.db.refresh(patch)
    assert patch.status == "deployed"
    assert patch.deployed_at is not None
    assert patch.approved_by == "test-user"
    assert patch.impact_report is not None


def test_deploy_patch_not_tested(patch_agent):
    """Test deploying a patch that hasn't been tested."""
    analysis = patch_agent.analyze_workflow("test-workflow", "security")
    
    patch_content = PatchContent(
        files_modified=["src/main.py"],
        changes={},
        dependencies=[],
        configuration={}
    )
    
    patch_data = WorkflowPatchCreate(
        patch_name="Untested Patch",
        patch_version="1.0.0",
        patch_type="bug_fix",
        description="Test",
        target_workflow="test-workflow",
        issue_identified="Test",
        patch_content=patch_content,
        severity="low"
    )
    
    patch = patch_agent.create_patch(analysis.id, patch_data)
    
    # Try to deploy without testing
    with pytest.raises(ValueError) as exc_info:
        patch_agent.deploy_patch(patch.id)
    
    assert "must be tested" in str(exc_info.value)


def test_get_workflow_health(patch_agent):
    """Test getting workflow health report."""
    workflow_name = "test-workflow"
    
    # Create some analyses and patches
    analysis1 = patch_agent.analyze_workflow(workflow_name, "security")
    analysis2 = patch_agent.analyze_workflow(workflow_name, "performance")
    
    # Get health report
    health_report = patch_agent.get_workflow_health(workflow_name)
    
    assert health_report is not None
    assert health_report.workflow_name == workflow_name
    assert health_report.health_score >= 0
    assert health_report.health_score <= 100
    assert health_report.issues_identified >= 0
    assert health_report.patches_pending >= 0
    assert health_report.patches_deployed >= 0
    assert health_report.last_analysis is not None


def test_rollback_patch(patch_agent):
    """Test rolling back a deployed patch."""
    # Create, test, and deploy a patch
    analysis = patch_agent.analyze_workflow("test-workflow", "security")
    
    patch_content = PatchContent(
        files_modified=["src/main.py"],
        changes={"fix": "Fix"},
        dependencies=[],
        configuration={}
    )
    
    patch_data = WorkflowPatchCreate(
        patch_name="Rollback Test Patch",
        patch_version="1.0.0",
        patch_type="bug_fix",
        description="Test rollback",
        target_workflow="test-workflow",
        issue_identified="Test",
        patch_content=patch_content,
        severity="medium"
    )
    
    patch = patch_agent.create_patch(analysis.id, patch_data)
    patch_agent.test_patch(patch.id)
    patch_agent.deploy_patch(patch.id)
    
    # Rollback the patch
    patch_agent._rollback_patch(patch)
    
    # Verify rollback
    patch_agent.db.refresh(patch)
    assert patch.status == "rolled_back"
    assert patch.rolled_back_at is not None


def test_deployment_config_defaults(patch_agent):
    """Test default deployment configuration."""
    config = patch_agent._create_default_deployment_config()
    
    assert config is not None
    assert "strategy" in config
    assert "stages" in config
    assert "health_checks" in config
    assert "auto_rollback" in config
    assert config["strategy"] == "progressive"
    assert len(config["stages"]) > 0
    assert config["health_checks"]["enabled"] is True
    assert config["auto_rollback"]["enabled"] is True


def test_rollback_config_creation(patch_agent):
    """Test rollback configuration creation."""
    patch_content = {
        "files_modified": ["test.py"],
        "changes": {}
    }
    
    config = patch_agent._create_rollback_config(patch_content)
    
    assert config is not None
    assert "backup_created" in config
    assert "rollback_steps" in config
    assert "rollback_duration_estimate_minutes" in config
    assert config["backup_created"] is True
    assert len(config["rollback_steps"]) > 0


def test_severity_calculation_critical(patch_agent):
    """Test severity calculation with critical issues."""
    findings = {
        "issues": [
            {"severity": "critical", "description": "Critical issue"}
        ],
        "inefficiencies": [],
        "opportunities": []
    }
    
    severity = patch_agent._calculate_severity(findings)
    assert severity == "critical"


def test_severity_calculation_high(patch_agent):
    """Test severity calculation with high issues."""
    findings = {
        "issues": [
            {"severity": "high", "description": "High issue"}
        ],
        "inefficiencies": [],
        "opportunities": []
    }
    
    severity = patch_agent._calculate_severity(findings)
    assert severity == "high"


def test_severity_calculation_medium(patch_agent):
    """Test severity calculation with medium issues."""
    findings = {
        "issues": [
            {"severity": "medium", "description": "Medium issue"}
        ],
        "inefficiencies": [],
        "opportunities": []
    }
    
    severity = patch_agent._calculate_severity(findings)
    assert severity == "medium"


def test_severity_calculation_low(patch_agent):
    """Test severity calculation with inefficiencies."""
    findings = {
        "issues": [],
        "inefficiencies": [
            {"description": "Inefficiency"}
        ],
        "opportunities": []
    }
    
    severity = patch_agent._calculate_severity(findings)
    assert severity == "low"


def test_severity_calculation_info(patch_agent):
    """Test severity calculation with no issues."""
    findings = {
        "issues": [],
        "inefficiencies": [],
        "opportunities": []
    }
    
    severity = patch_agent._calculate_severity(findings)
    assert severity == "info"


def test_health_score_with_issues(patch_agent):
    """Test health score calculation with issues."""
    workflow_name = "test-workflow"
    
    # Create analysis with issues
    analysis = patch_agent.analyze_workflow(workflow_name, "security")
    
    # Manually add some issues to findings
    analysis.findings = {
        "issues": [
            {"severity": "high", "description": "Issue 1"},
            {"severity": "medium", "description": "Issue 2"}
        ],
        "inefficiencies": [],
        "opportunities": []
    }
    patch_agent.db.commit()
    
    # Calculate health score
    analyses = [analysis]
    patches = []
    
    score = patch_agent._calculate_health_score(analyses, patches)
    
    # Score should be less than 100 due to issues
    assert score < 100
    assert score >= 0


def test_health_score_with_deployed_patches(patch_agent):
    """Test health score improvement with deployed patches."""
    workflow_name = "test-workflow"
    
    # Create and deploy a patch
    analysis = patch_agent.analyze_workflow(workflow_name, "security")
    
    patch_content = PatchContent(
        files_modified=["src/main.py"],
        changes={},
        dependencies=[],
        configuration={}
    )
    
    patch_data = WorkflowPatchCreate(
        patch_name="Deployed Patch",
        patch_version="1.0.0",
        patch_type="bug_fix",
        description="Test",
        target_workflow=workflow_name,
        issue_identified="Test",
        patch_content=patch_content,
        severity="low"
    )
    
    patch = patch_agent.create_patch(analysis.id, patch_data)
    patch_agent.test_patch(patch.id)
    patch_agent.deploy_patch(patch.id)
    
    # Get health with deployed patch
    health_report = patch_agent.get_workflow_health(workflow_name)
    
    assert health_report.patches_deployed >= 1
