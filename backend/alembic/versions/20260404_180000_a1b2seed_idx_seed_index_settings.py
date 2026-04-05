"""seed_index_settings — defaults aligned with telemetry_live_view METRIC_BANDS.

``warning_threshold`` = soft zone width w = (max_normal - min_normal) * warn_margin_ratio.
``critical_threshold`` = 2*w (same rule as ratio > 2 for metric critical in code).

Revision ID: a1b2seed_idx
Revises: 7fb9b25cb2d4
Create Date: 2026-04-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2seed_idx"
down_revision: Union[str, None] = "7fb9b25cb2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO loco.index_settings
              (metric_name, min_normal, max_normal, warning_threshold, critical_threshold, weight, enabled)
            VALUES
              ('speed', 0, 140, 7, 14, 1, true),
              ('fuel_level', 10, 100, 7.2, 14.4, 1, true),
              ('brake_pressure', 4.5, 6.5, 0.2, 0.4, 1, true),
              ('engine_temp', 0, 95, 5.7, 11.4, 1, true),
              ('voltage', 22, 28, 0.3, 0.6, 1, true),
              ('traction_current', 0, 450, 31.5, 63, 1, true)
            ON CONFLICT (metric_name) DO NOTHING;
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM loco.index_settings
            WHERE metric_name IN (
              'speed',
              'fuel_level',
              'brake_pressure',
              'engine_temp',
              'voltage',
              'traction_current'
            );
            """
        )
    )
