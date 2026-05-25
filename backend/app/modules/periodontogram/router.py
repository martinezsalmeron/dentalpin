"""Periodontogram FastAPI router.

PR-1 mounts an empty router so the module installs cleanly. Endpoints are
introduced in PR-2 (snapshot lifecycle) and PR-3 (indices + odontogram
pre-fill).
"""

from fastapi import APIRouter

router = APIRouter()
