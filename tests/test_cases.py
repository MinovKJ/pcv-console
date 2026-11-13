"""
Unit tests for cases and alert assignments schemas and validation.
"""
import pytest
from datetime import datetime, timezone
from app.db.models.case import CaseSeverity, CaseStatus
from app.cases.schemas import CaseCreate, CaseUpdate, CaseOut, AlertAssignRequest, AlertAssignOut


def test_case_create_defaults():
    c = CaseCreate(title="Suspicious Egress from svchost")
    assert c.title == "Suspicious Egress from svchost"
    assert c.severity == CaseSeverity.medium
    assert c.description is None
    assert c.assigned_to is None


def test_case_update_partial():
    u = CaseUpdate(severity=CaseSeverity.critical, status=CaseStatus.in_progress)
    data = u.model_dump(exclude_none=True)
    assert data == {
        "severity": CaseSeverity.critical,
        "status": CaseStatus.in_progress,
    }
    assert "title" not in data


def test_alert_assign_request():
    req = AlertAssignRequest(alert_mongo_id="mongo_alert_123")
    assert req.alert_mongo_id == "mongo_alert_123"
