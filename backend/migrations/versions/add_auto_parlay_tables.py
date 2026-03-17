"""Add auto-parlay tables and extend prop coverage

Revision ID: auto_parlay_001
Revises: 84db2cfe5eb8
Create Date: 2026-02-01 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'auto_parlay_001'
down_revision: Union[str, None] = '84db2cfe5eb8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===== 1. EXTEND PLAYER_MARGINALS TABLE =====
    # Add new columns for market metadata
    op.add_column('player_marginals', sa.Column('prop_category', sa.String(length=50), nullable=True))
    op.add_column('player_marginals', sa.Column('historical_hit_rate', sa.Float(), nullable=True))
    op.add_column('player_marginals', sa.Column('sharp_percentage', sa.Float(), nullable=True))
    op.add_column('player_marginals', sa.Column('public_percentage', sa.Float(), nullable=True))
    op.add_column('player_marginals', sa.Column('line_opened', sa.Float(), nullable=True))
    op.add_column('player_marginals', sa.Column('line_current', sa.Float(), nullable=True))
    op.add_column('player_marginals', sa.Column('steam_move', sa.Boolean(), default=False))

    # ===== 2. ALT_LINES TABLE =====
    # Stores alternative lines for props
    op.create_table(
        'alt_lines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prop_id', sa.UUID(), nullable=False),
        sa.Column('line_value', sa.Float(), nullable=False),
        sa.Column('over_odds', sa.Integer(), nullable=True),
        sa.Column('under_odds', sa.Integer(), nullable=True),
        sa.Column('line_type', sa.String(length=50), nullable=False),  # 'main', 'alt_high', 'alt_low'
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['prop_id'], ['player_marginals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alt_lines_prop_id'), 'alt_lines', ['prop_id'], unique=False)
    op.create_index(op.f('ix_alt_lines_line_type'), 'alt_lines', ['line_type'], unique=False)

    # ===== 3. GAME_PROPS TABLE =====
    # Stores game-level props (spread, total, moneyline)
    op.create_table(
        'game_props',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('game_id', sa.UUID(), nullable=False),
        sa.Column('prop_type', sa.String(length=50), nullable=False),  # PropType enum value
        sa.Column('team_id', sa.UUID(), nullable=True),  # For team-specific props
        sa.Column('line', sa.Float(), nullable=True),  # Line value (null for moneyline)
        sa.Column('over_odds', sa.Integer(), nullable=True),
        sa.Column('under_odds', sa.Integer(), nullable=True),
        sa.Column('favorite_odds', sa.Integer(), nullable=True),  # For spreads/ML
        sa.Column('underdog_odds', sa.Integer(), nullable=True),
        sa.Column('sharp_percentage', sa.Float(), nullable=True),
        sa.Column('public_percentage', sa.Float(), nullable=True),
        sa.Column('line_opened', sa.Float(), nullable=True),
        sa.Column('steam_move', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_props_game_id'), 'game_props', ['game_id'], unique=False)
    op.create_index(op.f('ix_game_props_prop_type'), 'game_props', ['prop_type'], unique=False)
    op.create_index(op.f('ix_game_props_team_id'), 'game_props', ['team_id'], unique=False)

    # ===== 4. PROP_METADATA TABLE =====
    # Stores historical and matchup data for props
    op.create_table(
        'prop_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prop_id', sa.UUID(), nullable=False),
        sa.Column('last_5_games', postgresql.JSONB(), nullable=True),  # Array of recent performance
        sa.Column('season_average', sa.Float(), nullable=True),
        sa.Column('career_average', sa.Float(), nullable=True),
        sa.Column('vs_opponent_average', sa.Float(), nullable=True),
        sa.Column('opponent_rank_vs_position', sa.Integer(), nullable=True),  # Defensive ranking
        sa.Column('opponent_yards_allowed', sa.Float(), nullable=True),
        sa.Column('pace_factor', sa.Float(), nullable=True),
        sa.Column('target_share', sa.Float(), nullable=True),
        sa.Column('snap_percentage', sa.Float(), nullable=True),
        sa.Column('redzone_usage', sa.Float(), nullable=True),
        sa.Column('projected_value', sa.Float(), nullable=True),
        sa.Column('projection_confidence', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['prop_id'], ['player_marginals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prop_metadata_prop_id'), 'prop_metadata', ['prop_id'], unique=True)

    # ===== 5. AUTO_PARLAY_REQUESTS TABLE =====
    # Stores user auto-parlay requests
    op.create_table(
        'auto_parlay_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('raw_input', sa.Text(), nullable=False),
        sa.Column('parsed_intent', postgresql.JSONB(), nullable=False),
        sa.Column('primary_parlay_id', sa.UUID(), nullable=True),
        sa.Column('alternatives', postgresql.JSONB(), nullable=True),  # Array of parlay IDs
        sa.Column('build_time_ms', sa.Integer(), nullable=True),
        sa.Column('candidates_considered', sa.Integer(), nullable=True),
        sa.Column('combinations_scored', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),  # 'success', 'failed', 'insufficient_data'
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auto_parlay_requests_user_id'), 'auto_parlay_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_auto_parlay_requests_status'), 'auto_parlay_requests', ['status'], unique=False)
    op.create_index(op.f('ix_auto_parlay_requests_created_at'), 'auto_parlay_requests', ['created_at'], unique=False)

    # ===== 6. BUILT_PARLAYS TABLE =====
    # Stores auto-built parlays with scores
    op.create_table(
        'built_parlays',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('request_id', sa.UUID(), nullable=True),
        sa.Column('legs', postgresql.JSONB(), nullable=False),  # Array of leg objects
        sa.Column('num_legs', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('expected_value', sa.Float(), nullable=True),
        sa.Column('win_probability', sa.Float(), nullable=True),
        sa.Column('variance', sa.Float(), nullable=True),
        sa.Column('correlation', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('copula_result', postgresql.JSONB(), nullable=True),
        sa.Column('risk_profile', sa.String(length=50), nullable=True),
        sa.Column('intent_alignment', sa.Float(), nullable=True),
        sa.Column('user_viewed', sa.Boolean(), default=False),
        sa.Column('user_accepted', sa.Boolean(), default=False),
        sa.Column('user_modified', sa.Boolean(), default=False),
        sa.Column('placed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['request_id'], ['auto_parlay_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_built_parlays_request_id'), 'built_parlays', ['request_id'], unique=False)
    op.create_index(op.f('ix_built_parlays_risk_profile'), 'built_parlays', ['risk_profile'], unique=False)
    op.create_index(op.f('ix_built_parlays_created_at'), 'built_parlays', ['created_at'], unique=False)

    # ===== 7. PARLAY_LEG_EXPLANATIONS TABLE =====
    # Stores explanations for each leg in auto-built parlays
    op.create_table(
        'parlay_leg_explanations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('parlay_id', sa.UUID(), nullable=False),
        sa.Column('leg_index', sa.Integer(), nullable=False),
        sa.Column('primary_reason', sa.Text(), nullable=True),
        sa.Column('supporting_factors', postgresql.JSONB(), nullable=True),  # Array of strings
        sa.Column('historical_context', sa.Text(), nullable=True),
        sa.Column('matchup_analysis', sa.Text(), nullable=True),
        sa.Column('sharp_action', sa.Text(), nullable=True),
        sa.Column('historical_advantage', sa.Float(), nullable=True),
        sa.Column('matchup_rating', sa.Float(), nullable=True),
        sa.Column('sharp_percentage', sa.Float(), nullable=True),
        sa.Column('weather_impact', sa.Float(), nullable=True),
        sa.Column('injury_impact', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['parlay_id'], ['built_parlays.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_parlay_leg_explanations_parlay_id'), 'parlay_leg_explanations', ['parlay_id'], unique=False)


def downgrade() -> None:
    # Drop all new tables in reverse order
    op.drop_index(op.f('ix_parlay_leg_explanations_parlay_id'), table_name='parlay_leg_explanations')
    op.drop_table('parlay_leg_explanations')

    op.drop_index(op.f('ix_built_parlays_created_at'), table_name='built_parlays')
    op.drop_index(op.f('ix_built_parlays_risk_profile'), table_name='built_parlays')
    op.drop_index(op.f('ix_built_parlays_request_id'), table_name='built_parlays')
    op.drop_table('built_parlays')

    op.drop_index(op.f('ix_auto_parlay_requests_created_at'), table_name='auto_parlay_requests')
    op.drop_index(op.f('ix_auto_parlay_requests_status'), table_name='auto_parlay_requests')
    op.drop_index(op.f('ix_auto_parlay_requests_user_id'), table_name='auto_parlay_requests')
    op.drop_table('auto_parlay_requests')

    op.drop_index(op.f('ix_prop_metadata_prop_id'), table_name='prop_metadata')
    op.drop_table('prop_metadata')

    op.drop_index(op.f('ix_game_props_team_id'), table_name='game_props')
    op.drop_index(op.f('ix_game_props_prop_type'), table_name='game_props')
    op.drop_index(op.f('ix_game_props_game_id'), table_name='game_props')
    op.drop_table('game_props')

    op.drop_index(op.f('ix_alt_lines_line_type'), table_name='alt_lines')
    op.drop_index(op.f('ix_alt_lines_prop_id'), table_name='alt_lines')
    op.drop_table('alt_lines')

    # Remove columns from player_marginals
    op.drop_column('player_marginals', 'steam_move')
    op.drop_column('player_marginals', 'line_current')
    op.drop_column('player_marginals', 'line_opened')
    op.drop_column('player_marginals', 'public_percentage')
    op.drop_column('player_marginals', 'sharp_percentage')
    op.drop_column('player_marginals', 'historical_hit_rate')
    op.drop_column('player_marginals', 'prop_category')
