// ============================================================
// VCFE — Layout shell (banner, sidebar) + Login screen
// ============================================================

const { useState } = React;

// ---- Icon helper ----
function Icon({ name, fill = false, className = "", style = {} }) {
  return (
    <span
      className={"ico " + (fill ? "ico--fill " : "") + className}
      style={style}
    >{name}</span>
  );
}

// ---- Top banner ----
function TopBanner({ user }) {
  return (
    <header className="banner">
      <div className="banner__logo" aria-label="Logo Công an nhân dân Việt Nam"></div>
      <div className="banner__titles">
        <div className="banner__eyebrow">Bộ Công an · Công an tỉnh Phú Thọ · Phòng PA01</div>
        <div className="banner__title">VCFED · Cơ sở Dữ liệu Người Việt có Yếu tố Nước ngoài</div>
        <div className="banner__sub">v2.0 · Bảo mật SQLCipher AES-256 · Offline / LAN nội bộ</div>
      </div>
      <div className="banner__spacer"></div>
      <div className="banner__sysstatus">
        <span className="dot"></span>
        <span>Hệ thống hoạt động · 127.0.0.1:9000</span>
      </div>
      <div className="banner__divider"></div>
      <div className="banner__user">
        <div className="avatar">{user.initials}</div>
        <div className="info">
          <div className="name">{user.name}</div>
          <div className="role">{user.rank} · {user.role}</div>
        </div>
        <Icon name="expand_more" style={{ color: "rgba(255,255,255,0.65)", marginLeft: 2 }} />
      </div>
    </header>
  );
}

// ---- Sidebar ----
const NAV = [
  {
    group: "Nghiệp vụ",
    items: [
      { id: "dashboard",  icon: "dashboard",        label: "Tổng quan" },
      { id: "danh-sach",  icon: "groups",           label: "Danh sách đối tượng", badge: "446" },
      { id: "ho-so",      icon: "badge",            label: "Hồ sơ chi tiết" },
      { id: "tra-cuu",    icon: "manage_search",    label: "Tra cứu nhanh" },
      { id: "mang-luoi",  icon: "hub",              label: "Mạng lưới quan hệ" },
    ],
  },
  {
    group: "Nhập liệu",
    items: [
      { id: "nhap-lieu",  icon: "person_add",       label: "Nhập hồ sơ mới" },
      { id: "nhap-excel", icon: "upload_file",      label: "Nhập từ Excel", badge: "Mới", badgeAlert: true },
      { id: "ra-soat",    icon: "fact_check",       label: "Rà soát danh sách" },
    ],
  },
  {
    group: "Hệ thống",
    items: [
      { id: "nhat-ky",    icon: "history",          label: "Nhật ký thao tác" },
      { id: "users",      icon: "admin_panel_settings", label: "Người dùng" },
      { id: "cai-dat",    icon: "settings",         label: "Cài đặt" },
    ],
  },
];

function Sidebar({ current, onNav }) {
  return (
    <aside className="sidebar">
      <div className="sidebar__top">
        <div className="sidebar__search-wrap">
          <Icon name="search" className="ico" />
          <input
            type="text"
            placeholder="Tìm CCCD, họ tên, số điện thoại..."
            className="sidebar__search"
          />
        </div>
      </div>
      <nav className="sidebar__nav">
        {NAV.map((g) => (
          <div className="nav-group" key={g.group}>
            <div className="nav-group__label">{g.group}</div>
            {g.items.map((it) => (
              <div
                key={it.id}
                className={"nav-item " + (current === it.id ? "nav-item--active" : "")}
                onClick={() => onNav(it.id)}
              >
                <Icon name={it.icon} fill={current === it.id} />
                <span>{it.label}</span>
                {it.badge && (
                  <span className={"badge " + (it.badgeAlert ? "badge--alert" : "")}>
                    {it.badge}
                  </span>
                )}
              </div>
            ))}
          </div>
        ))}
      </nav>
      <div className="sidebar__foot">
        <span className="badge-sec">AES-256</span>
        <div style={{ lineHeight: 1.25 }}>
          <div style={{ fontWeight: 600, color: "var(--ink-700)" }}>Phiên mã hóa</div>
          <div>Khóa DB · phiên 4h 12'</div>
        </div>
      </div>
    </aside>
  );
}

