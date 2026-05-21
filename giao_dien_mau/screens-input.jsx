// ============================================================
// VCFE — Nhập liệu, Nhập Excel, Rà soát
// ============================================================
const { PageHeader: PH_I, Icon: Ic_I } = window.VCFEShell;

// ---- Nhập hồ sơ mới (Draft flow) ----
function NhapLieuScreen({ onToast }) {
  const [step, setStep] = React.useState(2);

  const STEPS = [
    { n: 1, label: "Nhập CCCD" },
    { n: 2, label: "Thông tin cơ bản" },
    { n: 3, label: "Liên hệ & Tài chính" },
    { n: 4, label: "Thân nhân & Quá trình" },
    { n: 5, label: "Hồ sơ đặc thù" },
    { n: 6, label: "Xem lại & Hoàn tất" },
  ];

  return (
    <>
      <PH_I
        eyebrow="Quy trình bản nháp"
        title="Nhập hồ sơ đối tượng mới"
        sub="Hồ sơ được lưu dưới dạng bản nháp (is_draft = True). Mỗi bước được auto-save. Bấm 'Hoàn tất' ở bước cuối để chuyển trạng thái chính thức."
        actions={<>
          <button className="btn btn-secondary"><Ic_I name="save" /> Lưu nháp</button>
          <button className="btn btn-danger"><Ic_I name="delete" /> Huỷ nháp</button>
        </>}
      />

      {/* Stepper */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card__body" style={{ padding: 18 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
            {STEPS.map((s, i) => {
              const done = s.n < step;
              const active = s.n === step;
              return (
                <React.Fragment key={s.n}>
                  <button onClick={() => setStep(s.n)} style={{
                    background: "transparent", border: 0, padding: 0, cursor: "pointer",
                    display: "flex", flexDirection: "column", alignItems: "center", gap: 4, flex: "0 0 auto"
                  }}>
                    <div style={{
                      width: 30, height: 30, borderRadius: "50%",
                      background: active ? "var(--cand-red)" : done ? "var(--cand-green)" : "#fff",
                      color: active || done ? "#fff" : "var(--ink-500)",
                      border: "2px solid " + (active ? "var(--cand-red)" : done ? "var(--cand-green)" : "var(--line-2)"),
                      display: "grid", placeItems: "center", fontWeight: 700, fontSize: 12,
                      boxShadow: active ? "0 0 0 4px rgba(185,28,28,0.12)" : "none",
                    }}>
                      {done ? <Ic_I name="check" style={{ fontSize: 16 }} /> : s.n}
                    </div>
                    <div style={{ fontSize: 11.5, fontWeight: active ? 700 : 500, color: active ? "var(--cand-red)" : "var(--ink-700)" }}>
                      {s.label}
                    </div>
                  </button>
                  {i < STEPS.length - 1 && (
                    <div style={{ flex: 1, height: 2, background: done ? "var(--cand-green)" : "var(--line)", marginTop: -14 }}></div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Main form */}
        <div className="card">
          <div className="card__head">
            <h3>
              <Ic_I name="person" /> {STEPS[step - 1].label}
              <span className="pill pill-gold" style={{ marginLeft: 8 }}>
                <Ic_I name="draft" style={{ fontSize: 12 }} /> Bản nháp
              </span>
            </h3>
            <div className="sub">CCCD đang nhập: <strong className="mono">025199001458</strong></div>
          </div>
          <div className="card__body">
            {step === 1 && (
              <div className="form-grid">
                <div className="field col-3">
                  <label className="field__label">Số CCCD / CMND / Hộ chiếu<span className="req">*</span></label>
                  <input className="field__input" placeholder="9 hoặc 12 chữ số (CCCD), hoặc mã hộ chiếu" />
                  <div className="field__hint">
                    <Ic_I name="info" style={{ fontSize: 14, verticalAlign: "-3px", color: "var(--cand-red)" }} />
                    Hệ thống sẽ kiểm tra CCCD này đã tồn tại chưa, trước khi tạo bản nháp mới.
                  </div>
                </div>
              </div>
            )}
            {step === 2 && (
              <div className="form-grid">
                <div className="field col-2">
                  <label className="field__label">Họ và tên<span className="req">*</span></label>
                  <input className="field__input" placeholder="Tên sẽ được tự động chuyển sang VIẾT HOA" defaultValue="VŨ THỊ NGỌC LAN" />
                </div>
                <div className="field">
                  <label className="field__label">Giới tính</label>
                  <select className="field__select"><option>Nữ</option><option>Nam</option></select>
                </div>
                <div className="field">
                  <label className="field__label">Ngày sinh</label>
                  <input className="field__input" type="date" defaultValue="1995-08-14" />
                </div>
                <div className="field">
                  <label className="field__label">Dân tộc</label>
                  <input className="field__input" defaultValue="Kinh" />
                </div>
                <div className="field">
                  <label className="field__label">Quốc tịch</label>
                  <input className="field__input" defaultValue="Việt Nam" />
                </div>
                <div className="field">
                  <label className="field__label">Tỉnh / Thành</label>
                  <select className="field__select" defaultValue="Phú Thọ"><option>Phú Thọ</option><option>Khác</option></select>
                </div>
                <div className="field col-2">
                  <label className="field__label">Xã / Phường cư trú</label>
                  <select className="field__select">
                    {window.VCFE.XA_PHU_THO.map(x => <option key={x}>{x}</option>)}
                  </select>
                </div>
                <div className="field col-3">
                  <label className="field__label">Địa chỉ chi tiết</label>
                  <input className="field__input" placeholder="Số nhà, ngõ, đường..." defaultValue="Số 47 ngõ 12 đường Hùng Vương" />
                </div>
                <div className="field col-2">
                  <label className="field__label">Phân loại nghề nghiệp</label>
                  <select className="field__select" defaultValue="Doanh nghiệp FDI">
                    {window.VCFE.NGHE_NGHIEP.map(n => <option key={n}>{n}</option>)}
                  </select>
                </div>
                <div className="field">
                  <label className="field__label">Cán bộ phụ trách</label>
                  <select className="field__select"><option>Trung úy Lê Minh Tuấn</option><option>Thiếu úy Phạm Quỳnh Anh</option></select>
                </div>
                <div className="field col-3">
                  <label className="field__label">Chi tiết nghề nghiệp</label>
                  <textarea className="field__textarea" rows={2} defaultValue="Nhân viên kế toán — Cty TNHH Honda Lock Việt Nam (vốn Nhật Bản)"></textarea>
                </div>
                <div className="field col-3">
                  <label className="field__label">Ghi chú chung</label>
                  <textarea className="field__textarea" rows={3} placeholder="Ghi chú nội bộ, không hiển thị cho người ngoài..."></textarea>
                </div>
              </div>
            )}
            {step >= 3 && (
              <div className="empty-state">
                <Ic_I name="construction" />
                <div>Bước "{STEPS[step - 1].label}" — Nội dung được hiển thị khi điều hướng tới bước này trong quy trình thực tế.</div>
              </div>
            )}
          </div>
          <div className="card__foot" style={{ display: "flex", justifyContent: "space-between" }}>
            <button className="btn btn-secondary" disabled={step === 1} onClick={() => setStep(s => Math.max(1, s - 1))}>
              <Ic_I name="arrow_back" /> Bước trước
            </button>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn btn-ghost" onClick={() => onToast && onToast({ type: "success", msg: "Đã lưu nháp" })}>
                <Ic_I name="save" /> Lưu nháp
              </button>
              {step < STEPS.length ? (
                <button className="btn btn-primary" onClick={() => setStep(s => Math.min(STEPS.length, s + 1))}>
                  Bước tiếp theo <Ic_I name="arrow_forward" />
                </button>
              ) : (
                <button className="btn btn-primary">
                  <Ic_I name="task_alt" /> Hoàn tất hồ sơ
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Side panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div className="card">
            <div className="card__head"><h3><Ic_I name="auto_awesome" /> Hỗ trợ nhập liệu</h3></div>
            <div className="card__body" style={{ fontSize: 12.5, color: "var(--ink-700)", lineHeight: 1.7 }}>
              <p style={{ marginTop: 0 }}><strong>Tiến độ:</strong> 2/6 bước · ước tính còn ~6 phút</p>
              <ul style={{ paddingLeft: 18, margin: 0 }}>
                <li>Họ tên sẽ tự động chuyển sang chữ hoa.</li>
                <li>CCCD phải có 9 hoặc 12 chữ số.</li>
                <li>Mọi thao tác được ghi vào <em>audit_log</em>.</li>
                <li>Có thể quay lại bản nháp bất kỳ lúc nào trong danh sách <strong>Hồ sơ chưa hoàn tất</strong>.</li>
              </ul>
            </div>
          </div>
          <div className="card">
            <div className="card__head"><h3><Ic_I name="history" /> Bản nháp chưa hoàn tất</h3></div>
            <div className="card__body" style={{ padding: 0 }}>
              <div style={{ padding: "10px 16px", borderBottom: "1px solid var(--line)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <div style={{ fontWeight: 600 }}>VŨ THỊ NGỌC LAN</div>
                  <div className="row-sub mono">025199001458 · 2/6 bước · hôm nay</div>
                </div>
                <span className="pill pill-gold"><Ic_I name="draft" style={{ fontSize: 12 }} />Đang nhập</span>
              </div>
              <div style={{ padding: "10px 16px", borderBottom: "1px solid var(--line)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <div style={{ fontWeight: 600 }}>ĐOÀN VĂN QUYẾT</div>
                  <div className="row-sub mono">025188006612 · 4/6 bước · 14/05</div>
                </div>
                <span className="pill pill-gold"><Ic_I name="draft" style={{ fontSize: 12 }} />Đang nhập</span>
              </div>
              <div style={{ padding: "10px 16px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <div style={{ fontWeight: 600 }}>NGUYỄN VĂN HOÀNG</div>
                  <div className="row-sub mono">025196007713 · 5/6 bước · 13/05</div>
                </div>
                <span className="pill pill-gold"><Ic_I name="draft" style={{ fontSize: 12 }} />Đang nhập</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ---- Nhập từ Excel ----
function NhapExcelScreen({ onToast }) {
  const [stage, setStage] = React.useState("results"); // upload | processing | results

  return (
    <>
      <PH_I
        eyebrow="Bulk import"
        title="Nhập danh sách từ Excel"
        sub="Hỗ trợ đa sheet · Validate từng dòng · Commit theo chunk 50 dòng để tránh khoá SQLCipher"
        actions={<>
          <button className="btn btn-secondary"><Ic_I name="download" /> Tải mẫu Excel</button>
        </>}
      />

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Upload zone */}
        <div className="card">
          <div className="card__head">
            <h3><Ic_I name="upload_file" /> Tệp Excel nguồn</h3>
            <div className="sub">.xlsx hoặc .xls · tối đa 5 MB</div>
          </div>
          <div className="card__body">
            <div className="drop-zone" onClick={() => onToast && onToast({ type: "success", msg: "Chọn tệp..." })}>
              <Ic_I name="cloud_upload" fill />
              <h4>Kéo & thả tệp Excel vào đây</h4>
              <p>Hoặc <a href="#" style={{ color: "var(--cand-red)", fontWeight: 600 }}>chọn tệp từ máy tính</a></p>
              <p style={{ marginTop: 12, color: "var(--ink-500)" }}>
                Cột bắt buộc: <code style={{ background: "var(--paper-2)", padding: "1px 6px", borderRadius: 3 }}>cccd</code>, <code style={{ background: "var(--paper-2)", padding: "1px 6px", borderRadius: 3 }}>ho_ten</code>
              </p>
            </div>
            <div style={{ marginTop: 16, padding: 14, background: "var(--paper-2)", border: "1px solid var(--line)", borderRadius: 10 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ width: 40, height: 40, borderRadius: 8, background: "#1F8A4E", color: "#fff", display: "grid", placeItems: "center" }}>
                  <Ic_I name="description" fill />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600 }}>danh_sach_VCFE_thang5_2026.xlsx</div>
                  <div style={{ fontSize: 11.5, color: "var(--ink-500)" }}>183 dòng · 4 sheet · 2.4 MB · vừa tải lên</div>
                </div>
                <button className="btn btn-ghost btn-xs"><Ic_I name="close" /></button>
              </div>
              <div style={{ marginTop: 10, fontSize: 11.5, color: "var(--ink-500)" }}>
                Sheet phát hiện: <strong style={{ color: "var(--ink-900)" }}>doi_tuong (183), lien_he (412), tai_chinh (96), nhan_than (228)</strong>
              </div>
            </div>
          </div>
          <div className="card__foot" style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
            <button className="btn btn-secondary"><Ic_I name="visibility" /> Xem trước</button>
            <button className="btn btn-primary" onClick={() => setStage("results")}>
              <Ic_I name="play_arrow" /> Bắt đầu nhập
            </button>
          </div>
        </div>

        {/* Options */}
        <div className="card">
          <div className="card__head">
            <h3><Ic_I name="tune" /> Tùy chọn nhập</h3>
          </div>
          <div className="card__body" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <OptionRow label="Bỏ qua CCCD đã tồn tại"
                       hint="Khuyến nghị: bật để tránh ghi đè bản ghi cũ" defaultOn />
            <OptionRow label="Tự động chuyển họ tên sang chữ HOA"
                       hint="Theo chuẩn nhập liệu của hệ thống" defaultOn />
            <OptionRow label="Ghi nhật ký từng dòng vào audit_log"
                       hint="Có thể làm chậm với file lớn" defaultOn={false} />
            <OptionRow label="Gửi email báo cáo sau khi hoàn tất"
                       hint="Gửi đến: phuongvi@pa01.phutho.gov.vn" defaultOn={false} />
            <div>
              <label className="field__label">Kích thước chunk (dòng/commit)</label>
              <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                {[25, 50, 100, 200].map(n => (
                  <button key={n} className={"btn btn-sm " + (n === 50 ? "btn-primary" : "btn-secondary")}>{n}</button>
                ))}
              </div>
              <div className="field__hint" style={{ marginTop: 6 }}>50 là giá trị khuyến nghị (theo CLAUDE.md).</div>
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      {stage === "results" && (
        <>
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card__head">
              <h3><Ic_I name="task_alt" /> Kết quả nhập</h3>
              <div className="sub">Hoàn tất lúc 14:42:18 · Mất 8.6 giây · 4 chunk × 50 dòng</div>
            </div>
            <div className="card__body" style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
              <ResultStat color="#1F8A4E" icon="check_circle" label="Thành công" value={171} />
              <ResultStat color="#C99528" icon="warning"      label="Cảnh báo (mềm)" value={5} />
              <ResultStat color="#B91C1C" icon="error"        label="Lỗi (bỏ qua)" value={7} />
              <ResultStat color="#3A6E55" icon="schedule"     label="Thời gian" value="8.6s" />
            </div>
            <div style={{ padding: "0 20px 20px" }}>
              <div className="progress" style={{ marginTop: 16 }}>
                <div className="progress__bar" style={{ width: "94%" }}></div>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: 12, color: "var(--ink-500)" }}>
                <span>171 / 183 dòng được nhập thành công (94%)</span>
                <span><strong style={{ color: "var(--ink-900)" }}>Chunk 4/4 hoàn tất</strong></span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card__head">
              <h3><Ic_I name="bug_report" /> Chi tiết lỗi & cảnh báo</h3>
              <button className="btn btn-secondary btn-sm"><Ic_I name="file_download" /> Xuất CSV lỗi</button>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table className="tbl">
                <thead>
                  <tr><th>Dòng</th><th>Sheet</th><th>CCCD</th><th>Họ tên</th><th>Loại</th><th>Thông báo</th></tr>
                </thead>
                <tbody>
                  <ErrRow row={14} sheet="doi_tuong" cccd="0251980" name="LƯU MAI HƯƠNG" type="error" msg="CCCD không hợp lệ (chỉ có 7 chữ số, cần 9 hoặc 12)" />
                  <ErrRow row={28} sheet="doi_tuong" cccd="025198003142" name="NGUYỄN T. MAI HƯƠNG" type="error" msg="CCCD đã tồn tại trong CSDL (NGUYỄN THỊ MAI HƯƠNG)" />
                  <ErrRow row={42} sheet="doi_tuong" cccd="025193002671" name="TRẦN VĂN BÁCH" type="error" msg="CCCD đã tồn tại trong CSDL" />
                  <ErrRow row={67} sheet="doi_tuong" cccd="025191008276" name="—" type="error" msg="Thiếu trường bắt buộc: ho_ten" />
                  <ErrRow row={89} sheet="doi_tuong" cccd="025194002201" name="LÝ THỊ HỒNG" type="warn" msg="Ngày sinh không parse được, đã bỏ qua trường này" />
                  <ErrRow row={103} sheet="doi_tuong" cccd="025190007799" name="ĐOÀN TIẾN MẠNH" type="warn" msg="Giới tính 'M' không khớp Nam/Nữ, đã chuyển thành 'Nam'" />
                  <ErrRow row={118} sheet="doi_tuong" cccd="025196004422" name="PHAN THỊ HẰNG" type="warn" msg="Xã/phường không có trong danh mục, lưu dạng text tự do" />
                  <ErrRow row={142} sheet="lien_he"  cccd="025198003142" name="—" type="error" msg="Tham chiếu CCCD không tồn tại trong sheet doi_tuong và cũng không có sẵn trong CSDL" />
                  <ErrRow row={155} sheet="doi_tuong" cccd="" name="VÕ THANH SƠN" type="error" msg="Thiếu CCCD" />
                  <ErrRow row={167} sheet="tai_chinh" cccd="025195000485" name="—" type="error" msg="Ngân hàng 'BSB Bank' không có trong danh mục 18 NH được hỗ trợ" />
                  <ErrRow row={178} sheet="doi_tuong" cccd="025190004401" name="NGUYỄN BÁ LINH" type="error" msg="CCCD trùng trong cùng file Excel (lần 2)" />
                  <ErrRow row={181} sheet="doi_tuong" cccd="025198002233" name="PHẠM THỊ NGỌC" type="warn" msg="Loại nghề nghiệp 'Freelancer' không có trong danh mục, đã đổi thành 'Khác'" />
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </>
  );
}

function OptionRow({ label, hint, defaultOn }) {
  const [on, setOn] = React.useState(defaultOn);
  return (
    <label style={{ display: "flex", alignItems: "flex-start", gap: 12, cursor: "pointer" }}>
      <div onClick={() => setOn(!on)} style={{
        flexShrink: 0, marginTop: 2,
        width: 36, height: 20, borderRadius: 999,
        background: on ? "var(--cand-red)" : "var(--line-2)",
        position: "relative", transition: "background 0.15s",
      }}>
        <div style={{
          position: "absolute", top: 2, left: on ? 18 : 2,
          width: 16, height: 16, borderRadius: "50%", background: "#fff",
          transition: "left 0.15s", boxShadow: "0 1px 2px rgba(0,0,0,0.2)",
        }}></div>
      </div>
      <div>
        <div style={{ fontWeight: 600, fontSize: 13 }}>{label}</div>
        <div style={{ fontSize: 12, color: "var(--ink-500)" }}>{hint}</div>
      </div>
    </label>
  );
}

function ResultStat({ color, icon, label, value }) {
  return (
    <div style={{ padding: 14, border: "1px solid var(--line)", borderRadius: 10, background: "var(--paper)", display: "flex", gap: 12, alignItems: "center" }}>
      <div style={{ width: 40, height: 40, borderRadius: 10, background: color + "22", color, display: "grid", placeItems: "center" }}>
        <Ic_I name={icon} fill style={{ fontSize: 22 }} />
      </div>
      <div>
        <div style={{ fontSize: 10.5, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--ink-500)", fontWeight: 700 }}>{label}</div>
        <div style={{ fontSize: 22, fontWeight: 700, lineHeight: 1.1, fontVariantNumeric: "tabular-nums" }}>{value}</div>
      </div>
    </div>
  );
}

function ErrRow({ row, sheet, cccd, name, type, msg }) {
  return (
    <tr>
      <td className="mono"><strong>#{row}</strong></td>
      <td><span className="pill pill-gray">{sheet}</span></td>
      <td className="mono">{cccd || "—"}</td>
      <td>{name || "—"}</td>
      <td>
        {type === "error"
          ? <span className="pill pill-red"><Ic_I name="error" style={{ fontSize: 12 }} />Lỗi</span>
          : <span className="pill pill-gold"><Ic_I name="warning" style={{ fontSize: 12 }} />Cảnh báo</span>}
      </td>
      <td style={{ color: type === "error" ? "var(--cand-red-deep)" : "var(--ink-700)" }}>{msg}</td>
    </tr>
  );
}

// ---- Rà soát danh sách (Fuzzy Match) ----
function RaSoatScreen() {
  const RESULTS = [
    { in_name: "Nguyen Thi Mai Huong", cccd: "025198003142", db_name: "NGUYỄN THỊ MAI HƯƠNG", score: 97, quality: "high" },
    { in_name: "Tran Van Bach",         cccd: "025193002671", db_name: "TRẦN VĂN BÁCH",         score: 95, quality: "high" },
    { in_name: "Hoàng Quốc Khai",       cccd: "088192004012", db_name: "HOÀNG QUỐC KHẢI",       score: 92, quality: "high" },
    { in_name: "Le Thi Kim Ngan",       cccd: "025198009127", db_name: "LÊ THỊ KIM NGÂN",       score: 91, quality: "high" },
    { in_name: "Phạm Hồng Nhung",       cccd: "025191005533", db_name: "PHẠM THỊ HỒNG NHUNG",   score: 88, quality: "medium" },
    { in_name: "Vũ Thắng",              cccd: "025187003311", db_name: "VŨ ĐỨC THẮNG",          score: 85, quality: "medium" },
    { in_name: "Đặng Linh",             cccd: "025199008820", db_name: "ĐẶNG THÙY LINH",        score: 82, quality: "medium" },
    { in_name: "Bui Cuong",             cccd: "025190007722", db_name: "BÙI VĂN CƯỜNG",         score: 81, quality: "medium" },
    { in_name: "Nguyễn Văn Tuấn Anh",   cccd: null,           db_name: null,                    score: 0,  quality: "none" },
    { in_name: "Trần Hữu Thuần",        cccd: null,           db_name: null,                    score: 0,  quality: "none" },
    { in_name: "Đào Phương",            cccd: "025194002112", db_name: "ĐÀO PHƯƠNG THẢO",       score: 76, quality: "low" },
  ];

  const counts = {
    high: RESULTS.filter(r => r.quality === "high").length,
    medium: RESULTS.filter(r => r.quality === "medium").length,
    low: RESULTS.filter(r => r.quality === "low").length,
    none: RESULTS.filter(r => r.quality === "none").length,
  };

  return (
    <>
      <PH_I
        eyebrow="Đối chiếu"
        title="Rà soát danh sách bên ngoài"
        sub="Đối chiếu danh sách họ tên bên ngoài với toàn bộ đối tượng đã hoàn tất trong CSDL (Fuzzy matching, ngưỡng 80%)"
      />

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-tile">
          <div className="stat-tile__label"><Ic_I name="list_alt" /> Tổng đầu vào</div>
          <div className="stat-tile__value">{RESULTS.length}</div>
          <div className="stat-tile__delta">Từ file <strong style={{ color: "var(--ink-900)" }}>ds_dau_vao.xlsx</strong></div>
        </div>
        <div className="stat-tile">
          <div className="stat-tile__label"><Ic_I name="verified" /> Khớp cao (≥90%)</div>
          <div className="stat-tile__value" style={{ color: "var(--cand-green-deep)" }}>{counts.high}</div>
          <div className="stat-tile__delta">Có thể tự động liên kết</div>
        </div>
        <div className="stat-tile">
          <div className="stat-tile__label"><Ic_I name="warning" /> Khớp trung bình (80–89%)</div>
          <div className="stat-tile__value" style={{ color: "#7A5A12" }}>{counts.medium}</div>
          <div className="stat-tile__delta">Cần cán bộ xác nhận thủ công</div>
        </div>
        <div className="stat-tile">
          <div className="stat-tile__label"><Ic_I name="search_off" /> Không tìm thấy</div>
          <div className="stat-tile__value" style={{ color: "var(--cand-red)" }}>{counts.none + counts.low}</div>
          <div className="stat-tile__delta">Có thể là đối tượng mới</div>
        </div>
      </div>

      <div className="card">
        <div className="card__head">
          <h3><Ic_I name="fact_check" /> Kết quả khớp tên</h3>
          <div style={{ display: "flex", gap: 6 }}>
            <button className="btn btn-secondary btn-sm"><Ic_I name="filter_list" /> Lọc</button>
            <button className="btn btn-secondary btn-sm"><Ic_I name="file_download" /> Xuất Excel</button>
          </div>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table className="tbl">
            <thead>
              <tr>
                <th>Tên đầu vào</th>
                <th>Khớp với (trong CSDL)</th>
                <th>CCCD</th>
                <th>Điểm khớp</th>
                <th>Chất lượng</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {RESULTS.map((r, i) => (
                <tr key={i}>
                  <td><strong>{r.in_name}</strong></td>
                  <td>{r.db_name ? <span style={{ color: "var(--ink-900)" }}>{r.db_name}</span> : <span style={{ color: "var(--ink-500)" }}>— Không tìm thấy —</span>}</td>
                  <td className="mono">{r.cccd || "—"}</td>
                  <td>
                    {r.score > 0 ? (
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ width: 90, height: 6, background: "var(--paper-2)", borderRadius: 999, overflow: "hidden" }}>
                          <div style={{ width: `${r.score}%`, height: "100%",
                                        background: r.quality === "high" ? "var(--cand-green)" : r.quality === "medium" ? "var(--cand-gold)" : "var(--cand-red)" }}></div>
                        </div>
                        <span style={{ fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>{r.score}</span>
                      </div>
                    ) : "—"}
                  </td>
                  <td>
                    {r.quality === "high"   && <span className="pill pill-green"><span className="dot"></span>Cao</span>}
                    {r.quality === "medium" && <span className="pill pill-gold"><span className="dot"></span>Trung bình</span>}
                    {r.quality === "low"    && <span className="pill pill-red"><span className="dot"></span>Thấp</span>}
                    {r.quality === "none"   && <span className="pill pill-gray"><span className="dot"></span>Không khớp</span>}
                  </td>
                  <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                    {r.quality === "none" ? (
                      <button className="btn btn-secondary btn-xs"><Ic_I name="person_add" /> Tạo mới</button>
                    ) : (
                      <button className="btn btn-ghost btn-xs">Mở hồ sơ <Ic_I name="arrow_forward" style={{ fontSize: 14 }} /></button>
                    )}
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

window.VCFEInput = { NhapLieuScreen, NhapExcelScreen, RaSoatScreen };
