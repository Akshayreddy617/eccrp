"""ECCRP Module 6 - Election Timeline Planner."""

from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import User, Election
from app.core.security import get_current_active_user

router = APIRouter()


def _build_timeline_actions(election: Election) -> list:
    """Build action items and compliance deadlines from election dates."""
    actions = []

    def add_action(date: Optional[datetime], title: str, description: str,
                   category: str, days_before: int = 0):
        if not date:
            return
        action_date = date - timedelta(days=days_before) if days_before else date
        actions.append({
            "date": str(action_date.date()),
            "title": title,
            "description": description,
            "category": category,
            "is_deadline": days_before == 0,
        })

    # Notification
    add_action(election.notification_date, "Election Notification Issued",
               "ECI/SEC issues official election notification. MCC comes into force immediately.",
               "milestone")

    # Nomination window
    add_action(election.nomination_start_date, "Nomination Window Opens",
               "Candidates can begin filing nomination papers with Returning Officer.",
               "nomination")
    add_action(election.nomination_start_date, "Prepare Nomination Package",
               "Collect Form 26 (Affidavit), security deposit, electoral roll copy, "
               "photographs, PAN card.",
               "action", days_before=3)
    add_action(election.nomination_end_date, "DEADLINE: Last Day for Nomination",
               "Final day to file nomination. Arrive early — RO may stop accepting close to deadline.",
               "deadline")
    add_action(election.nomination_end_date, "Security Deposit Preparation",
               "Ensure security deposit is ready (Lok Sabha: ₹25,000 / ₹12,500 SC/ST; "
               "Assembly: ₹10,000 / ₹5,000 SC/ST)",
               "action", days_before=2)

    # Scrutiny
    add_action(election.nomination_scrutiny_date, "Nomination Scrutiny",
               "Returning Officer scrutinises all nominations. Be present to clarify any defects.",
               "milestone")
    add_action(election.nomination_scrutiny_date, "Review Nomination for Defects",
               "Double-check all fields in Form 26. Ensure no material facts are omitted.",
               "action", days_before=1)

    # Withdrawal
    add_action(election.withdrawal_date, "DEADLINE: Last Day for Withdrawal",
               "Candidates may withdraw nomination by this date. After this, name is final on ballot.",
               "deadline")

    # Campaign period
    if election.withdrawal_date and election.polling_date:
        campaign_start = election.withdrawal_date + timedelta(days=1)
        actions.append({
            "date": str(campaign_start.date()),
            "title": "Campaign Period Begins",
            "description": "Active campaigning can commence. All MCC rules apply. "
                           "Pre-certify all electronic media advertisements with MCMC.",
            "category": "campaign",
            "is_deadline": False,
        })

    # MCC silence period
    if election.polling_date:
        silence_start = election.polling_date - timedelta(hours=48)
        actions.append({
            "date": str(silence_start.date()),
            "title": "Campaign Silence Period Begins (48 Hours)",
            "description": "Section 126 RPA 1951: No campaigning, rallies, meetings, or "
                           "media broadcasts within 48 hours of polling. Strict ECI enforcement.",
            "category": "deadline",
            "is_deadline": True,
        })

    # Polling day
    add_action(election.polling_date, "POLLING DAY",
               "Election day. No campaign activities. Candidate or agent may be present at polling stations.",
               "milestone")

    # Expenditure account deadline
    if election.result_date:
        exp_deadline = election.result_date + timedelta(days=30)
        actions.append({
            "date": str(exp_deadline.date()),
            "title": "DEADLINE: File Expenditure Account",
            "description": "Section 78 RPA 1951: Submit complete election expenditure account "
                           "to District Election Officer within 30 days of election results. "
                           "Failure = disqualification under Section 10A for 3 years.",
            "category": "deadline",
            "is_deadline": True,
        })

    # Counting
    add_action(election.counting_date, "Counting Day",
               "Votes counted. Candidate or counting agent should be present.",
               "milestone")
    add_action(election.result_date, "Results Declared",
               "Official results declared by Returning Officer. 30-day expenditure clock starts.",
               "milestone")

    return sorted(actions, key=lambda x: x["date"])


@router.get("/{election_id}")
async def get_election_timeline(
    election_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Module 6: Election Timeline Planner.

    Generates complete timeline with:
    - All official election dates
    - Required actions and deadlines
    - Compliance checkpoints
    - Calendar export data
    """
    result = await db.execute(select(Election).where(Election.id == election_id))
    election = result.scalar_one_or_none()
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")

    actions = _build_timeline_actions(election)
    deadlines = [a for a in actions if a.get("is_deadline")]
    milestones = [a for a in actions if not a.get("is_deadline")]

    # Days remaining calculations
    today = datetime.utcnow()
    days_to_polling = None
    if election.polling_date:
        delta = election.polling_date - today
        days_to_polling = max(0, delta.days)

    days_to_nomination = None
    if election.nomination_end_date and election.nomination_end_date > today:
        delta = election.nomination_end_date - today
        days_to_nomination = max(0, delta.days)

    return {
        "election": {
            "id": str(election.id),
            "name": election.name,
            "election_type": election.election_type.value,
            "year": election.year,
            "expenditure_limit": float(election.expenditure_limit) if election.expenditure_limit else None,
        },
        "key_dates": {
            "notification_date": str(election.notification_date.date()) if election.notification_date else None,
            "nomination_start": str(election.nomination_start_date.date()) if election.nomination_start_date else None,
            "nomination_end": str(election.nomination_end_date.date()) if election.nomination_end_date else None,
            "scrutiny_date": str(election.nomination_scrutiny_date.date()) if election.nomination_scrutiny_date else None,
            "withdrawal_date": str(election.withdrawal_date.date()) if election.withdrawal_date else None,
            "polling_date": str(election.polling_date.date()) if election.polling_date else None,
            "counting_date": str(election.counting_date.date()) if election.counting_date else None,
            "result_date": str(election.result_date.date()) if election.result_date else None,
        },
        "countdown": {
            "days_to_polling": days_to_polling,
            "days_to_nomination_deadline": days_to_nomination,
        },
        "timeline": actions,
        "deadlines": deadlines,
        "milestones": milestones,
        "ical_export_url": f"/api/v1/timeline/{election_id}/export.ics",
        "legal_notes": [
            "MCC comes into force on the date of election notification announcement.",
            "Section 126 RPA 1951: 48-hour campaign silence is mandatory.",
            "Section 78 RPA 1951: Expenditure account must be filed within 30 days of results.",
            "Section 10A RPA 1951: Non-filing of expenditure account = 3-year disqualification.",
        ],
    }


@router.get("/{election_id}/export.ics")
async def export_timeline_ics(
    election_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Export election timeline as iCalendar (.ics) for calendar apps."""
    from fastapi.responses import Response

    result = await db.execute(select(Election).where(Election.id == election_id))
    election = result.scalar_one_or_none()
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")

    actions = _build_timeline_actions(election)

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//ECCRP//Election Compliance Platform//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:ECCRP - {election.name}",
    ]

    for i, action in enumerate(actions):
        date_str = action["date"].replace("-", "")
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"DTSTART;VALUE=DATE:{date_str}",
            f"DTEND;VALUE=DATE:{date_str}",
            f"SUMMARY:{action['title']}",
            f"DESCRIPTION:{action['description']}",
            f"UID:eccrp-{election_id}-{i}@eccrp.in",
            "END:VEVENT",
        ])

    ics_lines.append("END:VCALENDAR")
    ics_content = "\r\n".join(ics_lines)

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="election-{election.year}.ics"'},
    )
