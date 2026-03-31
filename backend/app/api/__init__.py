"""
API路由模块
"""

from flask import Blueprint

graph_bp = Blueprint('graph', __name__)
simulation_bp = Blueprint('simulation', __name__)
report_bp = Blueprint('report', __name__)

# Import route modules — guarded so that a missing optional dependency
# (e.g. camel-ai for simulation) does not prevent the whole app from starting.
from . import graph  # noqa: E402, F401

try:
    from . import simulation  # noqa: E402, F401
except Exception:
    pass

try:
    from . import report  # noqa: E402, F401
except Exception:
    pass
