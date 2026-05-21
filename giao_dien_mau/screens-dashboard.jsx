// ============================================================
// VCFE — Dashboard screen
// ============================================================
const { PageHeader, Icon } = window.VCFEShell;

function Sparkline({ data, w = 240, h = 56, color = "var(--cand-red)" }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const step = w / (data.length - 1);
  const points = data.map((d, i) => `${i * step},${h - ((d - min) / range) * (h - 6) - 3}`).join(" ");
  // Area fill polygon
  const areaPoints = `0,${h} ${points} ${w},${h}`;
  return (
    <svg className="spark" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" style={{ height: h }}>
      <defs>
        <linearGradient id="sparkfill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill="url(#sparkfill)" />
      <polyline points={points} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

function DonutChart({ data, size = 200 }) {
  const total = data.reduce((s, d) => s + d.count, 0);
  const colors = ["#B91C1C", "#C99528", "#1F4936", "#7F1212", "#E8C04D", "#3A6E55", "#A8A18C"];
  const cx = size/2, cy = size/2, r = size/2 - 14, sw = 18;
  const circumference = 2 * Math.PI * r;
  let offset = 0;
  return (
    <svg viewBox={`0 0 ${size} ${size}`} style={{ width: size, height: size }}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--paper-2)" strokeWidth={sw} />
      {data.map((d, i) => {
        const dash = (d.count / total) * circumference;
        const el = (
          <circle key={i}
            cx={cx} cy={cy} r={r} fill="none"
            stroke={colors[i % colors.length]} strokeWidth={sw}
            strokeDasharray={`${dash} ${circumference - dash}`}
            strokeDashoffset={-offset}
            transform={`rotate(-90 ${cx} ${cy})`}
            strokeLinecap="butt"
          />
        );
        offset += dash;
        return el;
      })}
      <text x={cx} y={cy - 4} textAnchor="middle" fontSize="11" fontWeight="700" letterSpacing="0.10em" fill="var(--ink-500)">TỔNG SỐ</text>
      <text x={cx} y={cy + 18} textAnchor="middle" fontSize="26" fontWeight="800" fill="var(--ink-900)">{total}</text>
    </svg>
  );
}

function BarChart30({ data, w = 720, h = 180 }) {
  const max = Math.max(...data);
  const bw = w / data.length;
  const days = ["T","T","T","T","T","T","T"];
  return (
    <svg viewBox={`0 0 ${w} ${h+24}`} style={{ width: "100%", height: h + 24 }}>
      {/* gridlines */}
      {[0, 0.25, 0.5, 0.75, 1].map((p, i) => (
        <line key={i} x1="0" y1={h - p * h + 4} x2={w} y2={h - p * h + 4}
              stroke="var(--line)" strokeDasharray="2 4" />
      ))}
      {data.map((d, i) => {
        const bh = (d / max) * (h - 12);
        const x = i * bw + 2;
        return (
          <g key={i}>
            <rect x={x} y={h - bh + 4} width={bw - 4} height={bh}
                  fill="url(#barfill)" rx="2" />
          </g>
        );
      })}
      <defs>
        <linearGradient id="barfill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#C9252A" />
          <stop offset="100%" stopColor="#7F1212" />
        </linearGradient>
      </defs>
      {/* x-axis label spots */}
      {[0, 7, 14, 21, 29].map((i) => (
        <text key={i} x={i * bw + bw/2} y={h + 18} textAnchor="middle"
              fontSize="10" fill="var(--ink-500)">
          {30 - i} ngày
        </text>
      ))}
    </svg>
  );
}

function DashboardScreen({ onNav }) {
  const { DOI_TUONG, ACTIVITY_30D, QUOC_GIA_STATS, LOAI_HINH_STATS } = window.VCFE;

  const recent = DOI_TUONG.slice(0, 5);

  return (
    <>
      <PageHeader
        eyebrow="Bảng điều khiển nghiệp vụ"
        title="Tổng quan hệ thống VCFED"
        sub="Cập nhật theo thời gian thực · Phiên đăng nhập: Đại úy Vi Ngọc Phương · 16/05/2026 14:42"
        actions={<>
          <button className="btn btn-secondary"><Icon name="file_download" /> Xuất báo cáo</button>
          <button className="btn btn-primary" onClick={() => onNav("nhap-lieu")}>
            <Icon name="person_add" /> Nhập hồ sơ mới
          </button>
        </>}
      />

      {/* Stat tiles */}
      <div className="stats-grid">
        <div className="stat-tile">
          <div className="stat-tile__label"><Icon name="groups" /> Tổng số đối tượng</div>
          <div className="stat-tile__value">446 <span className="unit">hồ sơ</span></div>
          <div className="stat-tile__delta">
            <span className="up"><Icon name="arrow_upward" className="ico" />+12</span>
            so với tháng trước
          </div>
        </div>
        <div className="stat-tile">
          <div className="stat-tile__label"><Icon name="task_alt" /> Đã xác minh</div>
          <div className="stat-tile__value">196 <span className="unit">/ 446</span></div>
          <div className="stat-tile__delta">Tỷ lệ <strong style={{ marginLeft: 3, color: "var(--cand-green)" }}>43.9%</strong></div>
        </div>
        <div className="stat-tile">
          <div className="stat-tile__label"><Icon name="warning" /> Vi phạm pháp luật NN</div>
          <div className="stat-tile__value">12 <span className="unit">đối tượng</span></div>
          <div className="stat-tile__delta">
            <span className="up"><Icon name="arrow_upward" className="ico" />+2</span>
            trong 30 ngày
          </div>
        </div>
        <div className="stat-tile">
          <div className="stat-tile__label"><Icon name="bolt" /> Thao tác hôm nay</div>
          <div className="stat-tile__value">31</div>
          <div className="stat-tile__delta">5 cán bộ đang trực hệ thống</div>
        </div>
      </div>

      {/* Activity + Donut */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card__head">
            <h3><Icon name="show_chart" /> Hoạt động hệ thống · 30 ngày gần nhất</h3>
            <div className="sub">Số thao tác đọc/ghi/cập nhật mỗi ngày</div>
          </div>
          <div className="card__body" style={{ paddingBottom: 8 }}>
            <BarChart30 data={ACTIVITY_30D} />
            <div style={{ display: "flex", gap: 16, marginTop: 12, fontSize: 12, color: "var(--ink-500)" }}>
              <span><Icon name="circle" fill style={{ color: "var(--cand-red)", fontSize: 10 }} /> Trung bình 22/ngày</span>
              <span><Icon name="arrow_upward" style={{ color: "#1F8A4E", fontSize: 14 }} /> Đỉnh: 42 thao tác (28 ngày trước)</span>
              <span><Icon name="schedule" style={{ fontSize: 14 }} /> 9h–11h là khung giờ cao điểm</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card__head">
            <h3><Icon name="donut_large" /> Phân bố theo quốc gia</h3>
            <button className="btn btn-ghost btn-xs"><Icon name="more_horiz" /></button>
          </div>
          <div className="card__body" style={{ display: "flex", gap: 16, alignItems: "center" }}>
            <DonutChart data={QUOC_GIA_STATS} size={172} />
            <div style={{ flex: 1, fontSize: 12.5 }}>
              {QUOC_GIA_STATS.map((q, i) => {
                const colors = ["#B91C1C", "#C99528", "#1F4936", "#7F1212", "#E8C04D", "#3A6E55", "#A8A18C"];
                return (
                  <div key={q.name} style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 0" }}>
                    <span style={{ width: 10, height: 10, borderRadius: 2, background: colors[i % colors.length] }}></span>
                    <span style={{ flex: 1 }}>{q.name}</span>
                    <span style={{ fontVariantNumeric: "tabular-nums", fontWeight: 600 }}>{q.count}</span>
                    <span style={{ color: "var(--ink-500)", width: 32, textAlign: "right" }}>{q.pct}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Loại hình + Quick actions */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card__head">
            <h3><Icon name="category" /> Phân loại hồ sơ đặc thù</h3>
            <div className="sub">Một đối tượng có thể thuộc nhiều loại</div>
          </div>
          <div className="card__body">
            <div className="bar-list">
              {LOAI_HINH_STATS.map((l) => {
                const max = Math.max(...LOAI_HINH_STATS.map(x => x.count));
                const w = (l.count / max) * 100;
                return (
                  <div key={l.code} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <div className="bar-row__label">
                      <span style={{ fontWeight: 600 }}>{l.name}</span>
                      <span style={{ color: "var(--ink-500)" }}>{l.count} hồ sơ</span>
                    </div>
                    <div className="bar-row__bar" style={{ "--w": `${w}%` }}></div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card__head">
            <h3><Icon name="bolt" /> Thao tác nhanh</h3>
          </div>
          <div className="card__body" style={{ display: "grid", gap: 10 }}>
            <button className="qa-card" onClick={() => onNav("nhap-lieu")}>
              <div className="qa-card__icon"><Icon name="person_add" /></div>
              <div>
                <div className="qa-card__title">Nhập hồ sơ đối tượng mới</div>
                <div className="qa-card__sub">Tạo bản nháp, lưu từng bước rồi hoàn tất</div>
              </div>
              <Icon name="arrow_forward" style={{ marginLeft: "auto", color: "var(--ink-500)" }} />
            </button>
            <button className="qa-card" onClick={() => onNav("nhap-excel")}>
              <div className="qa-card__icon"><Icon name="upload_file" /></div>
              <div>
                <div className="qa-card__title">Nhập danh sách từ Excel</div>
                <div className="qa-card__sub">Hỗ trợ đa sheet · validate từng dòng · commit 50/lần</div>
              </div>
              <Icon name="arrow_forward" style={{ marginLeft: "auto", color: "var(--ink-500)" }} />
            </button>
            <button className="qa-card" onClick={() => onNav("ra-soat")}>
              <div className="qa-card__icon"><Icon name="fact_check" /></div>
              <div>
                <div className="qa-card__title">Rà soát tên (Fuzzy Match)</div>
                <div className="qa-card__sub">Đối chiếu danh sách bên ngoài với CSDL nội bộ</div>
              </div>
              <Icon name="arrow_forward" style={{ marginLeft: "auto", color: "var(--ink-500)" }} />
            </button>
            <button className="qa-card" onClick={() => onNav("mang-luoi")}>
              <div className="qa-card__icon"><Icon name="hub" /></div>
              <div>
                <div className="qa-card__title">Phân tích mạng lưới 4D</div>
                <div className="qa-card__sub">Trực quan hoá mối liên hệ giữa các đối tượng</div>
              </div>
              <Icon name="arrow_forward" style={{ marginLeft: "auto", color: "var(--ink-500)" }} />
            </button>
          </div>
        </div>
      </div>

      {/* Recent records + Timeline */}
      <div className="grid-2">
        <div className="card">
          <div className="card__head">
            <h3><Icon name="schedule" /> Hồ sơ cập nhật gần đây</h3>
            <button className="btn btn-ghost btn-xs" onClick={() => onNav("danh-sach")}>
              Xem tất cả <Icon name="arrow_forward" style={{ fontSize: 14 }} />
            </button>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table className="tbl">
              <thead>
                <tr>
                  <th>Đối tượng</th>
                  <th>Loại hình</th>
                  <th>Quốc gia liên quan</th>
                  <th>Cập nhật</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {recent.map((d) => (
                  <tr key={d.cccd}>
                    <td>
                      <div className="row-person">
                        <div className="avatar-sm">{d.ho_ten.split(" ").slice(-1)[0][0]}</div>
                        <div>
                          <div className="row-name">{d.ho_ten}</div>
                          <div className="row-sub mono">{d.cccd} · {d.dia_chi_xa}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        {d.loai_hinh.slice(0, 2).map((lh) => {
                          const cls = lh === "Xac_Minh" ? "pill-green"
                                    : lh === "Vi_Pham_NN" ? "pill-red"
                                    : lh === "Hon_Nhan_NN" ? "pill-gold"
                                    : "pill-blue";
                          return <span key={lh} className={"pill " + cls}><span className="dot"></span>{window.VCFE.LOAI_HINH[lh]}</span>;
                        })}
                      </div>
                    </td>
                    <td>{d.quoc_gia}</td>
                    <td className="mono" style={{ color: "var(--ink-500)" }}>{d.cap_nhat}</td>
                    <td style={{ textAlign: "right" }}>
                      <button className="btn btn-ghost btn-xs" onClick={() => onNav("ho-so")}>
                        Chi tiết <Icon name="arrow_forward" style={{ fontSize: 14 }} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="card__head">
            <h3><Icon name="campaign" /> Cảnh báo & Sự kiện</h3>
          </div>
          <div className="card__body">
            <div className="timeline">
              <div className="timeline__item">
                <div className="when">Hôm nay · 14:32</div>
                <div className="what">
                  <strong>Nguyễn Thị Mai Hương</strong> được cập nhật thêm 1 tài khoản ngân hàng nước ngoài (Shinhan).
                </div>
              </div>
              <div className="timeline__item">
                <div className="when">Hôm nay · 13:48</div>
                <div className="what">
                  Hồ sơ mới: <strong>Đặng Thùy Linh</strong> (SV Sungkyunkwan — Hàn Quốc) được nhập bởi <em>anhph</em>.
                </div>
              </div>
              <div className="timeline__item">
                <div className="when">Hôm qua · 17:02</div>
                <div className="what">
                  ⚠️ 3 hồ sơ sắp hết hạn xác minh trong 30 ngày tới. <a href="#" style={{ color: "var(--cand-red)", fontWeight: 600 }}>Xem danh sách</a>
                </div>
              </div>
              <div className="timeline__item">
                <div className="when">14/05/2026 · 09:14</div>
                <div className="what">
                  Hệ thống tự động sao lưu CSDL (mã hóa). Dung lượng: 38.4 MB.
                </div>
              </div>
              <div className="timeline__item">
                <div className="when">13/05/2026 · 16:30</div>
                <div className="what">
                  <strong>Hoàng Quốc Khải</strong> được gán tag "Vi phạm pháp luật NN" (vi phạm hải quan TQ 2023).
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

window.VCFEDashboard = { DashboardScreen };
