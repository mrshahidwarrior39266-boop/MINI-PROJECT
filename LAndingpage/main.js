/* ==========================================================================
   ARCHALEARN — 3D NIGHT VALLEY ENGINE (FERNHOLLOW HERITAGE)
   Three.js r128 + Virtual Scroller Camera Flight + 3D Mouse Physics + Web Audio
   ========================================================================== */

(function () {
  'use strict';

  // --------------------------------------------------------------------------
  // 1. Procedural Ambient Audio Engine with Low-Pass Hover Filter
  // --------------------------------------------------------------------------
  class ValleyAudio {
    constructor() {
      this.ctx = null;
      this.isInitialized = false;
      this.isMuted = true;
      this.droneOsc1 = null;
      this.droneOsc2 = null;
      this.filter = null;
      this.masterGain = null;
    }

    initAudio() {
      if (this.isInitialized) return;
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      this.ctx = new AudioCtx();

      const t = this.ctx.currentTime;
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(0, t);

      // Lowpass Filter for Atmospheric Muffling
      this.filter = this.ctx.createBiquadFilter();
      this.filter.type = 'lowpass';
      this.filter.frequency.setValueAtTime(320, t);

      // Deep celestial drone (55Hz & 110Hz harmonic)
      this.droneOsc1 = this.ctx.createOscillator();
      this.droneOsc1.type = 'sine';
      this.droneOsc1.frequency.setValueAtTime(55, t);

      this.droneOsc2 = this.ctx.createOscillator();
      this.droneOsc2.type = 'triangle';
      this.droneOsc2.frequency.setValueAtTime(110, t);

      this.droneOsc1.connect(this.filter);
      this.droneOsc2.connect(this.filter);
      this.filter.connect(this.masterGain);
      this.masterGain.connect(this.ctx.destination);

      this.droneOsc1.start();
      this.droneOsc2.start();
      this.isInitialized = true;
    }

    toggleMute() {
      if (!this.isInitialized) this.initAudio();
      if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume();

      this.isMuted = !this.isMuted;
      const t = this.ctx.currentTime;
      if (!this.isMuted) {
        this.masterGain.gain.cancelScheduledValues(t);
        this.masterGain.gain.linearRampToValueAtTime(0.045, t + 1.2);
      } else {
        this.masterGain.gain.cancelScheduledValues(t);
        this.masterGain.gain.linearRampToValueAtTime(0, t + 0.5);
      }
      return this.isMuted;
    }

    muffleAudio(muffle = true) {
      if (!this.filter || !this.ctx) return;
      const t = this.ctx.currentTime;
      this.filter.frequency.cancelScheduledValues(t);
      // On hover, muffle to 120Hz; in flight, open up to 450Hz
      this.filter.frequency.exponentialRampToValueAtTime(muffle ? 120 : 420, t + 0.6);
    }
  }

  const audioStore = new ValleyAudio();

  // --------------------------------------------------------------------------
  // 2. Three.js 3D Night Valley & Architectural Flight Engine
  // --------------------------------------------------------------------------
  class ArchalearnValley {
    constructor(container, onLoaded, onIntroDone) {
      this.container = container;
      this.onLoaded = onLoaded;
      this.onIntroDone = onIntroDone;

      this.scene = new THREE.Scene();
      this.scene.fog = new THREE.FogExp2(0x000000, 0.0016);

      this.camera = new THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.1, 2000);
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
      this.renderer.setSize(window.innerWidth, window.innerHeight);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this.container.appendChild(this.renderer.domElement);

      // Simulation State
      this.flightProgress = 0;
      this.flightSpeed = 0.0008;
      this.isHovering = false;
      this.hoverDispersal = 0; // 0 (normal) to 1 (dispersed sparks)
      this.mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
      this.touchStartY = 0;

      // Construct Smooth 3D Flight Path (Closed Spline)
      this.splinePath = new THREE.CatmullRomCurve3([
        new THREE.Vector3(0, 20, 0),
        new THREE.Vector3(60, 45, -300),
        new THREE.Vector3(-80, 25, -650),
        new THREE.Vector3(40, 60, -1000),
        new THREE.Vector3(0, 30, -1400),
        new THREE.Vector3(-50, 15, -900),
        new THREE.Vector3(50, 35, -450),
        new THREE.Vector3(0, 20, 0)
      ], true);

      this.buildParticleValley();
      this.buildSubjectCathedral();
      this.buildNeuralLandscape();
      this.bindInputs();

      // Trigger Loader Finished
      setTimeout(() => {
        if (this.onLoaded) this.onLoaded();
        setTimeout(() => {
          if (this.onIntroDone) this.onIntroDone();
        }, 300);
      }, 700);

      this.animate = this.animate.bind(this);
      requestAnimationFrame(this.animate);
    }

    // Thousands of glowing 3D flower and neural particles scattered along terrain
    buildParticleValley() {
      const count = 4500;
      this.particlesGeo = new THREE.BufferGeometry();
      const positions = new Float32Array(count * 3);
      const originalPositions = new Float32Array(count * 3);
      const colors = new Float32Array(count * 3);
      const sizes = new Float32Array(count);

      const goldColor = new THREE.Color(0xe59b34);
      const tealColor = new THREE.Color(0x14b8a6);
      const creamColor = new THREE.Color(0xf5efe2);

      for (let i = 0; i < count; i++) {
        const i3 = i * 3;
        // Spread along a vast 3D canyon
        const angle = Math.random() * Math.PI * 2;
        const radius = Math.random() * 450 + 40;
        const x = Math.cos(angle) * radius;
        const y = (Math.random() - 0.4) * 180;
        const z = -Math.random() * 1600;

        positions[i3] = x;
        positions[i3 + 1] = y;
        positions[i3 + 2] = z;

        originalPositions[i3] = x;
        originalPositions[i3 + 1] = y;
        originalPositions[i3 + 2] = z;

        // Color blending: gold for canon, teal for mind, cream accents
        const rand = Math.random();
        const c = rand < 0.45 ? goldColor : rand < 0.85 ? tealColor : creamColor;
        colors[i3] = c.r;
        colors[i3 + 1] = c.g;
        colors[i3 + 2] = c.b;

        sizes[i] = Math.random() * 22 + 8;
      }

      this.particlesGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      this.particlesGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
      this.particlesGeo.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
      this.originalParticlePositions = originalPositions;

      // Soft circular point texture
      const canvas = document.createElement('canvas');
      canvas.width = canvas.height = 64;
      const ctx = canvas.getContext('2d');
      const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
      grad.addColorStop(0, 'rgba(255,255,255,1)');
      grad.addColorStop(0.3, 'rgba(255,255,255,0.7)');
      grad.addColorStop(0.7, 'rgba(255,255,255,0.2)');
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 64, 64);

      const texture = new THREE.CanvasTexture(canvas);

      const pMaterial = new THREE.PointsMaterial({
        size: 7,
        vertexColors: true,
        map: texture,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });

      this.particleSystem = new THREE.Points(this.particlesGeo, pMaterial);
      this.scene.add(this.particleSystem);
    }

    // Monolithic 3D Subject Cathedral (Tungsten Gold Lattice)
    buildSubjectCathedral() {
      const geo = new THREE.IcosahedronGeometry(75, 2);
      const wireMat = new THREE.MeshBasicMaterial({
        color: 0xe59b34,
        wireframe: true,
        transparent: true,
        opacity: 0.35,
        blending: THREE.AdditiveBlending
      });
      this.cathedral = new THREE.Mesh(geo, wireMat);
      this.cathedral.position.set(-140, 80, -450);
      this.scene.add(this.cathedral);

      // Inner glowing core
      const coreGeo = new THREE.SphereGeometry(25, 16, 16);
      const coreMat = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.85
      });
      this.cathedralCore = new THREE.Mesh(coreGeo, coreMat);
      this.cathedral.add(this.cathedralCore);
    }

    // Bioluminescent 3D Neural Landscape (Azure Teal)
    buildNeuralLandscape() {
      const curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(120, -20, -200),
        new THREE.Vector3(160, 40, -450),
        new THREE.Vector3(110, 80, -750),
        new THREE.Vector3(140, 20, -1100)
      ]);
      const tubeGeo = new THREE.TubeGeometry(curve, 80, 18, 12, false);
      const tubeMat = new THREE.MeshBasicMaterial({
        color: 0x14b8a6,
        wireframe: true,
        transparent: true,
        opacity: 0.3,
        blending: THREE.AdditiveBlending
      });
      this.neuralTube = new THREE.Mesh(tubeGeo, tubeMat);
      this.scene.add(this.neuralTube);
    }

    bindInputs() {
      window.addEventListener('resize', () => {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
      });

      window.addEventListener('mousemove', (e) => {
        this.mouse.targetX = (e.clientX / window.innerWidth - 0.5) * 2;
        this.mouse.targetY = (e.clientY / window.innerHeight - 0.5) * 2;
      });

      // Virtual Scroller: Wheel drives flight along spline
      window.addEventListener('wheel', (e) => {
        const delta = e.deltaY * 0.0004;
        this.flightProgress = (this.flightProgress + delta + 1) % 1;
        this.tightenVignette(Math.abs(delta) > 0.01);
      }, { passive: true });

      // Touch flight for mobile
      window.addEventListener('touchstart', (e) => {
        this.touchStartY = e.touches[0].clientY;
      }, { passive: true });

      window.addEventListener('touchmove', (e) => {
        const delta = (this.touchStartY - e.touches[0].clientY) * 0.0012;
        this.touchStartY = e.touches[0].clientY;
        this.flightProgress = (this.flightProgress + delta + 1) % 1;
      }, { passive: true });
    }

    tightenVignette(isFast) {
      const v = document.getElementById('vignette');
      if (v) v.classList.toggle('fast', isFast);
    }

    // Fernhollow Hover Transition (Flight stops, points disperse into floating sparks)
    startHoverTransition() {
      this.isHovering = true;
      audioStore.muffleAudio(true);
    }

    stopHoverTransition() {
      this.isHovering = false;
      audioStore.muffleAudio(false);
    }

    animate(time) {
      requestAnimationFrame(this.animate);

      // Smooth mouse damping
      this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.05;
      this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.05;

      // Handle hover transition interpolation
      const targetDispersal = this.isHovering ? 1 : 0;
      this.hoverDispersal += (targetDispersal - this.hoverDispersal) * 0.05;

      // Camera flight: Auto-drift forward when not hovering
      if (!this.isHovering) {
        this.flightProgress = (this.flightProgress + this.flightSpeed) % 1;
      }

      // Compute Camera Position along Spline Path
      const camPos = this.splinePath.getPointAt(this.flightProgress);
      const lookAtPos = this.splinePath.getPointAt((this.flightProgress + 0.03) % 1);

      this.camera.position.copy(camPos);
      // Mouse tilts camera subtly toward cursor
      this.camera.position.x += this.mouse.x * 14;
      this.camera.position.y -= this.mouse.y * 10;
      this.camera.lookAt(lookAtPos.x + this.mouse.x * 20, lookAtPos.y - this.mouse.y * 16, lookAtPos.z);

      // Rotate 3D Artifacts
      if (this.cathedral) {
        this.cathedral.rotation.x += 0.003;
        this.cathedral.rotation.y += 0.005;
      }
      if (this.neuralTube) {
        this.neuralTube.rotation.z += 0.002;
      }

      // Particle physics: Dispersal during hover & cursor repulsion
      const positions = this.particlesGeo.attributes.position.array;
      const count = positions.length / 3;

      for (let i = 0; i < count; i++) {
        const i3 = i * 3;
        const ox = this.originalParticlePositions[i3];
        const oy = this.originalParticlePositions[i3 + 1];
        const oz = this.originalParticlePositions[i3 + 2];

        // Dispersal vector outward when hovering portal
        if (this.hoverDispersal > 0.01) {
          const angle = Math.sin(i * 123.45) * Math.PI * 2;
          const disperseDist = 60 * this.hoverDispersal;
          positions[i3] = ox + Math.cos(angle) * disperseDist;
          positions[i3 + 1] = oy + Math.sin(angle) * disperseDist;
        } else {
          positions[i3] = ox;
          positions[i3 + 1] = oy;
        }

        // Bloom particle size as camera approaches
        const dist = this.camera.position.distanceTo(new THREE.Vector3(positions[i3], positions[i3 + 1], positions[i3 + 2]));
        if (dist < 100) {
          positions[i3 + 1] += Math.sin(time * 0.003 + i) * 0.4;
        }
      }
      this.particlesGeo.attributes.position.needsUpdate = true;

      this.renderer.render(this.scene, this.camera);
    }
  }

  // --------------------------------------------------------------------------
  // 3. Bootstrapping & UI Coordination
  // --------------------------------------------------------------------------
  const valleyStage = document.getElementById('valley-stage');
  const loader = document.getElementById('loader');
  const ui = document.getElementById('ui');
  const soundBtn = document.getElementById('sound-btn');
  const goBtn = document.getElementById('go-btn');
  const cockpitDrawer = document.getElementById('cockpit-drawer');
  const closeDrawerBtn = document.getElementById('close-drawer-btn');
  const cockpitTriggers = document.querySelectorAll('.open-cockpit-trigger');

  let valleyEngine = null;

  if (typeof THREE !== 'undefined' && valleyStage) {
    valleyEngine = new ArchalearnValley(
      valleyStage,
      () => { if (loader) loader.classList.add('gone'); },
      () => { if (ui) ui.classList.add('on'); }
    );
  }

  // Audio Toggle Button
  if (soundBtn) {
    soundBtn.onclick = () => {
      const isMuted = audioStore.toggleMute();
      soundBtn.setAttribute('aria-pressed', String(!isMuted));
    };
  }

  // Hover Transition Listeners on Central Portal Arrow
  if (goBtn && valleyEngine) {
    goBtn.addEventListener('pointerenter', () => valleyEngine.startHoverTransition());
    goBtn.addEventListener('pointerleave', () => valleyEngine.stopHoverTransition());
  }

  // Cockpit Drawer Controls
  cockpitTriggers.forEach((trigger) => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      if (cockpitDrawer) cockpitDrawer.classList.add('open');
      audioStore.muffleAudio(true);
    });
  });

  if (closeDrawerBtn) {
    closeDrawerBtn.addEventListener('click', () => {
      if (cockpitDrawer) cockpitDrawer.classList.remove('open');
      audioStore.muffleAudio(false);
    });
  }

  // Diagnostic Node Inspector in Cockpit
  const nodes = document.querySelectorAll('.cockpit-concept-node');
  const inspector = document.getElementById('node-diagnostic-output');

  nodes.forEach((node) => {
    node.addEventListener('click', () => {
      const concept = node.dataset.concept;
      const confidence = node.dataset.confidence;
      const reasoning = node.dataset.reasoning;

      if (inspector) {
        inspector.innerHTML = `
          <div style="padding:18px; background:rgba(20,184,166,0.08); border-left:3px solid var(--teal-primary); border-radius:6px;">
            <div style="font-family:var(--font-mono); font-size:0.75rem; color:var(--teal-primary); margin-bottom:6px; letter-spacing:0.12em;">
              [DIAGNOSTIC TRACE] ${concept.toUpperCase()} // CONFIDENCE: ${confidence}%
            </div>
            <p style="font-size:0.92rem; color:#f5efe2; line-height:1.7;">${reasoning}</p>
          </div>
        `;
      }
    });
  });

  console.log('%c ARCHALEARN // Night Valley 3D Engine Active', 'color: #e59b34; font-weight: bold;');
})();
