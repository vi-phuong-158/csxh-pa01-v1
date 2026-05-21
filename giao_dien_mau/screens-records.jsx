// ============================================================
// VCFE — Danh sách đối tượng, Hồ sơ chi tiết, Tra cứu nhanh
// ============================================================
const { PageHeader: PH_R, Icon: Ic_R } = window.VCFEShell;

// ---- Pill for loại hình ----
function LoaiHinhPill({ code, compact = false }) {
  const map = {
    "Xac_Minh":            { cls: "pill-green", icon: "verified" },
    "Vi_Pham_NN":          { cls: "pill-red",   icon: "report" },
    "Hon_Nhan_NN":         { cls: "pill-gold",  icon: "favorite" },
    "Lam_Viec_NN":         { cls: "pill-blue",  icon: "business" },
    "Hoc_Tap_Cong_Tac_NN": { cls: "pill-gray",  icon: "school" },
  };
  const m = map[code] || { cls: "pill-gray", icon: "label" };
  const label = window.VCFE.LOAI_HINH[code] || code;
  return (
    <span className={"pill " + m.cls}>
      <Ic_R name={m.icon} style={{ fontSize: 12 }} />
      {compact ? label.split(" ").slice(0, 2).join(" ") : label}
    </span>
  );
}

// ---- Danh sách đối tượng ----
function DanhSachScreen({ onNav, setSelectedCccd }) {
  const { DOI_TUONG } = window.VCFE;
  const [q, setQ] = React.useState("");
  const [filterLoai, setFilterLoai] = React.useState("Tất cả");
  const [filterQuocGia, setFilterQuocGia] = React.useState("Tất cả");
  const [selected, setSelected] = React.useState(null);

  const filtered = DOI_TUONG.filter(d => {
    if (q && !(d.ho_ten.toLowerCase().includes(q.toLowerCase()) || d.cccd.includes(q))) return false;
    if (filterLoai !== "Tất cả" && !d.loai_hinh.includes(filterLoai)) return false;
    if (filterQuocGia !== "Tất cả" && d.quoc_gia !== filterQuocGia) return false;
    return true;
  });

  function openProfile(cccd) {
    setSelectedCccd && setSelectedCccd(cccd);
    onNav("ho-so");
  }

  return (
    <>
      <PH_R
        eyebrow="Danh mục"
        title="Danh sách đối tượng"
        sub={`Tổng cộng ${DOI_TUONG.length} hồ sơ đã hoàn tất · Bộ lọc: hiển thị ${filtered.length} kết quả`}
        actions={<>
          <button className="btn btn-secondary"><Ic_R name="filter_list" /> Bộ lọc nâng cao</button>
          <button className="btn btn-secondary"><Ic_R name="file_download" /> Xuất Excel</button>
          <button className="btn btn-primary" onClick={() => onNav("nhap-lieu")}>
            <Ic_R name="person_add" /> Thêm hồ sơ
          </button>
        </>}
      />

      <div className="filter-bar">
        <div className="search-box">
          <Ic_R name="search" />
          <input
            className="field__input"
            placeholder="Tìm theo họ tên, CCCD..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <select className="field__select" style={{ width: "auto", height: 36 }}
                value={filterLoai} onChange={(e) => setFilterLoai(e.target.value)}>
          <option>Tất cả</option>
          {Object.entries(window.VCFE.LOAI_HINH).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select className="field__select" style={{ width: "auto", height: 36 }}
                value={filterQuocGia} onChange={(e) => setFilterQuocGia(e.target.value)}>
          <option>Tất cả</option>
          {["Hàn Quốc","Trung Quốc","Đài Loan","Nhật Bản","Mỹ","Singapore","Úc","Thụy Điển"].map(c =>
            <option key={c}>{c}</option>)}
        </select>
        <select className="field__select" style={{ width: "auto", height: 36 }}>
          <option>Tất cả xã/phường</option>
          {window.VCFE.XA_PHU_THO.slice(0, 10).map(x => <option key={x}>{x}</option>)}
        </select>
        <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--ink-500)" }}>
          Sắp xếp: <strong style={{ color: "var(--ink-900)" }}>Cập nhật mới nhất</strong>
        </span>
      </div>

      <div className="card">
        <div style={{ overflowX: "auto" }}>
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 36 }}>
                  <input type="checkbox" />
                </th>
                <th>Họ tên & CCCD</th>
                <th>Ngày sinh / Giới</th>
                <th>Cư trú</th>
                <th>Nghề nghiệp</th>
                <th>Loại hình</th>
                <th>Quốc gia</th>
                <th>Cán bộ phụ trách</th>
                <th>Cập nhật</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((d) => (
                <tr key={d.cccd} className={selected === d.cccd ? "is-selected" : ""}
                    onClick={() => setSelected(d.cccd)}>
                  <td><input type="checkbox" /></td>
                  <td>
                    <div className="row-person">
                      <div className="avatar-sm">{d.ho_ten.split(" ").slice(-1)[0][0]}</div>
                      <div>
                        <div className="row-name">{d.ho_ten}</div>
                        <div className="row-sub mono">{d.cccd}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div>{d.ngay_sinh}</div>
                    <div className="row-sub">{d.gioi_tinh}</div>
                  </td>
                  <td>
                    <div style={{ fontWeight: 500 }}>{d.dia_chi_xa}</div>
                    <div className="row-sub">Tỉnh {d.dia_chi_tinh}</div>
                  </td>
                  <td>
                    <div>{d.nghe}</div>
                    <div className="row-sub" style={{ maxWidth: 220, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {d.chi_tiet_nghe}
                    </div>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                      {d.loai_hinh.map(lh => <LoaiHinhPill key={lh} code={lh} compact />)}
                    </div>
                  </td>
                  <td>{d.quoc_gia}</td>
                  <td>
                    <div className="row-sub" style={{ fontSize: 12 }}>{d.phu_trach}</div>
                  </td>
                  <td className="mono" style={{ color: "var(--ink-500)" }}>{d.cap_nhat}</td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn btn-ghost btn-xs" onClick={() => openProfile(d.cccd)}>
                      <Ic_R name="open_in_new" style={{ fontSize: 14 }} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card__foot" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ fontSize: 12, color: "var(--ink-500)" }}>
            Hiển thị <strong style={{ color: "var(--ink-900)" }}>1–{filtered.length}</strong> trên tổng <strong style={{ color: "var(--ink-900)" }}>446</strong> hồ sơ
          </div>
          <div style={{ display: "flex", gap: 4 }}>
            <button className="btn btn-secondary btn-xs"><Ic_R name="chevron_left" /></button>
            <button className="btn btn-primary btn-xs" style={{ minWidth: 28 }}>1</button>
            <button className="btn btn-secondary btn-xs" style={{ minWidth: 28 }}>2</button>
            <button className="btn btn-secondary btn-xs" style={{ minWidth: 28 }}>3</button>
            <button className="btn btn-secondary btn-xs" style={{ minWidth: 28 }}>...</button>
            <button className="btn btn-secondary btn-xs" style={{ minWidth: 28 }}>38</button>
            <button className="btn btn-secondary btn-xs"><Ic_R name="chevron_right" /></button>
          </div>
        </div>
      </div>
    </>
  );
}

// ---- Hồ sơ chi tiết ----
function HoSoScreen({ onNav }) {
  const { DOI_TUONG, HO_SO_HUONG } = window.VCFE;
  const d = DOI_TUONG[0]; // Hương
  const ho_so = HO_SO_HUONG;

  const [tab, setTab] = React.useState("tong-quan");

  const TABS = [
    { id: "tong-quan",   icon: "person",       label: "Tổng quan" },
    { id: "lien-he",     icon: "call",         label: "Liên hệ",      count: ho_so.lien_he.length },
    { id: "tai-chinh",   icon: "account_balance", label: "Tài chính",  count: ho_so.tai_chinh.length },
    { id: "phuong-tien", icon: "directions_car", label: "Phương tiện", count: ho_so.phuong_tien.length },
    { id: "nhan-than",   icon: "family_restroom", label: "Thân nhân",  count: ho_so.nhan_than.length },
    { id: "dac-thu",     icon: "verified_user", label: "Hồ sơ đặc thù", count: ho_so.ho_so_dac_thu.length },
    { id: "tai-lieu",    icon: "folder",       label: "Tài liệu",     count: ho_so.tai_lieu.length },
    { id: "qua-trinh",   icon: "timeline",     label: "Quá trình",    count: ho_so.qua_trinh.length },
  ];

  return (
    <>
      <PH_R
        eyebrow={<><a href="#" onClick={(e) => { e.preventDefault(); onNav("danh-sach"); }} style={{ color: "var(--ink-500)" }}>Danh sách đối tượng</a> / Hồ sơ chi tiết</>}
        title={d.ho_ten}
        sub={`CCCD ${d.cccd} · Cập nhật lần cuối ${d.cap_nhat} · Phụ trách: ${d.phu_trach}`}
        actions={<>
          <button className="btn btn-secondary"><Ic_R name="print" /> In hồ sơ</button>
          <button className="btn btn-secondary"><Ic_R name="file_download" /> Xuất Word</button>
          <button className="btn btn-primary"><Ic_R name="edit" /> Sửa thông tin</button>
        </>}
      />

      {/* Hero card */}
      <div className="profile-hero" style={{ marginBottom: 24 }}>
        <div className="avatar-lg">NH</div>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <div className="profile-hero__name">{d.ho_ten}</div>
            {d.loai_hinh.map(lh => <LoaiHinhPill key={lh} code={lh} />)}
          </div>
          <div className="profile-hero__cccd">{d.cccd}</div>

          <div className="profile-hero__meta">
            <div className="meta-chip"><span className="k">Ngày sinh</span><span className="v">{d.ngay_sinh}</span></div>
            <div className="meta-chip"><span className="k">Giới tính</span><span className="v">{d.gioi_tinh}</span></div>
            <div className="meta-chip"><span className="k">Quốc gia liên quan</span><span className="v">{d.quoc_gia}</span></div>
            <div className="meta-chip"><span className="k">Cư trú</span><span className="v">{d.dia_chi_xa}</span></div>
            <div className="meta-chip"><span className="k">Nghề nghiệp</span><span className="v">{d.nghe}</span></div>
            <div className="meta-chip"><span className="k">Chi tiết</span><span className="v" style={{ maxWidth: 320 }}>{d.chi_tiet_nghe}</span></div>
          </div>

          {d.ghi_chu && (
            <div style={{ marginTop: 14, padding: "10px 12px", background: "var(--cand-gold-soft)",
                          border: "1px solid rgba(201, 149, 40, 0.30)", borderRadius: 8, fontSize: 13 }}>
              <Ic_R name="sticky_note_2" style={{ color: "#7A5A12", fontSize: 16, verticalAlign: "-3px", marginRight: 6 }} />
              <strong>Ghi chú chung:</strong> {d.ghi_chu}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {TABS.map(t => (
          <button key={t.id}
                  className={"tab " + (tab === t.id ? "is-active" : "")}
                  onClick={() => setTab(t.id)}>
            <Ic_R name={t.icon} />
            {t.label}
            {t.count != null && <span className="count">{t.count}</span>}
          </button>
        ))}
      </div>

      {tab === "tong-quan" && <ProfileOverview d={d} ho_so={ho_so} />}
      {tab === "lien-he"     && <ProfileLienHe lien_he={ho_so.lien_he} />}
      {tab === "tai-chinh"   && <ProfileTaiChinh tai_chinh={ho_so.tai_chinh} />}
      {tab === "phuong-tien" && <ProfilePhuongTien phuong_tien={ho_so.phuong_tien} />}
      {tab === "nhan-than"   && <ProfileNhanThan nhan_than={ho_so.nhan_than} />}
      {tab === "dac-thu"     && <ProfileDacThu items={ho_so.ho_so_dac_thu} />}
      {tab === "tai-lieu"    && <ProfileTaiLieu items={ho_so.tai_lieu} />}
      {tab === "qua-trinh"   && <ProfileQuaTrinh items={ho_so.qua_trinh} />}
    </>
  );
}

function ProfileOverview({ d, ho_so }) {
  return (
    <div className="grid-2">
      <div className="card">
        <div className="card__head"><h3><Ic_R name="info" /> Thông tin hành chính</h3></div>
        <div className="card__body">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px 24px" }}>
            <KV k="Họ và tên" v={d.ho_ten} />
            <KV k="Số CCCD" v={d.cccd} mono />
            <KV k="Ngày sinh" v={d.ngay_sinh} />
            <KV k="Giới tính" v={d.gioi_tinh} />
            <KV k="Quê quán" v="Xã Hùng Sơn, Phú Thọ" />
            <KV k="Dân tộc" v="Kinh" />
            <KV k="Tôn giáo" v="Không" />
            <KV k="Trình độ" v="Đại học — Cử nhân Ngôn ngữ Hàn" />
            <KV k="Nơi cư trú" v="Số 24, ngõ 38 Vân Phú, P. Vân Phú, Phú Thọ" />
            <KV k="Cán bộ phụ trách" v={d.phu_trach} />
          </div>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        <div className="card">
          <div className="card__head"><h3><Ic_R name="assessment" /> Chỉ số nhanh</h3></div>
          <div className="card__body" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <MiniStat icon="call" label="Liên hệ" value={ho_so.lien_he.length} />
            <MiniStat icon="account_balance" label="Tài khoản" value={ho_so.tai_chinh.length} />
            <MiniStat icon="directions_car" label="Phương tiện" value={ho_so.phuong_tien.length} />
            <MiniStat icon="family_restroom" label="Thân nhân" value={ho_so.nhan_than.length} />
            <MiniStat icon="folder" label="Tài liệu" value={ho_so.tai_lieu.length} />
            <MiniStat icon="hub" label="Quan hệ" value={3} />
          </div>
        </div>

        <div className="card">
          <div className="card__head"><h3><Ic_R name="history" /> Hoạt động gần đây</h3></div>
          <div className="card__body">
            <div className="timeline">
              <div className="timeline__item">
                <div className="when">14:32 hôm nay</div>
                <div className="what">Thêm tài khoản <strong>Shinhan Bank</strong> (KRW)</div>
              </div>
              <div className="timeline__item">
                <div className="when">04/05/2026</div>
                <div className="what">Cập nhật <strong>tài liệu xác minh lý lịch chồng người HQ</strong></div>
              </div>
              <div className="timeline__item">
                <div className="when">08/02/2025</div>
                <div className="what">Gán nhãn <strong>"Đã xác minh"</strong> bởi Đại úy Vi Ngọc Phương</div>
              </div>
              <div className="timeline__item">
                <div className="when">12/11/2024</div>
                <div className="what">Khởi tạo hồ sơ — diện <strong>Kết hôn với người NN</strong></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function KV({ k, v, mono }) {
  return (
    <div>
      <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.10em", textTransform: "uppercase", color: "var(--ink-500)" }}>{k}</div>
      <div style={{ fontSize: 13.5, marginTop: 2, fontFamily: mono ? "JetBrains Mono, monospace" : "inherit" }}>{v}</div>
    </div>
  );
}

function MiniStat({ icon, label, value }) {
  return (
    <div style={{ background: "var(--paper-2)", border: "1px solid var(--line)", borderRadius: 8, padding: "10px 12px", display: "flex", alignItems: "center", gap: 10 }}>
      <Ic_R name={icon} style={{ color: "var(--cand-red)", fontSize: 22 }} />
      <div>
        <div style={{ fontSize: 10.5, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--ink-500)", fontWeight: 700 }}>{label}</div>
        <div style={{ fontSize: 20, fontWeight: 700, lineHeight: 1.1, fontVariantNumeric: "tabular-nums" }}>{value}</div>
      </div>
    </div>
  );
}

function SubTableSection({ title, addLabel, headers, rows, renderRow }) {
  return (
    <div className="card">
      <div className="card__head">
        <h3>{title}</h3>
        <button className="btn btn-secondary btn-sm"><Ic_R name="add" /> {addLabel}</button>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table className="tbl">
          <thead><tr>{headers.map(h => <th key={h}>{h}</th>)}<th></th></tr></thead>
          <tbody>{rows.map(renderRow)}</tbody>
        </table>
      </div>
    </div>
  );
}

function RowActions() {
  return (
    <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
      <button className="btn btn-ghost btn-xs"><Ic_R name="edit" style={{ fontSize: 14 }} /></button>
      <button className="btn btn-ghost btn-xs" style={{ color: "var(--cand-red)" }}><Ic_R name="delete" style={{ fontSize: 14 }} /></button>
    </td>
  );
}

function ProfileLienHe({ lien_he }) {
  return SubTableSection({
    title: <><Ic_R name="call" /> Thông tin liên hệ</>,
    addLabel: "Thêm liên hệ",
    headers: ["Loại", "Giá trị", "Ghi chú"],
    rows: lien_he,
    renderRow: (r) => (
      <tr key={r.id}>
        <td><span className="pill pill-blue"><Ic_R name={
          r.loai === "Email" ? "mail" :
          r.loai === "Facebook" ? "facebook" :
          r.loai === "Zalo" ? "chat" : "call"
        } style={{ fontSize: 12 }} />{r.loai}</span></td>
        <td className="mono" style={{ fontWeight: 600, color: "var(--ink-900)" }}>{r.gia_tri}</td>
        <td style={{ color: "var(--ink-500)" }}>{r.ghi_chu || "—"}</td>
        <RowActions />
      </tr>
    ),
  });
}

function ProfileTaiChinh({ tai_chinh }) {
  return SubTableSection({
    title: <><Ic_R name="account_balance" /> Tài khoản ngân hàng</>,
    addLabel: "Thêm tài khoản",
    headers: ["Ngân hàng", "Số tài khoản", "Chủ tài khoản", "Ghi chú"],
    rows: tai_chinh,
    renderRow: (r) => (
      <tr key={r.id}>
        <td><strong>{r.ngan_hang}</strong></td>
        <td className="mono">{r.so_tk}</td>
        <td>{r.chu_tk}</td>
        <td style={{ color: "var(--ink-500)" }}>{r.ghi_chu || "—"}</td>
        <RowActions />
      </tr>
    ),
  });
}

function ProfilePhuongTien({ phuong_tien }) {
  return SubTableSection({
    title: <><Ic_R name="directions_car" /> Phương tiện sở hữu</>,
    addLabel: "Thêm phương tiện",
    headers: ["Loại", "Biển kiểm soát", "Tên / Nhãn hiệu", "Ghi chú"],
    rows: phuong_tien,
    renderRow: (r) => (
      <tr key={r.id}>
        <td><span className="pill pill-gray">{r.loai_xe}</span></td>
        <td className="mono" style={{ fontWeight: 700, fontSize: 13 }}>{r.bks}</td>
        <td>{r.ten}</td>
        <td style={{ color: "var(--ink-500)" }}>{r.ghi_chu || "—"}</td>
        <RowActions />
      </tr>
    ),
  });
}

function ProfileNhanThan({ nhan_than }) {
  return SubTableSection({
    title: <><Ic_R name="family_restroom" /> Thân nhân & quan hệ ruột thịt</>,
    addLabel: "Thêm thân nhân",
    headers: ["Quan hệ", "Họ tên", "CCCD / Hộ chiếu", "Ngày sinh", "Giới", "Nơi ở"],
    rows: nhan_than,
    renderRow: (r) => (
      <tr key={r.id}>
        <td>
          <span className={"pill " + (r.quan_he.includes("NN") ? "pill-red" : "pill-green")}>
            <span className="dot"></span>{r.quan_he}
          </span>
        </td>
        <td><strong>{r.ho_ten}</strong></td>
        <td className="mono">{r.cccd}</td>
        <td>{r.ngay_sinh}</td>
        <td>{r.gioi}</td>
        <td>{r.noi_o}</td>
        <RowActions />
      </tr>
    ),
  });
}

function ProfileDacThu({ items }) {
  return (
    <div className="card">
      <div className="card__head">
        <h3><Ic_R name="verified_user" /> Hồ sơ đặc thù (yếu tố nước ngoài)</h3>
        <button className="btn btn-secondary btn-sm"><Ic_R name="add" /> Thêm hồ sơ đặc thù</button>
      </div>
      <div className="card__body" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {items.map(it => (
          <div key={it.id} style={{ border: "1px solid var(--line)", borderRadius: 10, padding: 16, background: "var(--paper)" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <LoaiHinhPill code={it.loai} />
              <span style={{ fontSize: 11.5, color: "var(--ink-500)" }} className="mono">
                Cập nhật: {it.cap_nhat}
              </span>
            </div>
            <div style={{ fontSize: 13.5, lineHeight: 1.6 }}>{it.noi_dung}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProfileTaiLieu({ items }) {
  return (
    <div className="card">
      <div className="card__head">
        <h3><Ic_R name="folder" /> Tài liệu đính kèm</h3>
        <button className="btn btn-secondary btn-sm"><Ic_R name="cloud_upload" /> Tải lên</button>
      </div>
      <div className="card__body" style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12 }}>
        {items.map(it => {
          const ext = it.ten.split(".").pop().toLowerCase();
          const isImg = ["jpg","jpeg","png","webp"].includes(ext);
          return (
            <div key={it.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: 12, border: "1px solid var(--line)", borderRadius: 10, background: "#fff" }}>
              <div style={{
                width: 44, height: 44, borderRadius: 8,
                background: isImg ? "var(--cand-green-soft)" : "var(--cand-red-soft)",
                color: isImg ? "var(--cand-green)" : "var(--cand-red)",
                display: "grid", placeItems: "center",
              }}>
                <Ic_R name={isImg ? "image" : "picture_as_pdf"} fill style={{ fontSize: 22 }} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{it.ten}</div>
                <div style={{ fontSize: 11.5, color: "var(--ink-500)" }}>{it.loai} · {it.size} · {it.ngay}</div>
              </div>
              <button className="btn btn-ghost btn-xs"><Ic_R name="download" /></button>
              <button className="btn btn-ghost btn-xs"><Ic_R name="more_horiz" /></button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ProfileQuaTrinh({ items }) {
  return (
    <div className="card">
      <div className="card__head">
        <h3><Ic_R name="timeline" /> Quá trình hoạt động</h3>
        <button className="btn btn-secondary btn-sm"><Ic_R name="add" /> Thêm sự kiện</button>
      </div>
      <div className="card__body">
        <div className="timeline">
          {items.map(it => (
            <div className="timeline__item" key={it.id}>
              <div className="when">{it.thoi_gian}</div>
              <div className="what">{it.noi_dung}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---- Tra cứu nhanh ----
function TraCuuScreen() {
  const { DOI_TUONG } = window.VCFE;
  const [q, setQ] = React.useState("0912");
  const [type, setType] = React.useState("phone");

  // Mock results for phone search
  const phoneResults = [
    { ten: "NGUYỄN THỊ MAI HƯƠNG", cccd: "025198003142", match: "0912 384 590", loai: "SĐT chính", xa: "Phường Vân Phú" },
    { ten: "TRẦN VĂN BÁCH",        cccd: "025193002671", match: "0912 408 271", loai: "SĐT chính", xa: "Xã Hùng Sơn" },
    { ten: "PHẠM THỊ HỒNG NHUNG",  cccd: "025191005533", match: "0912 555 829", loai: "SĐT chính", xa: "Xã Hy Cương" },
  ];

  const bankResults = [
    { ten: "NGUYỄN THỊ MAI HƯƠNG", cccd: "025198003142", match: "0451 0000 384 122", nh: "Vietcombank" },
    { ten: "VŨ ĐỨC THẮNG",         cccd: "025187003311", match: "0451 0000 220 481", nh: "Vietcombank" },
  ];

  const results = type === "phone" ? phoneResults : type === "bank" ? bankResults : [];

  function highlight(text, q) {
    if (!q) return text;
    const i = text.toLowerCase().indexOf(q.toLowerCase());
    if (i < 0) return text;
    return <>{text.slice(0, i)}<mark>{text.slice(i, i + q.length)}</mark>{text.slice(i + q.length)}</>;
  }

  return (
    <>
      <PH_R
        eyebrow="Truy vấn nhanh"
        title="Tra cứu danh bạ toàn cục"
        sub="Tìm kiếm theo số điện thoại, số tài khoản, biển số xe... trên toàn bộ CSDL"
      />

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card__body" style={{ padding: 20 }}>
          <div style={{ display: "flex", gap: 0, border: "1px solid var(--line-2)", borderRadius: 10, overflow: "hidden" }}>
            <select value={type} onChange={(e) => setType(e.target.value)}
                    className="field__select" style={{ width: 180, border: 0, borderRight: "1px solid var(--line)", borderRadius: 0, background: "var(--paper-2)", fontWeight: 600 }}>
              <option value="phone">Số điện thoại</option>
              <option value="bank">Số tài khoản NH</option>
              <option value="vehicle">Biển số xe</option>
              <option value="email">Email</option>
              <option value="social">Mạng xã hội</option>
            </select>
            <div style={{ flex: 1, position: "relative" }}>
              <Ic_R name="search" style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", color: "var(--ink-500)" }} />
              <input value={q} onChange={(e) => setQ(e.target.value)}
                     placeholder="Nhập từ khoá... (tự động tìm sau 0.5s)"
                     style={{ width: "100%", border: 0, height: 44, padding: "0 14px 0 42px", fontSize: 15, outline: "none" }}/>
            </div>
            <button className="btn btn-primary" style={{ borderRadius: 0, height: "auto" }}>
              <Ic_R name="search" /> Tra cứu
            </button>
          </div>
          <div style={{ marginTop: 10, fontSize: 12, color: "var(--ink-500)", display: "flex", gap: 12, alignItems: "center" }}>
            <span><Ic_R name="bolt" style={{ fontSize: 14, color: "var(--cand-red)", verticalAlign: "-2px" }} /> Tự động tìm sau 500ms (HTMX delay)</span>
            <span>·</span>
            <span>Phím tắt: <span className="kbd">/</span> để focus</span>
            <span>·</span>
            <span>Kết quả: <strong style={{ color: "var(--ink-900)" }}>{results.length}</strong> bản ghi khớp</span>
          </div>
        </div>
      </div>

      {type === "phone" && (
        <div className="card">
          <div className="card__head">
            <h3><Ic_R name="call" /> Kết quả khớp số điện thoại</h3>
            <div className="sub">Khớp một phần với "{q}"</div>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Đối tượng</th>
                  <th>Số điện thoại khớp</th>
                  <th>Loại</th>
                  <th>Cư trú</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {phoneResults.map((r) => (
                  <tr key={r.cccd}>
                    <td>
                      <div className="row-person">
                        <div className="avatar-sm">{r.ten.split(" ").slice(-1)[0][0]}</div>
                        <div>
                          <div className="row-name">{r.ten}</div>
                          <div className="row-sub mono">{r.cccd}</div>
                        </div>
                      </div>
                    </td>
                    <td className="mono" style={{ fontWeight: 700, fontSize: 13.5 }}>{highlight(r.match, q)}</td>
                    <td><span className="pill pill-blue">{r.loai}</span></td>
                    <td>{r.xa}</td>
                    <td style={{ textAlign: "right" }}>
                      <button className="btn btn-ghost btn-xs">Mở hồ sơ <Ic_R name="arrow_forward" style={{ fontSize: 14 }} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {type === "bank" && (
        <div className="card">
          <div className="card__head">
            <h3><Ic_R name="account_balance" /> Kết quả khớp số tài khoản</h3>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table className="tbl">
              <thead>
                <tr><th>Đối tượng</th><th>Ngân hàng</th><th>Số TK khớp</th><th></th></tr>
              </thead>
              <tbody>
                {bankResults.map((r) => (
                  <tr key={r.cccd}>
                    <td>
                      <div className="row-person">
                        <div className="avatar-sm">{r.ten.split(" ").slice(-1)[0][0]}</div>
                        <div><div className="row-name">{r.ten}</div><div className="row-sub mono">{r.cccd}</div></div>
                      </div>
                    </td>
                    <td><strong>{r.nh}</strong></td>
                    <td className="mono" style={{ fontWeight: 700 }}>{highlight(r.match, q)}</td>
                    <td style={{ textAlign: "right" }}>
                      <button className="btn btn-ghost btn-xs">Mở hồ sơ <Ic_R name="arrow_forward" style={{ fontSize: 14 }} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {(type === "vehicle" || type === "email" || type === "social") && (
        <div className="card">
          <div className="card__body">
            <div className="empty-state">
              <Ic_R name="search_off" />
              <div>Nhập từ khoá để bắt đầu tra cứu trên trường <strong>{type === "vehicle" ? "Biển số xe" : type === "email" ? "Email" : "Mạng xã hội"}</strong></div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

window.VCFERecords = { DanhSachScreen, HoSoScreen, TraCuuScreen };
