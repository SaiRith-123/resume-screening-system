"""Export endpoints: CSV / Excel / PDF summary (spec §28)."""
from __future__ import annotations

import csv
import io
import os
import tempfile

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.job_repo import JobRepository
from app.repositories.screening_repo import ScreeningRepository

router = APIRouter(prefix="/jobs/{job_id}", tags=["export"])

HEADERS = [
    "Candidate", "Overall Score", "Eligibility", "Matched Skills", "Missing Skills",
    "Experience", "Education", "Recommendation",
]


def _rows(db: Session, job_id: int) -> list[list[str]]:
    data = [HEADERS]
    candidates = {c.id: c for c in CandidateRepository.list_for_job(db, job_id)}
    for res in ScreeningRepository.list_for_job(db, job_id):
        cand = candidates.get(res.candidate_id)
        structured = (cand.structured or {}) if cand else {}
        edu = "; ".join(
            str(e.get("degree", "")) for e in (structured.get("education") or [])
        )[:120]
        data.append([
            (cand.name if cand and cand.name else f"Candidate {res.candidate_id}"),
            f"{res.final_score:.1f}%",
            res.eligibility_status,
            ", ".join(res.matched_skills or [])[:200],
            ", ".join(res.missing_skills or [])[:200],
            f"{cand.total_experience_years if cand else 0:.1f} yrs",
            edu,
            res.recommendation,
        ])
    return data


@router.get("/export")
def export(job_id: int, fmt: str = Query("csv", pattern="^(csv|xlsx|pdf)$"),
           db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = JobRepository.get(db, job_id, user.id)
    if job is None:
        raise NotFoundError("Job not found")
    rows = _rows(db, job_id)
    safe_title = "".join(c if c.isalnum() else "_" for c in job.title)[:40] or "job"

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerows(rows)
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}_screening.csv"'},
        )

    if fmt == "xlsx":
        from openpyxl import Workbook
        from openpyxl.styles import Font

        wb = Workbook()
        ws = wb.active
        ws.title = "Screening Results"
        for r in rows:
            ws.append(r)
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for column_cells in ws.columns:
            ws.column_dimensions[column_cells[0].column_letter].width = 22
        tmp = os.path.join(tempfile.gettempdir(), f"{safe_title}_screening.xlsx")
        wb.save(tmp)
        return FileResponse(
            tmp, filename=f"{safe_title}_screening.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # pdf
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet

    tmp = os.path.join(tempfile.gettempdir(), f"{safe_title}_screening.pdf")
    doc = SimpleDocTemplate(tmp, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"Screening Results - {job.title}", styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            "This system provides decision-support recommendations. Final hiring "
            "decisions should be made by qualified human reviewers.",
            styles["Italic"],
        ),
        Spacer(1, 12),
        Table(rows, repeatRows=1, style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])),
    ]
    doc.build(elements)
    return FileResponse(tmp, filename=f"{safe_title}_screening.pdf", media_type="application/pdf")
