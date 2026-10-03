"""Evaluate weighted signing policies, approval deduplication, signer removal and threshold reachability."""

from .common import (
    number,
    integer,
    identity,
    records,
    chronology,
    allocate,
    result,
    validate_document,
)
from decimal import Decimal


def _analyze(d):
    signers = {
        identity(r["id"]): integer(r["weight"], 1) for r in records(d["signers"], "id")
    }
    threshold = integer(d["threshold"], 1)
    if threshold > sum(signers.values()):
        raise ValueError("unreachable threshold")
    proposals = []
    for p in records(d["proposals"], "id"):
        approvals = p["approvals"]
        if not isinstance(approvals, list) or any(a not in signers for a in approvals):
            raise ValueError("unknown signer")
        unique = set(approvals)
        weight = sum(signers[a] for a in unique)
        proposals.append(
            {
                "id": p["id"],
                "weight": weight,
                "authorized": weight >= threshold,
                "duplicates": len(approvals) - len(unique),
            }
        )
    removal = [
        {
            "signer": s,
            "remaining_weight": sum(signers.values()) - w,
            "reachable": sum(signers.values()) - w >= threshold,
        }
        for s, w in sorted(signers.items())
    ]
    return {
        "proposals": proposals,
        "removal_analysis": removal,
        "total_weight": sum(signers.values()),
    }


def analyze(document):
    validate_document(document)
    try:
        return result(_analyze(document))
    except (KeyError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("invalid domain input: " + str(error)) from error
