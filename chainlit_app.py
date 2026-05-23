"""
Regulatory Intelligence Console — Chainlit UI
=============================================
Enterprise-grade front-end for the Nigerian Financial Regulatory
Intelligence Platform.  Connects to the FastAPI backend, submits
analysis requests, streams agent workflow progress, and renders
structured compliance reports.

Run with:
    chainlit run chainlit_app.py --port 8080
"""

import asyncio
import os
from typing import Any

import httpx
import chainlit as cl
from chainlit.input_widget import Select, TextInput, Switch

# ---------------------------------------------------------------------------
# Backend configuration
# ---------------------------------------------------------------------------
API_BASE = os.getenv("REGULATORY_API_URL", "http://localhost:8000")
POLL_INTERVAL_S = 3
MAX_POLL_ATTEMPTS = 60  # 3 min ceiling

# ---------------------------------------------------------------------------
# Agent step labels for display
# ---------------------------------------------------------------------------
AGENT_LABELS = {
    "orchestrator": ("1/7", "Orchestrator", "Decomposing query into sub-tasks"),
    "jurisdiction_mapper": ("2/7", "Jurisdiction Mapper", "Identifying applicable regulators"),
    "researcher": ("3/7", "Research Agent", "Retrieving regulatory documents"),
    "reasoning": ("4/7", "Reasoning Agent", "Synthesising legal obligations"),
    "reasoner": ("4/7", "Reasoning Agent", "Synthesising legal obligations"),
    "auditor": ("5/7", "Compliance Auditor", "Assessing risks and gaps"),
    "citation_verifier": ("6/7", "Citation Verifier", "Validating regulatory citations"),
    "critic": ("7/7", "Critic Agent", "Reviewing output quality"),
}

RISK_BADGE = {
    "CRITICAL": "🔴 CRITICAL",
    "HIGH": "🟠 HIGH",
    "MEDIUM": "🟡 MEDIUM",
    "LOW": "🟢 LOW",
}

