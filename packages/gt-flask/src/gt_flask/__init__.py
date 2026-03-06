"""Flask integration for General Translation."""

from gt_i18n import t

from gt_flask._setup import initialize_gt

__all__ = ["initialize_gt", "t"]
