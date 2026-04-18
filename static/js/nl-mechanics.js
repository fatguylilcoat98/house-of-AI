/**
 * NymbleLogic Mechanics Library v1.0
 * The Good Neighbor Guard — Christopher Hughes
 *
 * Reusable mechanics as injectable JS string snippets.
 * Each returns a self-contained JS code block that can be
 * injected into template HTML via string interpolation.
 */

window.NL_MECHANICS = (() => {
  'use strict';

  /**
   * Each mechanic is a function returning a JS code string.
   * Templates call NL_MECHANICS.get('score_system') etc.
   * The returned string is injected into the template's <script>.
   */

  const MECHANICS = {

    score_system: () => `
// ── Score System ──────────────────────────────
let score = 0, highScore = parseInt(localStorage.getItem('nl_hs') || '0');
function addScore(n=1) {
  score += n;
  if (score > highScore) { highScore = score; localStorage.setItem('nl_hs', highScore); }
  renderScore();
}
function resetScore() { score = 0; renderScore(); }
function renderScore() {
  const el = document.getElementById('score'); if (el) el.textContent = score;
  const hs = document.getElementById('highscore'); if (hs) hs.textContent = highScore;
}
`,

    timer_system: (seconds = 60) => `
// ── Timer System ──────────────────────────────
let timeLeft = ${seconds}, timerHandle = null;
function startTimer(cb) {
  timerHandle = setInterval(() => {
    timeLeft--;
    const el = document.getElementById('timer'); if (el) el.textContent = timeLeft;
    if (timeLeft <= 0) { clearInterval(timerHandle); if (cb) cb(); }
  }, 1000);
}
function stopTimer() { clearInterval(timerHandle); }
function resetTimer(secs=${seconds}) { timeLeft = secs; stopTimer(); const el = document.getElementById('timer'); if (el) el.textContent = timeLeft; }
`,

    lives_system: (lives = 3) => `
// ── Lives System ──────────────────────────────
let lives = ${lives};
function loseLife() {
  lives--;
  const el = document.getElementById('lives'); if (el) el.textContent = '❤️'.repeat(Math.max(lives,0));
  return lives <= 0;
}
function resetLives(n=${lives}) { lives = n; const el = document.getElementById('lives'); if (el) el.textContent = '❤️'.repeat(n); }
`,

    keyboard_movement: (speed = 4) => `
// ── Keyboard Movement ─────────────────────────
const keys = {};
document.addEventListener('keydown', e => { keys[e.key] = true; e.preventDefault(); });
document.addEventListener('keyup',   e => { keys[e.key] = false; });
function applyKeyboardMove(obj, bounds) {
  const spd = ${speed};
  if ((keys['ArrowLeft']  || keys['a']) && obj.x > bounds.minX) obj.x -= spd;
  if ((keys['ArrowRight'] || keys['d']) && obj.x < bounds.maxX) obj.x += spd;
  if ((keys['ArrowUp']    || keys['w']) && obj.y > bounds.minY) obj.y -= spd;
  if ((keys['ArrowDown']  || keys['s']) && obj.y < bounds.maxY) obj.y += spd;
}
function applyKeyboardMoveH(obj, bounds) {
  const spd = ${speed};
  if ((keys['ArrowLeft']  || keys['a']) && obj.x > bounds.minX) obj.x -= spd;
  if ((keys['ArrowRight'] || keys['d']) && obj.x < bounds.maxX) obj.x += spd;
}
`,

    touch_movement: () => `
// ── Touch Movement ────────────────────────────
let touchStartX = 0, touchStartY = 0, touchDX = 0, touchDY = 0;
document.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; touchStartY = e.touches[0].clientY; }, {passive:true});
document.addEventListener('touchmove',  e => { touchDX = e.touches[0].clientX - touchStartX; touchDY = e.touches[0].clientY - touchStartY; }, {passive:true});
document.addEventListener('touchend',   () => { touchDX = 0; touchDY = 0; });
function applyTouchMove(obj, bounds, speed=4) {
  const threshold = 10;
  if (touchDX < -threshold && obj.x > bounds.minX) obj.x -= speed;
  if (touchDX >  threshold && obj.x < bounds.maxX) obj.x += speed;
}
`,

    mouse_follow: () => `
// ── Mouse Follow ──────────────────────────────
let mouseX = 200, mouseY = 200;
document.addEventListener('mousemove', e => { const r = canvas.getBoundingClientRect(); mouseX = e.clientX - r.left; mouseY = e.clientY - r.top; });
document.addEventListener('touchmove', e => { e.preventDefault(); const r = canvas.getBoundingClientRect(); mouseX = e.touches[0].clientX - r.left; mouseY = e.touches[0].clientY - r.top; }, {passive:false});
`,

    gravity_jump: (gravity = 0.5, jumpForce = -11) => `
// ── Gravity + Jump ────────────────────────────
let velY = 0, onGround = false;
const GRAVITY = ${gravity}, JUMP_FORCE = ${jumpForce};
function applyGravity(obj, groundY) {
  velY += GRAVITY;
  obj.y += velY;
  if (obj.y + obj.h >= groundY) { obj.y = groundY - obj.h; velY = 0; onGround = true; } else { onGround = false; }
}
function jump() { if (onGround) { velY = JUMP_FORCE; onGround = false; } }
document.addEventListener('keydown', e => { if (e.code === 'Space') { jump(); e.preventDefault(); }});
document.addEventListener('touchstart', () => jump(), {passive:true});
`,

    collision_detection: () => `
// ── Collision Detection ───────────────────────
function rectHit(a, b) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}
function circleHit(a, b) {
  const dx = (a.x+a.r) - (b.x+b.r), dy = (a.y+a.r) - (b.y+b.r);
  return Math.hypot(dx, dy) < a.r + b.r;
}
function pointInRect(px, py, r) {
  return px >= r.x && px <= r.x + r.w && py >= r.y && py <= r.y + r.h;
}
`,

    enemy_spawner: () => `
// ── Enemy Spawner ─────────────────────────────
let enemies = [], enemyInterval = null;
function startEnemySpawner(spawnFn, intervalMs=1200) {
  clearInterval(enemyInterval);
  enemyInterval = setInterval(() => { enemies.push(spawnFn()); }, intervalMs);
}
function stopEnemySpawner() { clearInterval(enemyInterval); }
function clearEnemies() { enemies = []; }
`,

    collectible_spawner: () => `
// ── Collectible Spawner ───────────────────────
let collectibles = [], collectInterval = null;
function startCollectibleSpawner(spawnFn, intervalMs=1500) {
  clearInterval(collectInterval);
  collectInterval = setInterval(() => { collectibles.push(spawnFn()); }, intervalMs);
}
function stopCollectibleSpawner() { clearInterval(collectInterval); }
function clearCollectibles() { collectibles = []; }
`,

    particle_effect: () => `
// ── Particle Effects ──────────────────────────
let particles = [];
function spawnParticles(x, y, color='#f59e0b', count=12) {
  for (let i = 0; i < count; i++) {
    const angle = (Math.PI*2*i)/count;
    particles.push({ x, y, vx: Math.cos(angle)*(2+Math.random()*3), vy: Math.sin(angle)*(2+Math.random()*3), alpha:1, color, r:3+Math.random()*3 });
  }
}
function updateParticles(ctx) {
  particles.forEach(p => { p.x+=p.vx; p.y+=p.vy; p.vy+=0.1; p.alpha-=0.03; if(p.alpha>0){ctx.save();ctx.globalAlpha=p.alpha;ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fillStyle=p.color;ctx.fill();ctx.restore();}});
  particles = particles.filter(p => p.alpha > 0);
}
`,

    win_overlay: () => `
// ── Win / Lose / Draw Overlays ────────────────
function showWin(msg='You Win! 🎉') {
  gameActive = false;
  const o = document.getElementById('overlay');
  if (!o) return;
  o.innerHTML = \`<div class="overlay-box win-box"><div class="ov-icon">🏆</div><div class="ov-title">\${msg}</div><div class="ov-score">Score: \${typeof score!=='undefined'?score:''}</div><button onclick="restartGame()" class="ov-btn">Play Again</button></div>\`;
  o.style.display = 'flex';
  if (typeof triggerWinFireworks === 'function') triggerWinFireworks();
}
function showLose(msg='Game Over 😢') {
  gameActive = false;
  const o = document.getElementById('overlay');
  if (!o) return;
  o.innerHTML = \`<div class="overlay-box lose-box"><div class="ov-icon">💀</div><div class="ov-title">\${msg}</div><div class="ov-score">Score: \${typeof score!=='undefined'?score:''}</div><button onclick="restartGame()" class="ov-btn">Try Again</button></div>\`;
  o.style.display = 'flex';
}
function showDraw(msg="It's a Draw! 🤝") {
  gameActive = false;
  const o = document.getElementById('overlay');
  if (!o) return;
  o.innerHTML = \`<div class="overlay-box draw-box"><div class="ov-icon">🤝</div><div class="ov-title">\${msg}</div><button onclick="restartGame()" class="ov-btn">Play Again</button></div>\`;
  o.style.display = 'flex';
}
function hideOverlay() { const o=document.getElementById('overlay'); if(o) o.style.display='none'; }
`,

    restart_flow: () => `
// ── Restart Flow ──────────────────────────────
function restartGame() {
  hideOverlay();
  if (typeof resetScore === 'function') resetScore();
  if (typeof resetLives === 'function') resetLives();
  if (typeof resetTimer === 'function') resetTimer();
  if (typeof clearEnemies === 'function') clearEnemies();
  if (typeof clearCollectibles === 'function') clearCollectibles();
  gameActive = true;
  initGame();
}
`,

    board_grid: (rows = 6, cols = 7) => `
// ── Board Grid Logic ──────────────────────────
const ROWS = ${rows}, COLS = ${cols};
let board = Array.from({length:ROWS}, () => Array(COLS).fill(null));
function resetBoard() { board = Array.from({length:ROWS}, () => Array(COLS).fill(null)); }
function checkLine(arr, val) { return arr.every(v => v === val); }
function getCol(c) { return board.map(r => r[c]); }
function getDiagDown(r,c) { const d=[]; for(let i=0;r+i<ROWS&&c+i<COLS;i++) d.push(board[r+i][c+i]); return d; }
function getDiagUp(r,c) { const d=[]; for(let i=0;r-i>=0&&c+i<COLS;i++) d.push(board[r-i][c+i]); return d; }
`,

    card_flip: () => `
// ── Card Flip Match ───────────────────────────
let flipped = [], matched = new Set(), lockCards = false;
function flipCard(idx, cards) {
  if (lockCards || matched.has(idx) || flipped.includes(idx)) return;
  flipped.push(idx);
  renderCards(cards);
  if (flipped.length === 2) {
    lockCards = true;
    setTimeout(() => {
      if (cards[flipped[0]].val === cards[flipped[1]].val) {
        flipped.forEach(i => matched.add(i));
        spawnParticles && spawnParticles(200, 200, '#f59e0b');
        if (matched.size === cards.length) showWin('All Matched! 🎉');
      }
      flipped = []; lockCards = false; renderCards(cards);
    }, 900);
  }
}
`,

    ai_opponent: () => `
// ── Basic AI Opponent ─────────────────────────
function aiMove(board, aiPlayer, humanPlayer, size=3) {
  // Try to win
  for (let i=0;i<size;i++) for(let j=0;j<size;j++) {
    if (!board[i][j]) { board[i][j]=aiPlayer; if(checkWinner(board,aiPlayer,size)) return [i,j]; board[i][j]=null; }
  }
  // Block human
  for (let i=0;i<size;i++) for(let j=0;j<size;j++) {
    if (!board[i][j]) { board[i][j]=humanPlayer; if(checkWinner(board,humanPlayer,size)) { board[i][j]=null; return [i,j]; } board[i][j]=null; }
  }
  // Center
  const mid=Math.floor(size/2); if (!board[mid][mid]) return [mid,mid];
  // Random
  const empties=[];
  for(let i=0;i<size;i++) for(let j=0;j<size;j++) if(!board[i][j]) empties.push([i,j]);
  return empties[Math.floor(Math.random()*empties.length)];
}
`,

    drag_drop: () => `
// ── Drag and Drop ─────────────────────────────
let dragging = null, dragOffX = 0, dragOffY = 0;
function enableDrag(el, onDrop) {
  el.addEventListener('mousedown', e => { dragging = el; dragOffX = e.offsetX; dragOffY = e.offsetY; el.style.position='absolute'; el.style.zIndex=999; e.preventDefault(); });
}
document.addEventListener('mousemove', e => { if (dragging) { dragging.style.left = (e.clientX-dragOffX)+'px'; dragging.style.top = (e.clientY-dragOffY)+'px'; }});
document.addEventListener('mouseup',   e => { if (dragging) { dragging = null; }});
`,

    countdown_flow: (secs = 3) => `
// ── Countdown Flow ────────────────────────────
function runCountdown(cb) {
  let n = ${secs};
  const el = document.getElementById('countdown');
  if (!el) { cb(); return; }
  el.style.display='flex';
  const tick = () => { el.textContent = n > 0 ? n : 'GO!'; if(n-- < 0){ el.style.display='none'; cb(); } else setTimeout(tick, 1000); };
  tick();
}
`,

  };

  // ── Public API ────────────────────────────────────────
  return {
    /**
     * Get one or more mechanic code strings.
     * Pass a string or array of mechanic names + optional args.
     * @param {string|string[]} names
     * @param {Object} args  — optional per-mechanic config
     */
    get(names, args = {}) {
      const list = Array.isArray(names) ? names : [names];
      return list.map(name => {
        const fn = MECHANICS[name];
        if (!fn) return `// mechanic "${name}" not found\n`;
        try { return fn(args[name]); } catch { return fn(); }
      }).join('\n');
    },

    /** List all available mechanic names */
    list() { return Object.keys(MECHANICS); },

    /** The shared overlay CSS — inject once per template */
    OVERLAY_CSS: `
<style>
#overlay {
  display:none; position:fixed; inset:0;
  background:rgba(0,0,0,0.65); z-index:999;
  align-items:center; justify-content:center; flex-direction:column;
}
.overlay-box {
  background:white; border-radius:20px; padding:36px 44px;
  text-align:center; box-shadow:0 20px 60px rgba(0,0,0,0.4);
  max-width:340px; width:90%;
}
.win-box  { border-top: 6px solid #10b981; }
.lose-box { border-top: 6px solid #ef4444; }
.draw-box { border-top: 6px solid #f59e0b; }
.ov-icon  { font-size:3rem; margin-bottom:8px; }
.ov-title { font-size:1.6rem; font-weight:800; margin-bottom:8px; }
.ov-score { font-size:1rem; color:#6b7280; margin-bottom:16px; }
.ov-btn   {
  background:#7c3aed; color:white; border:none; border-radius:12px;
  padding:12px 28px; font-size:1rem; font-weight:800; cursor:pointer;
}
.ov-btn:hover { background:#6d28d9; }
</style>
<div id="overlay"></div>
`,
  };
})();
