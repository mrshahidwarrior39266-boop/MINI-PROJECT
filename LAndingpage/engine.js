// Cinematic Scroll Storytelling — engine core.
// Pure logic: no DOM, no Three.js, no GSAP. Drop into any stack.
// Logic is covered by scripts/selftest.mjs. The DOM helpers at the bottom are NOT covered; verify in a browser.
//
// Units: scroll position is measured in "screens" (1 = one viewport height of virtual travel).

// ---------------------------------------------------------------- math helpers
export const clamp = (v, min = 0, max = 1) => Math.min(max, Math.max(min, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const remap = (v, inMin, inMax, outMin = 0, outMax = 1, clampOutput = true) => {
  const t = inMax === inMin ? 0 : (v - inMin) / (inMax - inMin);
  return lerp(outMin, outMax, clampOutput ? clamp(t) : t);
};
export const smoothstep = (t) => { const x = clamp(t); return x * x * (3 - 2 * x); };
export const easeOutExpo = (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp(t)));
export const easeInOutCubic = (t) => {
  const x = clamp(t);
  return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
};

// Frame-rate-independent damping. alpha60 is the per-frame lerp factor you'd have used at 60 fps.
export const lambdaFromAlpha = (alpha60) => -60 * Math.log(1 - alpha60);
export const damp = (current, target, lambda, dt) =>
  lerp(current, target, 1 - Math.exp(-lambda * dt));

// ---------------------------------------------------------------- virtual scroll
export class VirtualScroll {
  constructor({ total = 1, lambda = lambdaFromAlpha(0.1), epsilon = 1e-4 } = {}) {
    this.total = total;
    this.lambda = lambda;
    this.epsilon = epsilon;
    this.position = 0;   // eased value everything reads
    this.target = 0;     // where input wants to go
    this.velocity = 0;   // screens per second
    this.locks = new Map(); // id -> position where travel must stop (gates)
    this.auto = null;    // active auto-advance tween
  }

  get progress() { return this.total > 0 ? this.position / this.total : 0; }

  // Furthest position input may reach: next lock at/after the current position, else total.
  get ceiling() {
    let c = this.total;
    for (const p of this.locks.values()) {
      if (p >= this.position - this.epsilon && p < c) c = p;
    }
    return c;
  }

  setTotal(total) { this.total = total; this.target = clamp(this.target, 0, total); }

  feed(deltaScreens) {
    if (this.auto) return; // input is ignored during an auto-advance
    this.target = clamp(this.target + deltaScreens, 0, this.ceiling);
  }

  lock(id, position) {
    this.locks.set(id, position);
    this.target = Math.min(this.target, this.ceiling);
  }
  unlock(id) { this.locks.delete(id); }

  jumpTo(position) {
    this.position = this.target = clamp(position, 0, this.total);
    this.velocity = 0;
    this.auto = null;
  }

  // Smoothstep auto-advance (used when a gate completes). Ignores input until finished.
  autoTo(position, duration = 1.2, onDone) {
    this.auto = { from: this.position, to: clamp(position, 0, this.total), t: 0, duration, onDone };
  }

  update(dt) {
    const prev = this.position;
    if (this.auto) {
      const a = this.auto;
      a.t += dt;
      const k = smoothstep(a.duration > 0 ? a.t / a.duration : 1);
      this.position = this.target = lerp(a.from, a.to, k);
      if (a.t >= a.duration) {
        this.position = this.target = a.to;
        this.auto = null;
        if (a.onDone) a.onDone();
      }
    } else {
      this.position = damp(this.position, this.target, this.lambda, dt);
      if (Math.abs(this.target - this.position) < this.epsilon) this.position = this.target;
    }
    this.velocity = dt > 0 ? (this.position - prev) / dt : 0;
    return this.position;
  }
}

// ---------------------------------------------------------------- segment timeline
// segment: { id, scrollVh, enter?(ctx), scrub?(local, ctx), update?(dt, local, ctx), teardown?(ctx) }
// States: idle -> active -> done. A jump or fast scroll replays enter -> scrub(1) -> teardown for
// every earlier segment, so arriving anywhere initialises identically to a linear pass.
export class Timeline {
  constructor(segments) {
    let offset = 0;
    this.segments = segments.map((s) => {
      const seg = { ...s, state: 'idle', start: offset, end: offset + s.scrollVh };
      offset = seg.end;
      return seg;
    });
    this.total = offset;
  }

  indexAt(position) {
    const p = clamp(position, 0, this.total);
    for (let i = 0; i < this.segments.length; i++) if (p < this.segments[i].end) return i;
    return this.segments.length - 1;
  }

  localProgress(seg, position) {
    const len = seg.end - seg.start;
    return len <= 0 ? 1 : clamp((position - seg.start) / len);
  }

  sync(position, dt = 0, ctx) {
    if (this.segments.length === 0) return { index: -1, local: 0 };
    const p = clamp(position, 0, this.total);
    const idx = this.indexAt(p);

    // 1) Settle everything behind the current segment (forward travel or jump).
    for (let i = 0; i < idx; i++) {
      const s = this.segments[i];
      if (s.state === 'idle') { s.enter?.(ctx); s.scrub?.(1, ctx); s.teardown?.(ctx); s.state = 'done'; }
      else if (s.state === 'active') { s.scrub?.(1, ctx); s.teardown?.(ctx); s.state = 'done'; }
    }
    // 2) Reset everything ahead (rewind).
    for (let i = idx + 1; i < this.segments.length; i++) {
      const s = this.segments[i];
      if (s.state === 'active') { s.scrub?.(0, ctx); s.teardown?.(ctx); }
      s.state = 'idle';
    }
    // 3) Activate the current segment.
    const cur = this.segments[idx];
    if (cur.state !== 'active') { cur.enter?.(ctx); cur.state = 'active'; }
    const local = this.localProgress(cur, p);
    cur.scrub?.(local, ctx);
    cur.update?.(dt, local, ctx);
    return { index: idx, local, id: cur.id };
  }
}

// ---------------------------------------------------------------- hold gate
// States: hidden -> armed -> holding -> complete. Locks the scroll at `at` until satisfied.
export class HoldGate {
  constructor({
    id, at, holdDuration = 1.5, releaseLambda = 4, arriveEpsilon = 0.02,
    passScreens = 0.6, passDuration = 1.2,
    onShow, onHoldProgress, onHoldComplete,
  }) {
    Object.assign(this, {
      id, at, holdDuration, releaseLambda, arriveEpsilon, passScreens, passDuration,
      onShow, onHoldProgress, onHoldComplete,
    });
    this.state = 'hidden';
    this.charge = 0;
    this.scroll = null;
  }

  attach(scroll) { this.scroll = scroll; scroll.lock(this.id, this.at); return this; }

  press() { if (this.state === 'armed') this.state = 'holding'; }
  release() { if (this.state === 'holding') this.state = 'armed'; }

  update(dt) {
    const s = this.scroll;
    if (!s || this.state === 'complete') return;

    if (this.state === 'hidden' && s.position >= this.at - this.arriveEpsilon) {
      this.state = 'armed';
      this.onShow?.(this);
    }
    if (this.state === 'holding') {
      this.charge = Math.min(1, this.charge + dt / this.holdDuration);
    } else if (this.state === 'armed') {
      this.charge *= Math.exp(-this.releaseLambda * dt); // recoil on early release
      if (this.charge < 1e-3) this.charge = 0;
    }
    if (this.state === 'armed' || this.state === 'holding') {
      this.onHoldProgress?.(this.charge, smoothstep(this.charge));
    }
    if (this.state === 'holding' && this.charge >= 1) {
      this.state = 'complete';
      s.unlock(this.id);
      s.autoTo(this.at + this.passScreens, this.passDuration);
      this.onHoldComplete?.(this);
    }
  }
}

// ---------------------------------------------------------------- adaptive quality
// Rolling frame-time average with hysteresis and cooldown. Tiers change polish, never the story.
export class QualityManager {
  constructor({
    tiers = ['low', 'medium', 'high'], startIndex = 1, windowSize = 45,
    downMs = 22, upMs = 12, cooldownMs = 3000, maxSampleMs = 100, onChange,
  } = {}) {
    Object.assign(this, { tiers, windowSize, downMs, upMs, cooldownMs, maxSampleMs, onChange });
    this.index = startIndex;
    this.buf = [];
    this.lastChange = -Infinity;
  }

  get tier() { return this.tiers[this.index]; }
  get average() { return this.buf.length ? this.buf.reduce((a, b) => a + b, 0) / this.buf.length : 0; }

  push(frameMs, nowMs) {
    if (!(frameMs > 0) || frameMs > 1000) return; // hidden tab / breakpoint: not a performance signal
    this.buf.push(Math.min(frameMs, this.maxSampleMs));
    if (this.buf.length > this.windowSize) this.buf.shift();
    if (this.buf.length < this.windowSize) return;
    if (nowMs - this.lastChange < this.cooldownMs) return;
    const avg = this.average;
    if (avg > this.downMs && this.index > 0) this.#change(this.index - 1, nowMs);
    else if (avg < this.upMs && this.index < this.tiers.length - 1) this.#change(this.index + 1, nowMs);
  }

  #change(i, nowMs) {
    this.index = i;
    this.buf.length = 0;
    this.lastChange = nowMs;
    this.onChange?.(this.tiers[i], i);
  }
}

