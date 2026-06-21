"""ECCRP API v1 Router - aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    candidates,
    elections,
    eligibility,
    nomination,
    affidavit,
    compliance,
    expenditure,
    mcc,
    knowledge,
    judgments,
    ai_assistant,
    graph,
    dashboard,
    admin,
    public,
    timeline,
)

api_router = APIRouter()

api_router.include_router(auth.router,          prefix="/auth",       tags=["Authentication"])
api_router.include_router(candidates.router,    prefix="/candidates", tags=["Candidates"])
api_router.include_router(elections.router,     prefix="/elections",  tags=["Elections"])
api_router.include_router(eligibility.router,   prefix="/eligibility",tags=["Eligibility"])
api_router.include_router(nomination.router,    prefix="/nomination", tags=["Nomination"])
api_router.include_router(affidavit.router,     prefix="/affidavit",  tags=["Affidavit"])
api_router.include_router(compliance.router,    prefix="/compliance", tags=["Compliance Risk"])
api_router.include_router(expenditure.router,   prefix="/expenditure",tags=["Expenditure"])
api_router.include_router(mcc.router,           prefix="/mcc",        tags=["MCC"])
api_router.include_router(knowledge.router,     prefix="/knowledge",  tags=["Knowledge"])
api_router.include_router(judgments.router,     prefix="/judgments",  tags=["Judgments"])
api_router.include_router(ai_assistant.router,  prefix="/ai",         tags=["AI Assistant"])
api_router.include_router(graph.router,         prefix="/graph",      tags=["Knowledge Graph"])
api_router.include_router(dashboard.router,     prefix="/dashboard",  tags=["Dashboard"])
api_router.include_router(admin.router,         prefix="/admin",      tags=["Admin"])
api_router.include_router(public.router,        prefix="/public",     tags=["Public Transparency"])
api_router.include_router(timeline.router,      prefix="/timeline",   tags=["Election Timeline"])
