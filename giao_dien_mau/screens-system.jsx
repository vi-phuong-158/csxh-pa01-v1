// ============================================================
// VCFE — Mạng lưới, Nhật ký, Người dùng, Cài đặt
// ============================================================
const { PageHeader: PH_S, Icon: Ic_S } = window.VCFEShell;

// ---- Network Graph (SVG) ----
function NetworkScreen() {
  // Node layout
  const center = { id: "c", x: 380, y: 240, label: "NGUYỄN THỊ MAI HƯƠNG", sub: "025198003142", type: "main" };
  const nodes = [
    // Inner ring: thân nhân
    { id: "park", x: 600, y: 140, label: "PARK JOON-HO", sub: "Chồng · HQ", type: "foreign" },
    { id: "minw", x: 620, y: 280, label: "PARK MIN-WOO", sub: "Con (2019)", type: "person" },
    { id: "do",   x: 170, y: 130, label: "NGUYỄN VĂN ĐÔ", sub: "Bố", type: "person" },
    { id: "mien", x: 160, y: 260, label: "TRẦN THỊ MIÊN", sub: "Mẹ", type: "person" },
    { id: "truong", x: 240, y: 400, label: "NGUYỄN VĂN TRƯỜNG", sub: "Em ruột", type: "person" },
    // Outer ring: liên kết khác
    { id: "thang", x: 540, y: 410, label: "VŨ ĐỨC THẮNG", sub: "Đồng nghiệp · HQ", type: "object" },
    { id: "hyosung", x: 760, y: 220, label: "Cty Hyosung VN", sub: "Doanh nghiệp FDI HQ", type: "org" },
    { id: "shinhan", x: 80,  y: 380, label: "Shinhan Bank", sub: "TK ngoại tệ KRW", type: "bank" },
  ];

  const edges = [
    { from: "c", to: "park",   label: "Vợ chồng",      color: "#B91C1C", dash: false },
    { from: "c", to: "minw",   label: "Mẹ – Con",      color: "#1F4936", dash: false },
    { from: "c", to: "do",     label: "Con – Cha",     color: "#1F4936", dash: false },
    { from: "c", to: "mien",   label: "Con – Mẹ",      color: "#1F4936", dash: false },
    { from: "c", to: "truong", label: "Anh – Em",      color: "#1F4936", dash: false },
    { from: "c", to: "hyosung",label: "Nhân viên",     color: "#C99528", dash: true },
    { from: "c", to: "shinhan",label: "Sở hữu TK",     color: "#C99528", dash: true },
    { from: "c", to: "thang",  label: "Đồng nghiệp",   color: "#A8A18C", dash: true },
    { from: "park", to: "hyosung", label: "Liên hệ",   color: "#A8A18C", dash: true },
    { from: "thang", to: "hyosung", label: "Nhân viên",color: "#A8A18C", dash: true },
  ];

  const allNodes = [center, ...nodes];
  const idx = Object.fromEntries(allNodes.map(n => [n.id, n]));

  const colorOf = {
    main:    "#B91C1C",
    foreign: "#C99528",
    person:  "#1F4936",
    object:  "#5B7F6C",
    org:     "#7F1212",
    bank:    "#1F3B66",
  };
  const radiusOf = { main: 32, foreign: 24, person: 20, object: 20, org: 22, bank: 22 };

  return (
    <>
      <PH_S
        eyebrow="Phân tích 4D"
        title="Mạng lưới quan hệ"
        sub="Trực quan hoá mối liên hệ giữa các đối tượng, thân nhân, tổ chức và đơn vị tài chính"
        actions={<>
          <button className="btn btn-secondary"><Ic_S name="filter_list" /> Bộ lọc lớp</button>
          <button className="btn btn-secondary"><Ic_S name="fullscreen" /> Toàn màn hình</button>
          <button className="btn btn-primary"><Ic_S name="file_download" /> Xuất ảnh PNG</button>
        </>}
      />

      <div className="grid-2">
        <div className="network-stage">
          <svg viewBox="0 0 820 500" style={{ width: "100%", height: "100%" }}>
            <defs>
              {/* subtle radial vignette */}
              <radialGradient id="bgvignette">
                <stop offset="60%" stopColor="rgba(0,0,0,0)" />
                <stop offset="100%" stopColor="rgba(122,95,30,0.06)" />
              </radialGradient>
              <pattern id="dots" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
                <circle cx="2" cy="2" r="0.7" fill="#D9CEAF" />
              </pattern>
              <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#A8A18C" />
              </marker>
            </defs>
            <rect x="0" y="0" width="820" height="500" fill="url(#dots)" />
            <rect x="0" y="0" width="820" height="500" fill="url(#bgvignette)" />

            {/* Edges */}
            {edges.map((e, i) => {
              const a = idx[e.from], b = idx[e.to];
              const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
              return (
                <g key={i}>
                  <line x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                        stroke={e.color}
                        strokeWidth={e.from === "c" || e.to === "c" ? 1.8 : 1.2}
                        strokeDasharray={e.dash ? "4 4" : "0"}
                        strokeLinecap="round" opacity="0.7" />
                  <text x={mx} y={my - 4} fontSize="10" fill="var(--ink-500)" textAnchor="middle"
                        style={{ background: "#fff", paintOrder: "stroke", stroke: "var(--paper)", strokeWidth: 4 }}>
                    {e.label}
                  </text>
                </g>
              );
            })}

            {/* Nodes */}
            {allNodes.map(n => {
              const r = radiusOf[n.type] || 20;
              const fill = colorOf[n.type] || "#888";
              return (
                <g key={n.id}>
                  {n.type === "main" && (
                    <circle cx={n.x} cy={n.y} r={r + 8} fill="none" stroke={fill} strokeWidth="1" opacity="0.3" />
                  )}
                  <circle cx={n.x} cy={n.y} r={r} fill={fill}
                          stroke="#fff" strokeWidth="3"
                          style={{ filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.18))" }} />
                  <text x={n.x} y={n.y + 4} fontSize={n.type === "main" ? "12" : "10"} fontWeight="700" fill="#fff" textAnchor="middle">
                    {n.label.split(" ").slice(-2).map(w => w[0]).join("")}
                  </text>
                  <text x={n.x} y={n.y + r + 14} fontSize="10.5" fontWeight="700" fill="var(--ink-900)" textAnchor="middle">
                    {n.label}
                  </text>
                  <text x={n.x} y={n.y + r + 26} fontSize="9.5" fill="var(--ink-500)" textAnchor="middle">
                    {n.sub}
                  </text>
                </g>
              );
            })}
          </svg>

          <div className="network-legend">
            <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: "0.10em", textTransform: "uppercase", color: "var(--ink-500)", marginBottom: 6 }}>Chú thích</div>
            <div className="row"><span className="swatch" style={{ background: colorOf.main }}></span>Đối tượng chính</div>
            <div className="row"><span className="swatch" style={{ background: colorOf.foreign }}></span>Người nước ngoài</div>
            <div className="row"><span className="swatch" style={{ background: colorOf.person }}></span>Thân nhân Việt Nam</div>
            <div className="row"><span className="swatch" style={{ background: colorOf.org }}></span>Tổ chức / DN</div>
            <div className="row"><span className="swatch" style={{ background: colorOf.bank }}></span>Ngân hàng / TK</div>
          </div>
        </div>

        {/* Side panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div className="card">
            <div className="card__head"><h3><Ic_S name="settings" /> Tuỳ chọn hiển thị</h3></div>
            <div className="card__body" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <ToggleRow label="Quan hệ huyết thống" on />
              <ToggleRow label="Quan hệ hôn nhân" on />
              <ToggleRow label="Quan hệ công việc" on />
              <ToggleRow label="Tài chính (ngân hàng)" on />
              <ToggleRow label="Liên hệ (SĐT/MXH)" on={false} />
              <ToggleRow label="Phương tiện" on={false} />
            </div>
          </div>

          <div className="card">
            <div className="card__head"><h3><Ic_S name="filter_alt" /> Mức độ tin cậy</h3></div>
            <div className="card__body">
              <input type="range" min="0" max="100" defaultValue="60" style={{ width: "100%" }} />
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11.5, color: "var(--ink-500)", marginTop: 4 }}>
                <span>0 — Tất cả</span>
                <span><strong style={{ color: "var(--ink-900)" }}>≥60%</strong></span>
                <span>100 — Đã xác minh</span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card__head"><h3><Ic_S name="lightbulb" /> Phát hiện đáng chú ý</h3></div>
            <div className="card__body" style={{ fontSize: 13, lineHeight: 1.6 }}>
              <div style={{ padding: "8px 0", borderBottom: "1px solid var(--line)" }}>
                <strong>VŨ ĐỨC THẮNG</strong> cùng làm tại <em>Hyosung VN</em> — có thể là đầu mối hỗ trợ visa.
              </div>
              <div style={{ padding: "8px 0", borderBottom: "1px solid var(--line)" }}>
                <strong>PARK JOON-HO</strong> có liên kết trực tiếp với <em>Hyosung VN</em>.
              </div>
              <div style={{ padding: "8px 0" }}>
                <strong>Shinhan Bank KRW</strong>: tài khoản ngoại tệ — kiểm tra dòng tiền định kỳ.
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

function ToggleRow({ label, on: initial }) {
  const [on, setOn] = React.useState(initial);
  return (
    <label style={{ display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer" }}>
      <span style={{ fontSize: 13 }}>{label}</span>
      <div onClick={() => setOn(!on)} style={{
        width: 32, height: 18, borderRadius: 999,
        background: on ? "var(--cand-red)" : "var(--line-2)",
        position: "relative", transition: "background 0.15s",
      }}>
        <div style={{
          position: "absolute", top: 2, left: on ? 16 : 2,
          width: 14, height: 14, borderRadius: "50%", background: "#fff",
          transition: "left 0.15s",
        }}></div>
      </div>
    </label>
  );
}

// ---- Nhật ký thao tác ----
function NhatKyScreen() {
  const { AUDIT_LOG } = window.VCFE;
  return (
    <>
      <PH_S
        eyebrow="Hệ thống"
        title="Nhật ký thao tác (Audit Log)"
        sub="Mọi thao tác INSERT/UPDATE/DELETE đều được ghi nhận tự động · Bất biến · Không thể chỉnh sửa"
        actions={<>
          <button className="btn btn-secondary"><Ic_S name="filter_list" /> Bộ lọc</button>
          <button className="btn btn-secondary"><Ic_S name="file_download" /> Xuất CSV</button>
        </>}
      />

      <div className="filter-bar">
        <div className="search-box">
          <Ic_S name="search" />
          <input className="field__input" placeholder="Tìm theo username, bảng, khoá chính..." />
        </div>
        <select className="field__select" style={{ width: "auto", height: 36 }}>
          <option>Mọi hành động</option><option>INSERT</option><option>UPDATE</option><option>DELETE</option><option>BACKUP</option>
        </select>
        <select className="field__select" style={{ width: "auto", height: 36 }}>
          <option>Mọi bảng</option><option>doi_tuong</option><option>lien_he</option><option>tai_chinh</option><option>nhan_than</option>
        </select>
        <input type="date" className="field__input" style={{ height: 36, width: "auto" }} defaultValue="2026-05-16" />
        <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--ink-500)" }}>
          Tổng <strong style={{ color: "var(--ink-900)" }}>10 / 28,492</strong> bản ghi
        </span>
      </div>

      <div className="card">
        <div style={{ overflowX: "auto" }}>
          <table className="tbl">
            <thead>
              <tr>
                <th>Thời điểm</th>
                <th>Người thực hiện</th>
                <th>Bảng</th>
                <th>Hành động</th>
                <th>Khoá chính</th>
                <th>IP</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {AUDIT_LOG.map(l => (
                <tr key={l.id}>
                  <td className="mono" style={{ fontSize: 12 }}>{l.when}</td>
                  <td>
                    <div className="row-person">
                      <div className="avatar-sm" style={{ width: 26, height: 26, fontSize: 11 }}>
                        {l.who[0].toUpperCase()}
                      </div>
                      <strong>{l.who}</strong>
                    </div>
                  </td>
                  <td><span className="pill pill-gray">{l.bang}</span></td>
                  <td>
                    {l.hd === "INSERT" && <span className="pill pill-green"><Ic_S name="add" style={{ fontSize: 12 }} />INSERT</span>}
                    {l.hd === "UPDATE" && <span className="pill pill-blue"><Ic_S name="edit" style={{ fontSize: 12 }} />UPDATE</span>}
                    {l.hd === "DELETE" && <span className="pill pill-red"><Ic_S name="delete" style={{ fontSize: 12 }} />DELETE</span>}
                    {l.hd === "BACKUP" && <span className="pill pill-gold"><Ic_S name="backup" style={{ fontSize: 12 }} />BACKUP</span>}
                  </td>
                  <td className="mono">{l.khoa}</td>
                  <td className="mono" style={{ color: "var(--ink-500)" }}>{l.ip}</td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn btn-ghost btn-xs">Xem diff <Ic_S name="arrow_forward" style={{ fontSize: 14 }} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

// ---- Người dùng ----
function UsersScreen() {
  const { USERS } = window.VCFE;
  return (
    <>
      <PH_S
        eyebrow="Hệ thống"
        title="Quản lý người dùng"
        sub="Tài khoản cán bộ được cấp bởi Quản trị viên cấp cao · Vai trò: super_admin / user"
        actions={<>
          <button className="btn btn-primary"><Ic_S name="person_add" /> Tạo tài khoản</button>
        </>}
      />

      <div className="card">
        <div style={{ overflowX: "auto" }}>
          <table className="tbl">
            <thead>
              <tr>
                <th>Cán bộ</th>
                <th>Tên đăng nhập</th>
                <th>Vai trò</th>
                <th>Trạng thái</th>
                <th>Đăng nhập gần nhất</th>
                <th>Số hồ sơ phụ trách</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {USERS.map((u, i) => (
                <tr key={u.id}>
                  <td>
                    <div className="row-person">
                      <div className="avatar-sm" style={{ background: "linear-gradient(135deg, #E5DBC4, #C2AE7A)" }}>
                        {u.ho_ten.split(" ").slice(-1)[0][0]}
                      </div>
                      <div>
                        <div className="row-name">{u.ho_ten}</div>
                        <div className="row-sub">ID: {u.id}</div>
                      </div>
                    </div>
                  </td>
                  <td className="mono"><strong>{u.username}</strong></td>
                  <td>
                    {u.role === "super_admin"
                      ? <span className="pill pill-red"><Ic_S name="shield" style={{ fontSize: 12 }} />Quản trị cấp cao</span>
                      : <span className="pill pill-blue"><Ic_S name="person" style={{ fontSize: 12 }} />Cán bộ</span>}
                  </td>
                  <td>
                    {u.active
                      ? <span className="pill pill-green"><span className="dot"></span>Hoạt động</span>
                      : <span className="pill pill-gray"><span className="dot"></span>Đã khoá</span>}
                  </td>
                  <td className="mono" style={{ fontSize: 12, color: "var(--ink-500)" }}>{u.last}</td>
                  <td style={{ fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>{[112, 94, 138, 76, 26][i]}</td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn btn-ghost btn-xs"><Ic_S name="edit" style={{ fontSize: 14 }} /></button>
                    <button className="btn btn-ghost btn-xs"><Ic_S name="lock_reset" style={{ fontSize: 14 }} /></button>
                    <button className="btn btn-ghost btn-xs" style={{ color: "var(--cand-red)" }}><Ic_S name="block" style={{ fontSize: 14 }} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

// ---- Cài đặt ----
function CaiDatScreen() {
  return (
    <>
      <PH_S
        eyebrow="Hệ thống"
        title="Cài đặt"
        sub="Cấu hình bảo mật, sao lưu, và tham số vận hành"
      />

      <div className="grid-2">
        <div className="card">
          <div className="card__head"><h3><Ic_S name="shield_lock" /> Bảo mật</h3></div>
          <div className="card__body" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <SettingsRow label="Mã hoá CSDL" value="SQLCipher AES-256-CBC" pill="pill-green" pillText="Đang hoạt động" />
            <SettingsRow label="Lưu trữ khoá" value="Windows Credential Manager (Keyring)" />
            <SettingsRow label="Thuật toán SECRET_KEY" value="PBKDF2-HMAC-SHA256 · 600,000 iter" />
            <SettingsRow label="Băm mật khẩu cán bộ" value="bcrypt 12 rounds" />
            <SettingsRow label="Khoá tài khoản sau" value="5 lần đăng nhập thất bại" />
            <SettingsRow label="Phiên đăng nhập" value="JWT 8h · sliding refresh" />
            <button className="btn btn-secondary" style={{ alignSelf: "flex-start", marginTop: 4 }}>
              <Ic_S name="key" /> Đổi mật khẩu CSDL
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card__head"><h3><Ic_S name="backup" /> Sao lưu</h3></div>
          <div className="card__body" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <SettingsRow label="Sao lưu gần nhất" value="16/05/2026 08:42 · 38.4 MB" pill="pill-green" pillText="Thành công" />
            <SettingsRow label="Lịch sao lưu tự động" value="Hàng ngày, 08:30" />
            <SettingsRow label="Số bản giữ lại" value="30 bản · ~1.2 GB" />
            <SettingsRow label="Vị trí lưu" value="D:\\VCFED\\backups\\" mono />
            <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
              <button className="btn btn-secondary"><Ic_S name="cloud_upload" /> Sao lưu ngay</button>
              <button className="btn btn-ghost"><Ic_S name="restore" /> Khôi phục từ bản sao</button>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card__head"><h3><Ic_S name="palette" /> Hiển thị & Vận hành</h3></div>
          <div className="card__body" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <SettingsRow label="Cảng chạy server" value="127.0.0.1:9000" mono />
            <SettingsRow label="Chế độ HTTPS" value="Tắt (môi trường LAN nội bộ)" />
            <SettingsRow label="Số dòng/trang danh sách" value="20 dòng" />
            <SettingsRow label="Giao diện" value="Sang trọng — Phong cách CAND" />
            <SettingsRow label="Ngôn ngữ" value="Tiếng Việt (vi-VN)" />
          </div>
        </div>

        <div className="card">
          <div className="card__head"><h3><Ic_S name="memory" /> Trạng thái hệ thống</h3></div>
          <div className="card__body" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <SettingsRow label="Phiên bản" value="VCFED v2.0.4 (build 2026.05.12)" />
            <SettingsRow label="Python" value="3.11.4 (PyInstaller bundle)" />
            <SettingsRow label="FastAPI" value="0.108.0 · Uvicorn 0.27" />
            <SettingsRow label="Kích thước CSDL" value="42.1 MB (mã hoá)" />
            <SettingsRow label="Thời gian uptime" value="4 ngày 12 giờ 38 phút" />
            <SettingsRow label="Bộ nhớ" value="186 MB / 8 GB" />
          </div>
        </div>
      </div>
    </>
  );
}

function SettingsRow({ label, value, mono, pill, pillText }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, padding: "8px 0", borderBottom: "1px solid var(--line)" }}>
      <div style={{ fontSize: 12, color: "var(--ink-500)", fontWeight: 500 }}>{label}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 13, fontWeight: 600, fontFamily: mono ? "JetBrains Mono, monospace" : "inherit" }}>{value}</span>
        {pill && <span className={"pill " + pill}><span className="dot"></span>{pillText}</span>}
      </div>
    </div>
  );
}

window.VCFESystem = { NetworkScreen, NhatKyScreen, UsersScreen, CaiDatScreen };