// ---------------------------------------------------------------- circle ("draw a zero") gate
// points: [{x, y}] in a space where x and y share one scale (normalise by the shorter viewport side).
// Defaults are starting values from a published re-implementation; test with real hands.
export function strokeIsZero(points, {
  minPoints = 12, minRadius = 0.02, maxCv = 0.35, minTravel = 5.76, closureFactor = 1.0,
} = {}) {
  if (!Array.isArray(points) || points.length < minPoints) return { ok: false, reason: 'too-few-points' };
  const n = points.length;
  let cx = 0, cy = 0;
  for (const p of points) { cx += p.x; cy += p.y; }
  cx /= n; cy /= n;

  const radii = points.map((p) => Math.hypot(p.x - cx, p.y - cy));
  const r = radii.reduce((a, b) => a + b, 0) / n;
  if (r < minRadius) return { ok: false, reason: 'too-small', metrics: { r } };

  const variance = radii.reduce((a, x) => a + (x - r) * (x - r), 0) / n;
  const cv = Math.sqrt(Math.max(0, variance)) / r;
  if (cv > maxCv) return { ok: false, reason: 'not-round', metrics: { r, cv } };

  let travel = 0;
  let prev = Math.atan2(points[0].y - cy, points[0].x - cx);
  for (let i = 1; i < n; i++) {
    const a = Math.atan2(points[i].y - cy, points[i].x - cx);
    let d = a - prev;
    while (d > Math.PI) d -= 2 * Math.PI;
    while (d < -Math.PI) d += 2 * Math.PI;
    travel += d;
    prev = a;
  }
  if (Math.abs(travel) < minTravel) return { ok: false, reason: 'incomplete-loop', metrics: { r, cv, travel } };

  const gap = Math.hypot(points[n - 1].x - points[0].x, points[n - 1].y - points[0].y);
  if (gap > r * closureFactor) return { ok: false, reason: 'open-loop', metrics: { r, cv, travel, gap } };

  return { ok: true, metrics: { r, cv, travel, gap } };
}

