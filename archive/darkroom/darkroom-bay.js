/* ===========================================================================
   MayaTrail — the safelight bay.
   A pinned WebGL descent down a six-station darkroom bench. Scroll walks the
   camera; in each tray a coverage print develops out of grey, and at the
   observe station two of the four techniques never come up.
   Requires: vendor/three.min.js (r128, UMD global THREE)
   =========================================================================== */
(function () {
  'use strict';

  var mount = document.getElementById('bay');
  if (!mount) return;

  var canvas   = document.getElementById('bay-canvas');
  var track    = document.getElementById('bay-track');
  var openEl   = document.getElementById('bay-open');
  var hintEl   = document.getElementById('bay-hint');
  var clockEl  = document.getElementById('bay-clock');
  var nowEl    = document.getElementById('bay-now');
  var strip    = document.getElementById('bay-strip');
  var caps     = document.getElementById('bay-caps');
  var reduced  = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* A dead library must never look like a design decision. */
  if (typeof THREE === 'undefined') {
    var warn = document.createElement('p');
    warn.className = 'bay__fallback';
    warn.textContent = 'The 3D bay could not load. The page below carries the same information.';
    mount.appendChild(warn);
    return;
  }

  /* --- palette, matched to mayatrail-darkroom.css ------------------------- */
  var BAY = 0x0B0A09, AMBER = 0xC9762A, LIT = 0xE0913A,
      ENAMEL = 0xEFEAE2, SILVER = 0x6E6E6E, DIM = 0x3A3330;

  var STATIONS = ['Compose', 'Expose', 'Develop', 'Fix', 'Wash', 'Dry'];
  var N = STATIONS.length, GAP = 7.4;

  /* Station 03 runs the chain; station 04 is the verdict — 2 of 4 unread.
     Grid cells per tray: true = comes up, false = stays dim. */
  var VERDICT_ROW = [true, true, false, false];

  var renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    antialias: true,
    powerPreference: 'high-performance',
    stencil: false
  });
  /* Thin geometry needs the extra samples; 3 is the point of diminishing return. */
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 3));
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.setClearColor(BAY, 1);

  /* WebGL renders LineBasicMaterial at a hard 1px with no antialiasing, which
     is what reads as "pixellated". Every edge in this scene is real geometry
     instead: thin boxes the MSAA pass can actually smooth. */
  function frame(w, d, t, color, opacity) {
    var g = new THREE.Group();
    var mat = new THREE.MeshBasicMaterial({
      color: color, transparent: opacity < 1, opacity: opacity
    });
    var long = new THREE.BoxGeometry(w + t, t, t);
    var side = new THREE.BoxGeometry(t, t, d - t);
    var a = new THREE.Mesh(long, mat); a.position.z = -d / 2; g.add(a);
    var b = new THREE.Mesh(long, mat); b.position.z =  d / 2; g.add(b);
    var c = new THREE.Mesh(side, mat); c.position.x = -w / 2; g.add(c);
    var e = new THREE.Mesh(side, mat); e.position.x =  w / 2; g.add(e);
    g.userData.mat = mat;
    return g;
  }

  var scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(BAY, 0.024);
  var camera = new THREE.PerspectiveCamera(46, 1, 0.1, 200);
  var root = new THREE.Group();
  scene.add(root);

  /* --- the bench ---------------------------------------------------------- */
  var benchGeo = new THREE.BoxGeometry(4.6, 0.18, N * GAP + 18);
  var bench = new THREE.Mesh(benchGeo, new THREE.MeshBasicMaterial({ color: 0x2A2622 }));
  bench.position.set(0, -1.16, -(N * GAP) / 2 + 3);
  root.add(bench);
  var benchRail = frame(4.6, N * GAP + 18, 0.045, LIT, 0.62);
  benchRail.position.set(0, -1.06, bench.position.z);
  root.add(benchRail);

  /* --- six trays, each with a developing print ---------------------------- */
  var trays = [], hanging = [];

  for (var i = 0; i < N; i++) {
    var z = -i * GAP;

    var trayGeo = new THREE.BoxGeometry(3.1, 0.30, 2.15);
    var tray = new THREE.Mesh(trayGeo, new THREE.MeshBasicMaterial({ color: 0x151312 }));
    tray.position.set(0, -0.92, z);
    root.add(tray);

    var rim = frame(3.1, 2.15, 0.05, ENAMEL, 0.85);
    rim.position.set(0, -0.775, z);
    root.add(rim);

    /* the print itself — silver emulsion coming up out of grey */
    var print = new THREE.Mesh(
      new THREE.PlaneGeometry(2.6, 1.7),
      new THREE.MeshBasicMaterial({ color: SILVER, transparent: true, opacity: 0.12, side: THREE.DoubleSide })
    );
    print.rotation.x = -Math.PI / 2;
    print.position.set(0, -0.77, z);
    root.add(print);

    /* the image on it: a coverage grid, 4 columns of technique by 3 rows */
    var cells = [];
    for (var r = 0; r < 3; r++) {
      for (var c = 0; c < 4; c++) {
        /* the observe station carries the real verdict; the others fill in */
        var comesUp = (i === 3) ? VERDICT_ROW[c] : ((r * 4 + c) % 7 !== 5);
        var cell = new THREE.Mesh(
          new THREE.PlaneGeometry(0.5, 0.4),
          new THREE.MeshBasicMaterial({
            color: comesUp ? ENAMEL : DIM,
            transparent: true, opacity: 0
          })
        );
        cell.rotation.x = -Math.PI / 2;
        cell.position.set(-0.87 + c * 0.58, -0.762, z - 0.48 + r * 0.48);
        cell.userData = { up: comesUp, order: (r * 4 + c) / 12 };
        root.add(cell);
        cells.push(cell);
      }
    }

    trays.push({ rim: rim.userData.mat, print: print, cells: cells });

    /* enlarger over the exposure station */
    if (i === 1) {
      var post = new THREE.Mesh(
        new THREE.CylinderGeometry(0.07, 0.07, 3.6, 8),
        new THREE.MeshBasicMaterial({ color: 0x2A2622 })
      );
      post.position.set(1.62, 0.62, z);
      root.add(post);

      var headMesh = new THREE.Mesh(
        new THREE.BoxGeometry(0.8, 0.5, 0.62),
        new THREE.MeshBasicMaterial({ color: 0x332C27 })
      );
      headMesh.position.set(0, 1.72, z);
      root.add(headMesh);

      var beam = new THREE.Mesh(
        new THREE.ConeGeometry(1.4, 2.7, 26, 1, true),
        new THREE.MeshBasicMaterial({ color: LIT, transparent: true, opacity: 0.2, side: THREE.DoubleSide })
      );
      beam.position.set(0, 0.5, z);
      root.add(beam);
    }

    /* drying wire at the far end */
    if (i === N - 1) {
      var wire = new THREE.Mesh(
        new THREE.BoxGeometry(5.6, 0.028, 0.028),
        new THREE.MeshBasicMaterial({ color: ENAMEL, transparent: true, opacity: 0.42 })
      );
      wire.position.set(0, 1.48, z);
      wire.rotation.z = -0.027;
      root.add(wire);
      for (var h = 0; h < 4; h++) {
        var sheet = new THREE.Mesh(
          new THREE.PlaneGeometry(0.88, 1.14),
          new THREE.MeshBasicMaterial({ color: ENAMEL, transparent: true, opacity: 0.3, side: THREE.DoubleSide })
        );
        sheet.position.set(-2.0 + h * 1.32, 0.9, z);
        sheet.userData.phase = h * 1.3;
        root.add(sheet);
        hanging.push(sheet);
      }
    }
  }

  /* --- safelight itself, a warm bulb high on the back wall ---------------- */
  var lamp = new THREE.Mesh(
    new THREE.SphereGeometry(0.19, 14, 14),
    new THREE.MeshBasicMaterial({ color: LIT })
  );
  lamp.position.set(-2.5, 2.5, -N * GAP * 0.44);
  root.add(lamp);

  /* --- sizing ------------------------------------------------------------- */
  function resize() {
    var w = mount.clientWidth, h = mount.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);
  resize();

  /* --- scroll drives the walk, measured against the pinned track ---------- */
  var progress = 0, target = 0;
  function readScroll() {
    var max = track.offsetHeight - window.innerHeight;
    var y = window.pageYOffset - track.offsetTop;
    target = Math.max(0, Math.min(1, max > 0 ? y / max : 0));
  }
  window.addEventListener('scroll', readScroll, { passive: true });
  window.addEventListener('resize', readScroll);
  readScroll();

  var capEls = caps ? caps.children : [];
  var stripEls = strip ? strip.children : [];
  var t = 0, lastStation = -1;

  function tick() {
    window.requestAnimationFrame(tick);
    t += 0.016;
    progress += (target - progress) * (reduced ? 1 : 0.06);

    var pos = progress * (N - 1);
    var station = Math.min(N - 1, Math.round(pos));

    /* camera walks the bench */
    var sway = reduced ? 0 : Math.sin(t * 0.16) * 0.4;
    var z = 4.8 - progress * ((N - 1) * GAP);
    camera.position.set(sway, 1.36 + (reduced ? 0 : Math.sin(t * 0.11) * 0.1), z);
    camera.lookAt(sway * 0.4, -0.72, z - 6.6);

    /* each print develops as it is reached, and does not un-develop */
    for (var i = 0; i < N; i++) {
      var reach = Math.max(0, Math.min(1, (pos - (i - 0.6)) / 1.15));
      var tr = trays[i];
      tr.print.material.opacity = 0.1 + reach * 0.36;
      tr.rim.opacity = 0.45 + reach * 0.5;
      for (var c = 0; c < tr.cells.length; c++) {
        var cell = tr.cells[c];
        var em = Math.max(0, Math.min(1, (reach - cell.userData.order * 0.5) * 2.6));
        /* the ones that never come up stay a ghost, however long you look */
        cell.material.opacity = cell.userData.up ? em * 0.94 : em * 0.16;
      }
    }

    /* sheets on the wire move in the room's air */
    for (var s = 0; s < hanging.length; s++) {
      hanging[s].rotation.y = reduced ? 0.08 : Math.sin(t * 0.7 + hanging[s].userData.phase) * 0.15;
    }

    /* instruments */
    var secs = Math.round(progress * 186);
    clockEl.textContent = Math.floor(secs / 60) + ':' + String(secs % 60).padStart(2, '0');

    if (station !== lastStation) {
      lastStation = station;
      nowEl.textContent = STATIONS[station];
      for (var k = 0; k < stripEls.length; k++) {
        stripEls[k].classList.toggle('is-on', k === station);
      }
    }

    /* the opening statement holds screen one, then hands to the stations */
    var handover = progress > 0.09;
    openEl.classList.toggle('is-out', handover);
    hintEl.classList.toggle('is-out', handover);
    for (var q = 0; q < capEls.length; q++) {
      capEls[q].classList.toggle('is-on', handover && q === station);
    }

    renderer.render(scene, camera);
  }
  tick();
})();
