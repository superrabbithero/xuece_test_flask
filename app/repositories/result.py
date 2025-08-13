from dataclasses import dataclass
from typing import Any, Optional, Dict

@dataclass
class RepoResult:
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    @staticmethod
    def success(data: Optional[Dict[str, Any]] = None) -> "RepoResult":
        return RepoResult(ok=True, data=data or {})

    @staticmethod
    def fail(error: str) -> "RepoResult":
        return RepoResult(ok=False, error=error)