// ---------------------------------------------------------------- frame + idle queues
// FrameQueue: run callbacks right AFTER the next render call (sync audio to the first frame of an effect).
export class FrameQueue {
  #q = [];
  next(fn) { this.#q.push(fn); }
  flush() { const q = this.#q; this.#q = []; for (const fn of q) fn(); }
}

const defaultSchedule = (cb) =>
  typeof requestIdleCallback === 'function'
    ? requestIdleCallback(cb, { timeout: 200 })
    : setTimeout(() => cb({ timeRemaining: () => 8 }), 16);

// IdleQueue: queue expensive jobs (GPU texture uploads), drain on idle, flushSync() before they are needed.
export class IdleQueue {
  #q = [];
  #scheduled = false;
  constructor({ schedule = defaultSchedule, minSliceMs = 4 } = {}) {
    this.schedule = schedule;
    this.minSliceMs = minSliceMs;
  }
  get size() { return this.#q.length; }
  push(job) { this.#q.push(job); this.#kick(); }
  flushSync() { while (this.#q.length) this.#q.shift()(); }
  drain(deadline) {
    if (!this.#q.length) return;
    do { this.#q.shift()(); } // always at least one job per slice: no starvation
    while (this.#q.length && deadline && deadline.timeRemaining() > this.minSliceMs);
  }
  #kick() {
    if (this.#scheduled || !this.#q.length) return;
    this.#scheduled = true;
    this.schedule((deadline) => { this.#scheduled = false; this.drain(deadline); this.#kick(); });
  }
}

// ---------------------------------------------------------------- DOM helpers (browser only; not self-tested)
// Wheel / touch / keyboard -> VirtualScroll. Returns an unbind function.
export function bindDomInput(el, scroll, {
  wheelScale = 1, touchScale = 1.4, keyStep = 0.25, maxWheelStep = 0.12,
  viewportHeight = () => window.innerHeight, reserveSpace = () => false,
} = {}) {
  let lastY = null;
  const vh = () => Math.max(1, viewportHeight());

  const onWheel = (e) => {
    e.preventDefault();
    const unit = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? vh() : 1;
    const step = clamp((e.deltaY * unit) / vh() * wheelScale, -maxWheelStep, maxWheelStep);
    scroll.feed(step);
  };
  const onTouchStart = (e) => { lastY = e.touches[0].clientY; };
  const onTouchMove = (e) => {
    e.preventDefault();
    const y = e.touches[0].clientY;
    if (lastY !== null) scroll.feed(-((y - lastY) / vh()) * touchScale);
    lastY = y;
  };
  const onTouchEnd = () => { lastY = null; };
  const onKey = (e) => {
    switch (e.key) {
      case 'ArrowDown': case 'PageDown': scroll.feed(keyStep); break;
      case 'ArrowUp': case 'PageUp': scroll.feed(-keyStep); break;
      case ' ': if (!reserveSpace()) { scroll.feed(e.shiftKey ? -keyStep : keyStep); e.preventDefault(); } break;
      case 'Home': scroll.feed(-scroll.total); break;
      case 'End': scroll.feed(scroll.total); break;
      default: return;
    }
  };

  el.addEventListener('wheel', onWheel, { passive: false });
  el.addEventListener('touchstart', onTouchStart, { passive: true });
  el.addEventListener('touchmove', onTouchMove, { passive: false });
  el.addEventListener('touchend', onTouchEnd);
  el.addEventListener('touchcancel', onTouchEnd);
  window.addEventListener('keydown', onKey);
  return () => {
    el.removeEventListener('wheel', onWheel);
    el.removeEventListener('touchstart', onTouchStart);
    el.removeEventListener('touchmove', onTouchMove);
    el.removeEventListener('touchend', onTouchEnd);
    el.removeEventListener('touchcancel', onTouchEnd);
    window.removeEventListener('keydown', onKey);
  };
}

// Pointer + keyboard hold for a HoldGate. Always releases on cancel/blur/hidden so a hold can never get stuck.
export function bindHoldInput(gate, el, { key = ' ' } = {}) {
  const down = () => gate.press();
  const up = () => gate.release();
  const kd = (e) => { if (e.key === key && !e.repeat) { gate.press(); e.preventDefault(); } };
  const ku = (e) => { if (e.key === key) gate.release(); };
  const vis = () => { if (document.hidden) gate.release(); };

  el.addEventListener('pointerdown', down);
  window.addEventListener('pointerup', up);
  window.addEventListener('pointercancel', up);
  window.addEventListener('blur', up);
  window.addEventListener('keydown', kd);
  window.addEventListener('keyup', ku);
  document.addEventListener('visibilitychange', vis);
  return () => {
    el.removeEventListener('pointerdown', down);
    window.removeEventListener('pointerup', up);
    window.removeEventListener('pointercancel', up);
    window.removeEventListener('blur', up);
    window.removeEventListener('keydown', kd);
    window.removeEventListener('keyup', ku);
    document.removeEventListener('visibilitychange', vis);
  };
}
