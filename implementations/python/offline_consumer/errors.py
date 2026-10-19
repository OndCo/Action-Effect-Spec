"""Input-independent result construction and expected processing rejections."""

from typing import Any, Dict


def outcome(status: str, reason: str, **details: Any) -> Dict[str, Any]:
    return {"status": status, "reason": reason, "authority": "not_evaluated", **details}


class Rejection(Exception):
    def __init__(self, status: str, reason: str) -> None:
        super().__init__(status + "/" + reason)
        self.status = status
        self.reason = reason

    def result(self) -> Dict[str, Any]:
        return outcome(self.status, self.reason)
