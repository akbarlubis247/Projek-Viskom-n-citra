/* ==========================================================================
   VISKOM // LAB-05 — FRONTEND CONTROLLER
   ========================================================================== */

let currentAnalysis = null;
let currentSourceImageUrl = null;
let lastUploadedBlob = null;
let grabLiveCameraBlobFn = null;
let userSelectedTeachClass = false;
let activeMatrixGroup = "ALL";
let activeSingleStage = "annotated";
let cameraStream = null;
let cameraDevices = [];
let currentDeviceIndex = 0;
let isCameraMirrored = false;
let liveLoopTimer = null;
let isLiveInFlight = false;
let isLiveCameraOpen = false;
let isLiveFrozen = false;
let vfSizePct = 74;

// State untuk Modal Bingkai Fokus Manual (Upload / Foto saat ini)
let cropState = {
  sizePct: 75,
  centerXRatio: 0.5, // relatif terhadap area gambar yang dirender (0..1)
  centerYRatio: 0.5,
  isDragging: false,
  dragOffsetX: 0,
  dragOffsetY: 0,
  liveDebounce: null,
};

const STAGE_EXPLANATIONS = {
  annotated: {
    code: "TAHAP 2.1 // DETEKSI GEOMETRI & KONTUR",
    title: "Deteksi Kontur Terbesar, Convex Hull & Bounding Box",
    desc: "Dari mask biner hasil operasi morfologi, sistem mengekstrak kontur eksternal terbesar (cv2.RETR_EXTERNAL). Garis hijau menunjukkan kontur objek, garis jingga menunjukkan selubung cembung (Convex Hull), dan kotak putih menunjukkan Bounding Box (ROI).",
  },
  mask: {
    code: "TAHAP 2.2 // SEGMENTASI OTSU & MORFOLOGI",
    title: "Binerisasi Adaptif Otsu & Pembersihan Morfologi",
    desc: "Citra dihaluskan dengan Gaussian Blur (5×5) lalu dibinerisasi menggunakan metode Otsu. Sistem mengecek piksel tepi frame untuk memastikan objek selalu bernilai putih (255) dan latar belakang hitam (0), kemudian membersihkan lubang/noise dengan Morfologi Close & Open.",
  },
  isolated: {
    code: "TAHAP 2.3 // ISOLASI OBJEK (BITWISE MASKING)",
    title: "Eliminasi Latar Belakang untuk Ekstraksi Warna Murni",
    desc: "Mask biner diaplikasikan ke citra warna (cv2.bitwise_and) sehingga warna meja, lantai, atau dinding kamar diabaikan sepenuhnya. Histogram HSV (32 bin) dan rata-rata CIE-LAB (6 fitur) hanya dihitung pada piksel objek yang terisolasi ini.",
  },
  edges: {
    code: "TAHAP 2.4 // TEPI CANNY & ROI TEKSTUR (128×128)",
    title: "Pemotongan Bounding Box & Deteksi Tepi Canny",
    desc: "Citra keabuan dipotong (crop) tepat pada Bounding Box objek dan dinormalisasi ke 128×128 piksel. Selanjutnya dihitung matriks tekstur GLCM serta deteksi tepi Canny (ambang 40, 120) untuk mengukur kerapatan lekukan, lipatan kertas, atau cetakan label kaleng.",
  },
  original: {
    code: "TAHAP 2.0 // CITRA INPUT STANDAR (256×256)",
    title: "Citra Input Ternormalisasi (256×256 Piksel)",
    desc: "Citra mentah diseragamkan dimensinya menjadi 256×256 piksel agar perhitungan skala luas, keliling, dan matriks ketetanggaan piksel bersifat konsisten di seluruh sampel.",
  },
};

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initViewSwitchers();
  initRedesignUI();
  initUploadAndCamera();
  initDatasetTeaching();
  initMatrixToolbar();
  bootstrapSystemInfo();
});

function setStatus(text, isBusy = false) {
  const el = document.getElementById("pipeline-status");
  if (!el) return;
  el.textContent = text;
  el.classList.toggle("busy", isBusy);
}

/* --------------------------------------------------------------------------
   1. INITIALIZE SYSTEM INFO & PRESET TRAY
   -------------------------------------------------------------------------- */
async function bootstrapSystemInfo() {
  try {
    const res = await fetch("/api/info");
    if (!res.ok) throw new Error("Gagal memuat info sistem");
    const info = await res.json();

    document.getElementById("hdr-model-spec").textContent =
      `KNN (k=${info.n_neighbors} · ${info.metric} · ${info.weights})`;
    document.getElementById("hdr-dataset-spec").textContent =
      `${info.training_samples.toLocaleString("id-ID")} Sampel × ${info.feature_dimensions}-D`;

    const tray = document.getElementById("sample-tray");
    tray.innerHTML = "";

    info.presets.forEach((preset, idx) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "sample-chip" + (idx === 0 ? " active" : "");
      btn.dataset.sampleId = preset.id;
      btn.innerHTML = `
        <img src="/api/preset-image/${encodeURIComponent(preset.id)}" alt="${preset.label}" />
        <span>${preset.label.replace("Sampel ", "")}</span>
      `;
      btn.addEventListener("click", () => {
        document.querySelectorAll(".sample-chip").forEach((c) => c.classList.remove("active"));
        btn.classList.add("active");
        analyzePresetSample(preset.id);
      });
      tray.appendChild(btn);
    });

    // Auto-run first sample on startup so workbench is immediately populated
    if (info.presets.length > 0) {
      analyzePresetSample(info.presets[0].id);
    }
  } catch (err) {
    console.error(err);
    setStatus("Gagal memuat info model", true);
  }
}

async function analyzePresetSample(sampleId) {
  try {
    lastUploadedBlob = null;
    userSelectedTeachClass = false;
    currentSourceImageUrl = `/api/preset-image/${encodeURIComponent(sampleId)}`;
    setStatus("Memproses citra...", true);
    const res = await fetch("/api/analyze-sample", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sample_id: sampleId, random_from_dataset: false }),
    });
    if (!res.ok) throw new Error("Gagal memproses sampel");
    const data = await res.json();
    renderAnalysis(data);
    setStatus(`Selesai (${data.processing_time_ms} ms)`, false);
  } catch (err) {
    console.error(err);
    setStatus("Gagal memproses sampel", true);
  }
}

async function analyzeRandomDataset() {
  try {
    lastUploadedBlob = null;
    userSelectedTeachClass = false;
    currentSourceImageUrl = null;
    document.querySelectorAll(".sample-chip").forEach((c) => c.classList.remove("active"));
    setStatus("Mengambil sampel acak dataset...", true);
    const res = await fetch("/api/analyze-sample", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ random_from_dataset: true }),
    });
    if (!res.ok) throw new Error("Gagal mengambil sampel dataset");
    const data = await res.json();
    renderAnalysis(data);
    setStatus(`Selesai (${data.processing_time_ms} ms)`, false);
  } catch (err) {
    console.error(err);
    setStatus("Gagal memuat dataset", true);
  }
}

