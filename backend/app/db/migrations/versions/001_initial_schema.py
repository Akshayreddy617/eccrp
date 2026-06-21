"""Initial schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("""
        CREATE TYPE electiontype AS ENUM (
            'lok_sabha', 'rajya_sabha', 'legislative_assembly', 'legislative_council',
            'gram_panchayat', 'mandal_parishad', 'zilla_parishad', 'municipality', 'municipal_corporation'
        );
        CREATE TYPE eligibilitystatus AS ENUM ('eligible', 'potentially_eligible', 'high_risk', 'disqualified');
        CREATE TYPE risklevel AS ENUM ('low', 'medium', 'high', 'critical');
        CREATE TYPE mccstatus AS ENUM ('compliant', 'potential_violation', 'violation');
        CREATE TYPE userrole AS ENUM ('super_admin', 'admin', 'consultant', 'candidate', 'lawyer', 'journalist', 'researcher', 'public');
        CREATE TYPE documenttype AS ENUM ('form_26', 'assets_declaration', 'liabilities_declaration', 'criminal_disclosure', 'electoral_roll_proof', 'identity_proof', 'other');
        CREATE TYPE knowledgearticletype AS ENUM ('constitution_article', 'rp_act_1950', 'rp_act_1951', 'conduct_of_election_rules', 'eci_circular', 'sec_circular', 'pci_guideline', 'rni_rule', 'mcc_guideline');
        CREATE TYPE expenditurecategory AS ENUM ('vehicle', 'advertising_print', 'advertising_digital', 'advertising_outdoor', 'meetings_rallies', 'travel', 'volunteers', 'campaign_materials', 'sound_equipment', 'other');
    """)

    # States
    op.create_table('states',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(10), nullable=False),
        sa.Column('is_union_territory', sa.Boolean(), default=False),
        sa.Column('has_legislative_council', sa.Boolean(), default=False),
        sa.Column('sec_name', sa.String(200)),
        sa.Column('ec_contact', postgresql.JSONB()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code'),
    )

    # Districts
    op.create_table('districts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('state_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(20)),
        sa.Column('headquarters', sa.String(100)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['state_id'], ['states.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('state_id', 'name', name='uq_district_state_name'),
    )
    op.create_index('ix_districts_state_id', 'districts', ['state_id'])

    # Constituencies
    op.create_table('constituencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('state_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('district_id', postgresql.UUID(as_uuid=True)),
        sa.Column('election_type', sa.Enum('lok_sabha', 'rajya_sabha', 'legislative_assembly', 'legislative_council', 'gram_panchayat', 'mandal_parishad', 'zilla_parishad', 'municipality', 'municipal_corporation', name='electiontype'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('number', sa.Integer()),
        sa.Column('reservation_category', sa.String(50)),
        sa.Column('total_voters', sa.BigInteger()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['state_id'], ['states.id']),
        sa.ForeignKeyConstraint(['district_id'], ['districts.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_constituency_state_type', 'constituencies', ['state_id', 'election_type'])

    # Users
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('role', sa.Enum('super_admin', 'admin', 'consultant', 'candidate', 'lawyer', 'journalist', 'researcher', 'public', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('email_verified_at', sa.DateTime(timezone=True)),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('locked_until', sa.DateTime(timezone=True)),
        sa.Column('profile_data', postgresql.JSONB(), default={}),
        sa.Column('preferences', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Refresh tokens
    op.create_table('refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), default=False),
        sa.Column('device_info', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])

    # Add indexes for performance
    op.execute("CREATE INDEX ix_users_role ON users (role);")
    op.execute("CREATE INDEX ix_users_is_active ON users (is_active);")


def downgrade() -> None:
    op.drop_table('refresh_tokens')
    op.drop_table('users')
    op.drop_table('constituencies')
    op.drop_table('districts')
    op.drop_table('states')

    op.execute("""
        DROP TYPE IF EXISTS electiontype;
        DROP TYPE IF EXISTS eligibilitystatus;
        DROP TYPE IF EXISTS risklevel;
        DROP TYPE IF EXISTS mccstatus;
        DROP TYPE IF EXISTS userrole;
        DROP TYPE IF EXISTS documenttype;
        DROP TYPE IF EXISTS knowledgearticletype;
        DROP TYPE IF EXISTS expenditurecategory;
    """)
