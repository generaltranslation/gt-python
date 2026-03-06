"""Flask integration for General Translation."""

from gt_flask._setup import initialize_gt
from gt_i18n import t

__all__ = ["initialize_gt", "t"]
