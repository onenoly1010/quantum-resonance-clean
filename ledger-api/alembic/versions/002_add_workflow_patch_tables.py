"""002_add_workflow_patch_tables

Revision ID: 002_workflow_patches
Revises: 001_initial_ledger_schema
Create Date: 2024-12-11 20:55:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, TIMESTAMP

# revision identifiers, used by Alembic.
revision = '002_workflow_patches'
down_revision = '001_initial_ledger_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create workflow patch and analysis tables."""
    
    # Create workflow_patches table
    op.create_table(
        'workflow_patches',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('patch_name', sa.String(255), nullable=False),
        sa.Column('patch_version', sa.String(50), nullable=False),
        sa.Column('patch_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('target_workflow', sa.String(255), nullable=False),
        sa.Column('issue_identified', sa.Text, nullable=False),
        sa.Column('patch_content', JSONB, nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('created_by', sa.String(255), server_default='WorkflowPatchAgent'),
        sa.Column('reviewed_by', sa.String(255)),
        sa.Column('approved_by', sa.String(255)),
        sa.Column('test_results', JSONB),
        sa.Column('deployment_config', JSONB),
        sa.Column('rollback_config', JSONB),
        sa.Column('impact_report', JSONB),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('tested_at', TIMESTAMP(timezone=True)),
        sa.Column('deployed_at', TIMESTAMP(timezone=True)),
        sa.Column('rolled_back_at', TIMESTAMP(timezone=True)),
        sa.CheckConstraint(
            "patch_type IN ('bug_fix', 'performance', 'security', 'feature', 'refactor')",
            name='check_patch_type'
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'testing', 'tested', 'approved', 'deployed', 'failed', 'rolled_back')",
            name='check_patch_status'
        ),
        sa.CheckConstraint(
            "severity IN ('critical', 'high', 'medium', 'low')",
            name='check_patch_severity'
        )
    )
    
    # Create indexes for workflow_patches
    op.create_index('idx_workflow_patches_status', 'workflow_patches', ['status'])
    op.create_index('idx_workflow_patches_target_workflow', 'workflow_patches', ['target_workflow'])
    op.create_index('idx_workflow_patches_created_at', 'workflow_patches', ['created_at'])
    
    # Create workflow_analysis table
    op.create_table(
        'workflow_analysis',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_name', sa.String(255), nullable=False),
        sa.Column('analysis_type', sa.String(50), nullable=False),
        sa.Column('findings', JSONB, nullable=False),
        sa.Column('metrics', JSONB),
        sa.Column('recommendations', JSONB),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='new'),
        sa.Column('analyzed_by', sa.String(255), server_default='WorkflowPatchAgent'),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('addressed_at', TIMESTAMP(timezone=True)),
        sa.CheckConstraint(
            "analysis_type IN ('security', 'performance', 'efficiency', 'compatibility', 'quality')",
            name='check_analysis_type'
        ),
        sa.CheckConstraint(
            "severity IN ('critical', 'high', 'medium', 'low', 'info')",
            name='check_analysis_severity'
        ),
        sa.CheckConstraint(
            "status IN ('new', 'in_progress', 'addressed', 'ignored')",
            name='check_analysis_status'
        )
    )
    
    # Create indexes for workflow_analysis
    op.create_index('idx_workflow_analysis_workflow_name', 'workflow_analysis', ['workflow_name'])
    op.create_index('idx_workflow_analysis_status', 'workflow_analysis', ['status'])
    op.create_index('idx_workflow_analysis_severity', 'workflow_analysis', ['severity'])


def downgrade() -> None:
    """Drop workflow patch and analysis tables."""
    
    # Drop indexes for workflow_analysis
    op.drop_index('idx_workflow_analysis_severity', 'workflow_analysis')
    op.drop_index('idx_workflow_analysis_status', 'workflow_analysis')
    op.drop_index('idx_workflow_analysis_workflow_name', 'workflow_analysis')
    
    # Drop workflow_analysis table
    op.drop_table('workflow_analysis')
    
    # Drop indexes for workflow_patches
    op.drop_index('idx_workflow_patches_created_at', 'workflow_patches')
    op.drop_index('idx_workflow_patches_target_workflow', 'workflow_patches')
    op.drop_index('idx_workflow_patches_status', 'workflow_patches')
    
    # Drop workflow_patches table
    op.drop_table('workflow_patches')