async function analyzeFileBlob(fileOrBlob, filename = "capture.png", preserveSourceUrl = false) {
  try {
    lastUploadedBlob = fileOrBlob;
    userSelectedTeachClass = false;
    if (!preserveSourceUrl) {
      if (currentSourceImageUrl && currentSourceImageUrl.startsWith("blob:")) {
        URL.revokeObjectURL(currentSourceImageUrl);
      }
      currentSourceImageUrl = URL.createObjectURL(fileOrBlob);
    }
    document.querySelectorAll(".sample-chip").forEach((c) => c.classList.remove("active"));
    setStatus("Mengekstrak 49 fitur citra...", true);
    const formData = new FormData();
    formData.append("file", fileOrBlob, filename);

    const res = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Gagal menganalisis citra");
    }
    const data = await res.json();
    renderAnalysis(data);
    setStatus(`Selesai (${data.processing_time_ms} ms)`, false);
  } catch (err) {
    console.error(err);
    setStatus(err.message || "Error pemrosesan", true);
  }
}

/* --------------------------------------------------------------------------
   2. RENDER PIPELINE RESULTS TO WORKBENCH
   -------------------------------------------------------------------------- */
function renderAnalysis(data) {
  currentAnalysis = data;
  if (!currentSourceImageUrl || currentSourceImageUrl.startsWith("data:")) {
    currentSourceImageUrl = data.stages.original;
  }

  // Telemetry
  document.getElementById("tele-source").textContent = data.source_name;
  document.getElementById("tele-source").title = data.source_name;
  document.getElementById("tele-res").textContent = data.original_resolution;
  document.getElementById("tele-bbox").textContent = `${data.bbox.w}×${data.bbox.h} px`;
  document.getElementById("tele-coverage").textContent = `${data.mask_coverage_pct}% frame`;
  document.getElementById("tele-time").textContent = `${data.processing_time_ms} ms`;

  // Sync compact hero latency & preview images (UI only)
  const heroProc = document.getElementById("hero-proc-time");
  if (heroProc) heroProc.textContent = `${data.processing_time_ms} ms`;
  const inputPrev = document.getElementById("input-preview-img");
  if (inputPrev) inputPrev.src = data.stages.original;
  const knnPrev = document.getElementById("knn-preview-img");
  if (knnPrev) knnPrev.src = data.stages.annotated;

  // Quad images
  document.getElementById("img-quad-annotated").src = data.stages.annotated;
  document.getElementById("img-quad-mask").src = data.stages.mask;
  document.getElementById("img-quad-isolated").src = data.stages.isolated;
  document.getElementById("img-quad-edges").src = data.stages.edges;

  // Geometry details in Single Focus view
  document.getElementById("geom-contour-px").textContent = `${data.bbox.contour_px.toLocaleString("id-ID")} px²`;
  document.getElementById("geom-hull-px").textContent = `${data.bbox.hull_px.toLocaleString("id-ID")} px²`;
  document.getElementById("geom-perim-px").textContent = `${data.bbox.perimeter_px} px`;
  document.getElementById("geom-bbox-xy").textContent = `x:${data.bbox.x}, y:${data.bbox.y} (${data.bbox.w}×${data.bbox.h})`;
  updateSingleStageDisplay(activeSingleStage);

  // Verdict card
  const pred = data.prediction;
  const banner = document.getElementById("verdict-banner");
  banner.style.borderLeftColor = pred.accent || "var(--accent-forest)";
  document.getElementById("verdict-code").textContent = pred.code;
  document.getElementById("verdict-label").textContent = pred.label;
  document.getElementById("verdict-conf").textContent = `${pred.confidence_pct.toFixed(1)}%`;
  const confBar = document.getElementById("verdict-conf-bar");
  if (confBar) confBar.style.width = `${Math.max(2, Math.min(100, pred.confidence_pct))}%`;
  document.getElementById("verdict-material").textContent = `Material: ${pred.material}`;
  document.getElementById("verdict-recycle").textContent = pred.recyclable;
  document.getElementById("verdict-desc").textContent = pred.characteristic;

  // Sinkronkan pilihan dropdown "Tambah ke Dataset" selama pengguna tidak sedang memilih manual
  const teachSelect = document.getElementById("dataset-class-select");
  if (teachSelect && !userSelectedTeachClass && document.activeElement !== teachSelect) {
    teachSelect.value = pred.class_key;
  }

  // Probability distribution
  const probList = document.getElementById("prob-list");
  probList.innerHTML = "";
  data.probabilities.forEach((item, idx) => {
    const row = document.createElement("div");
    row.className = "prob-row" + (idx === 0 ? " winner" : "");
    row.innerHTML = `
      <div class="prob-label">
        <span>${item.label}</span>
      </div>
      <div class="prob-track">
        <div class="prob-fill" style="width: ${Math.max(1, item.probability)}%"></div>
      </div>
      <div class="prob-pct">${item.probability.toFixed(1)}%</div>
    `;
    probList.appendChild(row);
  });

  // Nearest Neighbors breakdown
  const nbTbody = document.getElementById("neighbors-tbody");
  nbTbody.innerHTML = "";
  data.neighbors.forEach((nb) => {
    const tr = document.createElement("tr");
    const isMatch = nb.class_key === pred.class_key;
    tr.innerHTML = `
      <td><strong>#${nb.rank}</strong></td>
      <td><code>Sampel-${nb.sample_index}</code></td>
      <td>
        <span style="font-weight:700; color:${isMatch ? "var(--accent-forest)" : "var(--ink-primary)"}">
          ${nb.class_label}
        </span>
      </td>
      <td>${nb.manhattan_distance.toFixed(3)}</td>
      <td><strong>${nb.vote_weight.toFixed(1)}%</strong></td>
    `;
    nbTbody.appendChild(tr);
  });

  // Domain A: Color Features
  renderColorDomain(data.color_analysis);

  // Domain B: Shape Features
  renderMetricCards("shape-metrics-list", data.shape_analysis);

  // Domain C: Texture Features
  renderMetricCards("texture-metrics-list", data.texture_analysis);

  // 49-D Matrix Table
  renderMatrixTable();
}

