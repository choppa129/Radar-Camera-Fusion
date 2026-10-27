/* Interactive teaching demo: NO actual YOLO inference, no synchronized radar input.
 * The photo is real (Unsplash); all targets/boxes below are synthetic examples.
 */
"use strict";

const BASE_DETECTIONS = [
  { id: "C01", label: "car", center: [270, 390], size: [132, 129], conf: 0.95 },
  { id: "C02", label: "car", center: [551, 463], size: [146, 168], conf: 0.91 },
  { id: "C03", label: "car", center: [725, 295], size: [86, 98], conf: 0.92 },
  { id: "C04", label: "car", center: [436, 341], size: [80, 88], conf: 0.87 },
  { id: "C05", label: "person", center: [809, 401], size: [65, 142], conf: 0.84 }
];
const BASE_RETURNS = [
  { id: "R01", lateral: -1.55, range: 7.52, velocity: -2.40 },
  { id: "R02", lateral: 0.10, range: 5.11, velocity: 3.70 },
  { id: "R03", lateral: 3.30, range: 17.90, velocity: -1.65 },
  { id: "R04", lateral: -0.45, range: 10.90, velocity: 1.25 },
  { id: "R05", lateral: 4.90, range: 8.00, velocity: -0.30 }
];
const FRAME_COUNT = 6;
const CAMERA_WIDTH = 1000;
const CAMERA_HEIGHT = 620;
const PHOTO_CREDIT = "Carlos Felipe Ramírez Mesa / Unsplash (Unsplash License)";
const $ = id => document.getElementById(id);
const state = { frame: 0, gate: 80, dx: 0, dy: 0, selected: null, playing: false, timer: null };

