"""Read-only access to evaluation evidence and versioned UI snapshots."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent
VERSIONS = ("v0", "v1", "v2", "v3")
METRICS = {"Pass": "case_accuracy", "Routing": "tool_routing_accuracy",
           "Arguments": "argument_accuracy", "Multi-turn": "multiturn_accuracy"}


@dataclass(frozen=True)
class RunRecord:
    path: Path
    data: dict[str, Any]

    @property
    def version(self) -> str:
        return str(self.data.get("version") or self.data.get("artifact_version", "")).split("+")[0]

    @property
    def cohort(self) -> tuple[str, ...]:
        dataset = self.data.get("dataset_id") or str(self.data.get("eval_cases", "unknown")).replace("\\", "/").split("/")[-1]
        return tuple(str(value) for value in (
            self.data.get("suite", "unknown"), self.data.get("provider", "unknown"),
            self.data.get("model", "unknown"), dataset,
        ))


def read_runs(root: Path = ROOT) -> tuple[list[RunRecord], list[str]]:
    runs, errors = [], []
    for path in sorted((root / "runs").rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict) or not isinstance(data.get("summary"), dict):
                raise ValueError("thiếu summary")
            record = RunRecord(path, data)
            if record.version in VERSIONS:
                runs.append(record)
        except (OSError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")
    return runs, errors


def latest_runs(runs: list[RunRecord], cohort: tuple[str, ...] | None) -> dict[str, RunRecord]:
    matching = [run for run in runs if run.cohort == cohort]
    # Stable tie-breaker; do not mix providers, models, suites or datasets.
    matching.sort(key=lambda run: (str(run.data.get("generated_at", "")), run.path.name))
    return {run.version: run for run in matching}


def comparison_rows(selected: dict[str, RunRecord]) -> list[dict[str, Any]]:
    rows = []
    for version in VERSIONS:
        run = selected.get(version)
        summary = run.data["summary"] if run else {}
        row: dict[str, Any] = {"Version": version}
        for label, key in METRICS.items():
            value = summary.get(key)
            valid = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and 0 <= value <= 1
            row[label] = f"{value:.2%}" if valid and summary.get("measured_cases") != 0 else "—"
        row["Đã đo / Tổng"] = f"{summary.get('measured_cases', '—')} / {summary.get('total_cases', '—')}" if run else "—"
        row["Lỗi provider"] = str(summary.get("provider_error_cases", "—"))
        row["Run JSON"] = run.path.name if run else "Chưa có run"
        rows.append(row)
    return rows


@dataclass(frozen=True)
class VersionSnapshot:
    version: str
    prompt_bytes: bytes
    tools_bytes: bytes
    prompt_source: str
    tools_source: str

    @property
    def prompt(self) -> str:
        return self.prompt_bytes.decode("utf-8-sig")

    @property
    def declarations(self) -> list[dict[str, Any]]:
        try:
            data = yaml.safe_load(self.tools_bytes.decode("utf-8-sig"))
        except yaml.YAMLError as exc:
            raise ValueError("Snapshot tools.yaml không đúng cú pháp YAML.") from exc
        if not isinstance(data, dict) or not isinstance(data.get("tools"), list):
            raise ValueError("Snapshot tools.yaml phải chứa danh sách tools.")
        names = [tool.get("name") for tool in data["tools"] if isinstance(tool, dict)]
        if len(names) != len(data["tools"]) or any(not isinstance(name, str) or not name for name in names) or len(set(names)) != len(names):
            raise ValueError("Snapshot có tên tool thiếu hoặc trùng.")
        return data["tools"]

    @property
    def hashes(self) -> tuple[str, str]:
        return (hashlib.sha256(self.prompt_bytes).hexdigest(), hashlib.sha256(self.tools_bytes).hexdigest())

    @property
    def evidence(self) -> dict[str, str]:
        prompt_hash, tools_hash = self.hashes
        return {"version": self.version, "artifact_version": f"{self.version}+p{prompt_hash[:12]}+t{tools_hash[:12]}",
                "prompt_hash": prompt_hash, "tools_hash": tools_hash}


def local_path(root: Path, value: str, suffixes: tuple[str, ...]) -> Path:
    # Run paths may be absolute paths from the original checkout. Rebase them.
    normalized = str(value).replace("\\", "/")
    if "starter_v0/" in normalized:
        normalized = normalized.split("starter_v0/", 1)[1]
    path = (root / normalized).resolve()
    if not path.is_relative_to(root.resolve()) or path.suffix.lower() not in suffixes:
        raise ValueError("Đường dẫn snapshot phải nằm trong starter_v0 và đúng loại file.")
    return path


def resolve_snapshot(version: str, root: Path = ROOT, run: RunRecord | None = None) -> VersionSnapshot:
    if version not in VERSIONS:
        raise ValueError("Chỉ hỗ trợ các phiên bản v0–v3.")
    manifest_path = root / "ui_versions.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig")) if manifest_path.exists() else {}
    if not isinstance(manifest, dict) or not isinstance(manifest.get("versions", {}), dict):
        raise ValueError("ui_versions.json phải chứa object versions.")
    config = manifest.get("versions", {}).get(version)
    if config is not None and not isinstance(config, dict):
        raise ValueError(f"Cấu hình snapshot {version} không hợp lệ.")
    if config is None:
        for parent in ("artifacts/versions", "artifacts/snapshots", "ui_snapshots"):
            folder = root / parent / version
            if (folder / "system_prompt.md").is_file() and (folder / "tools.yaml").is_file():
                config = {"prompt": str(folder / "system_prompt.md"), "tools": str(folder / "tools.yaml")}
                break
    if config is None and run and run.data.get("prompt_hash") and run.data.get("tools_hash"):
        config = {"prompt": run.data.get("system_prompt", ""), "tools": run.data.get("tools", "")}
    if config is None:
        raise ValueError(f"Chưa có snapshot {version}. Bổ sung đường dẫn prompt và tools trong ui_versions.json.")
    prompt_path = local_path(root, config.get("prompt", ""), (".md", ".txt"))
    tools_path = local_path(root, config.get("tools", ""), (".yaml", ".yml"))
    snapshot = VersionSnapshot(version, prompt_path.read_bytes(), tools_path.read_bytes(), str(prompt_path), str(tools_path))
    if not snapshot.prompt.strip():
        raise ValueError(f"Prompt snapshot {version} đang trống.")
    snapshot.declarations  # Validate before allowing a chat session.
    for evidence in (config, run.data if run else {}):
        for key, actual in zip(("prompt_hash", "tools_hash"), snapshot.hashes):
            if evidence.get(key) and evidence[key] != actual:
                raise ValueError(f"Snapshot {version} không khớp {key} trong cấu hình/run JSON. Cần đúng snapshot đã đánh giá.")
    return snapshot


TOOL_DESCRIPTIONS = {
    "clarify": "Hỏi lại thông tin còn thiếu hoặc yêu cầu xác nhận.",
    "timeline": "Đọc bài đăng gần đây của một tài khoản Twitter/X.",
    "social_search": "Tìm bài đăng Twitter/X theo từ khóa và mức phổ biến/thời gian.",
    "lookup": "Tìm thông tin, tin tức trên web theo khoảng thời gian.",
    "fetch": "Đọc nội dung một URL cụ thể.",
    "format": "Trình bày dữ liệu đã có thành bản tin Markdown.",
    "send": "Gửi bản nháp lên Telegram sau khi bấm xác nhận.",
    "policy": "Tìm trong tài liệu chính sách nội bộ của bài lab.",
    "papers": "Tìm bài báo khoa học trên arXiv.",
    "paper_text": "Đọc văn bản từ PDF arXiv theo giới hạn trang/ký tự.",
    "compare_sources": "So sánh URL đã thu thập, phát hiện trùng và đếm nguồn theo hostname; không chấm độ tin cậy.",
}


def tool_inventory(declarations: list[dict[str, Any]], registry: dict, root: Path = ROOT) -> list[dict[str, str]]:
    declared = {tool["name"]: tool for tool in declarations}
    rows = []
    for name in sorted(set(TOOL_DESCRIPTIONS) | set(declared) | set(registry)):
        status = "Sẵn sàng" if name in declared and name in registry else (
            "Chưa có implementation ở nhánh này" if name not in registry else "Không khai báo trong snapshot này")
        rows.append({"Tool": name, "Mô tả": TOOL_DESCRIPTIONS.get(name, declared.get(name, {}).get("description", "Tool của nhóm")),
                     "Nhóm": "Bonus" if name in {"send", "policy", "papers", "paper_text", "compare_sources"} else "Core / nhóm",
                     "Trạng thái": status})
    return rows
