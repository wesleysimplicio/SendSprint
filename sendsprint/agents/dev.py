"""DevAgent: dispatches development work by tech stack."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from ..models.reports import StepReport
from ..tech import TechFingerprint

logger = logging.getLogger(__name__)

INSTALL_COMMANDS: dict[str, list[str]] = {
    "npm": ["npm", "install"],
    "yarn": ["yarn", "install"],
    "pnpm": ["pnpm", "install"],
    "bun": ["bun", "install"],
    "pip": ["pip", "install", "-r", "requirements.txt"],
    "poetry": ["poetry", "install"],
    "uv": ["uv", "sync"],
    "nuget": ["dotnet", "restore"],
    "maven": ["mvn", "install", "-DskipTests"],
    "gradle": ["./gradlew", "assemble"],
    "cargo": ["cargo", "build"],
    "go": ["go", "build", "./..."],
    "pub": ["flutter", "pub", "get"],
    "bundler": ["bundle", "install"],
    "composer": ["composer", "install"],
}

BUILD_COMMANDS: dict[str, list[str]] = {
    "angular": ["npx", "ng", "build"],
    "react": ["npm", "run", "build"],
    "nextjs": ["npm", "run", "build"],
    "vue": ["npm", "run", "build"],
    "nestjs": ["npm", "run", "build"],
    "dotnet": ["dotnet", "build"],
    "spring": ["mvn", "package", "-DskipTests"],
    "java": ["mvn", "package", "-DskipTests"],
    "go": ["go", "build", "./..."],
    "rust": ["cargo", "build"],
    "flutter": ["flutter", "build"],
}


class DevAgent:
    """Runs install + build for a repo based on its tech fingerprint."""

    def __init__(self, repo_path: str | Path, fingerprint: TechFingerprint) -> None:
        self.repo = Path(repo_path).resolve()
        self.fp = fingerprint

    def install(self) -> StepReport:
        report = StepReport(step=3, name="install-deps", repo=str(self.repo))
        report.status = "running"
        pm = self.fp.package_managers[0] if self.fp.package_managers else None
        if not pm:
            report.status = "skipped"
            report.message = "no package manager detected"
            return report
        cmd = INSTALL_COMMANDS.get(pm)
        if not cmd:
            report.status = "skipped"
            report.message = f"no install command mapped for {pm}"
            return report
        return self._exec(cmd, report)

    def build(self, *, custom_command: str | None = None) -> StepReport:
        report = StepReport(step=3, name="build", repo=str(self.repo))
        report.status = "running"
        if custom_command:
            cmd = custom_command.split()
        else:
            tech = self.fp.primary_tech
            cmd_list = BUILD_COMMANDS.get(tech) if tech else None
            if not cmd_list:
                report.status = "skipped"
                report.message = f"no build command for tech={tech}"
                return report
            cmd = list(cmd_list)
        return self._exec(cmd, report)

    def _exec(self, cmd: list[str], report: StepReport) -> StepReport:
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.repo),
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                report.status = "ok"
                report.message = f"{' '.join(cmd)} succeeded"
            else:
                report.status = "failed"
                report.message = result.stderr[:2000] or result.stdout[:2000]
        except FileNotFoundError:
            report.status = "failed"
            report.message = f"command not found: {cmd[0]}"
        except subprocess.TimeoutExpired:
            report.status = "failed"
            report.message = f"timeout after 300s: {' '.join(cmd)}"
        return report
