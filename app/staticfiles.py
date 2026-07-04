"""StaticFiles helpers for mounted FastAPI deployments.

Starlette 0.35+ can return 404 for mounted ``StaticFiles`` when the parent
FastAPI app has a non-empty ``root_path`` and nginx strips the public prefix
before proxying. In that shape the mounted child scope has:

- ``scope['path']`` like ``/static/styles.css``
- ``scope['root_path']`` like ``/projects/practical-ai-journey/static``
- ``scope['app_root_path']`` like ``/projects/practical-ai-journey``

Starlette's default path extraction can fail to strip the mounted ``/static``
prefix from ``scope['path']``, causing it to look for
``static/static/styles.css`` and return 404 even though ``static/styles.css``
exists.
"""

from __future__ import annotations

import os
import re

from fastapi.staticfiles import StaticFiles
from starlette.types import Scope


class RootPathAwareStaticFiles(StaticFiles):
    """Serve mounted static files correctly when the parent app uses root_path."""

    def get_path(self, scope: Scope) -> str:
        root_path = str(scope.get("root_path") or "")
        app_root_path = str(scope.get("app_root_path") or "")
        path = str(scope.get("path") or "")

        if root_path and app_root_path and root_path.startswith(app_root_path):
            mount_prefix = re.sub("^" + re.escape(app_root_path), "", root_path)
            route_path = re.sub("^" + re.escape(mount_prefix), "", path)
            route_path = os.path.normpath(os.path.join(*route_path.split("/")))
            return "" if route_path == "." else route_path

        return super().get_path(scope)
