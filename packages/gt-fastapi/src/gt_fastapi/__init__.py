"""FastAPI integration for General Translation."""

from gt_fastapi._setup import initialize_gt
from gt_i18n import declare_static, declare_var, decode_vars, t

__all__ = ["initialize_gt", "t", "declare_var", "declare_static", "decode_vars"]