function renderColorDomain(color) {
  const swatch = document.getElementById("lab-color-swatch");
  swatch.style.backgroundColor = color.dominant_hex;
  document.getElementById("lab-hex-code").textContent = color.dominant_hex;

  const labGrid = document.getElementById("lab-channels-grid");
  const labels = [
    { name: "L* (Luminance)", mean: color.lab_mean[0], std: color.lab_std[0] },
    { name: "a* (Hijau–Merah)", mean: color.lab_mean[1], std: color.lab_std[1] },
    { name: "b* (Biru–Kuning)", mean: color.lab_mean[2], std: color.lab_std[2] },
  ];
  labGrid.innerHTML = labels
    .map(
      (ch) => `
      <div class="lab-stat-item">
        <span>${ch.name}</span>
        <strong>μ ${ch.mean} · σ ${ch.std}</strong>
      </div>
    `
    )
    .join("");

  // Hue 16 bins (0..360 deg)
  const hueWrap = document.getElementById("hist-hue-bars");
  const maxHue = Math.max(...color.hue_bins, 0.05);
  hueWrap.innerHTML = color.hue_bins
    .map((val, i) => {
      const hPct = Math.round((val / maxHue) * 100);
      const deg = Math.round(i * 22.5 + 11);
      return `
        <div class="hist-bar-col" title="Hue Bin ${i + 1} (${Math.round(i * 22.5)}°–${Math.round((i + 1) * 22.5)}°): ${(val * 100).toFixed(1)}%">
          <div class="hist-bar-fill" style="height:${Math.max(4, hPct)}%; background:hsl(${deg}, 80%, 50%)"></div>
          <span class="hist-bar-lbl">H${i + 1}</span>
        </div>
      `;
    })
    .join("");

  // Saturation 8 bins
  const satWrap = document.getElementById("hist-sat-bars");
  const maxSat = Math.max(...color.sat_bins, 0.05);
  satWrap.innerHTML = color.sat_bins
    .map((val, i) => {
      const hPct = Math.round((val / maxSat) * 100);
      const satPct = Math.round(((i + 1) / 8) * 85);
      return `
        <div class="hist-bar-col" title="Saturation Bin ${i + 1}: ${(val * 100).toFixed(1)}%">
          <div class="hist-bar-fill" style="height:${Math.max(4, hPct)}%; background:hsl(150, ${satPct}%, 40%)"></div>
          <span class="hist-bar-lbl">S${i + 1}</span>
        </div>
      `;
    })
    .join("");

  // Value 8 bins
  const valWrap = document.getElementById("hist-val-bars");
  const maxVal = Math.max(...color.val_bins, 0.05);
  valWrap.innerHTML = color.val_bins
    .map((val, i) => {
      const hPct = Math.round((val / maxVal) * 100);
      const lightPct = Math.round(18 + ((i + 1) / 8) * 72);
      return `
        <div class="hist-bar-col" title="Value Bin ${i + 1}: ${(val * 100).toFixed(1)}%">
          <div class="hist-bar-fill" style="height:${Math.max(4, hPct)}%; background:hsl(40, 10%, ${lightPct}%)"></div>
          <span class="hist-bar-lbl">V${i + 1}</span>
        </div>
      `;
    })
    .join("");
}

function renderMetricCards(containerId, items) {
  const container = document.getElementById(containerId);
  container.innerHTML = items
    .map((m) => {
      const zSign = m.z_score >= 0 ? `+${m.z_score.toFixed(2)}σ` : `${m.z_score.toFixed(2)}σ`;
      return `
        <div class="metric-card">
          <div class="metric-card-top">
            <span class="metric-name">${m.name}</span>
            <span class="metric-vals">
              ${m.value.toFixed(4)}
              <span class="metric-z">(${zSign})</span>
            </span>
          </div>
          <div class="metric-bar-track">
            <div class="metric-bar-fill" style="width:${Math.max(2, Math.min(100, m.pct))}%"></div>
          </div>
          <div class="metric-foot">
            <span>${m.desc}</span>
            <span class="metric-formula">${m.formula}</span>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderMatrixTable() {
  if (!currentAnalysis) return;
  const tbody = document.getElementById("matrix-tbody");
  const rows = currentAnalysis.vector_49d.filter(
    (item) => activeMatrixGroup === "ALL" || item.group === activeMatrixGroup
  );

  tbody.innerHTML = rows
    .map((r) => {
      const z = r.scaled;
      const clamped = Math.max(-3.0, Math.min(3.0, z));
      const widthPct = Math.abs(clamped / 3.0) * 50;
      const leftPct = z >= 0 ? 50 : 50 - widthPct;
      const barColor = z >= 0 ? "var(--accent-forest)" : "var(--accent-signal)";

      return `
        <tr>
          <td><code>f[${r.index}]</code></td>
          <td><strong>${r.code}</strong></td>
          <td>${r.group}</td>
          <td>${r.name}</td>
          <td>${r.raw.toFixed(5)}</td>
          <td><strong>${z >= 0 ? "+" : ""}${z.toFixed(4)}</strong></td>
          <td>
            <div class="z-bar-wrap" title="Z-Score: ${z.toFixed(3)}">
              <div class="z-bar-center"></div>
              <div class="z-bar-fill" style="left:${leftPct}%; width:${widthPct}%; background:${barColor}"></div>
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
}

/* --------------------------------------------------------------------------
   3. INTERACTIVE CONTROLS (VIEW MODES, TABS, UPLOAD, WEBCAM, THEME)
   -------------------------------------------------------------------------- */
function initViewSwitchers() {
  const btnGrid = document.getElementById("btn-view-grid");
  const btnSingle = document.getElementById("btn-view-single");
  const quadView = document.getElementById("optical-quad-view");
  const singleView = document.getElementById("optical-single-view");

  function setOpticalView(mode) {
    if (mode === "grid") {
      btnGrid.classList.add("active");
      btnSingle.classList.remove("active");
      quadView.classList.remove("hidden");
      singleView.classList.add("hidden");
    } else {
      btnSingle.classList.add("active");
      btnGrid.classList.remove("active");
      quadView.classList.add("hidden");
      singleView.classList.remove("hidden");
    }
  }

  btnGrid.addEventListener("click", () => setOpticalView("grid"));
  btnSingle.addEventListener("click", () => setOpticalView("single"));

  // Clicking any card in the 2x2 grid opens that stage in Single Focus view
  document.querySelectorAll(".stage-card").forEach((card) => {
    card.addEventListener("click", () => {
      const stage = card.dataset.stage;
      updateSingleStageDisplay(stage);
      setOpticalView("single");
    });
  });

  document.querySelectorAll(".stage-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      updateSingleStageDisplay(tab.dataset.target);
    });
  });

  // Feature bottom tabs (Visual vs 49-D Matrix)
  document.querySelectorAll(".feat-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".feat-tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const target = tab.dataset.tab;
      document.getElementById("feat-view-visual").classList.toggle("hidden", target !== "visual");
      document.getElementById("feat-view-matrix").classList.toggle("hidden", target !== "matrix");
    });
  });
}

