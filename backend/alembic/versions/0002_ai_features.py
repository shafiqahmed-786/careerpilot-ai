"""Mentor chat, resume analysis, AI roadmap metadata and job kinds."""

from alembic import op
import sqlalchemy as sa

revision = "0002_ai_features"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assessment_jobs", sa.Column("kind", sa.String(length=24), nullable=False, server_default="assessment"))
    op.add_column("assessment_jobs", sa.Column("params", sa.JSON(), nullable=True))

    op.add_column("roadmaps", sa.Column("source", sa.String(length=16), nullable=False, server_default="fallback"))
    op.add_column("roadmaps", sa.Column("milestones", sa.JSON(), nullable=True))
    op.add_column("roadmaps", sa.Column("adapted_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("roadmaps", sa.Column("adaptation_note", sa.Text(), nullable=True))

    op.create_table(
        "mentor_conversations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mentor_conversations_user_id", "mentor_conversations", ["user_id"])

    op.create_table(
        "mentor_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("conversation_id", sa.String(length=36), sa.ForeignKey("mentor_conversations.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=True),
        sa.Column("notice", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mentor_messages_conversation_id", "mentor_messages", ["conversation_id"])
    op.create_index("ix_mentor_messages_user_id", "mentor_messages", ["user_id"])

    op.create_table(
        "resume_analyses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=True),
        sa.Column("notice", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("analysis", sa.JSON(), nullable=True),
        sa.Column("comparison", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_resume_analyses_user_id", "resume_analyses", ["user_id"])


def downgrade() -> None:
    op.drop_table("resume_analyses")
    op.drop_table("mentor_messages")
    op.drop_table("mentor_conversations")
    for column in ("adaptation_note", "adapted_count", "milestones", "source"):
        op.drop_column("roadmaps", column)
    op.drop_column("assessment_jobs", "params")
    op.drop_column("assessment_jobs", "kind")
