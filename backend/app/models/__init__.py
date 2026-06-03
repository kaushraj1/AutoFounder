"""ORM models. Importing this package registers all models on ``Base.metadata``
so Alembic autogeneration and ``create_all`` see them.
"""

from app.models.artifact import Artifact
from app.models.gate import Gate
from app.models.run import Run

__all__ = ["Artifact", "Gate", "Run"]
