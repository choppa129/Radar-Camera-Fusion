# Standalone fusion demo site

This folder is an entirely separate **GitHub Pages project website** hosted
from the `Radar-Camera-Fusion` repository, not a part of the
personal portfolio repository.

Expected URL (after GitHub Pages is enabled):

https://choppa129.github.io/Radar-Camera-Fusion/

## Publishing

Repository → **Settings → Pages** → **Build and deployment**:
- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/docs`

Click Save. The website needs no build step, backend, server or Node packages.
Open `docs/index.html` locally for development, or serve `docs/` using
`python -m http.server --directory docs 8000`.

## Controls and data provenance

- **Real, licensed pasture photograph:** Abdou,
  [Unsplash: grazing cattle in a meadow](https://unsplash.com/photos/brown-cow-on-green-grass-field-during-daytime-Oql56ssll_c),
  [Unsplash License](https://unsplash.com/license).
  It is linked from the original image host and not stored in this repository.
- **Actual published radar image:** independent example from
  [Pitt-Radar](https://github.com/yujheli/Pitt-Radar), MIT license, by
  Yu-Jhe Li et al. (CVPR 2023). It has **no spatial or temporal relationship**
  to the photo or the synthetic overlays.
- **Illustrative nature-scene overlay:** three cow boxes were manually positioned
  over one fixed photographic frame; they are not YOLO detections. Six simulated
  radar samples contain independently synthesized ranges, velocities and jitter
  that change without moving the photograph. Values are coded in
  `app.js` and generated deterministically in the browser. These are not
  real sensor readings, not measured experimental performance and not the
  result of running YOLOv8 inference.
- Projection is illustrative: `u = 500 + 920·X/Z + offsetX` and
  `v = 230 + 1200/Z + offsetY` in the demo coordinate system.
  The original application uses OpenCV `projectPoints` with camera
  calibration and extrinsics, **not** these simplified equations.
- Matching pairs are sorted by pixel distance and assigned greedily,
  enforcing at most one radar point per camera detection and vice versa.
  The production code may follow a different greedy choice order.

The downloadable `data/demo-sequence.json` mirrors the six current pasture
samples. The per-sample export control produces a JSON record carrying a mandatory
`SIMULATED_INTERACTIVE_DEMO` label. The illustrative cattle annotations and
reference radar illustration should **not** be represented as genuine
field-robot experiments.

## Site assets

The site intentionally includes **no AI-generated photos or illustrations**.
It renders a licensed third-party photograph and uses simple CSS / canvas
shapes and labels for the interaction.
