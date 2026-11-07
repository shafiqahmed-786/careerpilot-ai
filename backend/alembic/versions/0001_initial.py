"""Initial CareerPilot schema."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("education", sa.String(length=500), nullable=False),
        sa.Column("experience_level", sa.String(length=32), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("projects", sa.Text(), nullable=False),
        sa.Column("target_career", sa.String(length=120), nullable=False),
        sa.Column("weekly_hours", sa.Integer(), nullable=False),
        sa.Column("timeline_weeks", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"], unique=True)

    op.create_table(
        "assessment_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("rq_job_id", sa.String(length=64), nullable=True),
        sa.Column("assessment_id", sa.String(length=36), nullable=True),
        sa.Column("roadmap_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_assessment_jobs_user_id", "assessment_jobs", ["user_id"])

    op.create_table(
        "assessments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("assessment_jobs.id"), nullable=False),
        sa.Column("target_career", sa.String(length=120), nullable=False),
        sa.Column("normalized_role", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("learn_first_reason", sa.Text(), nullable=False),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("rubric_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assessments_user_id", "assessments", ["user_id"])

    op.create_table(
        "competency_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("importance", sa.Integer(), nullable=False),
        sa.Column("target_level", sa.Integer(), nullable=False),
        sa.Column("self_reported_level", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False),
        sa.Column("why_it_matters", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
    )
    op.create_index("ix_competency_results_assessment_id", "competency_results", ["assessment_id"])
    op.create_index("ix_competency_results_user_id", "competency_results", ["user_id"])

    op.create_table(
        "learning_resources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("skill", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("relevance", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
    )
    op.create_index("ix_learning_resources_assessment_id", "learning_resources", ["assessment_id"])
    op.create_index("ix_learning_resources_user_id", "learning_resources", ["user_id"])

    op.create_table(
        "roadmaps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assessment_id", sa.String(length=36), sa.ForeignKey("assessments.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("timeline_weeks", sa.Integer(), nullable=False),
        sa.Column("weekly_hours", sa.Integer(), nullable=False),
        sa.Column("overview", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_roadmaps_user_id", "roadmaps", ["user_id"])

    op.create_table(
        "roadmap_tasks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("roadmap_id", sa.String(length=36), sa.ForeignKey("roadmaps.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("estimated_hours", sa.Integer(), nullable=False),
        sa.Column("expected_outcome", sa.Text(), nullable=False),
        sa.Column("completion_criteria", sa.Text(), nullable=False),
        sa.Column("resources", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("roadmap_id", "sort_order", name="uq_roadmap_task_order"),
    )
    op.create_index("ix_roadmap_tasks_roadmap_id", "roadmap_tasks", ["roadmap_id"])
    op.create_index("ix_roadmap_tasks_user_id", "roadmap_tasks", ["user_id"])


def downgrade() -> None:
    op.drop_table("roadmap_tasks")
    op.drop_table("roadmaps")
    op.drop_table("learning_resources")
    op.drop_table("competency_results")
    op.drop_table("assessments")
    op.drop_table("assessment_jobs")
    op.drop_table("profiles")
    op.drop_table("users")
