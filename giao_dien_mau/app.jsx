// ============================================================
// VCFE — App root (routing, layout, login, tweaks)
// ============================================================
const { useState: useStateApp, useEffect: useEffectApp } = React;
const { TopBanner, Sidebar, LoginScreen, ToastRegion } = window.VCFEShell;
const { DashboardScreen } = window.VCFEDashboard;
const { DanhSachScreen, HoSoScreen, TraCuuScreen } = window.VCFERecords;
const { NhapLieuScreen, NhapExcelScreen, RaSoatScreen } = window.VCFEInput;
const { NetworkScreen, NhatKyScreen, UsersScreen, CaiDatScreen } = window.VCFESystem;

function App() {
  const [loggedIn, setLoggedIn] = useStateApp(true);
  const [route, setRoute] = useStateApp("dashboard");
  const [toasts, setToasts] = useStateApp([]);

  const user = {
    name: "Vi Ngọc Phương",
    rank: "Đại úy",
    role: "Quản trị cấp cao",
    initials: "VP",
  };

  function pushToast(t) {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, ...t }]);
    setTimeout(() => setToasts(prev => prev.filter(x => x.id !== id)), 3200);
  }

  // Tweaks integration
  const TweakDefaults = /*EDITMODE-BEGIN*/{
    "accentTone": "red",
    "showWatermark": true,
    "fontScale": 100
  }/*EDITMODE-END*/;
  const [tweaks, setTweak] = window.useTweaks(TweakDefaults);

  useEffectApp(() => {
    // Apply theme overrides
    const r = document.documentElement;
    if (tweaks.accentTone === "green") {
      r.style.setProperty("--cand-red", "#1F4936");
      r.style.setProperty("--cand-red-deep", "#14352A");
      r.style.setProperty("--cand-red-soft", "#E6EFE9");
    } else if (tweaks.accentTone === "gold") {
      r.style.setProperty("--cand-red", "#A06A12");
      r.style.setProperty("--cand-red-deep", "#7A4A05");
      r.style.setProperty("--cand-red-soft", "#FBF3DA");
    } else {
      r.style.setProperty("--cand-red", "#B91C1C");
      r.style.setProperty("--cand-red-deep", "#7F1212");
      r.style.setProperty("--cand-red-soft", "#FAE7E7");
    }
    document.documentElement.style.fontSize = (tweaks.fontScale || 100) + "%";

    // Watermark toggle
    const styleEl = document.getElementById("__wm-toggle") || (() => {
      const e = document.createElement("style"); e.id = "__wm-toggle"; document.head.appendChild(e); return e;
    })();
    styleEl.textContent = tweaks.showWatermark === false ? ".main::before { display: none; }" : "";
  }, [tweaks.accentTone, tweaks.showWatermark, tweaks.fontScale]);

  if (!loggedIn) {
    return <LoginScreen onLogin={() => setLoggedIn(true)} />;
  }

  return (
    <>
      <div className="app-shell">
        <TopBanner user={user} />
        <Sidebar current={route} onNav={(r) => setRoute(r)} />
        <main className="main">
          <div className="main__inner">
            {route === "dashboard"  && <DashboardScreen onNav={setRoute} />}
            {route === "danh-sach"  && <DanhSachScreen onNav={setRoute} />}
            {route === "ho-so"      && <HoSoScreen onNav={setRoute} />}
            {route === "tra-cuu"    && <TraCuuScreen />}
            {route === "mang-luoi"  && <NetworkScreen />}
            {route === "nhap-lieu"  && <NhapLieuScreen onToast={pushToast} />}
            {route === "nhap-excel" && <NhapExcelScreen onToast={pushToast} />}
            {route === "ra-soat"    && <RaSoatScreen />}
            {route === "nhat-ky"    && <NhatKyScreen />}
            {route === "users"      && <UsersScreen />}
            {route === "cai-dat"    && <CaiDatScreen />}
          </div>
        </main>
      </div>

      <ToastRegion toasts={toasts} />

      {window.TweaksPanel && (
        <window.TweaksPanel title="Tweaks">
          <window.TweakSection label="Tông màu chủ đạo" />
          <window.TweakRadio
            label="Accent"
            value={tweaks.accentTone}
            options={[
              { value: "red",   label: "Đỏ CAND" },
              { value: "green", label: "Xanh CAND" },
              { value: "gold",  label: "Vàng kim" },
            ]}
            onChange={(v) => setTweak("accentTone", v)}
          />
          <window.TweakSection label="Trang trí" />
          <window.TweakToggle
            label="Watermark trống đồng"
            value={tweaks.showWatermark}
            onChange={(v) => setTweak("showWatermark", v)}
          />
          <window.TweakSection label="Cỡ chữ tổng" />
          <window.TweakRadio
            label="Scale"
            value={tweaks.fontScale}
            options={[
              { value: 90,  label: "Nhỏ" },
              { value: 100, label: "Vừa" },
              { value: 110, label: "Lớn" },
            ]}
            onChange={(v) => setTweak("fontScale", v)}
          />
        </window.TweaksPanel>
      )}
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
