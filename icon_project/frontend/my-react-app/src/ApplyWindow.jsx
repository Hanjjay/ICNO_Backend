// ApplyWindow.jsx - Discord 스타일 커스텀 아이콘 관리 UI
import { useState, useEffect, useRef } from "react";

const API = "http://localhost:8000";

// ── 색상 팔레트 ──────────────────────────────────────────────
const COLORS = [
  "#ffffff","#000000","#ff6b6b","#ffd93d","#6bcb77","#4d96ff",
  "#c77dff","#ff9f43","#00d2d3","#ff6b9d","#a29bfe","#fd79a8",
];

const POPULAR_FONTS = [
  "맑은 고딕","나눔고딕","나눔바른고딕","굴림","돋움","바탕",
  "Segoe UI","Arial","Verdana","Impact","Georgia","Comic Sans MS",
  "Tahoma","Trebuchet MS","Courier New",
];

// ── 유틸 ────────────────────────────────────────────────────
const api = (path, opt) => fetch(API + path, opt).then(r => r.json());

// ── 아이콘 수정 모달 ────────────────────────────────────────
function EditModal({ mapping, images, onClose, onUpdated, isActive }) {
  const [imgList,      setImgList]      = useState(images);
  const [selectedImg,  setSelectedImg]  = useState(
    images.find(i => i.path === mapping.image_path) ?? null
  );
  const [uploading,    setUploading]    = useState(false);
  const [iconName,     setIconName]     = useState(mapping.name ?? "");
  const [iconSize,     setIconSize]     = useState(mapping.size ?? 80);
  const [useHover,     setUseHover]     = useState(!!(mapping.hover_image_path));
  const [hoverImg,     setHoverImg]     = useState(
    images.find(i => i.path === mapping.hover_image_path) ?? null);
  const [showName,     setShowName]     = useState(mapping.show_name ?? true);
  const [fontFamily,   setFontFamily]   = useState(mapping.font_family ?? "맑은 고딕");
  const [fontSize,     setFontSize]     = useState(mapping.font_size ?? 10);
  const [fontBold,     setFontBold]     = useState(mapping.font_bold ?? true);
  const [fontItalic,   setFontItalic]   = useState(mapping.font_italic ?? false);
  const [fontColor,    setFontColor]    = useState(mapping.font_color ?? "#ffffff");
  const [outlineColor, setOutlineColor] = useState(mapping.outline_color ?? "#000000");
  const [saving,       setSaving]       = useState(false);
  const imgRef = useRef();

  async function uploadImage(file) {
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch(`${API}/api/icons/upload`, { method: "POST", body: fd });
      const data = await res.json();
      if (data.success) {
        const refreshed = await api("/api/icons/images");
        const newList = refreshed.images ?? [];
        setImgList(newList);
        const found = newList.find(i => i.filename === data.filename);
        if (found) setSelectedImg(found);
      }
    } finally { setUploading(false); }
  }

  async function handleUpdate() {
    setSaving(true);
    try {
      await api(`/api/icons/mapping/${mapping.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name:          iconName,
          image_path:    selectedImg?.path ?? mapping.image_path,
          target_path:   mapping.target_path ?? "",
          size:              Math.min(512, Math.max(40, iconSize || 80)),
          hover_image_path:  hoverImg?.path ?? "",
          show_name:         showName,
          font_family:   fontFamily,
          font_size:     fontSize,
          font_bold:     fontBold,
          font_italic:   fontItalic,
          font_color:    fontColor,
          outline_color: outlineColor,
        }),
      });
      await onUpdated();   // 데이터 갱신 완료 후 닫기
      onClose();
    } finally { setSaving(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
         onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="bg-[#282a36] rounded-2xl w-[820px] max-h-[88vh] flex flex-col
                      shadow-2xl border border-white/10 overflow-hidden">

        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div>
            <h2 className="text-white text-lg font-bold">아이콘 수정</h2>
            <p className="text-white/40 text-sm mt-0.5">"{mapping.name}" 설정 변경</p>
          </div>
          <button onClick={onClose} className="text-white/40 hover:text-white text-2xl">×</button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* 왼쪽: 편집 폼 */}
          <div className="flex-1 overflow-y-auto p-6 space-y-5">

            {/* 이름 */}
            <div>
              <label className="text-white/60 text-xs mb-1 block">아이콘 이름</label>
              <input value={iconName} onChange={e => setIconName(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl
                           px-4 py-2.5 text-white text-sm outline-none
                           focus:border-indigo-400 transition-all" />
            </div>

            {/* 이미지 선택 */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-white/60 text-xs">커스텀 이미지</label>
                <button disabled={uploading} onClick={() => imgRef.current.click()}
                  className="px-3 py-1 bg-indigo-500 hover:bg-indigo-600 text-white
                             text-xs rounded-lg transition-all disabled:opacity-50">
                  {uploading ? "업로드 중..." : "📁 업로드"}
                </button>
                <input ref={imgRef} type="file" accept=".png,.jpg,.jpeg,.gif"
                  className="hidden" onChange={e => {
                    if (e.target.files[0]) uploadImage(e.target.files[0]);
                  }} />
              </div>
              <div className="grid grid-cols-4 gap-2 max-h-40 overflow-y-auto">
                {imgList.map(img => (
                  <button key={img.filename} onClick={() => setSelectedImg(img)}
                    className={`relative rounded-xl overflow-hidden aspect-square border-2 transition-all
                      ${selectedImg?.filename === img.filename
                        ? "border-indigo-400 ring-2 ring-indigo-400/40"
                        : "border-transparent hover:border-white/30"}`}>
                    <img src={`${API}${img.url}`} className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            </div>

            {/* 아이콘 크기 */}
            <div>
              <label className="text-white/60 text-xs mb-1 block">
                아이콘 크기: <span className="text-white font-bold">{iconSize}px</span>
              </label>
              <div className="flex items-center gap-3">
                <span className="text-white/30 text-xs">40</span>
                <input type="range" min={40} max={512} value={iconSize}
                  onChange={e => setIconSize(+e.target.value)}
                  className="flex-1 accent-indigo-400 h-1.5" />
                <span className="text-white/30 text-xs">512</span>
                <input type="number" min={40} max={512} value={iconSize}
                  onChange={e => setIconSize(+e.target.value || 40)}
                  onBlur={e => setIconSize(Math.min(512, Math.max(40, +e.target.value || 40)))}
                  className="w-14 bg-white/5 border border-white/10 rounded-lg px-2 py-1
                             text-white text-xs text-center outline-none focus:border-indigo-400" />
              </div>
            </div>

            {/* 이름 표시 */}
            <label className="flex items-center gap-3 cursor-pointer">
              <div onClick={() => setShowName(v => !v)}
                className={`w-11 h-6 rounded-full transition-all relative
                  ${showName ? "bg-indigo-500" : "bg-white/20"}`}>
                <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-all
                  ${showName ? "left-5" : "left-0.5"}`} />
              </div>
              <span className="text-white/70 text-sm">이름 표시</span>
            </label>

            {showName && (<>
              {/* 폰트 */}
              <div>
                <label className="text-white/60 text-xs mb-1 block">폰트</label>
                <select value={fontFamily} onChange={e => setFontFamily(e.target.value)}
                  style={{ fontFamily }}
                  className="w-full bg-[#1e1f2e] border border-white/10 rounded-xl
                             px-4 py-2.5 text-white text-sm outline-none focus:border-indigo-400">
                  {POPULAR_FONTS.map(f => (
                    <option key={f} value={f} style={{ fontFamily: f }}>{f}</option>
                  ))}
                </select>
              </div>

              {/* 크기 + 스타일 */}
              <div className="flex gap-3 items-end">
                <div className="flex-1">
                  <label className="text-white/60 text-xs mb-1 block">크기: {fontSize}pt</label>
                  <input type="range" min={7} max={28} value={fontSize}
                    onChange={e => setFontSize(+e.target.value)}
                    className="w-full accent-indigo-400" />
                </div>
                <div className="flex gap-2 pb-1">
                  <button onClick={() => setFontBold(v => !v)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-bold transition-all
                      ${fontBold ? "bg-indigo-500 text-white" : "bg-white/10 text-white/50"}`}>B</button>
                  <button onClick={() => setFontItalic(v => !v)}
                    className={`px-3 py-1.5 rounded-lg text-sm italic transition-all
                      ${fontItalic ? "bg-indigo-500 text-white" : "bg-white/10 text-white/50"}`}>I</button>
                </div>
              </div>

              {/* 색상 */}
              {[
                { label: "글자색", val: fontColor, set: setFontColor },
                { label: "외곽선색", val: outlineColor, set: setOutlineColor },
              ].map(({ label, val, set }) => (
                <div key={label}>
                  <label className="text-white/60 text-xs mb-2 block">{label}</label>
                  <div className="flex flex-wrap gap-2">
                    {COLORS.map(c => (
                      <button key={c} onClick={() => set(c)} style={{ background: c }}
                        className={`w-7 h-7 rounded-lg border-2 transition-all
                          ${val === c ? "border-indigo-400 scale-110" : "border-transparent"}`} />
                    ))}
                    <label className="w-7 h-7 rounded-lg border-2 border-white/20 cursor-pointer overflow-hidden">
                      <input type="color" value={val} onChange={e => set(e.target.value)}
                        className="w-full h-full opacity-0 cursor-pointer" />
                      <div style={{ background: val }} className="w-full h-full -mt-7" />
                    </label>
                  </div>
                </div>
              ))}
            </>)}
          </div>

          {/* 미리보기 */}
          <div className="w-44 border-l border-white/10 flex flex-col items-center
                          justify-center gap-3 p-4 bg-[#1a1b27]">
            <p className="text-white/30 text-xs">미리보기</p>
            <div className="flex flex-col items-center gap-2 p-3 bg-[#1e1f2e]
                            rounded-xl border border-white/10">
              {selectedImg
                ? <img src={`${API}${selectedImg.url}`}
                       style={{ width: Math.min(iconSize, 200), height: Math.min(iconSize, 200), objectFit: 'contain' }}
                       className="rounded-lg" />
                : <div style={{ width: Math.min(iconSize, 200), height: Math.min(iconSize, 200) }}
                       className="rounded-lg bg-white/10" />}
              {showName && (
                <span style={{
                  fontFamily, fontSize: fontSize + "pt",
                  fontWeight: fontBold ? "bold" : "normal",
                  fontStyle: fontItalic ? "italic" : "normal",
                  color: fontColor,
                  textShadow: `-1px -1px 0 ${outlineColor}, 1px -1px 0 ${outlineColor},
                               -1px 1px 0 ${outlineColor}, 1px 1px 0 ${outlineColor}`,
                }} className="text-center max-w-[100px] break-words text-sm">
                  {iconName || mapping.name}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* 푸터 */}
        <div className="flex justify-between px-6 py-4 border-t border-white/10">
          <button onClick={onClose}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-sm rounded-xl">
            취소
          </button>
          <button onClick={handleUpdate} disabled={saving}
            className="px-6 py-2 bg-indigo-500 hover:bg-indigo-600 text-white
                       text-sm font-medium rounded-xl transition-all disabled:opacity-50">
            {saving ? "저장 중..." : "✅ 수정 완료"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── 상세 생성 모달 ──────────────────────────────────────────
function CreateModal({ desktopIcons, images, onClose, onCreated, isActive }) {
  const [step, setStep] = useState(1);           // 1:아이콘선택 2:이미지 3:스타일
  const [selectedIcon, setSelectedIcon] = useState(null);
  const [customFile,   setCustomFile]   = useState(null); // 직접 선택 파일
  const [selectedImg,  setSelectedImg]  = useState(null);
  const [imgList,      setImgList]      = useState(images);
  const [uploading,    setUploading]    = useState(false);
  const [fontFamily,   setFontFamily]   = useState("맑은 고딕");
  const [fontSize,     setFontSize]     = useState(10);
  const [fontBold,     setFontBold]     = useState(true);
  const [fontItalic,   setFontItalic]   = useState(false);
  const [fontColor,    setFontColor]    = useState("#ffffff");
  const [outlineColor, setOutlineColor] = useState("#000000");
  const [iconSize,     setIconSize]     = useState(80);
  const [useHover,     setUseHover]     = useState(false);
  const [hoverImg,     setHoverImg]     = useState(null);
  const [showName,     setShowName]     = useState(true);
  const [iconName,     setIconName]     = useState("");
  const [saving,       setSaving]       = useState(false);
  const fileRef  = useRef();
  const imgRef   = useRef();
  const hoverRef = useRef();

  const targetName = customFile
    ? customFile.name.replace(/\.[^.]+$/, "")
    : selectedIcon?.name ?? "";

  // iconName은 클릭 시 직접 설정 (useEffect 대신)

  // 이미지 업로드
  async function uploadImage(file) {
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch(`${API}/api/icons/upload`, { method: "POST", body: fd });
      const data = await res.json();
      if (data.success) {
        const refreshed = await api("/api/icons/images");
        const newList = refreshed.images ?? [];
        setImgList(newList);
        const found = newList.find(i => i.filename === data.filename);
        if (found) setSelectedImg(found);
      }
    } finally {
      setUploading(false);
    }
  }

  // 저장
  async function handleSave() {
    if (!selectedImg) return;
    setSaving(true);
    try {
      const res = await api("/api/icons/mapping", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          icon_name:     iconName || targetName || "아이콘",
          image_path:    selectedImg.path,
          target_path:   customFile ? customFile._path ?? "" : (selectedIcon?.target_path ?? ""),
          x: 100, y: 100,
          size:              Math.min(512, Math.max(40, iconSize || 80)),
          hover_image_path:  hoverImg?.path ?? "",
          show_name:         showName,
          font_family:   fontFamily,
          font_size:     fontSize,
          font_bold:     fontBold,
          font_italic:   fontItalic,
          font_color:    fontColor,
          outline_color: outlineColor,
        }),
      });

      await onCreated();   // 데이터 갱신 완료 후 닫기
      onClose();
    } finally {
      setSaving(false);
    }
  }

  const canNext1 = selectedIcon || customFile;
  const canNext2 = !!selectedImg;

  // ── 미리보기 ────────────────────────────────────────────
  const Preview = () => (
    <div className="flex flex-col items-center gap-2 p-4
                    bg-[#1e1f2e] rounded-xl border border-white/10 min-w-[120px]">
      {selectedImg
        ? <img src={`${API}${selectedImg.url}`}
               style={{ width: iconSize, height: iconSize, objectFit: 'contain' }}
               className="rounded-lg" />
        : <div style={{ width: iconSize, height: iconSize }}
               className="rounded-lg bg-white/10 flex items-center justify-center text-white/30 text-2xl">?</div>}
      {showName && (
        <span style={{
          fontFamily, fontSize: fontSize + "pt",
          fontWeight: fontBold ? "bold" : "normal",
          fontStyle: fontItalic ? "italic" : "normal",
          color: fontColor,
          textShadow: `
            -1px -1px 0 ${outlineColor}, 1px -1px 0 ${outlineColor},
            -1px  1px 0 ${outlineColor}, 1px  1px 0 ${outlineColor}`,
        }} className="text-center max-w-[110px] break-words">
          {iconName || targetName || "이름"}
        </span>
      )}
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
         onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="bg-[#282a36] rounded-2xl w-[820px] max-h-[88vh] flex flex-col
                      shadow-2xl border border-white/10 overflow-hidden">

        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4
                        border-b border-white/10">
          <div>
            <h2 className="text-white text-lg font-bold">새 커스텀 아이콘</h2>
            <p className="text-white/40 text-sm mt-0.5">
              {step === 1 && "어떤 프로그램에 적용할까요?"}
              {step === 2 && "사용할 이미지를 선택하세요"}
              {step === 3 && "텍스트 스타일을 설정하세요"}
            </p>
          </div>
          {/* 스텝 인디케이터 */}
          <div className="flex items-center gap-2">
            {[1,2,3].map(s => (
              <div key={s} className={`w-8 h-8 rounded-full flex items-center
                justify-center text-sm font-bold transition-all
                ${s < step ? "bg-indigo-500 text-white"
                  : s === step ? "bg-indigo-500 text-white ring-4 ring-indigo-500/30"
                  : "bg-white/10 text-white/40"}`}>
                {s < step ? "✓" : s}
              </div>
            ))}
          </div>
          <button onClick={onClose}
                  className="text-white/40 hover:text-white text-2xl leading-none">×</button>
        </div>

        {/* 바디 */}
        <div className="flex flex-1 overflow-hidden">
          {/* 메인 콘텐츠 */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">

            {/* STEP 1: 대상 선택 */}
            {step === 1 && (<>
              <p className="text-white/60 text-sm">바탕화면 아이콘에서 선택하거나 직접 파일을 지정하세요.</p>

              {/* 직접 파일 선택 버튼 */}
              <button
                onClick={async () => {
                  const res = await api("/api/icons/pick-file");
                  if (res.file_path) {
                    setCustomFile({ name: res.name, _path: res.file_path });
                    setSelectedIcon(null);
                    setIconName(res.name);
                  }
                }}
                className={`w-full py-3 rounded-xl border-2 border-dashed text-sm
                  font-medium transition-all
                  ${customFile
                    ? "border-indigo-400 bg-indigo-500/10 text-indigo-300"
                    : "border-white/20 text-white/50 hover:border-indigo-400 hover:text-white"}`}>
                {customFile ? `✅ ${customFile.name}` : "📂 파일 직접 선택 (exe, lnk 등)"}
              </button>

              {/* 바탕화면 아이콘 그리드 */}
              <p className="text-white/40 text-xs pt-2">또는 바탕화면 아이콘 선택:</p>
              <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-1">
                {desktopIcons.map(icon => (
                  <button key={icon.path}
                    onClick={() => {
                    setSelectedIcon(icon);
                    setCustomFile(null);
                    setIconName(icon.name);   // 선택 바꾸면 이름도 즉시 반영
                  }}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl
                      text-left text-sm transition-all
                      ${selectedIcon?.path === icon.path
                        ? "bg-indigo-500 text-white"
                        : "bg-white/5 hover:bg-white/10 text-white/70"}`}>
                    <span className="text-lg">🖥️</span>
                    <span className="truncate">{icon.name}</span>
                  </button>
                ))}
              </div>
            </>)}

            {/* STEP 2: 이미지 선택 */}
            {step === 2 && (<>
              <div className="flex gap-2">
                <button
                  disabled={uploading}
                  onClick={() => imgRef.current.click()}
                  className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600
                    text-white text-sm rounded-xl font-medium transition-all
                    disabled:opacity-50">
                  {uploading ? "업로드 중..." : "📁 이미지 업로드"}
                </button>
                <input ref={imgRef} type="file" accept=".png,.jpg,.jpeg,.gif"
                  className="hidden" onChange={e => {
                    if (e.target.files[0]) uploadImage(e.target.files[0]);
                  }} />
              </div>

              <div className="grid grid-cols-3 gap-3 max-h-72 overflow-y-auto pr-1">
                {imgList.map(img => (
                  <button key={img.filename}
                    onClick={() => setSelectedImg(img)}
                    className={`relative rounded-xl overflow-hidden aspect-square
                      border-2 transition-all
                      ${selectedImg?.filename === img.filename
                        ? "border-indigo-400 ring-2 ring-indigo-400/40"
                        : "border-transparent hover:border-white/30"}`}>
                    <img src={`${API}${img.url}`}
                      className="w-full h-full object-cover" />
                    {img.filename.toLowerCase().endsWith('.gif') && (
                      <span className="absolute top-1 right-1 bg-black/60 text-white
                                       text-[9px] px-1 rounded">GIF</span>
                    )}
                  </button>
                ))}
                {imgList.length === 0 && (
                  <div className="col-span-3 text-center py-10 text-white/30 text-sm">
                    업로드된 이미지가 없어요
                  </div>
                )}
              </div>

              {/* 반응형 아이콘 (호버 이미지) 토글 */}
              <div className="border-t border-white/10 pt-4">
                <label className="flex items-center gap-3 cursor-pointer mb-3">
                  <div onClick={() => { setUseHover(v => !v); if (useHover) setHoverImg(null); }}
                    className={`w-11 h-6 rounded-full transition-all relative
                      ${useHover ? "bg-indigo-500" : "bg-white/20"}`}>
                    <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-all
                      ${useHover ? "left-5" : "left-0.5"}`} />
                  </div>
                  <div>
                    <span className="text-white/80 text-sm font-medium">반응형 아이콘</span>
                    <span className="text-white/30 text-xs ml-2">마우스 올리면 다른 이미지 표시</span>
                  </div>
                </label>

                {useHover && (<>
                  <p className="text-white/50 text-xs mb-2">호버 이미지 선택 (GIF 가능)</p>
                  <div className="flex gap-2 mb-2">
                    <button disabled={uploading}
                      onClick={() => hoverRef.current.click()}
                      className="px-3 py-1.5 bg-indigo-500/30 hover:bg-indigo-500/50
                                 text-indigo-300 text-xs rounded-lg transition-all">
                      📁 호버 이미지 업로드
                    </button>
                    <input ref={hoverRef} type="file" accept=".png,.jpg,.jpeg,.gif"
                      className="hidden" onChange={async e => {
                        if (!e.target.files[0]) return;
                        const fd = new FormData();
                        fd.append("file", e.target.files[0]);
                        const res = await fetch(`${API}/api/icons/upload`, { method:"POST", body:fd });
                        const data = await res.json();
                        if (data.success) {
                          const r = await api("/api/icons/images");
                          const found = (r.images??[]).find(i => i.filename === data.filename);
                          if (found) setHoverImg(found);
                        }
                      }} />
                  </div>
                  <div className="grid grid-cols-3 gap-2 max-h-36 overflow-y-auto">
                    {imgList.map(img => (
                      <button key={img.filename} onClick={() => setHoverImg(img)}
                        className={`relative rounded-xl overflow-hidden aspect-square border-2 transition-all
                          ${hoverImg?.filename === img.filename
                            ? "border-indigo-400 ring-2 ring-indigo-400/40"
                            : "border-transparent hover:border-white/30"}`}>
                        <img src={`${API}${img.url}`} className="w-full h-full object-cover" />
                        {img.filename.toLowerCase().endsWith('.gif') && (
                          <span className="absolute top-1 right-1 bg-black/60 text-white
                                           text-[9px] px-1 rounded">GIF</span>
                        )}
                      </button>
                    ))}
                  </div>
                  {hoverImg && (
                    <p className="text-indigo-300 text-xs mt-2">
                      ✅ 호버: {hoverImg.filename}
                    </p>
                  )}
                </>)}
              </div>
            </>)}

            {/* STEP 3: 텍스트 스타일 */}
            {step === 3 && (<>
              {/* 이름 */}
              <div>
                <label className="text-white/60 text-xs mb-1 block">아이콘 이름</label>
                <input value={iconName} onChange={e => setIconName(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl
                             px-4 py-2.5 text-white text-sm outline-none
                             focus:border-indigo-400 transition-all"
                  placeholder="이름을 입력하세요" />
              </div>

              {/* 아이콘 크기 */}
              <div>
                <label className="text-white/60 text-xs mb-1 block">
                  아이콘 크기: <span className="text-white font-bold">{iconSize}px</span>
                </label>
                <div className="flex items-center gap-3">
                  <span className="text-white/30 text-xs">40</span>
                  <input type="range" min={40} max={512} value={iconSize}
                    onChange={e => setIconSize(+e.target.value)}
                    className="flex-1 accent-indigo-400 h-1.5" />
                  <span className="text-white/30 text-xs">512</span>
                  <input type="number" min={40} max={512} value={iconSize}
                    onChange={e => setIconSize(+e.target.value || 40)}
                    onBlur={e => setIconSize(Math.min(512, Math.max(40, +e.target.value || 40)))}
                    className="w-14 bg-white/5 border border-white/10 rounded-lg px-2 py-1
                               text-white text-xs text-center outline-none focus:border-indigo-400" />
                </div>
              </div>

              {/* 이름 표시 토글 */}
              <label className="flex items-center gap-3 cursor-pointer">
                <div onClick={() => setShowName(v => !v)}
                  className={`w-11 h-6 rounded-full transition-all relative
                    ${showName ? "bg-indigo-500" : "bg-white/20"}`}>
                  <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5
                    transition-all ${showName ? "left-5" : "left-0.5"}`} />
                </div>
                <span className="text-white/70 text-sm">이름 표시</span>
              </label>

              {showName && (<>
                {/* 폰트 패밀리 */}
                <div>
                  <label className="text-white/60 text-xs mb-1 block">폰트</label>
                  <select value={fontFamily} onChange={e => setFontFamily(e.target.value)}
                    style={{ fontFamily }}
                    className="w-full bg-[#1e1f2e] border border-white/10 rounded-xl
                               px-4 py-2.5 text-white text-sm outline-none
                               focus:border-indigo-400 transition-all">
                    {POPULAR_FONTS.map(f => (
                      <option key={f} value={f} style={{ fontFamily: f }}>{f}</option>
                    ))}
                  </select>
                </div>

                {/* 크기 + 스타일 */}
                <div className="flex gap-3">
                  <div className="flex-1">
                    <label className="text-white/60 text-xs mb-1 block">크기 (pt)</label>
                    <div className="flex items-center gap-2">
                      <input type="range" min={7} max={28} value={fontSize}
                        onChange={e => setFontSize(+e.target.value)}
                        className="flex-1 accent-indigo-400" />
                      <span className="text-white text-sm w-6 text-right">{fontSize}</span>
                    </div>
                  </div>
                  <div className="flex gap-2 items-end pb-1">
                    <button onClick={() => setFontBold(v => !v)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-bold transition-all
                        ${fontBold ? "bg-indigo-500 text-white" : "bg-white/10 text-white/50"}`}>
                      B
                    </button>
                    <button onClick={() => setFontItalic(v => !v)}
                      className={`px-3 py-1.5 rounded-lg text-sm italic transition-all
                        ${fontItalic ? "bg-indigo-500 text-white" : "bg-white/10 text-white/50"}`}>
                      I
                    </button>
                  </div>
                </div>

                {/* 글자색 */}
                <div>
                  <label className="text-white/60 text-xs mb-2 block">글자색</label>
                  <div className="flex flex-wrap gap-2">
                    {COLORS.map(c => (
                      <button key={c} onClick={() => setFontColor(c)}
                        style={{ background: c }}
                        className={`w-7 h-7 rounded-lg border-2 transition-all
                          ${fontColor === c ? "border-indigo-400 scale-110"
                                           : "border-transparent"}`} />
                    ))}
                    <label className="w-7 h-7 rounded-lg border-2 border-white/20
                                      cursor-pointer overflow-hidden">
                      <input type="color" value={fontColor}
                        onChange={e => setFontColor(e.target.value)}
                        className="w-full h-full opacity-0 cursor-pointer" />
                      <div style={{ background: fontColor }}
                           className="w-full h-full -mt-7" />
                    </label>
                  </div>
                </div>

                {/* 외곽선색 */}
                <div>
                  <label className="text-white/60 text-xs mb-2 block">외곽선색</label>
                  <div className="flex flex-wrap gap-2">
                    {COLORS.map(c => (
                      <button key={c} onClick={() => setOutlineColor(c)}
                        style={{ background: c }}
                        className={`w-7 h-7 rounded-lg border-2 transition-all
                          ${outlineColor === c ? "border-indigo-400 scale-110"
                                             : "border-transparent"}`} />
                    ))}
                    <label className="w-7 h-7 rounded-lg border-2 border-white/20
                                      cursor-pointer overflow-hidden">
                      <input type="color" value={outlineColor}
                        onChange={e => setOutlineColor(e.target.value)}
                        className="w-full h-full opacity-0 cursor-pointer" />
                      <div style={{ background: outlineColor }}
                           className="w-full h-full -mt-7" />
                    </label>
                  </div>
                </div>
              </>)}
            </>)}
          </div>

          {/* 오른쪽: 미리보기 */}
          <div className="w-48 border-l border-white/10 flex flex-col
                          items-center justify-center gap-4 p-4 bg-[#1a1b27]">
            <p className="text-white/30 text-xs">미리보기</p>
            <Preview />
          </div>
        </div>

        {/* 푸터 버튼 */}
        <div className="flex justify-between items-center px-6 py-4
                        border-t border-white/10">
          <button onClick={() => step > 1 ? setStep(s => s-1) : onClose()}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white
                       text-sm rounded-xl transition-all">
            {step === 1 ? "취소" : "← 이전"}
          </button>
          {step < 3
            ? <button
                disabled={step === 1 ? !canNext1 : !canNext2}
                onClick={() => setStep(s => s+1)}
                className="px-6 py-2 bg-indigo-500 hover:bg-indigo-600
                           text-white text-sm font-medium rounded-xl transition-all
                           disabled:opacity-30 disabled:cursor-not-allowed">
                다음 →
              </button>
            : <button
                disabled={saving}
                onClick={handleSave}
                className="px-6 py-2 bg-green-500 hover:bg-green-600
                           text-white text-sm font-medium rounded-xl transition-all
                           disabled:opacity-50">
                {saving ? "저장 중..." : "✅ 아이콘 추가"}
              </button>
          }
        </div>
      </div>
    </div>
  );
}

// ── 메인 컴포넌트 ────────────────────────────────────────────
export default function ApplyWindow() {
  const [isActive,   setIsActive]   = useState(false);
  const [mappings,   setMappings]   = useState([]);
  const [desktopIcons, setDesktopIcons] = useState([]);
  const [images,     setImages]     = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [status,     setStatus]     = useState({ msg: "연결 확인 중...", type: "idle" });
  const [loading,    setLoading]    = useState(false);
  const [gridMode,   setGridMode]   = useState(false);
  const [gridCellW,  setGridCellW]  = useState(110);
  const [gridCellH,  setGridCellH]  = useState(130);
  const [arranging,  setArranging]  = useState(false);
  const [editTarget, setEditTarget] = useState(null);  // 수정할 아이콘

  async function loadAll() {
    try {
      const [m, d, img, sett, ovStatus] = await Promise.all([
        api("/api/icons/mappings"),
        api("/api/icons/desktop"),
        api("/api/icons/images"),
        api("/api/settings"),
        api("/api/icons/overlay-status"),
      ]);
      setMappings(m.mappings ?? []);
      setDesktopIcons(d.icons ?? []);
      setImages(img.images ?? []);
      setGridMode(sett.mode === "grid");
      setGridCellW(sett.grid_cell_w ?? 110);
      setGridCellH(sett.grid_cell_h ?? 130);

      // ★ 오버레이 실제 실행 상태와 isActive 동기화
      const running = ovStatus.running ?? false;
      setIsActive(running);
      setStatus({
        msg: running ? "활성화됨 — 커스텀 아이콘 표시 중" : "백엔드 연결됨",
        type: running ? "ok" : "ok"
      });
    } catch {
      setStatus({ msg: "백엔드 연결 실패 — backend/main.py를 먼저 실행하세요", type: "err" });
    }
  }

  useEffect(() => { loadAll(); }, []);

  async function saveSettings(mode, cw, ch) {
    await api("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode, grid_cell_w: cw, grid_cell_h: ch, grid_cols: 0 }),
    });
    // 오버레이가 켜진 상태면 재시작해서 모드 즉시 반영
  }

  async function handleArrangeGrid() {
    setArranging(true);
    try {
      await api("/api/icons/arrange-grid", { method: "POST" });
      // 오버레이 켜진 상태면 반드시 재시작해서 새 위치 반영
      setStatus({ msg: "그리드 정렬 완료!", type: "ok" });
      loadAll();
    } finally {
      setArranging(false);
    }
  }

  async function handleModeToggle(newMode) {
    setGridMode(newMode === "grid");
    await saveSettings(newMode, gridCellW, gridCellH);
  }

  async function toggleOverlay() {
    setLoading(true);
    try {
      if (isActive) {
        await api("/api/icons/show-desktop", { method: "POST" });
        setIsActive(false);
        setStatus({ msg: "비활성화됨 — 원래 바탕화면 복구", type: "warn" });
      } else {
        await api("/api/icons/hide-desktop", { method: "POST" });
        await api("/api/icons/start-overlay", { method: "POST" });
        setIsActive(true);
        setStatus({ msg: "활성화됨 — 커스텀 아이콘 표시 중", type: "ok" });
      }
    } catch(e) {
      setStatus({ msg: "오류: " + e.message, type: "err" });
    } finally {
      setLoading(false);
    }
  }

  async function deleteMapping(id, name) {
    await api(`/api/icons/mapping/${id}`, { method: "DELETE" });
    setStatus({ msg: `'${name}' 삭제 완료`, type: "warn" });
    loadAll();
  }

  const statusStyle = {
    ok:   "bg-green-500/15 border-green-500/30 text-green-300",
    err:  "bg-red-500/15 border-red-500/30 text-red-300",
    warn: "bg-yellow-500/15 border-yellow-500/30 text-yellow-300",
    idle: "bg-white/5 border-white/10 text-white/50",
  }[status.type];

  return (
    <div className="min-h-screen bg-[#1e1f2e] text-white flex flex-col">

      {/* 헤더 */}
      <div className="flex items-center gap-3 px-6 py-4 bg-[#16171f]
                      border-b border-white/10">
        <span className="text-2xl">🎨</span>
        <h1 className="text-lg font-bold">커스텀 아이콘</h1>
        <span className="text-white/30 text-sm ml-1">바탕화면 커스터마이저</span>
        <div className="ml-auto flex items-center gap-3">
          {/* 상태 뱃지 */}
          <div className={`px-3 py-1 rounded-full text-xs border ${statusStyle}`}>
            {status.msg}
          </div>
          {/* 켜기/끄기 */}
          <button onClick={toggleOverlay} disabled={loading}
            className={`flex items-center gap-2 px-5 py-2 rounded-xl font-medium
              text-sm transition-all disabled:opacity-50
              ${isActive
                ? "bg-red-500 hover:bg-red-600 text-white"
                : "bg-indigo-500 hover:bg-indigo-600 text-white"}`}>
            {loading ? "⏳" : isActive ? "🔴 끄기" : "▶️ 켜기"}
          </button>
        </div>
      </div>

      {/* 바디 */}
      <div className="flex flex-1 overflow-hidden">

        {/* 사이드바: 현재 아이콘 목록 */}
        <div className="w-64 bg-[#16171f] border-r border-white/10
                        flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3
                          border-b border-white/10">
            <span className="text-white/60 text-xs font-semibold uppercase tracking-wider">
              현재 아이콘 ({mappings.length})
            </span>
          </div>
          <div className="flex-1 overflow-y-auto py-2">
            {mappings.length === 0 && (
              <div className="text-center py-10 text-white/20 text-sm">
                아이콘 없음
              </div>
            )}
            {mappings.map(m => (
              <div key={m.id}
                className="group flex items-center gap-3 px-4 py-2.5
                           hover:bg-white/5 transition-all cursor-pointer rounded-lg"
                onClick={() => setEditTarget(m)}>
                <div className="w-8 h-8 rounded-lg bg-white/10 overflow-hidden
                                flex-shrink-0 flex items-center justify-center">
                  {m.image_path
                    ? <img src={`${API}/custom_icons/${m.image_path.split(/[/\\]/).pop()}`}
                           className="w-full h-full object-cover" />
                    : <span className="text-lg">🖼️</span>}
                </div>
                <span className="flex-1 text-sm text-white/80 truncate">{m.name}</span>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100">
                  <span className="text-white/30 text-xs">수정</span>
                  <button
                    onClick={e => { e.stopPropagation(); deleteMapping(m.id, m.name); }}
                    className="text-white/30 hover:text-red-400 transition-all text-lg leading-none ml-1">
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* 새 아이콘 버튼 */}
          <div className="p-3 border-t border-white/10">
            <button onClick={() => setShowCreate(true)}
              className="w-full py-2.5 bg-indigo-500 hover:bg-indigo-600
                         text-white text-sm font-medium rounded-xl transition-all
                         flex items-center justify-center gap-2">
              <span className="text-lg leading-none">+</span>
              새 아이콘 추가
            </button>
          </div>
        </div>

        {/* 메인 영역 */}
        <div className="flex-1 flex flex-col items-center justify-center p-8 gap-6">
          {/* 활성화 상태 카드 */}
          <div className={`w-full max-w-md p-6 rounded-2xl border transition-all
            ${isActive
              ? "bg-green-500/10 border-green-500/30"
              : "bg-white/5 border-white/10"}`}>
            <div className="flex items-center gap-4">
              <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-3xl
                ${isActive ? "bg-green-500/20" : "bg-white/10"}`}>
                {isActive ? "✅" : "💤"}
              </div>
              <div>
                <p className="font-semibold text-white">
                  {isActive ? "오버레이 활성화됨" : "오버레이 꺼짐"}
                </p>
                <p className="text-white/40 text-sm mt-0.5">
                  {isActive
                    ? "바탕화면 숨김 + 커스텀 아이콘 표시 중"
                    : "켜기 버튼을 눌러 시작하세요"}
                </p>
              </div>
            </div>
          </div>

          {/* 통계 */}
          <div className="grid grid-cols-2 gap-4 w-full max-w-md">
            {[
              { label: "커스텀 아이콘", value: mappings.length, icon: "🖼️" },
              { label: "업로드 이미지", value: images.length,   icon: "📁" },
            ].map(s => (
              <div key={s.label}
                className="bg-white/5 border border-white/10 rounded-2xl p-4">
                <div className="text-2xl mb-1">{s.icon}</div>
                <div className="text-2xl font-bold text-white">{s.value}</div>
                <div className="text-white/40 text-sm">{s.label}</div>
              </div>
            ))}
          </div>

          <p className="text-white/20 text-sm text-center">
            왼쪽의 <strong className="text-white/40">+ 새 아이콘 추가</strong>를 눌러 시작하세요
          </p>

          {/* ── 배치 모드 패널 ── */}
          <div className="w-full max-w-md bg-white/5 border border-white/10
                          rounded-2xl p-5 space-y-4">
            <p className="text-white font-semibold text-sm">📐 배치 모드</p>

            {/* 모드 선택 토글 */}
            <div className="flex rounded-xl overflow-hidden border border-white/10">
              {[
                { id: "free", label: "🖱️ 자유 배치",  desc: "드래그로 자유롭게" },
                { id: "grid", label: "⊞ 그리드 정렬", desc: "격자에 맞춰 자동 스냅" },
              ].map(m => (
                <button key={m.id}
                  onClick={() => handleModeToggle(m.id)}
                  className={`flex-1 py-3 px-4 text-left transition-all
                    ${(m.id === "grid") === gridMode
                      ? "bg-indigo-500 text-white"
                      : "bg-transparent text-white/40 hover:text-white/70"}`}>
                  <div className="text-sm font-medium">{m.label}</div>
                  <div className="text-xs opacity-70 mt-0.5">{m.desc}</div>
                </button>
              ))}
            </div>

            {/* 그리드 세부 설정 */}
            {gridMode && (
              <div className="space-y-3 pt-1">
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: "셀 너비 (px)", val: gridCellW, set: setGridCellW, min: 80, max: 300 },
                    { label: "셀 높이 (px)", val: gridCellH, set: setGridCellH, min: 80, max: 300 },
                  ].map(({ label, val, set, min, max }) => (
                    <div key={label}>
                      <label className="text-white/50 text-xs mb-1 block">{label}</label>
                      <div className="flex items-center gap-2">
                        <input type="range" min={min} max={max} value={val}
                          onChange={e => set(+e.target.value)}
                          onMouseUp={() => saveSettings("grid", gridCellW, gridCellH)}
                          className="flex-1 accent-indigo-400 h-1" />
                        <span className="text-white text-xs w-8 text-right">{val}</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* 그리드 미리보기 */}
                <div className="bg-black/30 rounded-xl p-3 flex flex-wrap gap-1"
                     style={{ minHeight: 60 }}>
                  {Array.from({ length: Math.min(mappings.length, 12) }).map((_, i) => (
                    <div key={i}
                      style={{ width: Math.min(gridCellW * 0.25, 40),
                               height: Math.min(gridCellH * 0.25, 45) }}
                      className="bg-indigo-500/30 border border-indigo-400/40
                                 rounded flex flex-col items-center justify-center gap-0.5">
                      <div className="w-3 h-3 bg-indigo-400/60 rounded" />
                      <div className="w-4 h-0.5 bg-white/20 rounded" />
                    </div>
                  ))}
                  {mappings.length === 0 && (
                    <span className="text-white/20 text-xs self-center mx-auto">
                      아이콘을 추가하면 미리보기가 표시돼요
                    </span>
                  )}
                </div>

                {/* 지금 정렬 버튼 */}
                <button
                  disabled={arranging || mappings.length === 0}
                  onClick={handleArrangeGrid}
                  className="w-full py-2.5 bg-indigo-500 hover:bg-indigo-600
                             text-white text-sm font-medium rounded-xl transition-all
                             disabled:opacity-40 disabled:cursor-not-allowed
                             flex items-center justify-center gap-2">
                  {arranging ? "⏳ 정렬 중..." : "⊞ 지금 그리드에 맞춰 정렬"}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 상세 생성 모달 */}
      {editTarget && (
        <EditModal
          mapping={editTarget}
          images={images}
          onClose={() => setEditTarget(null)}
          onUpdated={loadAll}
          isActive={isActive}
        />
      )}

      {showCreate && (
        <CreateModal
          desktopIcons={desktopIcons}
          images={images}
          onClose={() => setShowCreate(false)}
          onCreated={loadAll}
          isActive={isActive}
        />
      )}
    </div>
  );
}
