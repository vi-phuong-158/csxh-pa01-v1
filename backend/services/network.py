from __future__ import annotations

from typing import Dict, List, Optional, Set

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.constants import get_quan_he_label
from backend.models.models import DoiTuong, QuanHeDoiTuong

_MAX_PROFILE = 100
_MAX_GLOBAL = 200


def _make_node(dt: DoiTuong, is_center: bool = False) -> Dict:
    return {
        "id": dt.cccd,
        "name": dt.ho_ten or f"[{dt.cccd}]",
        "symbolSize": 55 if is_center else 40,
        "category": dt.phan_loai_nghe_nghiep or "Chưa phân loại",
        "is_draft": dt.is_draft,
        "is_center": is_center,
        "label": {"show": True},
    }


def _make_link(edge: QuanHeDoiTuong, cccd_center: str) -> Dict:
    vi_tri = 1 if edge.cccd_1 == cccd_center else 2
    return {
        "source": edge.cccd_1,
        "target": edge.cccd_2,
        "label": get_quan_he_label(edge.loai_quan_he, vi_tri),
        "loai": edge.loai_quan_he or "",
        "do_tin_cay": edge.do_tin_cay or 50,
    }


def get_network_bfs(db: Session, cccd: str, depth: int = 2) -> Dict:
    """BFS từ 1 hồ sơ, trả JSON chuẩn ECharts Graph series."""
    visited: Set[str] = {cccd}
    frontier: Set[str] = {cccd}
    nodes: Dict[str, Dict] = {}
    links: List[Dict] = []
    link_ids_seen: Set[int] = set()

    dt = db.get(DoiTuong, cccd)
    if dt:
        nodes[cccd] = _make_node(dt, is_center=True)

    for _ in range(min(depth, 3)):
        if len(nodes) >= _MAX_PROFILE:
            break

        edges = db.execute(
            select(QuanHeDoiTuong).where(
                or_(
                    QuanHeDoiTuong.cccd_1.in_(list(frontier)),
                    QuanHeDoiTuong.cccd_2.in_(list(frontier)),
                )
            )
        ).scalars().all()

        new_frontier: Set[str] = set()
        for edge in edges:
            for cccd_x in (edge.cccd_1, edge.cccd_2):
                if cccd_x not in visited and len(nodes) < _MAX_PROFILE:
                    visited.add(cccd_x)
                    new_frontier.add(cccd_x)
                    dt_x = db.get(DoiTuong, cccd_x)
                    if dt_x:
                        nodes[cccd_x] = _make_node(dt_x)
            if edge.id not in link_ids_seen:
                link_ids_seen.add(edge.id)
                links.append(_make_link(edge, cccd))

        frontier = new_frontier

    categories = sorted({n["category"] for n in nodes.values()})
    return {
        "nodes": list(nodes.values()),
        "links": links,
        "categories": [{"name": c} for c in categories],
    }


def get_multi_bfs(db: Session, cccd_list: List[str], depth: int = 2) -> Dict:
    """Gộp BFS từ nhiều CCCD gốc, mark tất cả là center."""
    all_nodes: Dict[str, Dict] = {}
    all_links: Dict[tuple, Dict] = {}

    for cccd in cccd_list:
        result = get_network_bfs(db, cccd, depth)
        for node in result["nodes"]:
            if node["id"] not in all_nodes:
                all_nodes[node["id"]] = node
        for link in result["links"]:
            key = (link["source"], link["target"])
            if key not in all_links:
                all_links[key] = link

    for cccd in cccd_list:
        if cccd in all_nodes:
            all_nodes[cccd]["is_center"] = True
            all_nodes[cccd]["symbolSize"] = 55

    categories = sorted({n["category"] for n in all_nodes.values()})
    return {
        "nodes": list(all_nodes.values()),
        "links": list(all_links.values()),
        "categories": [{"name": c} for c in categories],
    }


def get_global_network(
    db: Session,
    dia_chi_xa: Optional[str] = None,
    nghe_nghiep: Optional[str] = None,
    loai_quan_he: Optional[str] = None,
) -> Dict:
    """Toàn bộ mạng lưới có filter, giới hạn _MAX_GLOBAL nodes."""
    edge_stmt = select(QuanHeDoiTuong)
    if loai_quan_he:
        edge_stmt = edge_stmt.where(QuanHeDoiTuong.loai_quan_he == loai_quan_he)
    edges = db.execute(edge_stmt).scalars().all()

    if not edges:
        return {"nodes": [], "links": [], "categories": []}

    cccd_set: Set[str] = set()
    for edge in edges:
        cccd_set.add(edge.cccd_1)
        cccd_set.add(edge.cccd_2)

    dt_stmt = select(DoiTuong).where(DoiTuong.cccd.in_(list(cccd_set)))
    if dia_chi_xa:
        dt_stmt = dt_stmt.where(DoiTuong.dia_chi_xa == dia_chi_xa)
    if nghe_nghiep:
        dt_stmt = dt_stmt.where(DoiTuong.phan_loai_nghe_nghiep == nghe_nghiep)
    dt_stmt = dt_stmt.order_by(DoiTuong.created_at.desc()).limit(_MAX_GLOBAL)

    doi_tuongs: Dict[str, DoiTuong] = {
        dt.cccd: dt for dt in db.execute(dt_stmt).scalars().all()
    }

    nodes = {cccd: _make_node(dt) for cccd, dt in doi_tuongs.items()}

    links = []
    for edge in edges:
        if edge.cccd_1 in nodes and edge.cccd_2 in nodes:
            links.append({
                "source": edge.cccd_1,
                "target": edge.cccd_2,
                "label": get_quan_he_label(edge.loai_quan_he, 1),
                "loai": edge.loai_quan_he or "",
                "do_tin_cay": edge.do_tin_cay or 50,
            })

    categories = sorted({n["category"] for n in nodes.values()})
    return {
        "nodes": list(nodes.values()),
        "links": links,
        "categories": [{"name": c} for c in categories],
    }
