"""Tests for app.services.email_service module."""
from app.services.email_service import (
    build_deadline_reminder_email,
    build_grant_alert_email,
)


class TestBuildGrantAlertEmail:
    def test_basic_alert_email(self):
        grants = [
            {"title": "Grant A", "agency": "Agency 1", "deadline": "2026-12-31", "award_amount": "$50,000"},
            {"title": "Grant B", "agency": "Agency 2", "deadline": "N/A", "award_amount": "$100,000"},
        ]
        html = build_grant_alert_email(grants, ["machine learning", "AI"])
        assert "Grant A" in html
        assert "Grant B" in html
        assert "Agency 1" in html
        assert "machine learning" in html
        assert "AI" in html
        assert "<html>" in html

    def test_empty_grants(self):
        html = build_grant_alert_email([], ["test"])
        assert "test" in html
        assert "<html>" in html

    def test_single_keyword(self):
        grants = [{"title": "G1", "agency": "A1", "deadline": "2026-01-01", "award_amount": ""}]
        html = build_grant_alert_email(grants, ["genomics"])
        assert "genomics" in html


class TestBuildDeadlineReminderEmail:
    def test_basic_reminder(self):
        grant = {
            "title": "Research Grant XYZ",
            "agency": "NSF",
            "deadline": "2026-07-15",
            "award_amount": "$200,000",
        }
        html = build_deadline_reminder_email(grant, 3)
        assert "Research Grant XYZ" in html
        assert "3 day(s)" in html
        assert "NSF" in html
        assert "$200,000" in html
        assert "Deadline Reminder" in html

    def test_one_day_reminder(self):
        grant = {"title": "Urgent Grant", "agency": "NIH", "deadline": "2026-07-01", "award_amount": ""}
        html = build_deadline_reminder_email(grant, 1)
        assert "1 day(s)" in html
        assert "Urgent Grant" in html

    def test_seven_day_reminder(self):
        grant = {"title": "Future Grant", "agency": "DOE", "deadline": "2026-08-01", "award_amount": "$500k"}
        html = build_deadline_reminder_email(grant, 7)
        assert "7 day(s)" in html