function updateSingleStageDisplay(stageKey) {
  activeSingleStage = stageKey;
  document.querySelectorAll(".stage-tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.target === stageKey);
  });
  if (currentAnalysis && currentAnalysis.stages[stageKey]) {
    document.getElementById("img-single-focus").src = currentAnalysis.stages[stageKey];
  }
  const info = STAGE_EXPLANATIONS[stageKey] || STAGE_EXPLANATIONS.annotated;
  document.getElementById("single-stage-code").textContent = info.code;
  document.getElementById("single-stage-title").textContent = info.title;
  document.getElementById("single-stage-desc").textContent = info.desc;
}

function initUploadAndCamera() {
  const fileInput = document.getElementById("file-upload");
  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      analyzeFileBlob(e.target.files[0], e.target.files[0].name);
      fileInput.value = "";
    }
  });

  // Global drag and drop support
  window.addEventListener("dragover", (e) => e.preventDefault());
  window.addEventListener("drop", (e) => {
    e.preventDefault();
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
      analyzeFileBlob(e.dataTransfer.files[0], e.dataTransfer.files[0].name);
    }
  });

  document.getElementById("btn-random-dataset").addEventListener("click", analyzeRandomDataset);

  // =========================================================================
  // INLINE LIVE CAMERA AUTO-DETECTION (NO CAPTURE CLICK NEEDED)
  // =========================================================================
  const liveDeck = document.getElementById("live-camera-deck");
  const vfStage = document.getElementById("vf-stage");
  const video = document.getElementById("camera-video");
  const canvas = document.getElementById("camera-canvas");
  const vfFrame = document.getElementById("vf-frame");
  const sizeSlider = document.getElementById("vf-size-slider");
  const sizeVal = document.getElementById("vf-size-val");
  const cropToggle = document.getElementById("vf-crop-toggle");
  const btnOpenCamera = document.getElementById("btn-open-camera");
  const btnCameraLabel = document.getElementById("btn-camera-label");
  const btnFreeze = document.getElementById("btn-freeze-live");
  const btnMirror = document.getElementById("btn-mirror-camera");
  const btnSwitch = document.getElementById("btn-switch-camera");
  const recDot = document.getElementById("live-rec-dot");

  function layoutViewfinderBox() {
    if (!vfStage || liveDeck.classList.contains("hidden")) return;
    const stageW = vfStage.clientWidth;
    const stageH = vfStage.clientHeight;
    if (stageW < 10 || stageH < 10) return;

    const boxSize = Math.round(Math.min(stageW, stageH) * (vfSizePct / 100));
    const left = Math.round((stageW - boxSize) / 2);
    const top = Math.round((stageH - boxSize) / 2);

    vfFrame.style.left = `${left}px`;
    vfFrame.style.top = `${top}px`;
    vfFrame.style.width = `${boxSize}px`;
    vfFrame.style.height = `${boxSize}px`;

    document.getElementById("vf-shade-top").style.cssText = `left:0; top:0; width:${stageW}px; height:${top}px;`;
    document.getElementById("vf-shade-bottom").style.cssText = `left:0; top:${top + boxSize}px; width:${stageW}px; height:${Math.max(0, stageH - top - boxSize)}px;`;
    document.getElementById("vf-shade-left").style.cssText = `left:0; top:${top}px; width:${left}px; height:${boxSize}px;`;
    document.getElementById("vf-shade-right").style.cssText = `left:${left + boxSize}px; top:${top}px; width:${Math.max(0, stageW - left - boxSize)}px; height:${boxSize}px;`;
  }

  function extractVideoFrameBlob(useFrameCrop, outputSize = 384) {
    return new Promise((resolve) => {
      const vw = video.videoWidth;
      const vh = video.videoHeight;
      if (!vw || !vh) {
        resolve(null);
        return;
      }

      const stageW = vfStage.clientWidth || vw;
      const stageH = vfStage.clientHeight || vh;
      const ctx = canvas.getContext("2d");

      if (useFrameCrop) {
        const boxSize = Math.min(stageW, stageH) * (vfSizePct / 100);
        const left = (stageW - boxSize) / 2;
        const top = (stageH - boxSize) / 2;

        // Mapping tepat dari koordinat object-fit: cover ke piksel asli kamera
        const coverScale = Math.max(stageW / vw, stageH / vh);
        const dispW = vw * coverScale;
        const dispH = vh * coverScale;
        const offsetX = (dispW - stageW) / 2;
        const offsetY = (dispH - stageH) / 2;

        const sx = Math.max(0, (left + offsetX) / coverScale);
        const sy = Math.max(0, (top + offsetY) / coverScale);
        const sw = Math.min(vw - sx, boxSize / coverScale);
        const sh = Math.min(vh - sy, boxSize / coverScale);

        canvas.width = outputSize;
        canvas.height = outputSize;
        ctx.save();
        if (isCameraMirrored) {
          ctx.translate(outputSize, 0);
          ctx.scale(-1, 1);
        }
        ctx.drawImage(video, sx, sy, sw, sh, 0, 0, outputSize, outputSize);
        ctx.restore();
      } else {
        canvas.width = vw;
        canvas.height = vh;
        ctx.save();
        if (isCameraMirrored) {
          ctx.translate(vw, 0);
          ctx.scale(-1, 1);
        }
        ctx.drawImage(video, 0, 0, vw, vh);
        ctx.restore();
      }

      canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.86);
    });
  }

  function renderTop3Bars(containerId, top3) {
    const el = document.getElementById(containerId);
    if (!el || !top3) return;
    el.innerHTML = top3
      .map(
        (item, idx) => `
        <div class="vf-top3-row">
          <div class="vf-top3-head">
            <span style="color:${idx === 0 ? item.accent : "var(--ink-primary)"}">${item.label}</span>
            <code>${item.probability.toFixed(1)}%</code>
          </div>
          <div class="vf-top3-track">
            <div class="vf-top3-fill" style="width:${Math.max(2, item.probability)}%; background:${idx === 0 ? item.accent : "var(--ink-muted)"}"></div>
          </div>
        </div>
      `
      )
      .join("");
  }

  async function runLiveAutoAnalysisStep() {
    if (!isLiveCameraOpen || !cameraStream || isLiveFrozen) return;
    if (isLiveInFlight) {
      liveLoopTimer = setTimeout(runLiveAutoAnalysisStep, 250);
      return;
    }

    isLiveInFlight = true;
    try {
      const blob = await extractVideoFrameBlob(cropToggle.checked, 384);
      if (blob && isLiveCameraOpen && !isLiveFrozen) {
        const fd = new FormData();
        fd.append("file", blob, "kamera_langsung.jpg");
        const res = await fetch("/api/analyze?fast=true", { method: "POST", body: fd });
        if (res.ok && isLiveCameraOpen && !isLiveFrozen) {
          const data = await res.json();
          const p = data.prediction;

          // Update seluruh dashboard & data sistem secara otomatis (Panel 02, 03, 04)
          currentSourceImageUrl = data.stages.original;
          renderAnalysis(data);
          setStatus(`LIVE: ${p.label} (${p.confidence_pct.toFixed(1)}%)`, false);

          // Update HUD langsung pada bingkai fokus kamera
          vfFrame.style.setProperty("--vf-accent", p.accent || "#22C55E");
          document.getElementById("vf-hud-code").textContent = p.code;
          document.getElementById("vf-hud-label").textContent = p.label.toUpperCase();
          document.getElementById("vf-hud-conf").textContent = `${p.confidence_pct.toFixed(1)}%`;
          document.getElementById("vf-latency").textContent = `LIVE: ${data.processing_time_ms} ms`;

          const guideEl = document.getElementById("vf-hud-bottom");
          if (data.mask_coverage_pct < 6) {
            guideEl.textContent = "Dekatkan objek sampah ke tengah bingkai";
            guideEl.className = "vf-hud-bottom warn";
          } else if (data.mask_coverage_pct > 84) {
            guideEl.textContent = "Bingkai penuh / latar ramai — sedikit jauhkan";
            guideEl.className = "vf-hud-bottom warn";
          } else {
            guideEl.textContent = `Terdeteksi otomatis: ${p.label} (${p.confidence_pct.toFixed(1)}%) · Semua data aktif`;
            guideEl.className = "vf-hud-bottom ready";
          }
        }
      }
    } catch (err) {
      console.warn("Live auto-scan skip:", err);
    } finally {
      isLiveInFlight = false;
      if (isLiveCameraOpen && !isLiveFrozen) {
        liveLoopTimer = setTimeout(runLiveAutoAnalysisStep, 450);
      }
    }
  }

  function stopLiveLoop() {
    if (liveLoopTimer) {
      clearTimeout(liveLoopTimer);
      liveLoopTimer = null;
    }
  }

  async function startCameraStream(deviceId = null) {
    if (cameraStream) {
      cameraStream.getTracks().forEach((t) => t.stop());
      cameraStream = null;
    }
    const videoConstraints = deviceId
      ? { deviceId: { exact: deviceId }, width: { ideal: 1280 }, height: { ideal: 720 } }
      : { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } };

    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: videoConstraints,
      audio: false,
    });
    video.srcObject = cameraStream;

    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      cameraDevices = devices.filter((d) => d.kind === "videoinput");
      btnSwitch.disabled = cameraDevices.length <= 1;
      btnSwitch.style.opacity = cameraDevices.length <= 1 ? "0.5" : "1";
    } catch (_) {}
  }

  function closeCamera() {
    isLiveCameraOpen = false;
    isLiveFrozen = false;
    stopLiveLoop();
    liveDeck.classList.add("hidden");
    btnOpenCamera.classList.remove("camera-on");
    btnCameraLabel.textContent = "Kamera Langsung (Auto-Deteksi)";
    btnFreeze.textContent = "Bekukan Data";
    btnFreeze.classList.remove("active");
    recDot.classList.remove("paused");
    const teachSrc = document.getElementById("dataset-teach-source");
    if (teachSrc) teachSrc.textContent = "Sumber: Foto Aktif";
    if (cameraStream) {
      cameraStream.getTracks().forEach((t) => t.stop());
      cameraStream = null;
    }
  }

  grabLiveCameraBlobFn = () => extractVideoFrameBlob(cropToggle.checked, 512);

  video.addEventListener("loadedmetadata", layoutViewfinderBox);

  window.addEventListener("beforeunload", closeCamera);
  window.addEventListener("pagehide", closeCamera);

  btnOpenCamera.addEventListener("click", async () => {
    if (isLiveCameraOpen) {
      closeCamera();
      return;
    }
    try {
      document.querySelectorAll(".sample-chip").forEach((c) => c.classList.remove("active"));
      await startCameraStream();
      isLiveCameraOpen = true;
      isLiveFrozen = false;
      liveDeck.classList.remove("hidden");
      btnOpenCamera.classList.add("camera-on");
      btnCameraLabel.textContent = "Matikan Kamera Langsung";
      btnFreeze.textContent = "Bekukan Data";
      btnFreeze.classList.remove("active");
      recDot.classList.remove("paused");
      const teachSrc = document.getElementById("dataset-teach-source");
      if (teachSrc) teachSrc.textContent = "Sumber: Bingkai Kamera Langsung";
      setStatus("Kamera aktif — auto-deteksi berjalan", true);

      requestAnimationFrame(() => {
        layoutViewfinderBox();
        stopLiveLoop();
        liveLoopTimer = setTimeout(runLiveAutoAnalysisStep, 450);
      });
    } catch (err) {
      const msg = (err && err.message) ? err.message : String(err);
      if (/in use|notreadable|could not start/i.test(msg)) {
        alert(
          "Kamera sedang dipakai aplikasi atau tab browser lain (Device in use).\n\n" +
          "Tutup dulu tab Microsoft Edge / tab lain yang membuka 127.0.0.1:8000, atau aplikasi seperti Discord/WhatsApp/Zoom/Camera Windows, lalu klik Kamera Langsung lagi."
        );
      } else {
        alert("Tidak dapat mengakses kamera perangkat: " + msg);
      }
    }
  });

  btnFreeze.addEventListener("click", () => {
    if (!isLiveCameraOpen) return;
    isLiveFrozen = !isLiveFrozen;
    btnFreeze.textContent = isLiveFrozen ? "Lanjutkan Auto-Scan" : "Bekukan Data";
    btnFreeze.classList.toggle("active", isLiveFrozen);
    recDot.classList.toggle("paused", isLiveFrozen);
    const guideEl = document.getElementById("vf-hud-bottom");
    if (isLiveFrozen) {
      stopLiveLoop();
      guideEl.textContent = "Data dibekukan — klik 'Lanjutkan Auto-Scan' untuk memindai barang lain";
      guideEl.className = "vf-hud-bottom";
      setStatus("Data dibekukan", false);
    } else {
      guideEl.textContent = "Melanjutkan deteksi otomatis...";
      runLiveAutoAnalysisStep();
    }
  });

  // Matikan kamera otomatis saat pengguna memilih sampel preset / upload / acak
  document.getElementById("sample-tray").addEventListener("click", () => {
    if (isLiveCameraOpen) closeCamera();
  });
  fileInput.addEventListener("click", () => {
    if (isLiveCameraOpen) closeCamera();
  });
  document.getElementById("btn-random-dataset").addEventListener("click", () => {
    if (isLiveCameraOpen) closeCamera();
  });

  window.addEventListener("resize", () => {
    layoutViewfinderBox();
    layoutCropBox();
  });

  sizeSlider.addEventListener("input", () => {
    vfSizePct = Number(sizeSlider.value);
    sizeVal.textContent = `${vfSizePct}%`;
    layoutViewfinderBox();
  });

  btnMirror.addEventListener("click", () => {
    isCameraMirrored = !isCameraMirrored;
    video.classList.toggle("mirrored", isCameraMirrored);
    btnMirror.textContent = `Mirror: ${isCameraMirrored ? "ON" : "OFF"}`;
  });

  btnSwitch.addEventListener("click", async () => {
    if (cameraDevices.length <= 1) return;
    currentDeviceIndex = (currentDeviceIndex + 1) % cameraDevices.length;
    try {
      await startCameraStream(cameraDevices[currentDeviceIndex].deviceId);
    } catch (err) {
      alert("Gagal mengganti kamera: " + err.message);
    }
  });

  document.getElementById("btn-close-camera").addEventListener("click", closeCamera);

  // =========================================================================
  // MANUAL FOCUS FRAME / CROP MODAL FOR UPLOADED OR CURRENT PHOTO
  // =========================================================================
  const cropModal = document.getElementById("crop-modal");
  const cropStage = document.getElementById("crop-stage");
  const cropImg = document.getElementById("crop-source-img");
  const cropBox = document.getElementById("crop-box");
  const cropCanvas = document.getElementById("crop-canvas");
  const cropSizeSlider = document.getElementById("crop-size-slider");
  const cropSizeVal = document.getElementById("crop-size-val");

  function getCropImgBounds() {
    const stageRect = cropStage.getBoundingClientRect();
    const imgRect = cropImg.getBoundingClientRect();
    return {
      stageW: stageRect.width,
      stageH: stageRect.height,
      imgLeft: imgRect.left - stageRect.left,
      imgTop: imgRect.top - stageRect.top,
      imgW: imgRect.width,
      imgH: imgRect.height,
    };
  }

  function layoutCropBox() {
    if (!cropModal || cropModal.classList.contains("hidden")) return;
    const b = getCropImgBounds();
    if (b.imgW < 10 || b.imgH < 10) return;

    const side = Math.round(Math.min(b.imgW, b.imgH) * (cropState.sizePct / 100));
    let cx = b.imgLeft + b.imgW * cropState.centerXRatio;
    let cy = b.imgTop + b.imgH * cropState.centerYRatio;

    const minLeft = b.imgLeft;
    const maxLeft = b.imgLeft + b.imgW - side;
    const minTop = b.imgTop;
    const maxTop = b.imgTop + b.imgH - side;

    const left = Math.round(Math.max(minLeft, Math.min(maxLeft, cx - side / 2)));
    const top = Math.round(Math.max(minTop, Math.min(maxTop, cy - side / 2)));

    cropState.centerXRatio = (left + side / 2 - b.imgLeft) / b.imgW;
    cropState.centerYRatio = (top + side / 2 - b.imgTop) / b.imgH;

    cropBox.style.left = `${left}px`;
    cropBox.style.top = `${top}px`;
    cropBox.style.width = `${side}px`;
    cropBox.style.height = `${side}px`;

    document.getElementById("crop-shade-top").style.cssText = `left:0; top:0; width:${b.stageW}px; height:${top}px;`;
    document.getElementById("crop-shade-bottom").style.cssText = `left:0; top:${top + side}px; width:${b.stageW}px; height:${Math.max(0, b.stageH - top - side)}px;`;
    document.getElementById("crop-shade-left").style.cssText = `left:0; top:${top}px; width:${left}px; height:${side}px;`;
    document.getElementById("crop-shade-right").style.cssText = `left:${left + side}px; top:${top}px; width:${Math.max(0, b.stageW - left - side)}px; height:${side}px;`;
  }

  function extractCroppedPhotoBlob(outputSize = 512) {
    return new Promise((resolve) => {
      const natW = cropImg.naturalWidth;
      const natH = cropImg.naturalHeight;
      const b = getCropImgBounds();
      if (!natW || !natH || b.imgW < 10) {
        resolve(null);
        return;
      }

      const boxRect = cropBox.getBoundingClientRect();
      const stageRect = cropStage.getBoundingClientRect();
      const boxLeft = boxRect.left - stageRect.left;
      const boxTop = boxRect.top - stageRect.top;
      const boxSide = boxRect.width;

      const scaleX = natW / b.imgW;
      const scaleY = natH / b.imgH;
      const sx = Math.max(0, (boxLeft - b.imgLeft) * scaleX);
      const sy = Math.max(0, (boxTop - b.imgTop) * scaleY);
      const sw = Math.min(natW - sx, boxSide * scaleX);
      const sh = Math.min(natH - sy, boxSide * scaleY);

      cropCanvas.width = outputSize;
      cropCanvas.height = outputSize;
      const ctx = cropCanvas.getContext("2d");
      ctx.drawImage(cropImg, sx, sy, sw, sh, 0, 0, outputSize, outputSize);
      cropCanvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.92);
    });
  }

  function scheduleCropLivePreview() {
    if (cropState.liveDebounce) clearTimeout(cropState.liveDebounce);
    cropState.liveDebounce = setTimeout(async () => {
      if (cropModal.classList.contains("hidden")) return;
      const blob = await extractCroppedPhotoBlob(256);
      if (!blob) return;
      try {
        const fd = new FormData();
        fd.append("file", blob, "crop_preview.jpg");
        const res = await fetch("/api/predict-live", { method: "POST", body: fd });
        if (!res.ok) return;
        const data = await res.json();
        const p = data.prediction;

        cropBox.style.setProperty("--vf-accent", p.accent || "#22C55E");
        document.getElementById("crop-hud-code").textContent = p.code;
        document.getElementById("crop-hud-label").textContent = p.label.toUpperCase();
        document.getElementById("crop-hud-conf").textContent = `${p.confidence_pct.toFixed(1)}%`;
        document.getElementById("crop-mini-mask").src = data.mini_mask;
        document.getElementById("crop-coverage-val").textContent = `${data.mask_coverage_pct}%`;
        document.getElementById("crop-guidance-text").textContent = data.guidance;
        renderTop3Bars("crop-top3-list", data.top3);
      } catch (err) {
        console.warn("Crop preview error:", err);
      }
    }, 280);
  }

  function openCropModal() {
    const src = currentSourceImageUrl || (currentAnalysis ? currentAnalysis.stages.original : null);
    if (!src) return;
    cropState.sizePct = 75;
    cropState.centerXRatio = 0.5;
    cropState.centerYRatio = 0.5;
    cropSizeSlider.value = "75";
    cropSizeVal.textContent = "75%";

    cropImg.onload = () => {
      layoutCropBox();
      scheduleCropLivePreview();
    };
    cropImg.src = src;
    cropModal.classList.remove("hidden");
    if (cropImg.complete) {
      requestAnimationFrame(() => {
        layoutCropBox();
        scheduleCropLivePreview();
      });
    }
  }

  function closeCropModal() {
    cropModal.classList.add("hidden");
  }

  document.getElementById("btn-open-crop").addEventListener("click", openCropModal);
  document.getElementById("btn-close-crop").addEventListener("click", closeCropModal);
  document.getElementById("btn-cancel-crop").addEventListener("click", closeCropModal);

  cropSizeSlider.addEventListener("input", () => {
    cropState.sizePct = Number(cropSizeSlider.value);
    cropSizeVal.textContent = `${cropState.sizePct}%`;
    layoutCropBox();
    scheduleCropLivePreview();
  });

  document.getElementById("btn-reset-crop").addEventListener("click", () => {
    cropState.sizePct = 75;
    cropState.centerXRatio = 0.5;
    cropState.centerYRatio = 0.5;
    cropSizeSlider.value = "75";
    cropSizeVal.textContent = "75%";
    layoutCropBox();
    scheduleCropLivePreview();
  });

  // Pointer dragging for crop box (mouse + touch)
  cropBox.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    cropBox.setPointerCapture(e.pointerId);
    cropState.isDragging = true;
    const rect = cropBox.getBoundingClientRect();
    cropState.dragOffsetX = e.clientX - (rect.left + rect.width / 2);
    cropState.dragOffsetY = e.clientY - (rect.top + rect.height / 2);
  });

  cropBox.addEventListener("pointermove", (e) => {
    if (!cropState.isDragging) return;
    const b = getCropImgBounds();
    const stageRect = cropStage.getBoundingClientRect();
    const targetCx = e.clientX - stageRect.left - cropState.dragOffsetX;
    const targetCy = e.clientY - stageRect.top - cropState.dragOffsetY;
    cropState.centerXRatio = (targetCx - b.imgLeft) / b.imgW;
    cropState.centerYRatio = (targetCy - b.imgTop) / b.imgH;
    layoutCropBox();
  });

  const endCropDrag = () => {
    if (!cropState.isDragging) return;
    cropState.isDragging = false;
    scheduleCropLivePreview();
  };
  cropBox.addEventListener("pointerup", endCropDrag);
  cropBox.addEventListener("pointercancel", endCropDrag);

  document.getElementById("btn-apply-crop").addEventListener("click", async () => {
    const blob = await extractCroppedPhotoBlob(512);
    closeCropModal();
    if (blob) {
      analyzeFileBlob(blob, "foto_bingkai_fokus.jpg", true);
    }
  });
}

