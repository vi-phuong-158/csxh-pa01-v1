from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.deps import require_admin
from backend.services import auth as auth_svc

router = APIRouter(prefix="/quan-ly-user", tags=["admin"])
templates = Jinja2Templates(directory="frontend/templates")


@router.get("", response_class=HTMLResponse)
def list_users(request: Request, user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    users = auth_svc.get_all_users(db)
    return templates.TemplateResponse(request, "quan_ly_user/index.html", {"user": user, "users": users})


@router.post("/create")
async def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    ho_ten: str = Form(""),
    role: str = Form("user"),
    must_change_password: str = Form("on"),
    user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ok, msg = auth_svc.create_user(db, username, password, ho_ten, role, must_change_password == "on")
    users = auth_svc.get_all_users(db)
    ctx = {"user": user, "users": users}
    if ok:
        ctx["success"] = msg
    else:
        ctx["error"] = msg
    return templates.TemplateResponse(request, "quan_ly_user/index.html", ctx)


@router.post("/{user_id}/delete")
def delete_user(user_id: int, user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    ok, msg = auth_svc.delete_user(db, user_id)
    return {"ok": ok, "message": msg}
