/**
 * nl-nym.js — Nym Mascot System v1.0
 * NymbleLogic / Nymble Jr
 * The Good Neighbor Guard — Christopher Hughes
 *
 * Nym = athletic urban-acrobat rabbit
 * Kid Mode ONLY — Pro Mode receives no Nym behavior
 *
 * Colors:
 *   Primary fur:  #2D3436
 *   Tech accent:  #00D2FF
 *   White:        #FFFFFF
 */

window.NYM = (() => {
  'use strict';

  // ═══════════════════════════════════════════════════════
  // SVG — Base Nym character (vector, high contrast)
  // ═══════════════════════════════════════════════════════
  const NYM_SVG = `
<svg id="nym-character" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 160" width="120" height="160" aria-label="Nym the rabbit">
  <!-- EARS — lightning V shape -->
  <g class="nym-ears">
    <!-- Left ear -->
    <path d="M38 72 L28 20 L34 18 L42 58 Z" fill="#2D3436" stroke="#00D2FF" stroke-width="1.5"/>
    <path d="M39 68 L31 26 L34 24 L41 60 Z" fill="#00D2FF" opacity="0.4"/>
    <!-- Right ear -->
    <path d="M82 72 L92 20 L86 18 L78 58 Z" fill="#2D3436" stroke="#00D2FF" stroke-width="1.5"/>
    <path d="M81 68 L89 26 L86 24 L79 60 Z" fill="#00D2FF" opacity="0.4"/>
  </g>
  <!-- SCARF / tech accent stripe -->
  <rect class="nym-scarf" x="42" y="96" width="36" height="8" rx="4" fill="#00D2FF" opacity="0.9"/>
  <!-- HEAD -->
  <ellipse class="nym-head" cx="60" cy="72" rx="26" ry="24" fill="#2D3436" stroke="#FFFFFF" stroke-width="1"/>
  <!-- FACE — eyes -->
  <ellipse cx="50" cy="70" rx="5" ry="5.5" fill="#FFFFFF"/>
  <ellipse cx="70" cy="70" rx="5" ry="5.5" fill="#FFFFFF"/>
  <circle  cx="51.5" cy="70.5" r="3" fill="#1a1040"/>
  <circle  cx="71.5" cy="70.5" r="3" fill="#1a1040"/>
  <!-- Eye glints -->
  <circle cx="53" cy="68.5" r="1.2" fill="#FFFFFF"/>
  <circle cx="73" cy="68.5" r="1.2" fill="#FFFFFF"/>
  <!-- Nose -->
  <ellipse cx="60" cy="79" rx="3" ry="2" fill="#00D2FF"/>
  <!-- Mouth — small confident smile -->
  <path d="M56 82 Q60 86 64 82" fill="none" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/>
  <!-- TORSO — tapered athletic -->
  <path d="M44 96 Q36 100 34 118 Q48 126 60 126 Q72 126 86 118 Q84 100 76 96 Z" fill="#2D3436" stroke="#FFFFFF" stroke-width="0.8"/>
  <!-- Tech stripe on chest -->
  <path d="M50 100 Q60 97 70 100 Q68 112 60 114 Q52 112 50 100Z" fill="#00D2FF" opacity="0.2"/>
  <!-- ARMS -->
  <path class="nym-arm-l" d="M44 100 Q30 108 28 120" fill="none" stroke="#2D3436" stroke-width="10" stroke-linecap="round"/>
  <path class="nym-arm-r" d="M76 100 Q90 108 92 120" fill="none" stroke="#2D3436" stroke-width="10" stroke-linecap="round"/>
  <!-- Hands -->
  <circle cx="28" cy="121" r="6" fill="#2D3436" stroke="#FFFFFF" stroke-width="0.8"/>
  <circle cx="92" cy="121" r="6" fill="#2D3436" stroke="#FFFFFF" stroke-width="0.8"/>
  <!-- LEGS — strong for jumping -->
  <path class="nym-leg-l" d="M48 124 Q44 138 38 148 Q44 152 50 150 Q54 140 54 126Z" fill="#2D3436" stroke="#FFFFFF" stroke-width="0.8"/>
  <path class="nym-leg-r" d="M72 124 Q76 138 82 148 Q76 152 70 150 Q66 140 66 126Z" fill="#2D3436" stroke="#FFFFFF" stroke-width="0.8"/>
  <!-- Feet — strong landing pads -->
  <ellipse cx="42" cy="151" rx="12" ry="6" fill="#2D3436" stroke="#00D2FF" stroke-width="1.2"/>
  <ellipse cx="78" cy="151" rx="12" ry="6" fill="#2D3436" stroke="#00D2FF" stroke-width="1.2"/>
  <!-- Tech ring glow under feet (landing effect, hidden by default) -->
  <ellipse class="nym-landing-glow" cx="60" cy="158" rx="30" ry="5" fill="#00D2FF" opacity="0" filter="blur(4px)"/>
</svg>`;

  // ═══════════════════════════════════════════════════════
  // PHRASE BANK
  // ═══════════════════════════════════════════════════════
  const PHRASES = {
    greeting: [
      "Yo! I'm Nym — what are we building today? 🔥",
      "Hey! Ready to snap something together? Let's go!",
      "What's up! Nym here — drop your idea and I'll make it real.",
      "Back for more? Let's build something awesome! 🚀",
      "Nym reporting for duty — what's the mission?",
    ],
    prompt_invite: [
      "Tell me what you want — game, app, anything! ⬆️",
      "Type your idea up there and hit BUILD 👆",
      "What's the vision? Games? Tools? Shoot your shot! 🎯",
      "Write it, I'll build it. Simple as that.",
      "Your idea goes in the box. My crew handles the rest. 👆",
    ],
    encouragement: [
      "You're on it! Keep going 💪",
      "That's a great idea — this is gonna be fun!",
      "Nice pick! Atlas and the crew are on it 🏗️",
      "Love the creativity! Let's snap this together.",
      "Oh this is gonna be good. Trust the process 🔥",
    ],
    help: [
      "Stuck? Try one of the starter chips below 👇",
      "Not sure what to build? Try: 'a snake game with space aliens'",
      "Tip: the more detail you give, the better the build!",
      "Feeling lost? Just describe what you want to PLAY or USE.",
      "No worries — even 'make me a clicker game' is enough to start!",
    ],
    success_celebrate: [
      "LETS GOOO! Your app is LIVE! 🎉🔥",
      "Built and ready! You just made something real! 🏆",
      "BOOM! The team delivered. Hit Play and go! 🚀",
      "That's a W! Download it, share it, remix it! 💥",
      "Your creation is ready! The House of AI came through! 🐇⚡",
    ],
    error_recovery: [
      "Oops! Let's shake that off and try again 💪",
      "Even the best builders hit bumps — tweak and rerun!",
      "No stress! Add more detail and let's go again.",
      "My crew hit a snag. A small change might fix it!",
      "That happens sometimes. Want to try a different idea?",
    ],
    remix_suggestion: [
      "Want to level it up? Hit Remix! 🪄",
      "Not quite right? Remix it — describe what to change.",
      "Looking good! Remix it to add more features 🔥",
      "Remix is your superpower — use it!",
      "One click and you can tweak anything. That's the magic.",
    ],
    goodbye: [
      "See ya! Come back when the next idea hits 🐇",
      "Switching to Pro? I'll be here if you come back!",
      "Later! Your projects are saved 💾",
      "Catch you next build! 🚀",
    ],
    loading: [
      "Atlas is drawing up the plans… 📐",
      "Byte is writing your code… 💻",
      "Scout is testing every corner… 🔍",
      "Shield is locking it down… 🛡️",
      "The crew is on it — almost there! ⚡",
    ],
  };

  // ── Track recent phrases per bank to avoid repetition ─
  const _recent = {};
  function getNymPhrase(bank) {
    const list = PHRASES[bank];
    if (!list) return '';
    if (!_recent[bank]) _recent[bank] = [];
    const available = list.filter(p => !_recent[bank].includes(p));
    const pool = available.length ? available : list;
    const pick = pool[Math.floor(Math.random() * pool.length)];
    _recent[bank].push(pick);
    if (_recent[bank].length > Math.floor(list.length / 2)) _recent[bank].shift();
    return pick;
  }

  // ═══════════════════════════════════════════════════════
  // DOM MOUNT — Nym widget container (Kid Mode only)
  // ═══════════════════════════════════════════════════════
  let _mounted = false;
  let _container = null;
  let _bubble = null;
  let _currentState = null;
  let _idleTimer = null;

  function mount() {
    if (_mounted) return;
    clearTimeout(_unmountTimer); // cancel any in-flight unmount (mode switch race)
    _mounted = true;

    // Wrapper fixed bottom-right
    _container = document.createElement('div');
    _container.id = 'nym-widget';
    _container.innerHTML = `
      <div id="nym-bubble" class="nym-bubble" role="status" aria-live="polite"></div>
      <div id="nym-svg-wrap" class="nym-svg-wrap">${NYM_SVG}</div>
    `;
    document.body.appendChild(_container);
    _bubble = document.getElementById('nym-bubble');

    // Click Nym → help phrase
    document.getElementById('nym-svg-wrap').addEventListener('click', () => {
      speak(getNymPhrase('help'), true);
    });

    // Inject styles
    injectStyles();
  }

  let _unmountTimer = null;
  function unmount() {
    if (!_mounted) return;
    const w = document.getElementById('nym-widget');
    if (w) w.remove();
    _mounted = false;
    _container = null;
    _bubble = null;
  }

  // ═══════════════════════════════════════════════════════
  // ANIMATION STATES
  // ═══════════════════════════════════════════════════════
  const STATES = {
    idle_active:       'nym-idle',
    enter_skid:        'nym-skid',
    point_target:      'nym-point',
    cheer_flip:        'nym-cheer',
    error_wobble:      'nym-wobble',
    celebrate_parkour: 'nym-celebrate',
    logo_morph:        'nym-logo-morph',
  };

  function setState(stateName) {
    if (!_mounted) return;
    const wrap = document.getElementById('nym-svg-wrap');
    if (!wrap) return;

    // Clear all state classes
    Object.values(STATES).forEach(cls => wrap.classList.remove(cls));
    _currentState = stateName;
    if (STATES[stateName]) wrap.classList.add(STATES[stateName]);

    // Auto-return to idle after action states
    const actionStates = ['enter_skid','cheer_flip','error_wobble','celebrate_parkour'];
    if (actionStates.includes(stateName)) {
      clearTimeout(_idleTimer);
      _idleTimer = setTimeout(() => setState('idle_active'), 2400);
    }
    resetIdleTimer();
  }

  function resetIdleTimer() {
    clearTimeout(_idleTimer);
    _idleTimer = setTimeout(() => {
      if (_currentState !== 'idle_active') setState('idle_active');
    }, 3000);
  }

  // ═══════════════════════════════════════════════════════
  // SPEECH BUBBLE
  // ═══════════════════════════════════════════════════════
  let _bubbleTimer = null;
  function speak(text, autoHide = true, durationMs = 4000) {
    if (!_bubble) return;
    _bubble.textContent = text;
    _bubble.classList.add('visible');
    clearTimeout(_bubbleTimer);
    if (autoHide) {
      _bubbleTimer = setTimeout(() => {
        _bubble.classList.remove('visible');
      }, durationMs);
    }
  }

  function hideBubble() {
    if (!_bubble) return;
    _bubble.classList.remove('visible');
  }

  // ═══════════════════════════════════════════════════════
  // AUDIO — Web Audio cues + TTS hookup
  // ═══════════════════════════════════════════════════════
  let _audioCtx = null;
  function getAudioCtx() {
    if (!_audioCtx) _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    return _audioCtx;
  }

  const AUDIO = {
    skid() {
      try {
        const ctx = getAudioCtx();
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.connect(g); g.connect(ctx.destination);
        o.type = 'sawtooth';
        o.frequency.setValueAtTime(400, ctx.currentTime);
        o.frequency.exponentialRampToValueAtTime(80, ctx.currentTime + 0.25);
        g.gain.setValueAtTime(0.15, ctx.currentTime);
        g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
        o.start(); o.stop(ctx.currentTime + 0.3);
      } catch {}
    },
    chime() {
      try {
        const ctx = getAudioCtx();
        [523, 659, 784].forEach((freq, i) => {
          const o = ctx.createOscillator();
          const g = ctx.createGain();
          o.connect(g); g.connect(ctx.destination);
          o.type = 'sine';
          o.frequency.value = freq;
          const t = ctx.currentTime + i * 0.1;
          g.gain.setValueAtTime(0.12, t);
          g.gain.exponentialRampToValueAtTime(0.001, t + 0.4);
          o.start(t); o.stop(t + 0.4);
        });
      } catch {}
    },
    boink() {
      try {
        const ctx = getAudioCtx();
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.connect(g); g.connect(ctx.destination);
        o.type = 'sine';
        o.frequency.setValueAtTime(300, ctx.currentTime);
        o.frequency.exponentialRampToValueAtTime(180, ctx.currentTime + 0.12);
        g.gain.setValueAtTime(0.1, ctx.currentTime);
        g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);
        o.start(); o.stop(ctx.currentTime + 0.2);
      } catch {}
    },
    fanfare() {
      try {
        const ctx = getAudioCtx();
        [[523,0],[659,0.12],[784,0.24],[1047,0.38]].forEach(([freq, delay]) => {
          const o = ctx.createOscillator();
          const g = ctx.createGain();
          o.connect(g); g.connect(ctx.destination);
          o.type = 'square';
          o.frequency.value = freq;
          const t = ctx.currentTime + delay;
          g.gain.setValueAtTime(0.08, t);
          g.gain.exponentialRampToValueAtTime(0.001, t + 0.5);
          o.start(t); o.stop(t + 0.5);
        });
      } catch {}
    },
    whoosh() {
      try {
        const ctx = getAudioCtx();
        const bufferSize = ctx.sampleRate * 0.3;
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize);
        const source = ctx.createBufferSource();
        const g = ctx.createGain();
        const filter = ctx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.setValueAtTime(800, ctx.currentTime);
        filter.frequency.exponentialRampToValueAtTime(200, ctx.currentTime + 0.3);
        source.buffer = buffer;
        source.connect(filter); filter.connect(g); g.connect(ctx.destination);
        g.gain.setValueAtTime(0.2, ctx.currentTime);
        g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
        source.start(); source.stop(ctx.currentTime + 0.3);
      } catch {}
    },
  };

  // TTS via backend (optional — fails silently if unavailable)
  async function tts(text) {
    try {
      const res = await fetch('/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: 'alloy' }),
      });
      if (!res.ok) return;
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.volume = 0.7;
      audio.play().catch(() => {});
      audio.onended = () => URL.revokeObjectURL(url);
    } catch {}
    // Silent fail — TTS is optional
  }

  // ═══════════════════════════════════════════════════════
  // TRIGGER API — mapped to app events
  // ═══════════════════════════════════════════════════════
  const TRIGGERS = {
    // First load in Kid Mode
    firstLoad() {
      if (!_mounted) return;
      setState('enter_skid');
      AUDIO.skid();
      setTimeout(() => {
        speak(getNymPhrase('greeting'), true, 5000);
        setTimeout(() => {
          setState('point_target');
          speak(getNymPhrase('prompt_invite'), true, 4000);
        }, 2000);
      }, 600);
    },

    // User started typing
    typingStart() {
      if (!_mounted) return;
      hideBubble();
      setState('idle_active');
    },

    // Build started
    buildStart() {
      if (!_mounted) return;
      setState('point_target');
      speak(getNymPhrase('loading'), false);
    },

    // Build succeeded
    buildSuccess() {
      if (!_mounted) return;
      setState('celebrate_parkour');
      AUDIO.fanfare();
      speak(getNymPhrase('success_celebrate'), true, 6000);
    },

    // Build failed / error
    buildError() {
      if (!_mounted) return;
      setState('error_wobble');
      AUDIO.boink();
      speak(getNymPhrase('error_recovery'), true, 5000);
    },

    // Game win in Kid Mode
    gameWin() {
      if (!_mounted) return;
      setState('celebrate_parkour');
      AUDIO.fanfare();
      speak(getNymPhrase('success_celebrate'), true, 5000);
    },

    // Remix suggested
    remixReady() {
      if (!_mounted) return;
      setState('cheer_flip');
      AUDIO.chime();
      speak(getNymPhrase('remix_suggestion'), true, 4000);
    },

    // Tutorial / hint
    showHint(customText) {
      if (!_mounted) return;
      setState('point_target');
      speak(customText || getNymPhrase('help'), true, 5000);
    },

    // User inactive 10s
    idle() {
      if (!_mounted) return;
      setState('idle_active');
      speak(getNymPhrase('prompt_invite'), true, 4000);
    },

    // Switching away from Kid Mode
    kidModeExit() {
      if (!_mounted) return;
      speak(getNymPhrase('goodbye'), false);
      clearTimeout(_unmountTimer);
      _unmountTimer = setTimeout(() => unmount(), 1800);
    },
  };

  // ═══════════════════════════════════════════════════════
  // FIRST-RUN ONBOARDING (Kid Mode only, once per session)
  // ═══════════════════════════════════════════════════════
  const ONBOARD_KEY = 'nl_nym_onboarded';
  function runOnboarding() {
    mount();
    const done = sessionStorage.getItem(ONBOARD_KEY);
    if (done) {
      // Not first run — just greet
      setTimeout(() => {
        setState('idle_active');
        speak(getNymPhrase('greeting'), true, 4000);
      }, 500);
      return;
    }
    sessionStorage.setItem(ONBOARD_KEY, '1');
    TRIGGERS.firstLoad();
  }

  // ═══════════════════════════════════════════════════════
  // INACTIVITY WATCHER
  // ═══════════════════════════════════════════════════════
  let _inactiveTimer = null;
  let _watchingInactivity = false;
  function watchInactivity() {
    if (_watchingInactivity) return; // prevent stacking on mode re-entry
    _watchingInactivity = true;
    const reset = () => {
      clearTimeout(_inactiveTimer);
      _inactiveTimer = setTimeout(() => TRIGGERS.idle(), 12000);
    };
    ['mousemove','keydown','touchstart','click'].forEach(ev =>
      document.addEventListener(ev, reset, { passive: true })
    );
    reset();
  }

  // ═══════════════════════════════════════════════════════
  // CSS INJECTION
  // ═══════════════════════════════════════════════════════
  function injectStyles() {
    if (document.getElementById('nym-styles')) return;
    const style = document.createElement('style');
    style.id = 'nym-styles';
    style.textContent = `
/* ── Nym Widget ─────────────────────────── */
#nym-widget {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 200;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  pointer-events: none;
}
.nym-svg-wrap {
  width: 90px;
  cursor: pointer;
  pointer-events: all;
  filter: drop-shadow(0 4px 12px rgba(0,210,255,0.25));
  transform-origin: bottom center;
}
.nym-bubble {
  background: #2D3436;
  color: #FFFFFF;
  border: 1.5px solid #00D2FF;
  border-radius: 16px 16px 4px 16px;
  padding: 10px 14px;
  font-family: 'Nunito', sans-serif;
  font-size: 0.82rem;
  font-weight: 700;
  max-width: 220px;
  line-height: 1.4;
  opacity: 0;
  transform: translateY(6px) scale(0.95);
  transition: opacity 0.25s, transform 0.25s;
  pointer-events: none;
}
.nym-bubble.visible {
  opacity: 1;
  transform: translateY(0) scale(1);
}

/* ── Animation States ───────────────────── */

/* idle_active — subtle weight shift + ear twitch */
.nym-idle #nym-character {
  animation: nymIdle 2.4s ease-in-out infinite;
}
.nym-idle .nym-ears {
  animation: nymEarTwitch 3.2s ease-in-out infinite;
}
@keyframes nymIdle {
  0%,100% { transform: translateY(0) rotate(0deg); }
  30%      { transform: translateY(-3px) rotate(-1deg); }
  70%      { transform: translateY(-1px) rotate(1deg); }
}
@keyframes nymEarTwitch {
  0%,80%,100% { transform: rotate(0deg); transform-origin: bottom center; }
  85%          { transform: rotate(-4deg); }
  92%          { transform: rotate(3deg); }
}

/* enter_skid — fast slide in from right + strong stop */
.nym-skid .nym-svg-wrap {
  animation: nymSkid 0.55s cubic-bezier(0.2, 0.8, 0.4, 1) forwards;
}
@keyframes nymSkid {
  0%   { transform: translateX(140px) scaleX(1.18); opacity: 0.2; }
  70%  { transform: translateX(-12px) scaleX(0.92); opacity: 1; }
  85%  { transform: translateX(5px)  scaleX(1.04); }
  100% { transform: translateX(0)    scaleX(1); }
}

/* point_target — lean forward, arm out */
.nym-point #nym-character {
  animation: nymPoint 0.4s ease forwards;
}
.nym-point .nym-arm-r {
  animation: nymArmPoint 0.4s ease forwards;
  transform-origin: top center;
}
@keyframes nymPoint {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(-6deg) translateX(-4px); }
}
@keyframes nymArmPoint {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(-40deg); }
}

/* cheer_flip — backflip */
.nym-cheer .nym-svg-wrap {
  animation: nymFlip 0.65s cubic-bezier(0.4, 0, 0.2, 1);
}
@keyframes nymFlip {
  0%   { transform: translateY(0) rotate(0deg) scaleX(1); }
  30%  { transform: translateY(-40px) rotate(-120deg) scaleX(0.9); }
  65%  { transform: translateY(-50px) rotate(-310deg) scaleX(1.05); }
  80%  { transform: translateY(-10px) rotate(-360deg) scaleX(1); }
  90%  { transform: translateY(4px) rotate(-360deg) scaleX(1.06); }
  100% { transform: translateY(0) rotate(-360deg) scaleX(1); }
}

/* error_wobble — head shake */
.nym-wobble #nym-character {
  animation: nymWobble 0.55s ease;
}
@keyframes nymWobble {
  0%,100% { transform: rotate(0deg) translateX(0); }
  15%     { transform: rotate(-8deg) translateX(-4px); }
  35%     { transform: rotate(6deg)  translateX(4px); }
  55%     { transform: rotate(-5deg) translateX(-3px); }
  75%     { transform: rotate(3deg)  translateX(2px); }
}

/* celebrate_parkour — cartwheel + backflip + hero landing */
.nym-celebrate .nym-svg-wrap {
  animation: nymParkour 1.1s cubic-bezier(0.3, 0, 0.2, 1);
}
.nym-celebrate .nym-landing-glow {
  animation: nymGlow 0.4s ease 0.9s forwards;
}
@keyframes nymParkour {
  0%   { transform: translateY(0)    rotate(0deg)    scaleX(1); }
  15%  { transform: translateY(-20px) rotate(90deg)   scaleX(0.85); }
  35%  { transform: translateY(-55px) rotate(270deg)  scaleX(1.05); }
  55%  { transform: translateY(-65px) rotate(-90deg)  scaleX(0.9); }
  75%  { transform: translateY(-30px) rotate(-340deg) scaleX(1); }
  88%  { transform: translateY(6px)   rotate(-360deg) scaleX(1.08); }
  95%  { transform: translateY(-3px)  rotate(-360deg) scaleX(0.96); }
  100% { transform: translateY(0)     rotate(-360deg) scaleX(1); }
}
@keyframes nymGlow {
  0%   { opacity: 0; }
  50%  { opacity: 0.7; }
  100% { opacity: 0; }
}

/* logo_morph — compact spin for loading/logo area */
.nym-logo-morph .nym-svg-wrap {
  animation: nymLogoSpin 1.8s ease-in-out infinite;
}
@keyframes nymLogoSpin {
  0%,100% { transform: scale(1) rotate(0deg); }
  25%     { transform: scale(1.08) rotate(-8deg); }
  50%     { transform: scale(0.95) rotate(0deg); }
  75%     { transform: scale(1.04) rotate(6deg); }
}

/* ── Reduced motion override ─────────────── */
@media (prefers-reduced-motion: reduce) {
  .nym-svg-wrap, #nym-character, .nym-ears,
  .nym-arm-r, .nym-landing-glow { animation: none !important; }
}

/* ── Kid Mode logo area ──────────────────── */
#nym-logo-area {
  display: flex;
  align-items: center;
  gap: 6px;
}
#nym-logo-area .nym-logo-svg {
  width: 32px;
  height: 32px;
  animation: nymLogoIdle 2.8s ease-in-out infinite;
}
@keyframes nymLogoIdle {
  0%,100% { transform: translateY(0); }
  50%     { transform: translateY(-4px); }
}
    `;
    document.head.appendChild(style);
  }

  // ═══════════════════════════════════════════════════════
  // PUBLIC API
  // ═══════════════════════════════════════════════════════
  return {
    // Mount / unmount
    mount,
    unmount,

    // State control
    setState,

    // Speech
    speak,
    hideBubble,

    // Phrase system
    getNymPhrase,

    // Trigger API (maps to app events)
    trigger: TRIGGERS,

    // Audio
    audio: AUDIO,
    tts,

    // Onboarding
    runOnboarding,
    watchInactivity,

    // SVG string (for embedding in other elements)
    SVG: NYM_SVG,

    // Tiny inline logo SVG (for header use)
    LOGO_SVG: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 54" class="nym-logo-svg">
      <path d="M12 24 L8 4 L13 3 L16 18Z" fill="#2D3436" stroke="#00D2FF" stroke-width="1.2"/>
      <path d="M28 24 L32 4 L27 3 L24 18Z" fill="#2D3436" stroke="#00D2FF" stroke-width="1.2"/>
      <ellipse cx="20" cy="26" rx="14" ry="13" fill="#2D3436"/>
      <ellipse cx="15" cy="24" rx="4" ry="4.5" fill="white"/>
      <ellipse cx="25" cy="24" rx="4" ry="4.5" fill="white"/>
      <circle cx="16" cy="24.5" r="2.5" fill="#1a1040"/>
      <circle cx="26" cy="24.5" r="2.5" fill="#1a1040"/>
      <ellipse cx="20" cy="30" rx="2.5" ry="1.8" fill="#00D2FF"/>
      <rect x="14" y="35" width="12" height="4" rx="2" fill="#00D2FF" opacity="0.8"/>
    </svg>`,
  };
})();
