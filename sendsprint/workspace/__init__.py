"""Workspace package: multi-repo configuration and loader."""

from .loader import load_workspace, new_project_dir, resolve_repo_path

__all__ = ["load_workspace", "new_project_dir", "resolve_repo_path"]