// ---- Page header (consistent across screens) ----
function PageHeader({ eyebrow, title, sub, actions, children }) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {sub && <p className="sub">{sub}</p>}
        {children}
      </div>
      {actions && <div className="page-header__actions">{actions}</div>}
    </div>
  );
}

// ---- Login Screen ----
function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState("phuongvi");
  const [password, setPassword] = useState("••••••••••");
  const [loading, setLoading] = useState(false);

  function submit(e) {
    e && e.preventDefault();
    setLoading(true);
    setTimeout(() => { onLogin(); }, 700);
  }

  return (
    <div className="login-screen">
      <div className="login-art">
        <div className="login-art__brand">
          <img src="assets/logo-cand.png" alt="CAND" />
          <div>
            <h2>CÔNG AN NHÂN DÂN VIỆT NAM</h2>
            <div className="org">Công an tỉnh Phú Thọ · Phòng An ninh Chính trị Nội bộ (PA01)</div>
          </div>
        </div>

        <div className="login-art__hero">
          <div className="eyebrow">Vì An ninh Tổ quốc</div>
          <h1>Hệ thống VCFED<br/>v2.0</h1>
          <p>
            Cơ sở dữ liệu chuyên biệt theo dõi, quản lý và phân tích mạng lưới
            người Việt Nam có yếu tố nước ngoài trên địa bàn tỉnh. Mã hóa toàn phần
            AES-256, vận hành nội bộ trên hệ thống mạng LAN khép kín.
          </p>
        </div>

        <div className="login-art__foot">
          <div><strong>Bảo mật</strong>SQLCipher · Keyring Windows</div>
          <div><strong>Kiến trúc</strong>FastAPI · HTMX · Alpine.js</div>
          <div><strong>Phiên bản</strong>2.0.4 — 05/2026</div>
        </div>
      </div>

      <div className="login-form-wrap">
        <form className="login-form" onSubmit={submit}>
          <h2>Đăng nhập hệ thống</h2>
          <div className="sub">Sử dụng tài khoản cán bộ được cấp bởi quản trị viên.</div>

          <div className="field">
            <label className="field__label">Tên đăng nhập</label>
            <input
              className="field__input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </div>

          <div className="field">
            <label className="field__label">Mật khẩu</label>
            <input
              className="field__input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading
              ? <><Icon name="autorenew" style={{ animation: "spin 1s linear infinite" }} /> Đang xác thực...</>
              : <><Icon name="login" /> Đăng nhập</>}
          </button>

          <div className="help-row">
            <span>
              <Icon name="shield_lock" style={{ verticalAlign: "-3px", color: "var(--cand-green)", fontSize: 16 }} /> Phiên mã hóa End-to-End
            </span>
            <a href="#" style={{ color: "var(--cand-red)", fontWeight: 600 }}>Hỗ trợ kỹ thuật</a>
          </div>
        </form>
      </div>

      <style>{`@keyframes spin { from { transform: rotate(0); } to { transform: rotate(360deg); }}`}</style>
    </div>
  );
}

// Toast container
function ToastRegion({ toasts }) {
  return (
    <div className="toast-region">
      {toasts.map((t) => (
        <div key={t.id} className={"toast " + (t.type === "error" ? "toast--error" : "")}>
          <Icon name={t.type === "error" ? "error" : "check_circle"} fill={true} />
          <div>{t.msg}</div>
        </div>
      ))}
    </div>
  );
}

window.VCFEShell = { TopBanner, Sidebar, PageHeader, LoginScreen, ToastRegion, Icon, NAV };
