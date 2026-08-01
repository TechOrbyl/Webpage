import logging
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .db import EarlyAccessEntry, get_db, init_db
from .schemas import EarlyAccessResponse, EarlyAccessSubmission

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = PROJECT_ROOT / "pages"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("orbyl")

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, same_site="lax", https_only=False)
app.mount("/style", StaticFiles(directory=PROJECT_ROOT / "style"), name="style")
app.mount("/script", StaticFiles(directory=PROJECT_ROOT / "script"), name="script")
app.mount("/assests", StaticFiles(directory=PROJECT_ROOT / "assests"), name="assests")
app.mount("/pages", StaticFiles(directory=PAGES_DIR), name="pages")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

_memory_entries: list[EarlyAccessResponse] = []


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Request started: %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled exception while processing %s %s", request.method, request.url.path)
        raise
    logger.info("Request completed: %s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@app.on_event("startup")
def startup() -> None:
    logger.info("Starting application")
    init_db()
    logger.info("Database initialization complete")


def _save_submission(payload: EarlyAccessSubmission, db: Session | None) -> EarlyAccessResponse:
    logger.info("Saving early access submission for %s <%s>", payload.name, payload.email)
    if db is not None:
        try:
            row = EarlyAccessEntry(
                name=payload.name,
                phone=payload.phone,
                email=payload.email,
                lost_invoices_or_warranty=payload.lost,
                features=", ".join(payload.features),
                ownership_problems=", ".join(payload.problems),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return EarlyAccessResponse(
                id=row.id, name=row.name, phone=row.phone, email=row.email, lost=row.lost_invoices_or_warranty,
                features=payload.features, problems=payload.problems, created_at=row.created_at,
            )
        except Exception:
            db.rollback()
    entry = EarlyAccessResponse(
        id=len(_memory_entries) + 1, name=payload.name, phone=payload.phone, email=payload.email,
        lost=payload.lost, features=payload.features, problems=payload.problems,
    )
    _memory_entries.append(entry)
    return entry


def _entries(db: Session | None) -> list[EarlyAccessResponse]:
    if db is not None:
        try:
            rows = db.scalars(select(EarlyAccessEntry).order_by(EarlyAccessEntry.created_at.desc())).all()
            return [EarlyAccessResponse(
                id=row.id, name=row.name, phone=row.phone, email=row.email,
                lost=row.lost_invoices_or_warranty, features=[x for x in row.features.split(", ") if x],
                problems=[x for x in row.ownership_problems.split(", ") if x], created_at=row.created_at,
            ) for row in rows]
        except Exception:
            pass
    return list(reversed(_memory_entries))


def _require_admin(request: Request) -> bool:
    return request.session.get("admin") is True


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(PAGES_DIR / "index.html")




PAGE_ALIASES = {"about", "earlyaccess", "faqs", "privacy", "terms", "contact", "thankyou", "404"}


@app.get("/{page_name}.html", include_in_schema=False)
def page_alias(page_name: str) -> FileResponse:
    if page_name not in PAGE_ALIASES:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(PROJECT_ROOT / "404.html" if page_name == "404" else PAGES_DIR / f"{page_name}.html")
@app.get("/404.html", include_in_schema=False)
def not_found_page() -> FileResponse:
    return FileResponse(PROJECT_ROOT / "404.html")


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def admin(request: Request, db: Session | None = Depends(get_db)) -> HTMLResponse:
    if not _require_admin(request):
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "entries": _entries(db)})


@app.post("/admin/login", response_class=HTMLResponse, include_in_schema=False)
def admin_login(request: Request, username: Annotated[str, Form()], password: Annotated[str, Form()]) -> HTMLResponse:
    if username == settings.admin_username and password == settings.admin_password:
        logger.info("Admin login succeeded for user %s", username)
        request.session["admin"] = True
        return RedirectResponse("/admin", status_code=303)
    logger.warning("Admin login failed for user %s", username)
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid credentials."}, status_code=401)


@app.get("/admin/logout", include_in_schema=False)
def admin_logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse("/admin", status_code=303)


@app.post("/api/early-access")
async def create_early_access(request: Request, db: Session | None = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/x-www-form-urlencoded") or content_type.startswith("multipart/form-data"):
        form = await request.form()
        payload = EarlyAccessSubmission(
            name=form.get("name", ""),
            phone=form.get("phone", ""),
            email=form.get("email", ""),
            lost=form.get("lost", ""),
            features=form.getlist("features"),
            problems=form.getlist("problems"),
        )
        _save_submission(payload, db)
        return RedirectResponse("/pages/thankyou.html", status_code=303)
    payload = EarlyAccessSubmission.model_validate(await request.json())
    return _save_submission(payload, db)


@app.get("/api/early-access", response_model=list[EarlyAccessResponse])
def list_early_access(request: Request, db: Session | None = Depends(get_db)) -> list[EarlyAccessResponse]:
    if not _require_admin(request):
        return []
    return _entries(db)
