/**
 * nl-nym.js — NymController v2.0
 * NymbleLogic / Nymble Jr — Kid Mode only
 * The Good Neighbor Guard — Christopher Hughes
 *
 * Asset-based mascot system. No SVG drawing.
 * Assets live at /static/nym_[state].svg
 */

window.NYM = (() => {
  'use strict';

  // ═══════════════════════════════════════════════════
  // ASSETS
  // ═══════════════════════════════════════════════════
  const ASSETS = {
    idle:      '/static/nym_idle.svg',
    greet:     '/static/nym_greet.svg',
    point:     '/static/nym_point.svg',
    think:     '/static/nym_think.svg',
    cheer:     '/static/nym_cheer.svg',
    error:     '/static/nym_error.svg',
    celebrate: '/static/nym_celebrate.svg',
    icon:      '/static/nym_icon.svg',
    head:      '/static/nym_head.svg',
  };

  const STATE_ANIM = {
    idle:      'nym-anim-idle',
    greet:     'nym-anim-greet',
    point:     'nym-anim-point',
    think:     'nym-anim-think',
    cheer:     'nym-anim-cheer',
    error:     'nym-anim-error',
    celebrate: 'nym-anim-celebrate',
  };

  // ═══════════════════════════════════════════════════
  // PHRASE BANK
  // ═══════════════════════════════════════════════════
  const PHRASES = {
    greeting: [
      "Yo! I'm Nym — what are we building today? 🔥",
      "Hey! Ready to snap something together?",
      "Nym here — drop your idea and I'll make it real.",
      "Back for more? Let's build something awesome! 🚀",
      "Nym reporting for duty — what's the mission?",
    ],
    prompt_invite: [
      "Tell me what you want — game, app, anything!",
      "Type your idea up there and hit BUILD 👆",
      "What's the vision? Shoot your shot! 🎯",
      "Write it, I'll build it. Simple as that.",
      "Your idea goes in the box. My crew handles the rest.",
    ],
    encouragement: [
      "You're on it! Keep going 💪",
      "That's a great idea — this is gonna be fun!",
      "Nice pick! Atlas and the crew are on it 🏗️",
      "Oh this is gonna be good. Trust the process 🔥",
    ],
    help: [
      "Stuck? Try one of the starter chips below 👇",
      "Not sure? Try: 'a snake game with space aliens'",
      "Tip: more detail = better build!",
      "Just describe what you want to PLAY or USE.",
    ],
    success_celebrate: [
      "LETS GOOO! Your app is LIVE! 🎉🔥",
      "Built and ready! You just made something real! 🏆",
      "BOOM! The team delivered. Hit Play! 🚀",
      "That's a W! Download it, share it, remix it! 💥",
    ],
    error_recovery: [
      "Oops! Let's shake that off and try again 💪",
      "Even the best builders hit bumps — tweak and rerun!",
      "No stress! Add more detail and let's go again.",
      "My crew hit a snag. A small change might fix it!",
    ],
    remix_suggestion: [
      "Want to level it up? Hit Remix! 🪄",
      "Not quite right? Remix it — describe the change.",
      "Looking good! Remix to add more features 🔥",
      "Remix is your superpower — use it!",
    ],
    loading: [
      "Atlas is drawing up the plans… 📐",
      "Byte is writing your code… 💻",
      "Scout is testing every corner… 🔍",
      "The crew is on it — almost there! ⚡",
    ],
    goodbye: [
      "See ya! Come back when the next idea hits 🐇",
      "Switching modes — I'll be here if you return.",
    ],
  };

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

  // ═══════════════════════════════════════════════════
  // INTERNAL STATE
  // ═══════════════════════════════════════════════════
  let _mounted          = false;
  let _currentState     = 'idle';
  let _idleTimer        = null;
  let _unmountTimer     = null;
  let _bubbleTimer      = null;
  let _watchingInactive = false;
  let _inactiveTimer    = null;
  let _sequenceAbort    = false;

  let _widget       = null;
  let _img          = null;
  let _bubble       = null;
  let _bubbleTxt    = null;

  const HOME = { bottom: '20px', right: '20px' };

  // ═══════════════════════════════════════════════════
  // STYLES
  // ═══════════════════════════════════════════════════
  function injectStyles() {
    if (document.getElementById('nym-styles')) return;
    const s = document.createElement('style');
    s.id = 'nym-styles';
    s.textContent = `
#nym-widget {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9100;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  pointer-events: none;
  transition:
    bottom 0.52s cubic-bezier(0.34,1.56,0.64,1),
    right  0.52s cubic-bezier(0.34,1.56,0.64,1),
    left   0.52s cubic-bezier(0.34,1.56,0.64,1),
    top    0.52s cubic-bezier(0.34,1.56,0.64,1);
}

#nym-img {
  width: 108px;
  height: auto;
  pointer-events: all;
  cursor: pointer;
  filter: drop-shadow(0 6px 18px rgba(0,160,255,0.30));
  transform-origin: bottom center;
  transition: opacity 0.16s ease;
  user-select: none;
  display: block;
}
#nym-img.swapping { opacity: 0; }

#nym-bubble {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #1c1e28;
  color: #f0f0f0;
  border: 1.5px solid #00aaff;
  border-radius: 14px 14px 4px 14px;
  padding: 10px 12px;
  font-family: 'Nunito', system-ui, sans-serif;
  font-size: 0.80rem;
  font-weight: 700;
  max-width: 205px;
  line-height: 1.45;
  pointer-events: none;
  opacity: 0;
  transform: translateY(8px) scale(0.93);
  transition: opacity 0.20s ease, transform 0.20s ease;
  box-shadow: 0 4px 24px rgba(0,0,0,0.45);
}
#nym-bubble.show {
  opacity: 1;
  transform: translateY(0) scale(1);
}
#nym-bubble-avatar {
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #252830;
  border: 1px solid #00aaff;
  overflow: hidden;
}
#nym-bubble-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
#nym-bubble-text { flex: 1; }

/* ── Animations ── */
.nym-anim-idle   #nym-img { animation: nymFloat  3.2s ease-in-out infinite; }
.nym-anim-greet  #nym-img { animation: nymGreet  0.48s ease-in-out 3; }
.nym-anim-point  #nym-img { animation: nymPoint  1.1s ease-in-out infinite; }
.nym-anim-think  #nym-img { animation: nymThink  2s ease-in-out infinite; }
.nym-anim-cheer  #nym-img { animation: nymCheer  0.42s cubic-bezier(0.36,.07,.19,.97) 4; }
.nym-anim-error  #nym-img { animation: nymError  0.48s ease 2; }
.nym-anim-celebrate #nym-img { animation: nymCelebrate 0.8s cubic-bezier(0.4,0,0.2,1) 2; }
.nym-enter       #nym-img { animation: nymEnter  0.52s cubic-bezier(0.2,0.8,0.4,1) forwards; }
.nym-exit        #nym-img { animation: nymExit   0.38s ease-in forwards; }

@keyframes nymFloat     { 0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)} }
@keyframes nymGreet     { 0%,100%{transform:translateY(0)rotate(0)}35%{transform:translateY(-10px)rotate(-5deg)}70%{transform:translateY(-4px)rotate(4deg)} }
@keyframes nymPoint     { 0%,100%{transform:translateX(0)rotate(0)}50%{transform:translateX(-6px)rotate(-3deg)} }
@keyframes nymThink     { 0%,100%{transform:rotate(0)}30%{transform:rotate(-3deg)}70%{transform:rotate(3deg)} }
@keyframes nymCheer     { 0%,100%{transform:translateY(0)scale(1)}40%{transform:translateY(-20px)scale(1.06)}75%{transform:translateY(-8px)scale(0.97)} }
@keyframes nymError     { 0%,100%{transform:translateX(0)}20%{transform:translateX(-8px)rotate(-4deg)}40%{transform:translateX(8px)rotate(4deg)}60%{transform:translateX(-5px)rotate(-3deg)}80%{transform:translateX(4px)rotate(2deg)} }
@keyframes nymCelebrate { 0%{transform:translateY(0)rotate(0)scale(1)}25%{transform:translateY(-32px)rotate(-120deg)scale(1.1)}55%{transform:translateY(-44px)rotate(-340deg)scale(1.08)}85%{transform:translateY(-6px)rotate(-360deg)scale(1)}100%{transform:translateY(0)rotate(-360deg)scale(1)} }
@keyframes nymEnter     { 0%{transform:translateX(150px)scaleX(1.1);opacity:0}65%{transform:translateX(-10px)scaleX(0.94);opacity:1}82%{transform:translateX(4px)scaleX(1.03)}100%{transform:translateX(0)scaleX(1)} }
@keyframes nymExit      { 0%{transform:translateX(0);opacity:1}100%{transform:translateX(160px);opacity:0} }

@media (prefers-reduced-motion: reduce) {
  #nym-img, #nym-bubble { animation: none !important; transition: none !important; }
}
    `;
    document.head.appendChild(s);
  }

  // ═══════════════════════════════════════════════════
  // MOUNT / UNMOUNT
  // ═══════════════════════════════════════════════════
  function mount() {
    if (_mounted) return;
    clearTimeout(_unmountTimer);
    injectStyles();
    _mounted = true;

    _widget = document.createElement('div');
    _widget.id = 'nym-widget';

    // Speech bubble
    _bubble = document.createElement('div');
    _bubble.id = 'nym-bubble';
    _bubble.setAttribute('role', 'status');
    _bubble.setAttribute('aria-live', 'polite');

    const avatar = document.createElement('div');
    avatar.id = 'nym-bubble-avatar';
    avatar.innerHTML = `<img src="${ASSETS.head}" alt=""/>`;

    _bubbleTxt = document.createElement('div');
    _bubbleTxt.id = 'nym-bubble-text';

    _bubble.appendChild(avatar);
    _bubble.appendChild(_bubbleTxt);

    // Character image
    _img = document.createElement('img');
    _img.id  = 'nym-img';
    _img.alt = 'Nym';
    _img.src = ASSETS.idle;
    _img.title = 'Click Nym for a hint!';
    _img.addEventListener('click', () => {
      say(getNymPhrase('help'));
      setState('point');
    });

    _widget.appendChild(_bubble);
    _widget.appendChild(_img);
    document.body.appendChild(_widget);

    // Enter animation — guard so early setState calls inside runOnboarding
    // don't fire animationend before the slide-in finishes
    let _enterDone = false;
    _widget.classList.add('nym-enter');
    const _onEnterEnd = (e) => {
      if (e.target !== _img) return;
      if (_enterDone) return;
      _enterDone = true;
      _widget.removeEventListener('animationend', _onEnterEnd);
      _widget.classList.remove('nym-enter');
      if (!Object.values(STATE_ANIM).some(c => _widget.classList.contains(c))) {
        _widget.classList.add(STATE_ANIM['idle']);
      }
    };
    _widget.addEventListener('animationend', _onEnterEnd);
    // Safety: force-complete enter after 700ms regardless
    setTimeout(() => {
      if (!_enterDone && _widget) {
        _enterDone = true;
        _widget.classList.remove('nym-enter');
        if (!Object.values(STATE_ANIM).some(c => _widget.classList.contains(c))) {
          _widget.classList.add(STATE_ANIM['idle']);
        }
      }
    }, 700);
  }

  function unmount() {
    if (!_mounted || !_widget) return;
    clearTimeout(_unmountTimer);
    _watchingInactive = false;
    clearTimeout(_inactiveTimer);
    _widget.classList.add('nym-exit');
    _unmountTimer = setTimeout(() => {
      _widget && _widget.remove();
      _widget = _img = _bubble = _bubbleTxt = null;
      _mounted = false;
    }, 420);
  }

  // ═══════════════════════════════════════════════════
  // STATE SWAP
  // ═══════════════════════════════════════════════════
  function setState(state) {
    if (!_mounted || !_img || !ASSETS[state]) return;
    Object.values(STATE_ANIM).forEach(c => _widget.classList.remove(c));
    _widget.classList.remove('nym-enter', 'nym-exit');

    _img.classList.add('swapping');

    function _applyState() {
      if (!_img) return;
      _img.onload = _img.onerror = null;
      _img.classList.remove('swapping');
      if (STATE_ANIM[state]) _widget.classList.add(STATE_ANIM[state]);
      _currentState = state;
    }

    setTimeout(() => {
      if (!_img) return;
      _img.onload  = null;
      _img.onerror = null;
      _img.onload  = _applyState;
      _img.onerror = _applyState; // show widget even if asset 404s
      _img.src = ASSETS[state];
      // Cached image: complete+naturalWidth set synchronously after src assign
      if (_img.complete && _img.naturalWidth > 0) {
        _img.onload = _img.onerror = null;
        _applyState();
      }
    }, 160);

    _resetIdleTimer();
  }

  function _resetIdleTimer() {
    clearTimeout(_idleTimer);
    _idleTimer = setTimeout(() => {
      if (_currentState !== 'idle') setState('idle');
    }, 5000);
  }

  // ═══════════════════════════════════════════════════
  // SPEECH BUBBLE + TTS
  // ═══════════════════════════════════════════════════
  function say(text, useTTS = true, durationMs = 4800) {
    if (!_mounted || !_bubble) return;
    _bubbleTxt.textContent = text;
    _bubble.classList.add('show');
    clearTimeout(_bubbleTimer);
    _bubbleTimer = setTimeout(() => _bubble && _bubble.classList.remove('show'), durationMs);
    if (useTTS) _tts(text); // fire-and-forget
  }

  function hideBubble() {
    clearTimeout(_bubbleTimer);
    _bubble && _bubble.classList.remove('show');
  }

  async function _tts(text) {
    try {
      const res = await fetch('/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.replace(/[🔥🚀🎉💪🏆💥🪄🎯🏗️⚡📐💻🔍👆👇]/gu, '').slice(0, 280) }),
      });
      if (!res.ok) return;
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const aud  = new Audio(url);
      aud.volume = 0.75;
      aud.play().catch(() => {});
      aud.onended = () => URL.revokeObjectURL(url);
    } catch (_) {}
  }

  // ═══════════════════════════════════════════════════
  // MOVEMENT
  // ═══════════════════════════════════════════════════
  function moveToElement(selector) {
    if (!_widget) return;
    const el = selector ? document.querySelector(selector) : null;
    if (!el) { returnHome(); return; }

    const rect = el.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const WW = 130, WH = 160; // widget footprint estimate

    // Try right of element first, then left
    if (rect.right + WW + 12 < vw) {
      _widget.style.right = (vw - rect.right - WW - 8) + 'px';
      _widget.style.left  = 'auto';
    } else {
      _widget.style.left  = Math.max(8, rect.left - WW - 8) + 'px';
      _widget.style.right = 'auto';
    }
    const desiredBottom = vh - rect.top - WH / 2;
    _widget.style.bottom = Math.max(8, Math.min(desiredBottom, vh - WH - 8)) + 'px';
    _widget.style.top    = 'auto';
  }

  function returnHome() {
    if (!_widget) return;
    _widget.style.bottom = HOME.bottom;
    _widget.style.right  = HOME.right;
    _widget.style.left   = 'auto';
    _widget.style.top    = 'auto';
  }

  function pointAt(selector) {
    moveToElement(selector);
    setState('point');
  }

  // ═══════════════════════════════════════════════════
  // SEQUENCE RUNNER
  // ═══════════════════════════════════════════════════
  function _wait(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  async function playSequence(actions) {
    _sequenceAbort = false;
    for (const a of actions) {
      if (_sequenceAbort) break;
      if (a.state)  setState(a.state);
      if (a.move)   moveToElement(a.move);
      if (a.point)  pointAt(a.point);
      if (a.home)   returnHome();
      if (a.say)    say(a.say, a.tts !== false, a.duration || 4800);
      if (a.wait)   await _wait(a.wait);
    }
  }

  function abortSequence() { _sequenceAbort = true; }

  // ═══════════════════════════════════════════════════
  // ONBOARDING
  // ═══════════════════════════════════════════════════
  const ONBOARD_KEY = 'nl_nym_v2_onboarded';

  async function runOnboarding() {
    mount();
    const done = sessionStorage.getItem(ONBOARD_KEY);
    if (done) {
      // Returning to Kid Mode — quick greet only
      await _wait(350);
      setState('greet');
      say(getNymPhrase('greeting'), true, 3800);
      await _wait(4000);
      setState('idle');
      return;
    }
    sessionStorage.setItem(ONBOARD_KEY, '1');

    // Full first-run tour
    await playSequence([
      { wait: 600 },
      { state: 'greet',
        say: "Yo! I'm Nym — your build partner! Let's make something! 🔥",
        duration: 4000 },
      { wait: 2200 },
      { point: '#taskInput',
        say: "Type your idea here.", duration: 3200, tts: true },
      { wait: 3500 },
      { point: '#buildBtn',
        say: "Then tap this button and let's build it.", duration: 3500, tts: true },
      { wait: 3800 },
      { home: true, state: 'idle',
        say: getNymPhrase('encouragement'), duration: 3000 },
      { wait: 3200 },
    ]);
    setState('idle');
  }

  // ═══════════════════════════════════════════════════
  // INACTIVITY WATCHER
  // ═══════════════════════════════════════════════════
  function watchInactivity() {
    if (_watchingInactive) return;
    _watchingInactive = true;

    const reset = () => {
      clearTimeout(_inactiveTimer);
      _inactiveTimer = setTimeout(() => {
        if (!_mounted) return;
        pointAt('#taskInput');
        say(getNymPhrase('prompt_invite'), true, 4500);
        setTimeout(() => { returnHome(); setState('idle'); }, 5200);
      }, 14000);
    };

    ['mousemove', 'keydown', 'touchstart', 'click'].forEach(ev =>
      document.addEventListener(ev, reset, { passive: true })
    );
    reset();
  }

  // ═══════════════════════════════════════════════════
  // TRIGGERS — called by index.html app lifecycle hooks
  // ═══════════════════════════════════════════════════
  const trigger = {

    kidModeEnter() {
      clearTimeout(_unmountTimer);
      runOnboarding();
      watchInactivity();
    },

    kidModeExit() {
      if (!_mounted) return;
      say(getNymPhrase('goodbye'), false, 2000);
      setTimeout(() => unmount(), 2200);
    },

    typingStart() {
      if (!_mounted) return;
      hideBubble();
      abortSequence();
      setState('think');
    },

    buildStart() {
      if (!_mounted) return;
      abortSequence();
      returnHome();
      setState('think');
      say(getNymPhrase('loading'), false, 6000);
    },

    buildSuccess() {
      if (!_mounted) return;
      abortSequence();
      returnHome();
      setState('cheer');
      say(getNymPhrase('success_celebrate'), true, 6000);
    },

    buildError() {
      if (!_mounted) return;
      abortSequence();
      returnHome();
      setState('error');
      say(getNymPhrase('error_recovery'), true, 5000);
    },

    remixReady() {
      if (!_mounted) return;
      abortSequence();
      setState('greet');
      say(getNymPhrase('remix_suggestion'), true, 4500);
    },

    gameWin() {
      if (!_mounted) return;
      abortSequence();
      returnHome();
      setState('celebrate');
      say(getNymPhrase('success_celebrate'), true, 5500);
    },

    hint(text) {
      if (!_mounted) return;
      pointAt('#taskInput');
      say(text || getNymPhrase('help'), true, 5000);
    },
  };

  // ═══════════════════════════════════════════════════
  // PUBLIC API
  // ═══════════════════════════════════════════════════
  return {
    mount, unmount, setState, say, hideBubble,
    moveToElement, pointAt, returnHome,
    playSequence, abortSequence,
    runOnboarding, watchInactivity,
    getNymPhrase,
    trigger,
    ASSETS,
    LOGO_HTML: `<img src="/static/nym_icon.svg" alt="Nym" style="width:26px;height:26px;object-fit:contain;vertical-align:middle;"/>`,
  };
})();
