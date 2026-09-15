from __future__ import annotations

from .audio_script import AudioQualityFinding, AudioScriptGateError, AudioScriptView

_SEPARATOR = "␟"


def attention_finding_key(finding: AudioQualityFinding) -> str:
    """Stable, human-auditable identity for one exact ATTENTION finding."""
    return _SEPARATOR.join((finding.code, finding.location, finding.detail))


def accepted_attention_values(
    script: AudioScriptView,
    accepted_finding_keys: list[str],
) -> list[str]:
    """Require an explicit disposition for every exact ATTENTION finding.

    The returned list deliberately includes both the exact finding keys and their legacy codes.
    AudioScriptService can therefore keep its existing code-level compatibility while the public
    author workflows fail closed unless every current finding/location was individually accepted.
    The exact keys are retained in the approval JSON for auditability.

    An already human-approved, current script is allowed through unchanged so a transient export
    failure can be retried idempotently without asking the human to approve the same findings again.
    """
    if script.status == "APPROVED" and script.ready_for_export:
        return []

    findings = [
        finding
        for check in script.quality_checks
        for finding in check.findings
        if finding.severity == "ATTENTION"
    ]
    required = {attention_finding_key(finding): finding for finding in findings}
    accepted = set(accepted_finding_keys)
    missing = [required[key] for key in sorted(required.keys() - accepted)]
    if missing:
        sample = "; ".join(f"{item.code} @ {item.location}: {item.detail}" for item in missing[:5])
        raise AudioScriptGateError(
            "human must explicitly disposition every ATTENTION finding by exact location"
            + (f": {sample}" if sample else "")
        )
    legacy_codes = {finding.code for finding in findings}
    return sorted(accepted | legacy_codes)