function initDatasetTeaching() {
  const selectEl = document.getElementById("dataset-class-select");
  const btnSave = document.getElementById("btn-save-dataset");
  const feedbackEl = document.getElementById("dataset-save-feedback");
  if (!selectEl || !btnSave || !feedbackEl) return;

  selectEl.addEventListener("change", () => {
    userSelectedTeachClass = true;
  });

  btnSave.addEventListener("click", async () => {
    const category = selectEl.value;
    btnSave.disabled = true;
    const prevLabel = btnSave.textContent;
    btnSave.textContent = "Menyimpan...";
    feedbackEl.classList.remove("hidden", "error");
    feedbackEl.textContent = "Menyimpan foto ke folder dataset & memperbarui model KNN...";

    try {
      let blobToSave = null;
      let filename = `user_${category}.jpg`;

      if (isLiveCameraOpen && cameraStream && grabLiveCameraBlobFn) {
        blobToSave = await grabLiveCameraBlobFn();
        filename = `kamera_${category}.jpg`;
      } else if (lastUploadedBlob) {
        blobToSave = lastUploadedBlob;
      } else if (currentSourceImageUrl) {
        const resp = await fetch(currentSourceImageUrl);
        blobToSave = await resp.blob();
      } else if (currentAnalysis && currentAnalysis.stages && currentAnalysis.stages.original) {
        const resp = await fetch(currentAnalysis.stages.original);
        blobToSave = await resp.blob();
      }

      if (!blobToSave) {
        throw new Error("Belum ada foto aktif untuk disimpan ke dataset.");
      }

      const fd = new FormData();
      fd.append("file", blobToSave, filename);
      fd.append("category", category);

      const res = await fetch("/api/dataset/add", {
        method: "POST",
        body: fd,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Gagal menambahkan foto ke dataset.");
      }

      // Perbarui header jumlah sampel latih secara langsung
      document.getElementById("hdr-dataset-spec").textContent =
        `${data.total_training_samples.toLocaleString("id-ID")} Sampel × ${data.feature_dimensions}-D`;

      feedbackEl.classList.remove("error");
      feedbackEl.innerHTML =
        `<strong>Berhasil disimpan &amp; dipelajari!</strong> ` +
        `<code>${data.saved_path}</code> · Total kelas ${data.category_label}: ` +
        `<strong>${data.class_dataset_count}</strong> foto · Model KNN diperbarui ` +
        `(<strong>${data.total_training_samples.toLocaleString("id-ID")}</strong> sampel, ${data.elapsed_ms} ms).`;

      userSelectedTeachClass = false;

      // Jika bukan mode live kamera, langsung analisis ulang agar hasil prediksi & tetangga terbaru langsung tampak
      if (!isLiveCameraOpen) {
        analyzeFileBlob(blobToSave, filename, true);
      }
    } catch (err) {
      console.error(err);
      feedbackEl.classList.add("error");
      feedbackEl.textContent = err.message || "Terjadi kesalahan saat menyimpan ke dataset.";
    } finally {
      btnSave.disabled = false;
      btnSave.textContent = prevLabel;
    }
  });
}

function initMatrixToolbar() {
  document.querySelectorAll(".filter-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".filter-chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      activeMatrixGroup = chip.dataset.group;
      renderMatrixTable();
    });
  });

  document.getElementById("btn-copy-json").addEventListener("click", () => {
    if (!currentAnalysis) return;
    const payload = {
      source: currentAnalysis.source_name,
      prediction: currentAnalysis.prediction,
      vector_49d: currentAnalysis.vector_49d,
    };
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    const btn = document.getElementById("btn-copy-json");
    const oldText = btn.textContent;
    btn.textContent = "Tersalin ke Clipboard!";
    setTimeout(() => (btn.textContent = oldText), 1800);
  });

  document.getElementById("btn-export-csv").addEventListener("click", () => {
    if (!currentAnalysis) return;
    const headers = ["index", "code", "group", "name", "raw_value", "z_score_scaled"];
    const lines = [headers.join(",")];
    currentAnalysis.vector_49d.forEach((r) => {
      lines.push(
        [
          r.index,
          r.code,
          `"${r.group}"`,
          `"${r.name}"`,
          r.raw.toFixed(6),
          r.scaled.toFixed(6),
        ].join(",")
      );
    });
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `vektor_fitur_49d_${currentAnalysis.prediction.class_key}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  });
}

function initThemeToggle() {
  const btn = document.getElementById("btn-theme-toggle");
  const lbl = document.getElementById("theme-label");
  if (!btn || !lbl) return;
  btn.addEventListener("click", () => {
    const html = document.documentElement;
    const next = html.getAttribute("data-theme") === "paper" ? "darkroom" : "paper";
    html.setAttribute("data-theme", next);
    lbl.textContent = next === "paper" ? "Mode Kamar Gelap" : "Mode Kertas Terang";
  });
}

/* --------------------------------------------------------------------------
   UI-ONLY ENHANCEMENTS (Sidebar Drawer, Nav Scroll, 3-Tier Tabs, Toast)
   Preserves 100% of existing logic and event listeners.
   -------------------------------------------------------------------------- */
function showUiToast(msg) {
  const t = document.getElementById("ui-toast");
  if (!t) return;
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(window._uiToastTimer);
  window._uiToastTimer = setTimeout(() => t.classList.remove("show"), 2200);
}

function initRedesignUI() {
  const sidebar = document.getElementById("app-sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  const btnOpen = document.getElementById("btn-open-sidebar");
  const btnClose = document.getElementById("btn-close-sidebar");
  const crumbActive = document.getElementById("header-crumb-active");

  function setSidebarOpen(open) {
    if (!sidebar || !backdrop) return;
    sidebar.classList.toggle("open", open);
    backdrop.classList.toggle("hidden", !open);
  }

  if (btnOpen) btnOpen.addEventListener("click", () => setSidebarOpen(true));
  if (btnClose) btnClose.addEventListener("click", () => setSidebarOpen(false));
  if (backdrop) backdrop.addEventListener("click", () => setSidebarOpen(false));

  // Sidebar navigation active states, breadcrumb update & mobile auto-close
  const allNavItems = document.querySelectorAll(".sidebar-nav .nav-link");
  function markNavActive(el) {
    allNavItems.forEach((l) => l.classList.remove("active"));
    if (el) {
      el.classList.add("active");
      if (crumbActive && el.dataset.label) crumbActive.textContent = el.dataset.label;
    }
  }

  document.querySelectorAll(".sidebar-nav .nav-link[data-nav]").forEach((link) => {
    link.addEventListener("click", () => {
      markNavActive(link);
      setSidebarOpen(false);
    });
  });

  // Sidebar shortcuts directly invoking existing camera, ROI, and dataset panels
  const navCam = document.getElementById("nav-trigger-camera");
  if (navCam) {
    navCam.addEventListener("click", () => {
      markNavActive(navCam);
      setSidebarOpen(false);
      const camBtn = document.getElementById("btn-open-camera");
      if (camBtn && !isLiveCameraOpen) camBtn.click();
      const deck = document.getElementById("live-camera-deck");
      if (deck) deck.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }

  const navRoi = document.getElementById("nav-trigger-roi");
  if (navRoi) {
    navRoi.addEventListener("click", () => {
      markNavActive(navRoi);
      setSidebarOpen(false);
      const cropBtn = document.getElementById("btn-open-crop");
      if (cropBtn) cropBtn.click();
    });
  }

  // Tier-3 KNN Tabs (Ringkasan | Tetangga Terdekat | Tambah ke Dataset)
  const knnTabBtns = document.querySelectorAll("[data-knn-tab]");
  const knnTabPanes = document.querySelectorAll("[data-knn-pane]");
  function activateKnnTab(key) {
    knnTabBtns.forEach((b) => b.classList.toggle("active", b.dataset.knnTab === key));
    knnTabPanes.forEach((p) => p.classList.toggle("hidden", p.dataset.knnPane !== key));
  }
  knnTabBtns.forEach((btn) => {
    btn.addEventListener("click", () => activateKnnTab(btn.dataset.knnTab));
  });

  const navDataset = document.getElementById("nav-trigger-dataset");
  if (navDataset) {
    navDataset.addEventListener("click", () => {
      markNavActive(navDataset);
      setSidebarOpen(false);
      activateKnnTab("dataset");
      const sec = document.getElementById("sec-classification");
      if (sec) sec.scrollIntoView({ behavior: "smooth", block: "center" });
      showUiToast("Panel Tambah ke Dataset dibuka");
    });
  }

  const btnJumpDetail = document.getElementById("btn-jump-detail");
  if (btnJumpDetail) {
    btnJumpDetail.addEventListener("click", () => {
      const sec = document.getElementById("sec-classification");
      if (sec) sec.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  // Visual Domain Selector inside Feature Explorer (Color / Morphology / Texture / All)
  const domainBtns = document.querySelectorAll("#visual-domain-selector .domain-pill");
  const visualGrid = document.getElementById("feat-view-visual");
  const domainPanels = document.querySelectorAll("#feat-view-visual [data-domain-panel]");

  domainBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      domainBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const sel = btn.dataset.domain;

      const visualTab = document.querySelector('.feat-tab[data-tab="visual"]');
      if (visualTab && !visualTab.classList.contains("active")) {
        visualTab.click();
      }

      if (visualGrid) {
        visualGrid.classList.toggle("single-domain-mode", sel !== "all");
      }
      domainPanels.forEach((panel) => {
        const match = sel === "all" || panel.dataset.domainPanel === sel;
        panel.classList.toggle("hidden", !match);
      });
    });
  });

  // Hide visual domain bar when user switches to Matrix 49-D tab
  const domainBar = document.getElementById("visual-domain-selector");
  document.querySelectorAll(".feat-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      if (domainBar) domainBar.classList.toggle("hidden", tab.dataset.tab !== "visual");
    });
  });

  // Drag-and-drop visual highlight on input drop zone
  const dropArea = document.getElementById("input-drop-area");
  if (dropArea) {
    let dragCounter = 0;
    window.addEventListener("dragenter", () => {
      dragCounter++;
      dropArea.classList.add("drag-active");
    });
    window.addEventListener("dragleave", () => {
      dragCounter = Math.max(0, dragCounter - 1);
      if (dragCounter === 0) dropArea.classList.remove("drag-active");
    });
    window.addEventListener("drop", () => {
      dragCounter = 0;
      dropArea.classList.remove("drag-active");
    });
  }
}