SECTOR_OPTIONS = [
    "Fintech",
    "Banking",
    "Insurance",
    "Capital Markets",
    "Payment Services",
    "Digital Assets / Crypto",
    "Microfinance",
    "Other",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def api_get(path: str) -> dict:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        r = await client.get(f"{API_BASE}{path}")
        r.raise_for_status()
        return r.json()


async def api_post(path: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        r = await client.post(f"{API_BASE}{path}", json=payload)
        r.raise_for_status()
        return r.json()


def _risk_badge(level: str | None) -> str:
    level = (level or "UNKNOWN").upper()
    return RISK_BADGE.get(level, f"⚪ {level}")


def _score_bar(score: int | None) -> str:
    if score is None:
        return "—"
    filled = min(int(score), 10)
    return "█" * filled + "░" * (10 - filled) + f"  {filled}/10"


def _extract_text(item: str | dict) -> str:
    if isinstance(item, str):
        return item
    return (
        item.get("description")
        or item.get("obligation")
        or item.get("item")
        or item.get("requirement")
        or item.get("gap_description")
        or item.get("license_type")
        or item.get("text")
        or str(item)
    )


def _fmt_list(items: list[str] | list[dict] | None, limit: int = 8) -> str:
    if not items:
        return "*None identified.*"
    lines = []
    for item in items[:limit]:
        lines.append(f"- {_extract_text(item)}")
    if len(items) > limit:
        lines.append(f"- *…and {len(items) - limit} more*")
    return "\n".join(lines)


def _fmt_checklist(items: list[str] | list[dict] | None) -> str:
    if not items:
        return "*No checklist items.*"
    lines = []
    for item in items or []:
        text = _extract_text(item)
        if isinstance(item, dict):
            raw_status = (item.get("status") or "").upper()
            if raw_status in ("MET", "COMPLIANT", "PASS"):
                icon = "✅"
            elif raw_status in ("UNKNOWN", "PARTIAL"):
                icon = "⚠️"
            else:
                icon = "☐"
            notes = item.get("notes") or ""
            citation = item.get("citation") or ""
            extra = f" — *{notes}*" if notes else ""
            lines.append(f"{icon} **{text}**{extra}")
        else:
            lines.append(f"☐ {text}")
    return "\n".join(lines)


def _fmt_licensing(items: list[str] | list[dict] | None) -> str:
    if not items:
        return "*None identified.*"
    lines = []
    for item in items:
        if isinstance(item, str):
            lines.append(f"- {item}")
        else:
            name = item.get("license_type") or item.get("description") or str(item)
            reg = item.get("regulator", "")
            basis = item.get("requirement_basis") or item.get("basis") or ""
            badge = f"**[{reg}]** " if reg else ""
            detail = f" — *{basis}*" if basis else ""
            lines.append(f"- {badge}{name}{detail}")
    return "\n".join(lines)


def _fmt_gaps(items: list[str] | list[dict] | None) -> str:
    if not items:
        return "*No gaps identified.*"
    lines = []
    for item in items:
        if isinstance(item, str):
            lines.append(f"- {item}")
        else:
            desc = item.get("gap_description") or item.get("description") or str(item)
            risk = item.get("risk_level", "")
            reg = item.get("applicable_regulation") or item.get("regulator") or ""
            fix = item.get("remediation_action") or item.get("remediation") or ""
            risk_badge = f" `{risk}`" if risk else ""
            reg_badge = f" [{reg}]" if reg else ""
            lines.append(f"- **{desc}**{risk_badge}{reg_badge}")
            if fix:
                lines.append(f"  *Remediation: {fix}*")
    return "\n".join(lines)


def _fmt_citations(citations: list[dict] | None) -> str:
    if not citations:
        return "*No citations retrieved.*"
    lines = []
    seen: set[str] = set()
    for c in citations:
        doc = c.get("document") or c.get("source") or "Unknown source"
        reg = c.get("regulator", "")
        page = c.get("page_number")
        key = f"{doc}:{page}"
        if key in seen:
            continue
        seen.add(key)
        badge = f"[{reg}] " if reg else ""
        page_str = f" — page {page}" if page else ""
        lines.append(f"- {badge}**{doc}**{page_str}")
    return "\n".join(lines[:10])


def _fmt_agent_trace(trace: list[dict] | None) -> str:
    if not trace:
        return "*No trace available.*"
    parts = []
    for step in trace:
        agent = step.get("agent", "Agent")
        msg = step.get("message") or step.get("summary") or ""
        parts.append(f"**{agent}**: {msg}")
    return "\n\n".join(parts)


def _build_report_message(result: dict, console_session_id: str = "—") -> str:
    report = result.get("report") or {}
    risk_level = result.get("report", {}).get("risk_level") or result.get("overall_risk_level")
    risk_score = report.get("risk_score")
    audit_id = result.get("audit_id", "—")

    regulators = report.get("applicable_regulators") or []
    obligations = report.get("obligations") or []
    prohibitions = report.get("prohibitions") or []
    permissions = report.get("permissions") or []
    conflicts = report.get("conflicts") or []
    gaps = report.get("compliance_gaps") or []
    checklist = report.get("compliance_checklist") or []
    licensing = report.get("licensing_requirements") or []
    recommendations = report.get("recommendations") or []
    citations = report.get("citations") or []
    summary = report.get("executive_summary") or ""

    lines = [
        "---",
        "## 📋 Compliance Analysis Report",
        "",
        f"### Risk Assessment: {_risk_badge(risk_level)}",
        f"**Risk Score:** `{_score_bar(risk_score)}`",
        "",
    ]

    if regulators:
        lines += [
            f"**Applicable Regulators:** {' · '.join(f'`{r}`' for r in regulators)}",
            "",
        ]

    lines += [
        "---",
        "### Executive Summary",
        summary or "*Not available.*",
        "",
        "---",
        f"### Obligations ({len(obligations)})",
        _fmt_list(obligations),
        "",
        f"### Prohibitions ({len(prohibitions)})",
        _fmt_list(prohibitions),
        "",
        f"### Permissions & Exemptions ({len(permissions)})",
        _fmt_list(permissions),
        "",
    ]

    if conflicts:
        lines += [
            "### ⚠️ Regulatory Conflicts",
            _fmt_list(conflicts),
            "",
        ]

    if licensing:
        lines += [
            "### 🪪 Licensing Requirements",
            _fmt_licensing(licensing),
            "",
        ]

    if gaps:
        lines += [
            f"### 🔍 Compliance Gaps ({len(gaps)})",
            _fmt_gaps(gaps),
            "",
        ]

    lines += [
        "---",
        "### ✅ Compliance Checklist",
        _fmt_checklist(checklist),
        "",
    ]

    if recommendations:
        lines += [
            "### 💡 Recommendations",
            _fmt_list(recommendations),
            "",
        ]

    lines += [
        "---",
        "### 📚 Regulatory Citations",
        _fmt_citations(citations),
        "",
        "---",
        "### 🔎 Audit Metadata",
        f"| Field | Value |",
        f"|---|---|",
        f"| Audit ID | `{audit_id}` |",
        f"| Session ID | `{console_session_id}` |",
    ]

    raw_score = result.get("grounding_score")
    # Citation verifier returns 0-100, not 0.0-1.0
    score_str = f"{raw_score:.0f}" if raw_score is not None else "—"
    hallucination = result.get("hallucination_risk") or "—"
    iterations = result.get("iteration_count", "—")
    lines += [
        f"| Grounding Score | {score_str}% |",
        f"| Hallucination Risk | {hallucination} |",
        f"| Iterations | {iterations} |",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@cl.on_chat_start
async def on_chat_start():
    """Initialize session and display the welcome screen."""
    # Health check
    try:
        health = await api_get("/health")
        status_line = (
            "✅ Backend online"
            if health.get("status") == "ok"
            else "⚠️ Backend degraded"
        )
    except Exception:
        status_line = "❌ Backend unreachable — ensure FastAPI server is running on port 8000"

    # Store session state
    cl.user_session.set("mode", None)  # "analyze" | "gap"
    # Generate a stable session UUID for this chat. Every query in this chat
    # will share this ID so GET /audit/session/{id} returns the full history.
    # When the user opens a new chat, on_chat_start fires again with a fresh UUID.
    import uuid as _uuid
    cl.user_session.set("console_session_id", str(_uuid.uuid4()))

    welcome = f"""# 🏛️ Regulatory Intelligence Console
**Nigerian Financial & Compliance Regulations Platform**

{status_line}

---

This platform performs **agentic multi-step regulatory analysis** using a 7-agent AI workflow:

`Orchestrator → Jurisdiction Mapper → Research → Reasoning → Auditor → Citation Verifier → Critic`

Every output is **retrieval-grounded** with citations from CBN, SEC, NDIC, FIRS, EFCC, and other Nigerian regulatory bodies.

---

**Choose an action to begin:**
"""

    actions = [
        cl.Action(
            name="analyze_business",
            label="🔍 Analyze Business Model",
            description="Identify applicable regulators, licensing needs, and obligations for your fintech/business",
            payload={"mode": "analyze"},
        ),
        cl.Action(
            name="compliance_gap",
            label="📊 Check Compliance Gaps",
            description="Compare your current operations against regulatory requirements and detect missing controls",
            payload={"mode": "gap"},
        ),
        cl.Action(
            name="list_regulations",
            label="📚 List Ingested Regulations",
            description="View all regulatory documents currently available in the knowledge base",
            payload={"mode": "list"},
        ),
    ]

    await cl.Message(content=welcome, actions=actions).send()


# ---------------------------------------------------------------------------
# Action handlers
# ---------------------------------------------------------------------------

@cl.action_callback("analyze_business")
async def on_analyze_action(action: cl.Action):
    cl.user_session.set("mode", "analyze")
    await cl.Message(
        content=(
            "### 🔍 Business Model Analysis\n\n"
            "Describe your business model or product in detail.\n"
            "Include features, revenue model, target users, and planned operations.\n\n"
            "_Example: We are launching a mobile app that allows users to invest in Nigerian Treasury Bills, "
            "earn interest, and send money to other users. We plan to hold customer funds in a pooled account._"
        )
    ).send()


@cl.action_callback("compliance_gap")
async def on_gap_action(action: cl.Action):
    cl.user_session.set("mode", "gap")
    await cl.Message(
        content=(
            "### 📊 Compliance Gap Analysis\n\n"
            "Describe your business and the compliance controls you already have in place.\n"
            "The system will identify what is missing against Nigerian regulatory requirements.\n\n"
            "_Example: We are a licensed fintech processing payments. We have KYC, AML policies, "
            "and a FIRS tax registration. We want to identify regulatory gaps before an expansion._"
        )
    ).send()


@cl.action_callback("list_regulations")
async def on_list_regulations(action: cl.Action):
    msg = cl.Message(content="Fetching ingested regulations…")
    await msg.send()
    try:
        data = await api_get("/regulations")
        docs = data if isinstance(data, list) else data.get("documents", [])
        if not docs:
            msg.content = "No regulations ingested yet. Use `POST /upload-regulation` to ingest documents."
            await msg.update()
            return
        lines = ["### 📚 Ingested Regulatory Documents\n"]
        for d in docs:
            reg = d.get("regulator", "Unknown")
            name = d.get("file_name", "Unknown")
            chunks = d.get("chunks_ingested", "?")
            lines.append(f"- **[{reg}]** {name} — {chunks} chunks")
        msg.content = "\n".join(lines)
        await msg.update()
    except Exception as e:
        msg.content = f"❌ Could not fetch regulations: {e}"
        await msg.update()


# ---------------------------------------------------------------------------
# Main message handler — runs after user provides business description
# ---------------------------------------------------------------------------

@cl.on_message
async def on_message(message: cl.Message):
    mode = cl.user_session.get("mode")

    if not mode:
        await cl.Message(
            content="Please choose an action above to begin.",
        ).send()
        return

    # Reset mode so user can start fresh after this completes
    cl.user_session.set("mode", None)

    query = message.content.strip()
    if len(query) < 20:
        await cl.Message(
            content="⚠️ Please provide a more detailed description (at least 20 characters)."
        ).send()
        return

    endpoint = "/analyze/analyze-business" if mode == "analyze" else "/analyze/compliance-gap"
    console_session_id = cl.user_session.get("console_session_id", "—")
    payload = {
        "business_description": query,
        "session_id": console_session_id,
    }

    await _run_analysis(endpoint, payload, mode, console_session_id)


# ---------------------------------------------------------------------------
# Core analysis flow
# ---------------------------------------------------------------------------

async def _run_analysis(endpoint: str, payload: dict, mode: str, console_session_id: str = "—") -> None:
    """Submit to FastAPI, poll with progress steps, display structured report."""

    # 1. Submit
    submit_msg = cl.Message(content="⏳ Submitting to regulatory intelligence workflow…")
    await submit_msg.send()

    try:
        init = await api_post(endpoint, payload)
    except Exception as e:
        submit_msg.content = f"❌ Failed to submit analysis: {e}"
        await submit_msg.update()
        return

    report_id = str(init.get("report_id"))
    submit_msg.content = (
        f"✅ Analysis queued — **Report ID**: `{report_id}`\n\n"
        f"Running 7-agent workflow. This takes ~60–120 seconds…"
    )
    await submit_msg.update()

    # 2. Workflow progress display
    async with cl.Step(name="Multi-Agent Workflow", type="run", show_input=False) as workflow_step:
        workflow_step.output = "Agents initialising…"
        await workflow_step.update()

        # Poll until done
        result = None
        for attempt in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL_S)

            try:
                poll = await api_get(f"/analyze/report/{report_id}")
            except Exception:
                continue

            status = poll.get("status", "running")

            if status == "completed":
                result = poll
                workflow_step.output = "✅ All 7 agents completed."
                await workflow_step.update()
                break
            elif status == "failed":
                workflow_step.output = f"❌ Workflow failed: {poll.get('error', 'unknown error')}"
                await workflow_step.update()
                await cl.Message(content=f"❌ Analysis failed: {poll.get('error', 'Unknown error')}").send()
                return
            else:
                elapsed = (attempt + 1) * POLL_INTERVAL_S
                workflow_step.output = f"⏳ Running… ({elapsed}s elapsed)"
                await workflow_step.update()

        if result is None:
            await cl.Message(content="⏱️ Analysis timed out. Try `GET /analyze/report/{report_id}` manually.").send()
            return

    # 3. Render agent trace — use real trace from API, fall back to static labels
    full_result = result.get("report") or {}
    agent_trace = result.get("agent_trace") or []

    if agent_trace:
        for entry in agent_trace:
            agent_key = entry.get("agent", "")
            label_info = AGENT_LABELS.get(agent_key)
            if label_info:
                step_num, name, summary = label_info
                async with cl.Step(name=f"[{step_num}] {name}", type="tool", show_input=False) as step:
                    step.output = f"✅ {summary}"
            elif agent_key:
                async with cl.Step(name=agent_key.replace("_", " ").title(), type="tool", show_input=False) as step:
                    step.output = "✅ Completed"
    else:
        # Fallback when trace is not present in the poll response — deduplicate by step number
        seen_steps: set[str] = set()
        for step_num, name, summary in AGENT_LABELS.values():
            if step_num not in seen_steps:
                seen_steps.add(step_num)
                async with cl.Step(name=name, type="tool", show_input=False) as step:
                    step.output = f"✅ {summary}"

    # 4. Sources retrieved sub-step
    citations = full_result.get("citations") or []
    if citations:
        async with cl.Step(name="📚 Sources Retrieved", type="retrieval", show_input=False) as src_step:
            lines = []
            seen: set[str] = set()
            for c in citations[:12]:
                doc = c.get("document") or c.get("source") or "Unknown"
                reg = c.get("regulator", "")
                page = c.get("page_number")
                key = f"{doc}:{page}"
                if key in seen:
                    continue
                seen.add(key)
                badge = f"[{reg}] " if reg else ""
                page_str = f" (p.{page})" if page else ""
                lines.append(f"- {badge}{doc}{page_str}")
            src_step.output = "\n".join(lines)

    # 4b. LLM metrics as a collapsed dev step — kept out of the main compliance report
    metrics = result.get("llm_metrics") or {}
    if metrics:
        async with cl.Step(name="⚙️ Workflow Metrics", type="tool", show_input=False) as m_step:
            cost = metrics.get("cost_usd", 0)
            m_step.output = (
                f"Model: `{metrics.get('model', 'gpt-4o-mini')}` | "
                f"LLM Calls: {metrics.get('llm_calls', 0)} | "
                f"Tokens: {metrics.get('total_tokens', 0):,} | "
                f"Cost: ${cost:.4f} USD"
            )

    # 5. Final structured report
    report_md = _build_report_message(result, console_session_id)
    await cl.Message(content=report_md).send()

    # 6. Follow-up actions
    actions = [
        cl.Action(
            name="analyze_business",
            label="🔍 New Analysis",
            description="Start a new business model analysis",
            payload={"mode": "analyze"},
        ),
        cl.Action(
            name="compliance_gap",
            label="📊 New Gap Check",
            description="Run a new compliance gap analysis",
            payload={"mode": "gap"},
        ),
    ]
    await cl.Message(
        content="_Analysis complete. Start a new query above or choose an action:_",
        actions=actions,
    ).send()