function getFrame(index) {
  const phase = Number(index);
  const detections = BASE_DETECTIONS.map((item, i) => ({
    ...item,
    center: [
      item.center[0] + Math.round(phase * (i % 2 === 0 ? 5 : -6)),
      item.center[1] + Math.round(phase * (i % 2 === 0 ? 2 : -3))
    ]
  }));
  const radar = BASE_RETURNS.map((item, i) => ({
    ...item,
    lateral: Number((item.lateral + phase * ((i % 2 === 0 ? 0.06 : -0.05))).toFixed(2)),
    range: Number((item.range + phase * ((i % 2 === 0 ? -0.13 : 0.10))).toFixed(2)),
    velocity: Number((item.velocity + phase * ((i % 2 === 0 ? 0.14 : -0.11))).toFixed(2))
  }));
  return { frame: index + 1, timeSeconds: Number((phase * 0.12).toFixed(2)), detections, radar };
}
function projectRadar(target) {
  // Simplified pinhole-style projection in an illustrative normalized canvas;
  // camera/radar extrinsics and image rectification in the real project differ.
  return {
    u: 500 + 920 * target.lateral / target.range + state.dx,
    v: 230 + 1200 / target.range + state.dy
  };
}
function calculateMatches(frame) {
  const projected = frame.radar.map(target => ({ ...target, ...projectRadar(target) }));
  const candidates = [];
  for (const det of frame.detections) {
    for (const target of projected) {
      const distance = Math.hypot(det.center[0] - target.u, det.center[1] - target.v);
      if (distance <= state.gate) candidates.push({ detection: det.id, radar: target.id, error: distance, target });
    }
  }
  candidates.sort((a, b) => a.error - b.error);
  const assignedCamera = new Set(), assignedRadar = new Set(), matches = new Map();
  for (const candidate of candidates) {
    if (assignedCamera.has(candidate.detection) || assignedRadar.has(candidate.radar)) continue;
    assignedCamera.add(candidate.detection);
    assignedRadar.add(candidate.radar);
    matches.set(candidate.detection, candidate);
  }
  return { projected, matches };
}
function rounded(value, digits = 1) { return Number(value).toFixed(digits); }
function showSigned(value) { return value >= 0 ? "+" + rounded(value) : rounded(value); }
function createElement(tag, className, textContent) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (textContent != null) el.textContent = String(textContent);
  return el;
}
function drawCamera(frame, projected, matches) {
  const boxes = $("det-boxes"), marks = $("radar-projections"), lines = $("match-lines");
  boxes.replaceChildren(); marks.replaceChildren(); lines.replaceChildren();
  const showPoints = $("show-radar").checked;
  const showLines = $("show-lines").checked;
  const showLabels = $("show-labels").checked;

  for (const target of projected) {
    if (!showPoints) continue;
    if (target.u < 0 || target.u > CAMERA_WIDTH || target.v < 0 || target.v > CAMERA_HEIGHT) continue;
    const marker = createElement("div", "return-mark");
    marker.title = target.id + " · " + rounded(target.range) + " m · " + showSigned(target.velocity) + " m/s · simulated";
    marker.style.left = (target.u / CAMERA_WIDTH * 100) + "%";
    marker.style.top = (target.v / CAMERA_HEIGHT * 100) + "%";
    marks.appendChild(marker);
  }
  for (const det of frame.detections) {
    const associated = matches.get(det.id);
    const box = createElement("button", "detection-box" + (associated ? "" : " unmatched") + (state.selected === det.id ? " selected" : ""));
    box.type = "button";
    box.style.left = ((det.center[0] - det.size[0] / 2) / CAMERA_WIDTH * 100) + "%";
    box.style.top = ((det.center[1] - det.size[1] / 2) / CAMERA_HEIGHT * 100) + "%";
    box.style.width = (det.size[0] / CAMERA_WIDTH * 100) + "%";
    box.style.height = (det.size[1] / CAMERA_HEIGHT * 100) + "%";
    box.setAttribute("aria-label", det.id + ": simulated " + det.label + ", " + (associated ? "radar match " + associated.radar : "unmatched") + "; inspect");
    box.addEventListener("click", () => selectDetection(det.id));
    if (showLabels) {
      const label = createElement("span", "detection-label", det.id + " / " + det.label + " " + rounded(det.conf, 2) +
        (associated ? " · " + showSigned(associated.target.velocity) + " m/s" : " · NO RADAR"));
      box.appendChild(label);
    }
    boxes.appendChild(box);
    if (associated && showLines && showPoints) {
      const link = document.createElementNS("http://www.w3.org/2000/svg", "line");
      link.setAttribute("x1", rounded(det.center[0], 2));
      link.setAttribute("y1", rounded(det.center[1], 2));
      link.setAttribute("x2", rounded(associated.target.u, 2));
      link.setAttribute("y2", rounded(associated.target.v, 2));
      link.setAttribute("stroke", state.selected === det.id ? "#afffeb" : "#2be0ba");
      link.setAttribute("stroke-width", state.selected === det.id ? "3" : "1.75");
      link.setAttribute("stroke-dasharray", "5 5");
      link.setAttribute("opacity", ".95");
      lines.appendChild(link);
    }
  }
}
function selectDetection(id) { state.selected = state.selected === id ? null : id; render(); }
function drawTable(frame, matches) {
  const tbody = $("match-table");
  tbody.replaceChildren();
  for (const det of frame.detections) {
    const match = matches.get(det.id);
    const tr = createElement("tr", state.selected === det.id ? "selected" : "");
    tr.addEventListener("click", () => selectDetection(det.id));
    tr.tabIndex = 0;
    tr.setAttribute("role", "button");
    tr.setAttribute("aria-label", det.id + " details");
    tr.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectDetection(det.id); } });
    function cell(value) { tr.appendChild(createElement("td", null, value)); }
    cell(det.id + " / " + det.label);
    const statusCell = createElement("td");
    statusCell.appendChild(createElement("span", "status-pill" + (match ? "" : " missing"), match ? match.radar : "NO MATCH"));
    tr.appendChild(statusCell);
    cell(match ? rounded(match.target.range) + " m" : "—");
    cell(match ? showSigned(match.target.velocity) + " m/s" : "—");
    cell(match ? rounded(match.error) + " px" : "—");
    tbody.appendChild(tr);
  }
}
function drawRadar(frame, matches) {
  const canvas = $("radar-canvas");
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(200, rect.width);
  const height = Math.max(120, rect.height);
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.floor(width * dpr);
  canvas.height = Math.floor(height * dpr);
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);
  const centerX = width * .5;
  const originY = height - 30;
  const scaleY = (height - 60) / 25;
  const scaleX = Math.min(width * .07, 27);
  ctx.lineWidth = 1;
  ctx.strokeStyle = "rgba(80, 100, 100, .21)";
  ctx.fillStyle = "#444444";
  ctx.font = "12px IBM Plex Mono, monospace";
  for (const range of [5, 10, 15, 20, 25]) {
    const y = originY - range * scaleY;
    ctx.beginPath(); ctx.moveTo(18, y); ctx.lineTo(width - 12, y); ctx.stroke();
    ctx.fillText(range + "m", 18, y - 5);
  }
  for (const lateral of [-6, -3, 0, 3, 6]) {
    const x = centerX + lateral * scaleX;
    ctx.beginPath(); ctx.moveTo(x, 12); ctx.lineTo(x, originY); ctx.stroke();
    if (lateral !== 0) ctx.fillText(lateral.toString(), x - 6, originY + 14);
  }
  // Sensor origin and viewing rays are schematic (not radar antenna physics).
  ctx.strokeStyle = "rgba(50, 100, 90, .17)";
  for (const rad of [-.54, 0, .54]) {
    ctx.beginPath(); ctx.moveTo(centerX, originY);
    ctx.lineTo(centerX + Math.sin(rad) * height, originY - Math.cos(rad) * height);
    ctx.stroke();
  }
  ctx.beginPath(); ctx.moveTo(centerX, originY - 7); ctx.lineTo(centerX - 6, originY + 5); ctx.lineTo(centerX + 6, originY + 5); ctx.closePath();
  ctx.fillStyle = "#262626"; ctx.fill();
  const matchedRadarIds = new Set(Array.from(matches.values()).map(m => m.radar));
  for (const target of frame.radar) {
    const x = centerX + target.lateral * scaleX;
    const y = originY - target.range * scaleY;
    if (x < 10 || x > width - 10 || y < 0 || y > height) continue;
    const matched = matchedRadarIds.has(target.id);
    ctx.beginPath(); ctx.arc(x, y, 12, 0, Math.PI * 2);
    ctx.fillStyle = matched ? "rgba(10, 130, 105, .16)" : "rgba(185, 90, 10, .12)"; ctx.fill();
    ctx.beginPath(); ctx.arc(x, y, matched ? 4.2 : 3.2, 0, Math.PI * 2);
    ctx.fillStyle = matched ? "#008c75" : "#b45a13";
    if (matched) ctx.fill(); else { ctx.lineWidth = 2; ctx.strokeStyle = "#b45a13"; ctx.stroke(); }
    ctx.fillStyle = "#222222";
    ctx.font = "12px IBM Plex Mono, monospace";
    ctx.fillText(target.id + " " + showSigned(target.velocity), x + 9, y - 9);
  }
}
function render() {
  const frame = getFrame(state.frame);
  const { projected, matches } = calculateMatches(frame);
  $("frame-label").textContent = "FRAME " + String(frame.frame).padStart(2, "0") + " / " + String(FRAME_COUNT).padStart(2, "0");
  $("time-code").textContent = "SIM T+" + rounded(frame.timeSeconds, 2) + "s";
  $("matched-stat").textContent = String(matches.size).padStart(2, "0");
  $("unmatched-stat").textContent = String(frame.detections.length - matches.size).padStart(2, "0");
  const errors = Array.from(matches.values()).map(m => m.error);
  $("error-stat").textContent = errors.length ? rounded(errors.reduce((a, b) => a + b, 0) / errors.length) : "—";
  $("gate-stat").textContent = state.gate + " px";
  $("radar-count").textContent = String(frame.radar.length).padStart(2, "0") + " TARGETS";
  $("gate-output").textContent = state.gate;
  $("offset-x-output").textContent = state.dx >= 0 ? "+" + state.dx : state.dx;
  $("offset-y-output").textContent = state.dy >= 0 ? "+" + state.dy : state.dy;
  drawCamera(frame, projected, matches);
  drawTable(frame, matches);
  drawRadar(frame, matches);
}
function moveFrame(step) { state.frame = (state.frame + step + FRAME_COUNT) % FRAME_COUNT; render(); }
function stopPlayback() {
  if (state.timer !== null) clearInterval(state.timer);
  state.timer = null; state.playing = false;
  $("play-icon").textContent = "▶";
  $("play-label").textContent = "Play";
  $("play").setAttribute("aria-label", "Play simulated frames");
}
function togglePlayback() {
  if (state.playing) { stopPlayback(); return; }
  state.playing = true;
  $("play-icon").textContent = "Ⅱ"; $("play-label").textContent = "Pause";
  $("play").setAttribute("aria-label", "Pause simulated frames");
  state.timer = setInterval(() => moveFrame(1), 1100);
}
function exportCurrent() {
  const frame = getFrame(state.frame);
  const { matches } = calculateMatches(frame);
  const payload = {
    metadata: {
      kind: "SIMULATED_INTERACTIVE_DEMO",
      warning: "No synchronized sensor data or YOLO inference. Do not use as measured results.",
      frame: frame.frame, timeSeconds: frame.timeSeconds,
      visualAsset: PHOTO_CREDIT,
      projection: "illustrative pinhole-style normalization: u=500+920*X/Z+offsetX; v=230+1200/Z+offsetY",
      association: "global-greedy-nearest-pair, single radar return per detection",
      matchingThresholdPixels: state.gate,
      offsetX: state.dx, offsetY: state.dy
    },
    cameraDetections: frame.detections,
    simulatedRadarTargets: frame.radar,
    associations: Array.from(matches.values()).map(m => ({
      detectionId: m.detection, radarId: m.radar, imageDistancePixels: Number(m.error.toFixed(2))
    }))
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const a = createElement("a");
  a.href = url; a.download = "radar-camera-demo-frame-" + frame.frame + ".json";
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

$("prev").addEventListener("click", () => { stopPlayback(); moveFrame(-1); });
$("next").addEventListener("click", () => { stopPlayback(); moveFrame(1); });
$("play").addEventListener("click", togglePlayback);
$("export").addEventListener("click", exportCurrent);
$("reset").addEventListener("click", () => {
  stopPlayback();
  state.frame = 0; state.gate = 80; state.dx = 0; state.dy = 0; state.selected = null;
  for (const id of ["gate", "offset-x", "offset-y"]) {
    $(id).value = id === "gate" ? 80 : 0;
  }
  for (const id of ["show-lines", "show-radar", "show-labels"]) $(id).checked = true;
  render();
});
for (const [id, property] of [["gate", "gate"], ["offset-x", "dx"], ["offset-y", "dy"]]) {
  $(id).addEventListener("input", e => { state[property] = Number(e.target.value); render(); });
}
for (const id of ["show-lines", "show-radar", "show-labels"]) $(id).addEventListener("change", render);
$("scene-photo").addEventListener("error", () => $("camera-stage").classList.add("no-photo"));
document.addEventListener("visibilitychange", () => { if (document.hidden) stopPlayback(); });
window.addEventListener("resize", () => { drawRadar(getFrame(state.frame), calculateMatches(getFrame(state.frame)).matches); });
render();
