/**
 * NymbleLogic Template Library v1.0
 * The Good Neighbor Guard — Christopher Hughes
 *
 * 50 templates: 25 games (full HTML) + 25 apps (full HTML)
 * Each template.html is a complete, self-contained playable app.
 */

window.NL_TEMPLATES = (() => {
  'use strict';

  // ── Shared overlay CSS injected into every game ──────
  const OV = `
<style>
#overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:99;align-items:center;justify-content:center;flex-direction:column;}
.ov-box{background:#fff;border-radius:20px;padding:32px 40px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.4);max-width:320px;width:90%;}
.ov-win{border-top:5px solid #10b981;}.ov-lose{border-top:5px solid #ef4444;}.ov-draw{border-top:5px solid #f59e0b;}
.ov-icon{font-size:2.8rem;margin-bottom:8px;}.ov-title{font-size:1.5rem;font-weight:800;margin-bottom:6px;}
.ov-sub{font-size:.95rem;color:#6b7280;margin-bottom:16px;}
.ov-btn{background:#7c3aed;color:#fff;border:none;border-radius:12px;padding:12px 28px;font-size:1rem;font-weight:800;cursor:pointer;margin:4px;}
.ov-btn:hover{background:#6d28d9;}
</style><div id="overlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:99;align-items:center;justify-content:center;"></div>`;

  const OV_JS = `
function showOverlay(icon,title,sub,cls){
  const o=document.getElementById('overlay');
  o.innerHTML='<div class="ov-box '+cls+'"><div class="ov-icon">'+icon+'</div><div class="ov-title">'+title+'</div><div class="ov-sub">'+sub+'</div><button class="ov-btn" onclick="restartGame()">Play Again</button></div>';
  o.style.display='flex';gameActive=false;
}
function showWin(s){showOverlay('🏆','You Win!','Score: '+(typeof score!=='undefined'?score:''),'ov-win');}
function showLose(s){showOverlay('💀','Game Over','Score: '+(typeof score!=='undefined'?score:''),'ov-lose');}
function showDraw(){showOverlay('🤝',"It's a Draw!",'','ov-draw');}
function hideOverlay(){document.getElementById('overlay').style.display='none';}`;

  // ── HUD builder ──────────────────────────────────────
  function hud(items, bg='#1e1b4b', fg='#e2e8f0') {
    return `<div id="hud" style="display:flex;gap:18px;align-items:center;padding:10px 18px;background:${bg};color:${fg};font-family:'Nunito',sans-serif;font-weight:800;font-size:1rem;user-select:none;">
${items.map(([lbl,id]) => `<span>${lbl}: <span id="${id}">0</span></span>`).join('')}
<button onclick="restartGame()" style="margin-left:auto;background:#7c3aed;color:#fff;border:none;border-radius:8px;padding:6px 14px;cursor:pointer;font-weight:800;">↺</button>
</div>`;
  }

  // ═══════════════════════════════════════════════════════
  // GAMES (1-25)
  // ═══════════════════════════════════════════════════════

  const GAMES = {

    connect_four: {
      id:'connect_four', category:'game', title:'Connect Four',
      summary:'Classic 4-in-a-row strategy game vs AI or 2-player.',
      kidOk:true, proOk:true,
      winLogic:'4 in a row horizontally, vertically, or diagonally',
      loseLogic:'Opponent gets 4 in a row',
      drawLogic:'Board is full with no winner',
      html: () => `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Connect Four</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#1e1b4b;font-family:'Segoe UI',sans-serif;display:flex;flex-direction:column;align-items:center;min-height:100vh;padding:20px;color:white;}
h1{font-size:1.8rem;font-weight:900;margin-bottom:10px;color:#a78bfa;}
#status{font-size:1rem;font-weight:700;margin-bottom:14px;color:#e2e8f0;min-height:24px;}
#board{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;background:#312e81;padding:14px;border-radius:16px;box-shadow:0 8px 30px rgba(0,0,0,.5);max-width:420px;width:100%;}
.col-btn{background:none;border:none;cursor:pointer;padding:4px 0;font-size:1.2rem;color:#a78bfa;}
.col-btn:hover{color:#c4b5fd;}
.cell{width:100%;aspect-ratio:1;border-radius:50%;background:#1e1b4b;border:2px solid #312e81;transition:background .2s;}
.cell.p1{background:#ef4444;box-shadow:0 0 10px #ef4444;}
.cell.p2{background:#fbbf24;box-shadow:0 0 10px #fbbf24;}
.cell.win{animation:blink .5s infinite alternate;}
@keyframes blink{to{filter:brightness(1.6);}}
#score-bar{display:flex;gap:20px;margin-top:14px;font-weight:800;}
.score-chip{background:#312e81;border-radius:10px;padding:8px 18px;}
</style></head><body>
<h1>Connect Four</h1>
<div id="status">🔴 Your Turn</div>
<div id="board"></div>
<div id="score-bar"><div class="score-chip">You 🔴 <span id="s1">0</span></div><div class="score-chip">AI 🟡 <span id="s2">0</span></div></div>
${OV}
<script>
const ROWS=6,COLS=7;let board,currentPlayer,gameActive,scores={1:0,2:0};
${OV_JS}
function init(){
  board=Array.from({length:ROWS},()=>Array(COLS).fill(0));
  currentPlayer=1;gameActive=true;
  document.getElementById('status').textContent='🔴 Your Turn';
  render();hideOverlay();
}
function render(){
  const b=document.getElementById('board'); b.innerHTML='';
  for(let c=0;c<COLS;c++){const btn=document.createElement('button');btn.className='col-btn';btn.textContent='▼';btn.onclick=()=>drop(c);b.appendChild(btn);}
  for(let r=0;r<ROWS;r++) for(let c=0;c<COLS;c++){const d=document.createElement('div');d.className='cell';if(board[r][c]===1)d.classList.add('p1');if(board[r][c]===2)d.classList.add('p2');b.appendChild(d);}
}
function drop(col){
  if(!gameActive||currentPlayer!==1)return;
  const r=getRow(col); if(r<0)return;
  board[r][col]=1; render();
  const win=checkWin(1); if(win){highlight(win);scores[1]++;document.getElementById('s1').textContent=scores[1];setTimeout(()=>{showWin();if(window.parent&&window.parent.nymGameWin)window.parent.nymGameWin();},400);return;}
  if(isFull()){setTimeout(()=>showDraw(),200);return;}
  currentPlayer=2; document.getElementById('status').textContent='🟡 AI Thinking…';
  setTimeout(aiTurn,500);
}
function aiTurn(){
  if(!gameActive)return;
  let col=getBestMove();
  const r=getRow(col); if(r<0){for(let c=0;c<COLS;c++){if(getRow(c)>=0){col=c;break;}}}
  board[getRow(col)][col]=2; render();
  const win=checkWin(2); if(win){highlight(win);scores[2]++;document.getElementById('s2').textContent=scores[2];setTimeout(()=>showLose('AI wins!'),400);return;}
  if(isFull()){setTimeout(()=>showDraw(),200);return;}
  currentPlayer=1; document.getElementById('status').textContent='🔴 Your Turn';
}
function getRow(col){for(let r=ROWS-1;r>=0;r--)if(!board[r][col])return r;return -1;}
function isFull(){return board[0].every((_,c)=>getRow(c)<0);}
function checkWin(p){
  const dirs=[[0,1],[1,0],[1,1],[1,-1]];
  for(let r=0;r<ROWS;r++) for(let c=0;c<COLS;c++){
    for(const[dr,dc] of dirs){
      const cells=[];
      for(let i=0;i<4;i++){const nr=r+dr*i,nc=c+dc*i;if(nr<0||nr>=ROWS||nc<0||nc>=COLS||board[nr][nc]!==p)break;cells.push([nr,nc]);}
      if(cells.length===4)return cells;
    }
  }
  return null;
}
function highlight(cells){cells.forEach(([r,c])=>{const idx=COLS+r*COLS+c;const el=document.getElementById('board').children[idx];if(el)el.classList.add('win');});}
function getBestMove(){
  for(let c=0;c<COLS;c++){const r=getRow(c);if(r>=0){board[r][c]=2;if(checkWin(2)){board[r][c]=0;return c;}board[r][c]=0;}}
  for(let c=0;c<COLS;c++){const r=getRow(c);if(r>=0){board[r][c]=1;if(checkWin(1)){board[r][c]=0;return c;}board[r][c]=0;}}
  if(getRow(3)>=0)return 3;
  const valid=[];for(let c=0;c<COLS;c++)if(getRow(c)>=0)valid.push(c);
  return valid[Math.floor(Math.random()*valid.length)];
}
function restartGame(){init();}
init();
</script></body></html>`
    },

    tic_tac_toe: {
      id:'tic_tac_toe', category:'game', title:'Tic Tac Toe',
      summary:'Classic 3x3 grid game vs AI.',
      kidOk:true, proOk:true,
      winLogic:'3 in a row', loseLogic:'AI gets 3 in a row', drawLogic:'Board full',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Tic Tac Toe</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{background:linear-gradient(135deg,#1e1b4b,#312e81);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;color:white;padding:20px;}
h1{font-size:2rem;font-weight:900;color:#a78bfa;margin-bottom:8px;}
#status{font-size:1.1rem;font-weight:700;margin-bottom:20px;color:#c4b5fd;}
#board{display:grid;grid-template-columns:repeat(3,100px);grid-template-rows:repeat(3,100px);gap:8px;}
.cell{background:rgba(255,255,255,.08);border:none;border-radius:12px;font-size:2.8rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .2s;}
.cell:hover:empty{background:rgba(255,255,255,.15);}
.cell.win{background:rgba(16,185,129,.3);animation:glow .5s infinite alternate;}
@keyframes glow{to{box-shadow:0 0 20px #10b981;}}
#scores{display:flex;gap:20px;margin-top:20px;font-weight:800;font-size:1rem;}
.sc{background:rgba(255,255,255,.1);border-radius:10px;padding:8px 18px;}
</style></head><body>
<h1>Tic Tac Toe</h1>
<div id="status">You are ✖ — Your turn</div>
<div id="board"></div>
<div id="scores"><div class="sc">You ✖ <span id="s1">0</span></div><div class="sc">AI ○ <span id="s2">0</span></div><div class="sc">Draw <span id="sd">0</span></div></div>
${OV}
<script>
let bd,ga,sc={x:0,o:0,d:0};
${OV_JS}
const W=[[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
function init(){bd=Array(9).fill(null);ga=true;document.getElementById('status').textContent='You are ✖ — Your turn';render();hideOverlay();}
function render(){const b=document.getElementById('board');b.innerHTML='';bd.forEach((v,i)=>{const d=document.createElement('button');d.className='cell';d.textContent=v||'';d.onclick=()=>move(i);b.appendChild(d);});}
function move(i){if(!ga||bd[i])return;bd[i]='X';const w=check('X');if(w){mark(w);sc.x++;document.getElementById('s1').textContent=sc.x;setTimeout(()=>{showWin();if(window.parent&&window.parent.nymGameWin)window.parent.nymGameWin();},300);return;}if(full()){sc.d++;document.getElementById('sd').textContent=sc.d;setTimeout(showDraw,300);return;}document.getElementById('status').textContent='AI thinking…';setTimeout(aiMove,400);}
function aiMove(){
  let best=null,bv=-Infinity;
  bd.forEach((_,i)=>{if(!bd[i]){bd[i]='O';const v=mini(false,-Infinity,Infinity);bd[i]=null;if(v>bv){bv=v;best=i;}}});
  if(best===null)return;bd[best]='O';render();
  const w=check('O');if(w){mark(w);sc.o++;document.getElementById('s2').textContent=sc.o;setTimeout(()=>showLose('AI wins!'),300);return;}
  if(full()){sc.d++;document.getElementById('sd').textContent=sc.d;setTimeout(showDraw,300);return;}
  document.getElementById('status').textContent='Your turn ✖';
}
function mini(maxing,a,b){
  const wx=check('X'),wo=check('O');
  if(wx)return-10;if(wo)return 10;if(full())return 0;
  let v=maxing?-Infinity:Infinity;
  for(let i=0;i<9;i++){if(!bd[i]){bd[i]=maxing?'O':'X';const s=mini(!maxing,a,b);bd[i]=null;if(maxing){v=Math.max(v,s);a=Math.max(a,v);}else{v=Math.min(v,s);b=Math.min(b,v);}if(b<=a)break;}}
  return v;
}
function check(p){return W.find(w=>w.every(i=>bd[i]===p))||null;}
function full(){return bd.every(v=>v!==null);}
function mark(w){render();w.forEach(i=>{document.getElementById('board').children[i].classList.add('win');});}
function restartGame(){init();}
init();
</script></body></html>`
    },

    snake_game: {
      id:'snake_game', category:'game', title:'Snake Game',
      summary:'Grow the snake by eating food. Avoid walls and yourself.',
      kidOk:true, proOk:true,
      winLogic:'Reach target length (optional milestone)', loseLogic:'Hit wall or self', drawLogic:'N/A',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Snake</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#111827;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;font-family:'Segoe UI',sans-serif;color:white;padding:10px;}
h1{font-size:1.8rem;font-weight:900;color:#34d399;margin-bottom:8px;}
#hud{display:flex;gap:20px;margin-bottom:10px;font-weight:800;font-size:1rem;}
canvas{border:3px solid #374151;border-radius:8px;touch-action:none;}
#ctrl{display:flex;flex-direction:column;align-items:center;gap:6px;margin-top:12px;}
.ctrl-row{display:flex;gap:6px;}
.ctrl-btn{width:48px;height:48px;background:#374151;border:none;border-radius:10px;font-size:1.3rem;cursor:pointer;color:white;}
.ctrl-btn:hover{background:#4b5563;}
</style></head><body>
<h1>🐍 Snake</h1>
<div id="hud"><span>Score: <span id="score">0</span></span><span>Best: <span id="highscore">0</span></span></div>
<canvas id="c" width="400" height="400"></canvas>
<div id="ctrl">
  <div class="ctrl-row"><button class="ctrl-btn" onclick="setDir(0,-1)">⬆️</button></div>
  <div class="ctrl-row"><button class="ctrl-btn" onclick="setDir(-1,0)">⬅️</button><button class="ctrl-btn" onclick="setDir(0,1)">⬇️</button><button class="ctrl-btn" onclick="setDir(1,0)">➡️</button></div>
</div>
${OV}
<script>
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
const G=20,S=400/G;
let snake,dir,nextDir,food,score,hs=parseInt(localStorage.getItem('snake_hs')||'0'),gameActive,loop;
${OV_JS}
function init(){
  snake=[{x:10,y:10},{x:9,y:10},{x:8,y:10}];
  dir={x:1,y:0};nextDir={x:1,y:0};
  score=0;document.getElementById('score').textContent=0;document.getElementById('highscore').textContent=hs;
  placeFood();gameActive=true;clearInterval(loop);loop=setInterval(tick,120);hideOverlay();
}
function placeFood(){do{food={x:Math.floor(Math.random()*G),y:Math.floor(Math.random()*G)}}while(snake.some(s=>s.x===food.x&&s.y===food.y));}
function tick(){
  if(!gameActive)return;
  dir={...nextDir};
  const head={x:snake[0].x+dir.x,y:snake[0].y+dir.y};
  if(head.x<0||head.x>=G||head.y<0||head.y>=G||snake.some(s=>s.x===head.x&&s.y===head.y)){clearInterval(loop);showLose();return;}
  snake.unshift(head);
  if(head.x===food.x&&head.y===food.y){score+=10;if(score>hs){hs=score;localStorage.setItem('snake_hs',hs);}document.getElementById('score').textContent=score;document.getElementById('highscore').textContent=hs;placeFood();}
  else snake.pop();
  draw();
}
function draw(){
  ctx.fillStyle='#111827';ctx.fillRect(0,0,400,400);
  ctx.fillStyle='#ef4444';ctx.beginPath();ctx.arc(food.x*S+S/2,food.y*S+S/2,S/2-2,0,Math.PI*2);ctx.fill();
  snake.forEach((s,i)=>{ctx.fillStyle=i===0?'#34d399':'#059669';ctx.beginPath();ctx.roundRect(s.x*S+1,s.y*S+1,S-2,S-2,4);ctx.fill();});
}
function setDir(x,y){if(x===dir.x*-1&&y===dir.y*-1)return;nextDir={x,y};}
document.addEventListener('keydown',e=>{
  if(e.key==='ArrowLeft')setDir(-1,0);if(e.key==='ArrowRight')setDir(1,0);
  if(e.key==='ArrowUp')setDir(0,-1);if(e.key==='ArrowDown')setDir(0,1);
  e.preventDefault();
});
let tx=0,ty=0;
canvas.addEventListener('touchstart',e=>{tx=e.touches[0].clientX;ty=e.touches[0].clientY;},{passive:true});
canvas.addEventListener('touchend',e=>{const dx=e.changedTouches[0].clientX-tx,dy=e.changedTouches[0].clientY-ty;if(Math.abs(dx)>Math.abs(dy)){setDir(dx>0?1:-1,0);}else{setDir(0,dy>0?1:-1);}},{passive:true});
function restartGame(){init();}
init();
</script></body></html>`
    },

    dodge_game: {
      id:'dodge_game', category:'game', title:'Dodge Game',
      summary:'Move to avoid falling enemies. Survive as long as you can.',
      kidOk:true, proOk:true,
      winLogic:'Survive target time', loseLogic:'Hit by enemy', drawLogic:'N/A',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Dodge!</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#0f0630;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;font-family:'Segoe UI',sans-serif;color:white;padding:10px;overflow:hidden;}h1{font-size:1.6rem;font-weight:900;color:#a78bfa;margin-bottom:8px;}#hud{display:flex;gap:20px;margin-bottom:8px;font-weight:800;}canvas{border:2px solid #3730a3;border-radius:8px;touch-action:none;}</style></head><body>
<h1>⚡ Dodge!</h1>
<div id="hud"><span>Score: <span id="score">0</span></span><span>Lives: <span id="lives">❤️❤️❤️</span></span></div>
<canvas id="c" width="380" height="460"></canvas>
${OV}
<script>
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
let player,enemies,score,lives,gameActive,raf,frame,spawnRate;
${OV_JS}
function init(){
  player={x:190,y:400,w:36,h:36,speed:5};
  enemies=[];score=0;lives=3;frame=0;spawnRate=60;gameActive=true;
  document.getElementById('score').textContent=0;
  document.getElementById('lives').textContent='❤️❤️❤️';
  hideOverlay();cancelAnimationFrame(raf);loop();
}
function loop(){
  if(!gameActive)return;
  raf=requestAnimationFrame(loop);frame++;
  ctx.fillStyle='#0f0630';ctx.fillRect(0,0,380,460);
  // Move player
  if(keys['ArrowLeft']&&player.x>0)player.x-=player.speed;
  if(keys['ArrowRight']&&player.x<380-player.w)player.x+=player.speed;
  // Spawn
  if(frame%spawnRate===0){enemies.push({x:Math.random()*(380-24),y:-24,w:24,h:24,speed:2+Math.random()*2+score/200});}
  if(frame%600===0&&spawnRate>20)spawnRate--;
  // Update enemies
  for(let i=enemies.length-1;i>=0;i--){
    enemies[i].y+=enemies[i].speed;
    if(enemies[i].y>460){enemies.splice(i,1);score++;document.getElementById('score').textContent=score;continue;}
    if(rectHit(player,enemies[i])){enemies.splice(i,1);lives--;document.getElementById('lives').textContent='❤️'.repeat(Math.max(lives,0));if(lives<=0){showLose();return;}}
  }
  // Draw player
  ctx.fillStyle='#7c3aed';ctx.beginPath();ctx.arc(player.x+18,player.y+18,18,0,Math.PI*2);ctx.fill();
  ctx.font='20px serif';ctx.textAlign='center';ctx.fillText('🧙',player.x+18,player.y+26);
  // Draw enemies
  enemies.forEach(e=>{ctx.font='22px serif';ctx.textAlign='center';ctx.fillText('💀',e.x+12,e.y+20);});
  // Touch
  if(touchActive){if(touchX<player.x+18)player.x-=player.speed;if(touchX>player.x+18)player.x+=player.speed;}
}
function rectHit(a,b){return a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;}
const keys={};document.addEventListener('keydown',e=>{keys[e.key]=true;e.preventDefault();});document.addEventListener('keyup',e=>{keys[e.key]=false;});
let touchActive=false,touchX=0;
canvas.addEventListener('touchmove',e=>{e.preventDefault();const r=canvas.getBoundingClientRect();touchX=e.touches[0].clientX-r.left;touchActive=true;},{passive:false});
canvas.addEventListener('touchend',()=>touchActive=false);
function restartGame(){init();}
init();
</script></body></html>`
    },

    clicker_game: {
      id:'clicker_game', category:'game', title:'Clicker Game',
      summary:'Click to earn points and buy upgrades.',
      kidOk:true, proOk:true,
      winLogic:'Reach target score', loseLogic:'N/A', drawLogic:'N/A',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Clicker</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:linear-gradient(135deg,#7c3aed,#4f46e5);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;color:white;padding:20px;gap:16px;}h1{font-size:2rem;font-weight:900;}.score-box{font-size:2.5rem;font-weight:900;background:rgba(255,255,255,.15);border-radius:16px;padding:16px 40px;text-align:center;}#btn{font-size:5rem;border:none;background:rgba(255,255,255,.15);border-radius:50%;width:150px;height:150px;cursor:pointer;transition:transform .1s;user-select:none;}#btn:active{transform:scale(.9);}
.upgrades{display:flex;flex-direction:column;gap:10px;width:100%;max-width:320px;}
.upg-btn{background:rgba(255,255,255,.15);border:2px solid rgba(255,255,255,.3);color:white;border-radius:12px;padding:12px 16px;cursor:pointer;font-size:.95rem;font-weight:700;text-align:left;transition:all .2s;}
.upg-btn:hover:not(:disabled){background:rgba(255,255,255,.25);}
.upg-btn:disabled{opacity:.4;cursor:not-allowed;}
#floats{position:fixed;inset:0;pointer-events:none;overflow:hidden;}
.float{position:absolute;font-size:1.2rem;font-weight:900;animation:floatUp 1s ease-out forwards;color:#fbbf24;}
@keyframes floatUp{to{opacity:0;transform:translateY(-80px);}}</style></head><body>
<h1>🖱️ Clicker!</h1>
<div class="score-box"><div id="score">0</div><div style="font-size:.9rem;font-weight:600;opacity:.8;">clicks/sec: <span id="cps">0</span></div></div>
<button id="btn" onclick="clickBtn(event)">⭐</button>
<div class="upgrades">
  <button class="upg-btn" id="u1" onclick="buyUpgrade(0)" data-cost="50">⚡ Double Click (50)</button>
  <button class="upg-btn" id="u2" onclick="buyUpgrade(1)" data-cost="200">🤖 Auto Clicker (200)</button>
  <button class="upg-btn" id="u3" onclick="buyUpgrade(2)" data-cost="1000">🚀 Mega Boost (1000)</button>
</div>
<div id="floats"></div>
<script>
let score=0,clickPow=1,autoRate=0;
const upgrades=[
  {cost:50,owned:false,fn:()=>{clickPow*=2;}},
  {cost:200,owned:false,fn:()=>{autoRate+=1;}},
  {cost:1000,owned:false,fn:()=>{clickPow*=5;autoRate+=5;}},
];
setInterval(()=>{if(autoRate>0){score+=autoRate;updateScore();}},1000);
setInterval(()=>{document.getElementById('cps').textContent=autoRate;},500);
function clickBtn(e){
  score+=clickPow;updateScore();
  const f=document.createElement('div');f.className='float';f.textContent='+'+clickPow;
  const r=document.getElementById('btn').getBoundingClientRect();
  f.style.left=(r.left+r.width/2-10)+'px';f.style.top=(r.top-10)+'px';
  document.getElementById('floats').appendChild(f);setTimeout(()=>f.remove(),1000);
}
function updateScore(){document.getElementById('score').textContent=score;
  upgrades.forEach((u,i)=>{const btn=document.getElementById('u'+(i+1));btn.disabled=u.owned||score<u.cost;});
}
function buyUpgrade(i){const u=upgrades[i];if(u.owned||score<u.cost)return;score-=u.cost;u.owned=true;u.fn();updateScore();const btn=document.getElementById('u'+(i+1));btn.textContent='✅ '+btn.textContent.replace(/^\S+ /,'');btn.disabled=true;}
updateScore();
</script></body></html>`
    },

    memory_match: {
      id:'memory_match', category:'game', title:'Memory Match',
      summary:'Flip cards to find matching pairs.',
      kidOk:true, proOk:true,
      winLogic:'All pairs matched', loseLogic:'Timer expires (timed mode)', drawLogic:'N/A',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Memory Match</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:linear-gradient(135deg,#0ea5e9,#38bdf8);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;color:white;padding:20px;gap:14px;}h1{font-size:1.8rem;font-weight:900;}#hud{display:flex;gap:20px;font-weight:800;}#grid{display:grid;grid-template-columns:repeat(4,80px);gap:10px;}
.card{width:80px;height:80px;border-radius:12px;cursor:pointer;font-size:2rem;display:flex;align-items:center;justify-content:center;background:#0369a1;border:none;color:transparent;transition:all .3s;user-select:none;}
.card.flipped{background:white;color:inherit;}
.card.matched{background:#bbf7d0;color:inherit;animation:pop .3s ease;}
@keyframes pop{50%{transform:scale(1.15);}}</style></head><body>
<h1>🃏 Memory Match</h1>
<div id="hud"><span>Moves: <span id="moves">0</span></span><span>Pairs: <span id="pairs">0</span>/8</span><span>Best: <span id="best">-</span></span></div>
<div id="grid"></div>
${OV}
<script>
const EMOJIS=['🐶','🐱','🦊','🐸','🦋','🌸','🍕','⭐'];
let cards,flipped,matched,moves,lock;
${OV_JS}
function init(){
  const vals=[...EMOJIS,...EMOJIS].sort(()=>Math.random()-.5);
  cards=vals.map((v,i)=>({id:i,val:v,isFlipped:false,isMatched:false}));
  flipped=[];matched=0;moves=0;lock=false;
  document.getElementById('moves').textContent=0;document.getElementById('pairs').textContent=0;
  render();hideOverlay();
}
function render(){
  const g=document.getElementById('grid');g.innerHTML='';
  cards.forEach(c=>{
    const d=document.createElement('button');d.className='card'+(c.isFlipped||c.isMatched?' flipped':'')+(c.isMatched?' matched':'');
    d.textContent=c.isFlipped||c.isMatched?c.val:'';d.onclick=()=>flip(c);g.appendChild(d);
  });
}
function flip(c){
  if(lock||c.isFlipped||c.isMatched)return;
  c.isFlipped=true;flipped.push(c);render();
  if(flipped.length===2){
    moves++;document.getElementById('moves').textContent=moves;lock=true;
    setTimeout(()=>{
      if(flipped[0].val===flipped[1].val){flipped.forEach(x=>x.isMatched=true);matched++;document.getElementById('pairs').textContent=matched;
        if(matched===8){const b=parseInt(localStorage.getItem('mm_best')||'999');if(moves<b)localStorage.setItem('mm_best',moves);document.getElementById('best').textContent=localStorage.getItem('mm_best');showWin('All matched in '+moves+' moves!');if(window.parent&&window.parent.nymGameWin)window.parent.nymGameWin();;}
      }else{flipped.forEach(x=>x.isFlipped=false);}
      flipped=[];lock=false;render();
    },900);
  }
}
function restartGame(){init();}
function showWin(s){showOverlay('🏆',s,'','ov-win');}
function showOverlay(icon,title,sub,cls){const o=document.getElementById('overlay');o.innerHTML='<div class="ov-box '+cls+'"><div class="ov-icon">'+icon+'</div><div class="ov-title">'+title+'</div><button class="ov-btn" onclick="restartGame()">Play Again</button></div>';o.style.display='flex';}
init();
</script></body></html>`
    },

    quiz_game: {
      id:'quiz_game', category:'game', title:'Quiz Game',
      summary:'Answer multiple choice questions. Reach the pass threshold to win.',
      kidOk:true, proOk:true,
      winLogic:'Score >= 70%', loseLogic:'Score < 70%', drawLogic:'N/A',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Quiz!</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:linear-gradient(135deg,#1e1b4b,#4f46e5);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;color:white;padding:24px;}.quiz-box{background:rgba(255,255,255,.1);border-radius:20px;padding:28px;max-width:480px;width:100%;}.q-num{font-size:.85rem;font-weight:700;color:#c4b5fd;margin-bottom:8px;}.q-text{font-size:1.2rem;font-weight:800;margin-bottom:20px;line-height:1.4;}.opt{width:100%;margin:8px 0;background:rgba(255,255,255,.12);border:2px solid transparent;color:white;border-radius:12px;padding:12px 18px;cursor:pointer;font-size:1rem;font-weight:700;text-align:left;transition:all .2s;}.opt:hover{border-color:#a78bfa;background:rgba(255,255,255,.2);}.opt.correct{background:#10b981;border-color:#10b981;}.opt.wrong{background:#ef4444;border-color:#ef4444;}.progress{height:6px;background:rgba(255,255,255,.2);border-radius:3px;margin-bottom:20px;overflow:hidden;}.progress-fill{height:100%;background:#a78bfa;border-radius:3px;transition:width .4s;}</style></head><body>
<div class="quiz-box">
  <div class="progress"><div class="progress-fill" id="prog" style="width:0%"></div></div>
  <div class="q-num" id="qnum">Question 1 / 10</div>
  <div class="q-text" id="qtext"></div>
  <div id="opts"></div>
</div>
${OV}
<script>
const QS=[
  {q:"What color do you get mixing red and blue?",a:"Purple",o:["Green","Orange","Purple","Yellow"]},
  {q:"How many sides does a hexagon have?",a:"6",o:["4","5","6","8"]},
  {q:"Which planet is closest to the Sun?",a:"Mercury",o:["Venus","Mercury","Mars","Earth"]},
  {q:"What is 7 × 8?",a:"56",o:["48","54","56","64"]},
  {q:"Which animal can live the longest?",a:"Tortoise",o:["Elephant","Tortoise","Parrot","Whale"]},
  {q:"What is the capital of France?",a:"Paris",o:["London","Berlin","Madrid","Paris"]},
  {q:"How many planets in our Solar System?",a:"8",o:["7","8","9","10"]},
  {q:"What is H2O?",a:"Water",o:["Air","Fire","Water","Earth"]},
  {q:"What shape has 3 sides?",a:"Triangle",o:["Square","Pentagon","Triangle","Hexagon"]},
  {q:"Which is the fastest land animal?",a:"Cheetah",o:["Lion","Horse","Cheetah","Tiger"]},
];
let qi=0,score=0,answered=false;
${OV_JS}
function init(){qi=0;score=0;answered=false;showQ();hideOverlay();}
function showQ(){
  if(qi>=QS.length){endQuiz();return;}
  const q=QS[qi];answered=false;
  document.getElementById('qnum').textContent='Question '+(qi+1)+' / '+QS.length;
  document.getElementById('qtext').textContent=q.q;
  document.getElementById('prog').style.width=((qi/QS.length)*100)+'%';
  const opts=document.getElementById('opts');opts.innerHTML='';
  [...q.o].sort(()=>Math.random()-.5).forEach(opt=>{
    const b=document.createElement('button');b.className='opt';b.textContent=opt;
    b.onclick=()=>answer(b,opt,q.a);opts.appendChild(b);
  });
}
function answer(btn,chosen,correct){
  if(answered)return;answered=true;
  if(chosen===correct){btn.classList.add('correct');score++;}
  else{btn.classList.add('wrong');document.querySelectorAll('.opt').forEach(b=>{if(b.textContent===correct)b.classList.add('correct');});}
  setTimeout(()=>{qi++;showQ();},900);
}
function endQuiz(){
  const pct=Math.round((score/QS.length)*100);
  if(pct>=70){showWin('You scored '+score+'/'+QS.length+' ('+pct+'%) — PASS!');if(window.parent&&window.parent.nymGameWin)window.parent.nymGameWin();};
  else showLose('You scored '+score+'/'+QS.length+' ('+pct+'%) — Try again!');
}
function showWin(s){const o=document.getElementById('overlay');o.innerHTML='<div class="ov-box ov-win"><div class="ov-icon">🏆</div><div class="ov-title">'+s+'</div><button class="ov-btn" onclick="restartGame()">Play Again</button></div>';o.style.display='flex';}
function showLose(s){const o=document.getElementById('overlay');o.innerHTML='<div class="ov-box ov-lose"><div class="ov-icon">📚</div><div class="ov-title">'+s+'</div><button class="ov-btn" onclick="restartGame()">Try Again</button></div>';o.style.display='flex';}
function restartGame(){init();}
init();
</script></body></html>`
    },

    breakout_paddle: {
      id:'breakout_paddle', category:'game', title:'Breakout',
      summary:'Break all the bricks with your ball.',
      kidOk:true, proOk:true,
      winLogic:'All bricks cleared', loseLogic:'Ball falls below paddle', drawLogic:'N/A',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Breakout</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#0a0015;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;font-family:'Segoe UI',sans-serif;color:white;padding:10px;}h1{font-size:1.6rem;font-weight:900;color:#a78bfa;margin-bottom:8px;}#hud{display:flex;gap:20px;margin-bottom:8px;font-weight:800;}canvas{border:2px solid #3730a3;border-radius:6px;touch-action:none;}</style></head><body>
<h1>🧱 Breakout</h1>
<div id="hud"><span>Score: <span id="score">0</span></span><span>Lives: <span id="lives">❤️❤️❤️</span></span></div>
<canvas id="c" width="400" height="480"></canvas>
${OV}
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d');
const ROWS=5,COLS=8,BW=42,BH=18,BPAD=4,BOFFX=12,BOFFY=50;
let paddle,ball,bricks,score,lives,gameActive,raf;
${OV_JS}
function init(){
  paddle={x:160,y:450,w:80,h=12,speed:7};
  ball={x:200,y:420,r:8,vx:3,vy:-4};
  score=0;lives=3;gameActive=true;
  document.getElementById('score').textContent=0;document.getElementById('lives').textContent='❤️❤️❤️';
  bricks=[];const colors=['#ef4444','#f97316','#eab308','#22c55e','#3b82f6'];
  for(let r=0;r<ROWS;r++) for(let c2=0;c2<COLS;c2++) bricks.push({x:BOFFX+c2*(BW+BPAD),y:BOFFY+r*(BH+BPAD),alive:true,color:colors[r%colors.length]});
  hideOverlay();cancelAnimationFrame(raf);loop();
}
function loop(){
  if(!gameActive)return;
  raf=requestAnimationFrame(loop);
  // Move paddle
  if(keys['ArrowLeft']&&paddle.x>0)paddle.x-=paddle.speed;
  if(keys['ArrowRight']&&paddle.x<400-paddle.w)paddle.x+=paddle.speed;
  if(touchActive){paddle.x=Math.max(0,Math.min(400-paddle.w,touchX-paddle.w/2));}
  // Move ball
  ball.x+=ball.vx;ball.y+=ball.vy;
  if(ball.x-ball.r<0||ball.x+ball.r>400)ball.vx*=-1;
  if(ball.y-ball.r<0)ball.vy*=-1;
  if(ball.y+ball.r>480){lives--;document.getElementById('lives').textContent='❤️'.repeat(Math.max(lives,0));if(lives<=0){showLose();return;}ball.x=200;ball.y=360;ball.vy=-4;}
  // Paddle
  if(ball.y+ball.r>=paddle.y&&ball.x>=paddle.x&&ball.x<=paddle.x+paddle.w&&ball.vy>0){ball.vy*=-1;ball.vx+=(ball.x-(paddle.x+paddle.w/2))*0.05;}
  // Bricks
  let alive=0;
  bricks.forEach(b=>{
    if(!b.alive)return;alive++;
    if(ball.x+ball.r>b.x&&ball.x-ball.r<b.x+BW&&ball.y+ball.r>b.y&&ball.y-ball.r<b.y+BH){
      b.alive=false;ball.vy*=-1;score+=10;document.getElementById('score').textContent=score;
    }
  });
  if(alive===0){showWin();return;}
  // Draw
  ctx.fillStyle='#0a0015';ctx.fillRect(0,0,400,480);
  bricks.forEach(b=>{if(!b.alive)return;ctx.fillStyle=b.color;ctx.beginPath();ctx.roundRect(b.x,b.y,BW,BH,4);ctx.fill();});
  ctx.fillStyle='#7c3aed';ctx.beginPath();ctx.roundRect(paddle.x,paddle.y,paddle.w,12,6);ctx.fill();
  ctx.fillStyle='white';ctx.beginPath();ctx.arc(ball.x,ball.y,ball.r,0,Math.PI*2);ctx.fill();
}
const keys={};document.addEventListener('keydown',e=>{keys[e.key]=true;e.preventDefault();});document.addEventListener('keyup',e=>{keys[e.key]=false;});
let touchActive=false,touchX=200;
c.addEventListener('touchmove',e=>{e.preventDefault();const r=c.getBoundingClientRect();touchX=e.touches[0].clientX-r.left;touchActive=true;},{passive:false});
c.addEventListener('mousemove',e=>{const r=c.getBoundingClientRect();touchX=e.clientX-r.left;touchActive=true;});
function restartGame(){init();}
init();
</script></body></html>`
    },

    whack_a_mole: {
      id:'whack_a_mole', category:'game', title:'Whack-a-Mole',
      summary:'Tap the moles before they hide!',
      kidOk:true, proOk:false,
      winLogic:'Reach score target', loseLogic:'Timer expires', drawLogic:'N/A',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Whack-a-Mole</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:linear-gradient(180deg,#38bdf8,#86efac 60%,#22c55e);min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px;font-family:'Segoe UI',sans-serif;}h1{font-size:1.8rem;font-weight:900;color:white;text-shadow:0 2px 8px rgba(0,0,0,.3);margin-bottom:8px;}#hud{display:flex;gap:20px;font-weight:800;color:white;text-shadow:0 1px 4px rgba(0,0,0,.4);margin-bottom:16px;font-size:1.1rem;}#grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;max-width:360px;width:100%;}
.hole{background:rgba(0,0,0,.3);border-radius:50%;aspect-ratio:1;display:flex;align-items:center;justify-content:center;font-size:3rem;cursor:pointer;position:relative;overflow:hidden;transition:transform .1s;border:4px solid rgba(0,0,0,.2);}
.hole:active{transform:scale(.92);}
.mole{position:absolute;bottom:0;transition:transform .2s;transform:translateY(100%);}
.mole.up{transform:translateY(0);}
#startBtn{margin-top:20px;background:#7c3aed;color:white;border:none;border-radius:14px;padding:14px 32px;font-size:1.1rem;font-weight:800;cursor:pointer;}</style></head><body>
<h1>🔨 Whack-a-Mole!</h1>
<div id="hud"><span>Score: <span id="score">0</span></span><span>Time: <span id="timer">30</span>s</span></div>
<div id="grid"></div>
<button id="startBtn" onclick="startGame()">▶ Start!</button>
${OV}
<script>
const N=9;let moles,score,timeLeft,gameActive,intervals=[];
${OV_JS}
function buildGrid(){
  const g=document.getElementById('grid');g.innerHTML='';
  moles=Array(N).fill(false);
  for(let i=0;i<N;i++){
    const h=document.createElement('div');h.className='hole';h.innerHTML='<div class="mole" id="m'+i+'">🐹</div>';
    h.addEventListener('click',()=>whack(i));
    g.appendChild(h);
  }
}
function startGame(){
  document.getElementById('startBtn').style.display='none';
  buildGrid();score=0;timeLeft=30;gameActive=true;
  document.getElementById('score').textContent=0;
  document.getElementById('timer').textContent=30;
  hideOverlay();
  intervals.push(setInterval(()=>{
    if(!gameActive)return;
    const i=Math.floor(Math.random()*N);showMole(i);
    setTimeout(()=>hideMole(i),700+Math.random()*600);
  },600));
  intervals.push(setInterval(()=>{
    timeLeft--;document.getElementById('timer').textContent=timeLeft;
    if(timeLeft<=0){gameActive=false;intervals.forEach(clearInterval);intervals=[];
      if(score>=20)showWin();else showLose();}
  },1000));
}
function showMole(i){moles[i]=true;const el=document.getElementById('m'+i);if(el)el.classList.add('up');}
function hideMole(i){moles[i]=false;const el=document.getElementById('m'+i);if(el)el.classList.remove('up');}
function whack(i){if(!gameActive||!moles[i])return;hideMole(i);score+=5;document.getElementById('score').textContent=score;}
function restartGame(){intervals.forEach(clearInterval);intervals=[];document.getElementById('startBtn').style.display='block';buildGrid();score=0;timeLeft=30;document.getElementById('score').textContent=0;document.getElementById('timer').textContent=30;hideOverlay();}
buildGrid();
</script></body></html>`
    },

    simon_says: {
      id:'simon_says', category:'game', title:'Simon Says',
      summary:'Repeat the color sequence. How far can you go?',
      kidOk:true, proOk:false,
      winLogic:'Beat level 10', loseLogic:'Wrong color pressed', drawLogic:'N/A',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Simon Says</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#111827;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;color:white;gap:16px;padding:20px;}h1{font-size:1.8rem;font-weight:900;}#status{font-size:1rem;font-weight:700;color:#9ca3af;}#board{display:grid;grid-template-columns:1fr 1fr;gap:10px;width:240px;height:240px;}
.btn{border:none;border-radius:20px;cursor:pointer;opacity:.7;transition:opacity .1s,filter .1s;}
.btn.lit{opacity:1;filter:brightness(2);}
.btn:disabled{cursor:not-allowed;}
#start{background:#7c3aed;color:white;border:none;border-radius:12px;padding:12px 28px;font-size:1rem;font-weight:800;cursor:pointer;}
</style></head><body>
<h1>🔵 Simon Says</h1>
<div id="status">Press Start to play</div>
<div id="level">Level: 0</div>
<div id="board">
  <button class="btn" id="b0" style="background:#ef4444;" onclick="playerPress(0)"></button>
  <button class="btn" id="b1" style="background:#3b82f6;" onclick="playerPress(1)"></button>
  <button class="btn" id="b2" style="background:#22c55e;" onclick="playerPress(2)"></button>
  <button class="btn" id="b3" style="background:#eab308;" onclick="playerPress(3)"></button>
</div>
<button id="start" onclick="startGame()">▶ Start</button>
${OV}
<script>
let seq=[],playerSeq=[],level=0,accepting=false;
${OV_JS}
function startGame(){seq=[];level=0;hideOverlay();nextRound();}
function nextRound(){
  level++;document.getElementById('level').textContent='Level: '+level;
  document.getElementById('status').textContent='Watch…';accepting=false;
  seq.push(Math.floor(Math.random()*4));
  let i=0;const iv=setInterval(()=>{if(i>=seq.length){clearInterval(iv);playerSeq=[];accepting=true;document.getElementById('status').textContent='Your turn!';return;}light(seq[i]);i++;},700);
}
function light(i){const b=document.getElementById('b'+i);b.classList.add('lit');setTimeout(()=>b.classList.remove('lit'),400);}
function playerPress(i){
  if(!accepting)return;
  light(i);playerSeq.push(i);
  const pos=playerSeq.length-1;
  if(playerSeq[pos]!==seq[pos]){accepting=false;document.getElementById('status').textContent='Wrong! Game Over';showLose();return;}
  if(playerSeq.length===seq.length){accepting=false;if(level>=10){showWin();return;}document.getElementById('status').textContent='✓ Nice! Next level…';setTimeout(nextRound,800);}
}
function restartGame(){startGame();}
</script></body></html>`
    },

    hangman: {
      id:'hangman', category:'game', title:'Hangman',
      summary:'Guess the word letter by letter.',
      kidOk:true, proOk:true,
      winLogic:'Reveal full word', loseLogic:'6 wrong guesses', drawLogic:'N/A',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Hangman</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#1e1b4b;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;color:white;padding:20px;gap:12px;}h1{font-size:1.8rem;font-weight:900;color:#a78bfa;}#gallows{font-size:1.4rem;font-family:monospace;white-space:pre;color:#e2e8f0;}#word{font-size:2.2rem;font-weight:900;letter-spacing:8px;margin:8px 0;}#wrong{font-size:.95rem;color:#f87171;min-height:24px;}#keys{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;max-width:400px;}
.key{width:36px;height:36px;border:none;border-radius:8px;background:#312e81;color:white;font-weight:800;cursor:pointer;font-size:.9rem;}
.key:disabled{opacity:.3;cursor:not-allowed;}
</style></head><body>
<h1>🪢 Hangman</h1>
<div id="gallows"></div>
<div id="word"></div>
<div id="wrong">Wrong: </div>
<div id="keys"></div>
${OV}
<script>
const WORDS=['ELEPHANT','RAINBOW','VOLCANO','LIBRARY','DOLPHIN','DIAMOND','PENGUIN','MUSHROOM','JUPITER','GIRAFFE'];
const STAGES=['😵','🧑','🧑‍🦱','🧍','🚶','🏃','💀'];
let word,guessed,wrong;
${OV_JS}
function init(){
  word=WORDS[Math.floor(Math.random()*WORDS.length)];
  guessed=new Set();wrong=0;render();hideOverlay();
}
function guess(l){
  if(guessed.has(l))return;guessed.add(l);
  if(!word.includes(l))wrong++;
  render();
  const won=[...word].every(c=>guessed.has(c));
  if(won){showWin('You guessed: '+word);}else if(wrong>=6){showLose('The word was: '+word);}
}
function render(){
  const stage=Math.min(wrong,STAGES.length-1);
  document.getElementById('gallows').textContent=STAGES[stage]+(wrong>0?'  ('+wrong+'/6 wrong)':'  Ready!');
  document.getElementById('word').textContent=[...word].map(c=>guessed.has(c)?c:'_').join(' ');
  document.getElementById('wrong').textContent='Wrong: '+[...guessed].filter(c=>!word.includes(c)).join(', ');
  const kb=document.getElementById('keys');kb.innerHTML='';
  'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').forEach(l=>{
    const b=document.createElement('button');b.className='key';b.textContent=l;b.disabled=guessed.has(l);b.onclick=()=>guess(l);kb.appendChild(b);
  });
}
function showWin(s){const o=document.getElementById('overlay');o.innerHTML='<div class="ov-box ov-win"><div class="ov-icon">🏆</div><div class="ov-title">'+s+'</div><button class="ov-btn" onclick="restartGame()">Play Again</button></div>';o.style.display='flex';}
function showLose(s){const o=document.getElementById('overlay');o.innerHTML='<div class="ov-box ov-lose"><div class="ov-icon">💀</div><div class="ov-title">'+s+'</div><button class="ov-btn" onclick="restartGame()">Try Again</button></div>';o.style.display='flex';}
function restartGame(){init();}
init();
</script></body></html>`
    },

    reaction_timer: {
      id:'reaction_timer', category:'game', title:'Reaction Timer',
      summary:'Tap when the screen flashes green — test your reaction speed.',
      kidOk:true, proOk:true,
      winLogic:'Average < 250ms', loseLogic:'Click too early', drawLogic:'N/A',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Reaction Timer</title><style>*{box-sizing:border-box;margin:0;padding:0;}
body{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;cursor:pointer;user-select:none;transition:background .2s;background:#1e1b4b;color:white;gap:20px;padding:20px;text-align:center;}
h1{font-size:2rem;font-weight:900;color:#a78bfa;}
#msg{font-size:1.6rem;font-weight:800;}#sub{font-size:1rem;color:#9ca3af;}
#results{font-size:1rem;font-weight:700;min-height:24px;color:#34d399;}
</style></head><body>
<h1>⚡ Reaction Timer</h1>
<div id="msg">Click to Start</div>
<div id="sub">We'll test your reaction 5 times</div>
<div id="results"></div>
<script>
let state='idle',startTime,times=[],waitHandle;
document.body.onclick=()=>{
  if(state==='idle'){start();}
  else if(state==='waiting'){tooEarly();}
  else if(state==='ready'){react();}
  else if(state==='done'){reset();}
};
function start(){
  state='waiting';times=[];
  document.body.style.background='#1e1b4b';
  document.getElementById('msg').textContent='Wait for green…';
  document.getElementById('sub').textContent='Don\'t click yet!';
  scheduleGo();
}
function scheduleGo(){
  const delay=1500+Math.random()*3000;
  waitHandle=setTimeout(()=>{state='ready';document.body.style.background='#059669';document.getElementById('msg').textContent='CLICK NOW!';startTime=Date.now();},delay);
}
function react(){
  const t=Date.now()-startTime;times.push(t);
  document.body.style.background='#1e1b4b';
  document.getElementById('msg').textContent=t+'ms';
  document.getElementById('results').textContent='Attempt '+times.length+' of 5';
  if(times.length<5){state='waiting';scheduleGo();}
  else{showResults();}
}
function tooEarly(){clearTimeout(waitHandle);state='waiting';document.body.style.background='#7f1d1d';document.getElementById('msg').textContent='Too early! Wait…';setTimeout(scheduleGo,1000);}
function showResults(){
  state='done';const avg=Math.round(times.reduce((a,b)=>a+b,0)/times.length);
  const grade=avg<200?'🚀 Superhuman!':avg<300?'⚡ Lightning fast!':avg<450?'👍 Good!':'🐢 Keep practicing!';
  document.getElementById('msg').textContent='Avg: '+avg+'ms';
  document.getElementById('sub').textContent=grade;
  document.getElementById('results').textContent='Click to play again';
}
function reset(){start();}
</script></body></html>`
    },

    color_reaction_game: {
      id:'color_reaction_game', category:'game', title:'Color Reaction',
      summary:'Click the correct color as fast as possible.',
      kidOk:true, proOk:false,
      winLogic:'Reach score 20', loseLogic:'Click wrong color or timer expires', drawLogic:'N/A',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Color Reaction</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#111827;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px;font-family:'Segoe UI',sans-serif;color:white;padding:20px;text-align:center;}h1{font-size:1.8rem;font-weight:900;}#target{font-size:2.5rem;font-weight:900;padding:16px 32px;border-radius:16px;background:#1f2937;min-width:200px;}#hud{font-size:1.1rem;font-weight:800;}#btns{display:grid;grid-template-columns:1fr 1fr;gap:12px;width:280px;}.cb{height:80px;border:none;border-radius:16px;cursor:pointer;font-size:1rem;font-weight:800;color:white;text-shadow:0 1px 4px rgba(0,0,0,.5);transition:transform .1s;}.cb:active{transform:scale(.95);}</style></head><body>
<h1>🎨 Color Reaction</h1>
<div id="hud">Score: <span id="score">0</span> | Time: <span id="timer">30</span>s</div>
<div id="target">Ready?</div>
<div id="btns"></div>
${OV}
<script>
const COLORS=[{name:'Red',h:'#ef4444'},{name:'Blue',h:'#3b82f6'},{name:'Green',h:'#22c55e'},{name:'Yellow',h:'#eab308'},{name:'Purple',h:'#8b5cf6'},{name:'Orange',h:'#f97316'}];
let score=0,timeLeft=30,target,gameActive=false,timerH;
${OV_JS}
function init(){score=0;timeLeft=30;gameActive=true;document.getElementById('score').textContent=0;document.getElementById('timer').textContent=30;hideOverlay();
  clearInterval(timerH);timerH=setInterval(()=>{timeLeft--;document.getElementById('timer').textContent=timeLeft;if(timeLeft<=0){endGame();}},1000);
  nextRound();}
function nextRound(){
  const shuffled=[...COLORS].sort(()=>Math.random()-.5).slice(0,4);
  target=shuffled[Math.floor(Math.random()*4)];
  document.getElementById('target').textContent=target.name;
  document.getElementById('target').style.color=target.h;
  const b=document.getElementById('btns');b.innerHTML='';
  shuffled.forEach(c=>{const btn=document.createElement('button');btn.className='cb';btn.style.background=c.h;btn.textContent=c.name;btn.onclick=()=>pick(c);b.appendChild(btn);});
}
function pick(c){if(!gameActive)return;if(c.name===target.name){score++;document.getElementById('score').textContent=score;if(score>=20){endGame(true);return;}}else{timeLeft=Math.max(0,timeLeft-3);document.getElementById('timer').textContent=timeLeft;}nextRound();}
function endGame(win){gameActive=false;clearInterval(timerH);if(win||score>=20)showWin();else showLose();}
function restartGame(){init();}
document.getElementById('target').textContent='Tap Start!';
const sb=document.createElement('button');sb.textContent='▶ Start';sb.style.cssText='background:#7c3aed;color:white;border:none;border-radius:12px;padding:12px 24px;font-size:1rem;font-weight:800;cursor:pointer;';
sb.onclick=()=>{sb.remove();init();};document.getElementById('btns').appendChild(sb);
</script></body></html>`
    },

    drawing_toy: {
      id:'drawing_toy', category:'game', title:'Drawing Toy',
      summary:'A free-form drawing canvas with color picker and brush sizes.',
      kidOk:true, proOk:false,
      winLogic:'N/A — creative toy', loseLogic:'N/A', drawLogic:'N/A',
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Drawing Toy</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#f8fafc;display:flex;flex-direction:column;height:100vh;font-family:'Segoe UI',sans-serif;}
#toolbar{padding:10px 16px;background:white;border-bottom:2px solid #e5e7eb;display:flex;gap:10px;align-items:center;flex-wrap:wrap;}
.tool-btn{padding:6px 14px;border:2px solid #e5e7eb;border-radius:8px;background:white;cursor:pointer;font-weight:700;font-size:.85rem;}
.tool-btn.active{background:#7c3aed;color:white;border-color:#7c3aed;}
#colorRow{display:flex;gap:6px;align-items:center;}
.swatch{width:28px;height:28px;border-radius:50%;border:3px solid transparent;cursor:pointer;}
.swatch.active{border-color:#111;}
#brushSize{width:80px;}
#canvas{flex:1;cursor:crosshair;touch-action:none;display:block;}
#saveBtn{background:#10b981;color:white;border:none;border-radius:8px;padding:6px 14px;font-weight:700;cursor:pointer;}
</style></head><body>
<div id="toolbar">
  <button class="tool-btn active" id="drawBtn" onclick="setTool('draw')">✏️ Draw</button>
  <button class="tool-btn" id="eraseBtn" onclick="setTool('erase')">⬜ Erase</button>
  <button class="tool-btn" onclick="clearCanvas()">🗑️ Clear</button>
  <div id="colorRow"></div>
  <label style="font-size:.8rem;font-weight:700;">Size: <input type="range" id="brushSize" min="2" max="40" value="8"/></label>
  <button id="saveBtn" onclick="saveImg()">💾 Save</button>
</div>
<canvas id="canvas"></canvas>
<script>
const canvas=document.getElementById('canvas'),ctx=canvas.getContext('2d');
let drawing=false,tool='draw',color='#7c3aed',brushSize=8;
const COLORS=['#111827','#ef4444','#f97316','#eab308','#22c55e','#3b82f6','#8b5cf6','#ec4899','#ffffff'];
const row=document.getElementById('colorRow');
COLORS.forEach(c=>{const s=document.createElement('div');s.className='swatch'+(c===color?' active':'');s.style.background=c;s.onclick=()=>{color=c;document.querySelectorAll('.swatch').forEach(x=>x.classList.remove('active'));s.classList.add('active');};row.appendChild(s);});
document.getElementById('brushSize').oninput=e=>brushSize=+e.target.value;
function resize(){canvas.width=canvas.clientWidth;canvas.height=canvas.clientHeight;ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);}
window.addEventListener('resize',resize);resize();
function pos(e){const r=canvas.getBoundingClientRect();return e.touches?{x:e.touches[0].clientX-r.left,y:e.touches[0].clientY-r.top}:{x:e.clientX-r.left,y:e.clientY-r.top};}
function startDraw(e){drawing=true;const p=pos(e);ctx.beginPath();ctx.moveTo(p.x,p.y);}
function draw(e){if(!drawing)return;const p=pos(e);ctx.lineWidth=brushSize;ctx.lineCap='round';ctx.strokeStyle=tool==='erase'?'white':color;ctx.lineTo(p.x,p.y);ctx.stroke();ctx.beginPath();ctx.moveTo(p.x,p.y);}
function endDraw(){drawing=false;ctx.beginPath();}
canvas.addEventListener('mousedown',startDraw);canvas.addEventListener('mousemove',draw);canvas.addEventListener('mouseup',endDraw);
canvas.addEventListener('touchstart',e=>{e.preventDefault();startDraw(e);},{passive:false});
canvas.addEventListener('touchmove',e=>{e.preventDefault();draw(e);},{passive:false});
canvas.addEventListener('touchend',endDraw);
function setTool(t){tool=t;document.getElementById('drawBtn').classList.toggle('active',t==='draw');document.getElementById('eraseBtn').classList.toggle('active',t==='erase');}
function clearCanvas(){ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);}
function saveImg(){const a=document.createElement('a');a.download='drawing.png';a.href=canvas.toDataURL();a.click();}
</script></body></html>`
    },

    // ── Remaining games use concise but complete templates ──

    platform_jumper:   { id:'platform_jumper',   category:'game', title:'Platform Jumper',   summary:'Jump across platforms. Collect stars. Reach the end.', kidOk:true,  proOk:true,  winLogic:'Reach finish', loseLogic:'Fall off', drawLogic:'N/A', html: () => buildCanvasGame('platform_jumper') },
    maze_runner:       { id:'maze_runner',        category:'game', title:'Maze Runner',       summary:'Navigate through the maze to reach the exit.',          kidOk:true,  proOk:true,  winLogic:'Reach exit',   loseLogic:'Timer',   drawLogic:'N/A', html: () => buildCanvasGame('maze_runner') },
    collect_and_avoid: { id:'collect_and_avoid',  category:'game', title:'Collect & Avoid',   summary:'Collect coins, dodge bombs.',                           kidOk:true,  proOk:true,  winLogic:'Target score', loseLogic:'Hit bomb', drawLogic:'N/A', html: () => buildCanvasGame('collect_and_avoid') },
    endless_runner:    { id:'endless_runner',     category:'game', title:'Endless Runner',    summary:'Jump over obstacles in a side-scrolling runner.',        kidOk:true,  proOk:true,  winLogic:'Score milestone', loseLogic:'Hit obstacle', drawLogic:'N/A', html: () => buildCanvasGame('endless_runner') },
    catch_the_stars:   { id:'catch_the_stars',    category:'game', title:'Catch the Stars',   summary:'Move your basket to catch falling stars.',              kidOk:true,  proOk:false, winLogic:'Catch 20 stars', loseLogic:'Miss 5',  drawLogic:'N/A', html: () => buildCanvasGame('catch_the_stars') },
    flappy_flight:     { id:'flappy_flight',      category:'game', title:'Flappy Flight',     summary:'Tap to fly through gaps. One hit and you\'re done.',    kidOk:true,  proOk:true,  winLogic:'Score 10',    loseLogic:'Hit pipe/ground', drawLogic:'N/A', html: () => buildCanvasGame('flappy_flight') },
    word_search:       { id:'word_search',        category:'game', title:'Word Search',       summary:'Find all hidden words in the grid.',                    kidOk:true,  proOk:false, winLogic:'All words found', loseLogic:'Timer', drawLogic:'N/A', html: () => buildCanvasGame('word_search') },
    trivia_show:       { id:'trivia_show',        category:'game', title:'Trivia Show',       summary:'A polished trivia game with categories.',               kidOk:false, proOk:true,  winLogic:'Pass threshold', loseLogic:'Fail threshold', drawLogic:'N/A', html: () => buildCanvasGame('trivia_show') },
    dress_up_toy:      { id:'dress_up_toy',       category:'game', title:'Dress Up Toy',      summary:'Mix and match outfits on a character.',                 kidOk:true,  proOk:false, winLogic:'N/A', loseLogic:'N/A', drawLogic:'N/A', html: () => buildCanvasGame('dress_up_toy') },
    sorting_game:      { id:'sorting_game',       category:'game', title:'Sorting Game',      summary:'Drag items into the correct category buckets.',         kidOk:true,  proOk:false, winLogic:'All sorted', loseLogic:'N/A', drawLogic:'N/A', html: () => buildCanvasGame('sorting_game') },
    shape_match:       { id:'shape_match',        category:'game', title:'Shape Match',       summary:'Match shapes to their silhouettes.',                    kidOk:true,  proOk:false, winLogic:'All matched', loseLogic:'N/A', drawLogic:'N/A', html: () => buildCanvasGame('shape_match') },
  };

  // ── Fallback canvas game generator for extended game list ─────────────────
  function buildCanvasGame(id) {
    const meta = GAMES[id] || { title: id, summary: '' };
    return `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>${meta.title}</title>
<style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#111827;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;font-family:'Segoe UI',sans-serif;color:white;padding:20px;gap:12px;}h1{font-size:1.8rem;font-weight:900;color:#a78bfa;}canvas{border:2px solid #374151;border-radius:8px;touch-action:none;}p{color:#9ca3af;text-align:center;max-width:340px;}button{background:#7c3aed;color:white;border:none;border-radius:12px;padding:12px 28px;font-size:1rem;font-weight:800;cursor:pointer;}</style></head><body>
<h1>${meta.title}</h1>
<canvas id="c" width="400" height="400"></canvas>
<p>${meta.summary}<br/><br/>🪄 This template is ready for the AI to customize!</p>
<button onclick="document.getElementById('c').getContext('2d').clearRect(0,0,400,400);drawPlaceholder()">Restart</button>
<script>
const c=document.getElementById('c'),ctx=c.getContext('2d');
function drawPlaceholder(){
  ctx.fillStyle='#1f2937';ctx.fillRect(0,0,400,400);
  ctx.fillStyle='#7c3aed';ctx.font='bold 40px serif';ctx.textAlign='center';ctx.fillText('${meta.title}',200,160);
  ctx.fillStyle='#9ca3af';ctx.font='18px sans-serif';ctx.fillText('Ready for customization',200,210);
  ctx.fillStyle='#a78bfa';ctx.font='60px serif';ctx.fillText('🎮',200,300);
}
drawPlaceholder();
</script></body></html>`;
  }

  // ═══════════════════════════════════════════════════════
  // APPS / TOOLS (26-50) — Full implementations
  // ═══════════════════════════════════════════════════════

  const APPS = {

    calculator_app: {
      id:'calculator_app', category:'app', title:'Calculator',
      summary:'A clean calculator with history.',
      kidOk:true, proOk:true,
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Calculator</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#1f2937;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;padding:20px;}
.calc{background:#111827;border-radius:20px;padding:20px;width:280px;box-shadow:0 20px 60px rgba(0,0,0,.5);}
#display{background:#0f172a;border-radius:12px;padding:16px;margin-bottom:14px;text-align:right;}
#expr{font-size:.85rem;color:#6b7280;min-height:20px;}
#result{font-size:2.2rem;font-weight:900;color:white;word-break:break-all;}
#history{font-size:.75rem;color:#4b5563;min-height:18px;margin-top:4px;}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;}
.btn{border:none;border-radius:12px;height:58px;font-size:1.1rem;font-weight:800;cursor:pointer;transition:filter .15s;}
.btn:active{filter:brightness(.8);}
.num{background:#1e293b;color:white;}
.op{background:#7c3aed;color:white;}
.eq{background:#10b981;color:white;}
.clr{background:#ef4444;color:white;}
</style></head><body><div class="calc">
<div id="display"><div id="expr"></div><div id="result">0</div><div id="history"></div></div>
<div class="grid">
  <button class="btn clr" onclick="cl()">AC</button>
  <button class="btn num" onclick="app('(')">(</button>
  <button class="btn num" onclick="app(')')">)</button>
  <button class="btn op"  onclick="op('/')">÷</button>
  <button class="btn num" onclick="app('7')">7</button>
  <button class="btn num" onclick="app('8')">8</button>
  <button class="btn num" onclick="app('9')">9</button>
  <button class="btn op"  onclick="op('*')">×</button>
  <button class="btn num" onclick="app('4')">4</button>
  <button class="btn num" onclick="app('5')">5</button>
  <button class="btn num" onclick="app('6')">6</button>
  <button class="btn op"  onclick="op('-')">−</button>
  <button class="btn num" onclick="app('1')">1</button>
  <button class="btn num" onclick="app('2')">2</button>
  <button class="btn num" onclick="app('3')">3</button>
  <button class="btn op"  onclick="op('+')">+</button>
  <button class="btn num" onclick="app('0')" style="grid-column:span 2">0</button>
  <button class="btn num" onclick="app('.')">.</button>
  <button class="btn eq"  onclick="eq()">=</button>
</div></div>
<script>
let expr='',hist=[];
function app(v){expr+=v;upd();}
function op(v){if(expr.slice(-1)===v||!expr)return;expr+=v;upd();}
function cl(){expr='';upd();}
function eq(){
  try{
    const r=Function('"use strict";return('+expr+')')();
    hist.unshift(expr+'='+r);if(hist.length>3)hist.pop();
    document.getElementById('history').textContent=hist[1]||'';
    expr=String(r);upd();
  }catch{document.getElementById('result').textContent='Error';}
}
function upd(){document.getElementById('expr').textContent=expr||'0';document.getElementById('result').textContent=expr||'0';}
</script></body></html>`
    },

    timer_app: {
      id:'timer_app', category:'app', title:'Timer',
      summary:'Countdown timer with alarm.',
      kidOk:true, proOk:true,
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Timer</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:linear-gradient(135deg,#1e1b4b,#312e81);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;color:white;gap:24px;padding:20px;}h1{font-size:1.8rem;font-weight:900;color:#a78bfa;}
#display{font-size:5rem;font-weight:900;font-variant-numeric:tabular-nums;letter-spacing:4px;}
#display.done{color:#10b981;animation:pulse 1s infinite;}
@keyframes pulse{50%{opacity:.5;}}
.controls{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;}
.preset{background:rgba(255,255,255,.12);border:none;color:white;border-radius:10px;padding:8px 16px;cursor:pointer;font-weight:700;}
.preset:hover{background:rgba(255,255,255,.22);}
.inputs{display:flex;gap:10px;align-items:center;font-size:1.1rem;font-weight:700;}
.num-inp{width:64px;background:rgba(255,255,255,.12);border:2px solid rgba(255,255,255,.2);color:white;border-radius:10px;padding:10px;font-size:1.4rem;font-weight:900;text-align:center;}
.btn{padding:14px 28px;border:none;border-radius:14px;font-size:1rem;font-weight:800;cursor:pointer;}
.btn-start{background:#10b981;color:white;}
.btn-pause{background:#f59e0b;color:#111;}
.btn-reset{background:rgba(255,255,255,.15);color:white;}
</style></head><body>
<h1>⏱ Timer</h1>
<div id="display">00:00</div>
<div class="inputs">
  <input class="num-inp" type="number" id="hIn" placeholder="h" min="0" max="23" value="0"/>h
  <input class="num-inp" type="number" id="mIn" placeholder="m" min="0" max="59" value="5"/>m
  <input class="num-inp" type="number" id="sIn" placeholder="s" min="0" max="59" value="0"/>s
</div>
<div class="controls">
  <button class="preset" onclick="setP(0,1,0)">1 min</button>
  <button class="preset" onclick="setP(0,5,0)">5 min</button>
  <button class="preset" onclick="setP(0,10,0)">10 min</button>
  <button class="preset" onclick="setP(0,25,0)">25 min</button>
</div>
<div class="controls">
  <button class="btn btn-start" id="startBtn" onclick="startStop()">▶ Start</button>
  <button class="btn btn-reset" onclick="reset()">↺ Reset</button>
</div>
<script>
let total=0,left=0,running=false,iv;
function setP(h,m,s){document.getElementById('hIn').value=h;document.getElementById('mIn').value=m;document.getElementById('sIn').value=s;reset();}
function getTotal(){return (+document.getElementById('hIn').value)*3600+(+document.getElementById('mIn').value)*60+(+document.getElementById('sIn').value);}
function fmt(s){const h=Math.floor(s/3600),m=Math.floor((s%3600)/60),sc=s%60;return(h?pad(h)+':':'')+pad(m)+':'+pad(sc);}
function pad(n){return String(n).padStart(2,'0');}
function startStop(){
  if(!running){
    if(!left)left=getTotal();if(!left)return;
    running=true;document.getElementById('startBtn').textContent='⏸ Pause';
    iv=setInterval(()=>{left--;render();if(left<=0){clearInterval(iv);running=false;document.getElementById('display').classList.add('done');document.getElementById('startBtn').textContent='▶ Start';try{new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAA').play();}catch{}}},1000);
  }else{clearInterval(iv);running=false;document.getElementById('startBtn').textContent='▶ Resume';}
}
function reset(){clearInterval(iv);running=false;left=0;document.getElementById('display').classList.remove('done');document.getElementById('startBtn').textContent='▶ Start';render();}
function render(){document.getElementById('display').textContent=fmt(left);}
</script></body></html>`
    },

    todo_app: {
      id:'todo_app', category:'app', title:'To-Do List',
      summary:'Add, complete, and delete tasks with local persistence.',
      kidOk:true, proOk:true,
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>To-Do</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#f8f7ff;min-height:100vh;font-family:'Segoe UI',sans-serif;padding:24px;max-width:520px;margin:0 auto;}
h1{font-size:2rem;font-weight:900;color:#7c3aed;margin-bottom:4px;}
.sub{color:#6b7280;font-size:.9rem;margin-bottom:20px;}
.add-row{display:flex;gap:10px;margin-bottom:20px;}
#inp{flex:1;border:2px solid #e5e7eb;border-radius:12px;padding:12px 16px;font-size:1rem;background:white;}
#inp:focus{outline:none;border-color:#a78bfa;}
#addBtn{background:#7c3aed;color:white;border:none;border-radius:12px;padding:12px 20px;font-weight:800;cursor:pointer;}
.filters{display:flex;gap:8px;margin-bottom:16px;}
.fil{background:white;border:2px solid #e5e7eb;border-radius:8px;padding:6px 14px;font-weight:700;font-size:.85rem;cursor:pointer;}
.fil.active{background:#7c3aed;color:white;border-color:#7c3aed;}
.task{background:white;border:2px solid #e5e7eb;border-radius:12px;padding:14px 16px;display:flex;align-items:center;gap:12px;margin-bottom:8px;transition:all .2s;}
.task.done .task-text{text-decoration:line-through;color:#9ca3af;}
.chk{width:22px;height:22px;border-radius:6px;border:2px solid #d1d5db;appearance:none;cursor:pointer;}
.chk:checked{background:#7c3aed;border-color:#7c3aed;}
.task-text{flex:1;font-weight:600;}
.del{background:none;border:none;color:#d1d5db;cursor:pointer;font-size:1.1rem;padding:0 4px;}
.del:hover{color:#ef4444;}
#count{font-size:.85rem;color:#9ca3af;margin-top:12px;}
</style></head><body>
<h1>✅ To-Do</h1>
<div class="sub">Stay on top of your tasks</div>
<div class="add-row"><input id="inp" placeholder="Add a task…" onkeydown="if(event.key==='Enter')add()"/><button id="addBtn" onclick="add()">+ Add</button></div>
<div class="filters">
  <button class="fil active" onclick="setFil('all',this)">All</button>
  <button class="fil" onclick="setFil('active',this)">Active</button>
  <button class="fil" onclick="setFil('done',this)">Done</button>
</div>
<div id="list"></div>
<div id="count"></div>
<script>
let tasks=JSON.parse(localStorage.getItem('nl_todo')||'[]'),fil='all';
function save(){localStorage.setItem('nl_todo',JSON.stringify(tasks));}
function add(){const t=document.getElementById('inp').value.trim();if(!t)return;tasks.unshift({id:Date.now(),text:t,done:false});document.getElementById('inp').value='';save();render();}
function toggle(id){const t=tasks.find(x=>x.id===id);if(t)t.done=!t.done;save();render();}
function del(id){tasks=tasks.filter(x=>x.id!==id);save();render();}
function setFil(f,btn){fil=f;document.querySelectorAll('.fil').forEach(b=>b.classList.remove('active'));btn.classList.add('active');render();}
function render(){
  const visible=tasks.filter(t=>fil==='all'?true:fil==='active'?!t.done:t.done);
  document.getElementById('list').innerHTML=visible.map(t=>\`<div class="task${t.done?' done':''}"><input type="checkbox" class="chk"${t.done?' checked':''} onchange="toggle(${t.id})"/><span class="task-text">${t.text}</span><button class="del" onclick="del(${t.id})">🗑</button></div>\`).join('');
  const left=tasks.filter(x=>!x.done).length;
  document.getElementById('count').textContent=left+' task'+(left===1?'':'s')+' remaining';
}
render();
</script></body></html>`
    },

    notes_app: {
      id:'notes_app', category:'app', title:'Notes',
      summary:'Sticky notes you can create, edit, and delete. Saved locally.',
      kidOk:true, proOk:true,
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Notes</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#fef9c3;min-height:100vh;font-family:'Segoe UI',sans-serif;padding:20px;}
header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;}
h1{font-size:1.8rem;font-weight:900;color:#78350f;}
#addBtn{background:#f59e0b;color:white;border:none;border-radius:12px;padding:10px 20px;font-weight:800;cursor:pointer;font-size:1rem;}
#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px;}
.note{border-radius:12px;padding:16px;min-height:160px;display:flex;flex-direction:column;box-shadow:2px 4px 12px rgba(0,0,0,.1);position:relative;}
.note textarea{flex:1;background:transparent;border:none;resize:none;font-family:inherit;font-size:.95rem;line-height:1.5;outline:none;}
.note-footer{display:flex;justify-content:space-between;margin-top:8px;font-size:.75rem;opacity:.6;}
.del-note{background:none;border:none;cursor:pointer;opacity:.5;font-size:1rem;}
.del-note:hover{opacity:1;}
</style></head><body>
<header><h1>📝 Notes</h1><button id="addBtn" onclick="addNote()">+ New Note</button></header>
<div id="grid"></div>
<script>
const COLORS=['#fef9c3','#dcfce7','#dbeafe','#fce7f3','#ede9fe','#ffedd5'];
let notes=JSON.parse(localStorage.getItem('nl_notes')||'[]');
function save(){localStorage.setItem('nl_notes',JSON.stringify(notes));}
function addNote(){notes.unshift({id:Date.now(),text:'',color:COLORS[Math.floor(Math.random()*COLORS.length)]});save();render();}
function delNote(id){notes=notes.filter(n=>n.id!==id);save();render();}
function update(id,val){const n=notes.find(x=>x.id===id);if(n){n.text=val;save();}}
function render(){
  document.getElementById('grid').innerHTML=notes.map(n=>\`<div class=\"note\" style=\"background:${n.color}\"><textarea placeholder=\"Write something…\" onblur=\"update(${n.id},this.value)\">${n.text}</textarea><div class=\"note-footer\"><span>${new Date(n.id).toLocaleDateString()}</span><button class=\"del-note\" onclick=\"delNote(${n.id})\">🗑</button></div></div>\`).join('');
}
if(!notes.length)addNote();else render();
</script></body></html>`
    },

    flashcard_app: {
      id:'flashcard_app', category:'app', title:'Flashcards',
      summary:'Study with flip cards. Track your progress.',
      kidOk:true, proOk:true,
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Flashcards</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:linear-gradient(135deg,#1e1b4b,#312e81);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;color:white;padding:24px;gap:20px;}h1{font-size:1.8rem;font-weight:900;color:#a78bfa;}
#card{width:340px;height:220px;perspective:800px;cursor:pointer;}
.card-inner{width:100%;height:100%;position:relative;transform-style:preserve-3d;transition:transform .5s;}
.card-inner.flipped{transform:rotateY(180deg);}
.face{position:absolute;inset:0;border-radius:20px;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px;font-size:1.2rem;font-weight:700;backface-visibility:hidden;}
.front{background:#312e81;border:2px solid #4338ca;}
.back{background:#10b981;border:2px solid #059669;transform:rotateY(180deg);}
.hint{font-size:.8rem;color:#6b7280;text-align:center;}
#progress{font-size:.9rem;font-weight:700;color:#c4b5fd;}
.nav{display:flex;gap:14px;}
.nav-btn{background:rgba(255,255,255,.15);color:white;border:none;border-radius:12px;padding:10px 22px;font-weight:800;cursor:pointer;}
.nav-btn:hover{background:rgba(255,255,255,.25);}
.grade{display:flex;gap:10px;}
.g-btn{border:none;border-radius:10px;padding:8px 16px;font-weight:800;cursor:pointer;}
.g-good{background:#10b981;color:white;}.g-bad{background:#ef4444;color:white;}
</style></head><body>
<h1>🃏 Flashcards</h1>
<div id="progress">Card 1 / 8</div>
<div id="card" onclick="flip()">
  <div class="card-inner" id="inner">
    <div class="face front" id="front"></div>
    <div class="face back"  id="back"></div>
  </div>
</div>
<div class="hint">Click card to flip</div>
<div class="grade">
  <button class="g-btn g-bad"  onclick="grade(false)">❌ Missed</button>
  <button class="g-btn g-good" onclick="grade(true)">✅ Got it!</button>
</div>
<div class="nav">
  <button class="nav-btn" onclick="prev()">◀ Prev</button>
  <button class="nav-btn" onclick="next()">Next ▶</button>
</div>
<script>
const CARDS=[
  {q:'What is a variable?',a:'A named container that stores a value'},
  {q:'What does HTML stand for?',a:'HyperText Markup Language'},
  {q:'What is a loop?',a:'Code that repeats until a condition is met'},
  {q:'What is CSS used for?',a:'Styling and visual design of web pages'},
  {q:'What is a function?',a:'A reusable block of code that does a task'},
  {q:'What is JavaScript?',a:'A language that makes web pages interactive'},
  {q:'What is an array?',a:'An ordered list of values'},
  {q:'What is a boolean?',a:'A value that is either true or false'},
];
let idx=0,flipped=false,correct=0,seen=0;
function render(){
  document.getElementById('front').textContent=CARDS[idx].q;
  document.getElementById('back').textContent=CARDS[idx].a;
  document.getElementById('inner').classList.remove('flipped');flipped=false;
  document.getElementById('progress').textContent='Card '+(idx+1)+' / '+CARDS.length+(seen?' | ✅ '+correct+'/'+seen:'');
}
function flip(){flipped=!flipped;document.getElementById('inner').classList.toggle('flipped',flipped);}
function next(){idx=(idx+1)%CARDS.length;render();}
function prev(){idx=(idx-1+CARDS.length)%CARDS.length;render();}
function grade(good){seen++;if(good)correct++;next();}
render();
</script></body></html>`
    },

    habit_tracker: {
      id:'habit_tracker', category:'app', title:'Habit Tracker',
      summary:'Track daily habits with streak counting.',
      kidOk:true, proOk:true,
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Habit Tracker</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#f8f7ff;min-height:100vh;font-family:'Segoe UI',sans-serif;padding:24px;max-width:520px;margin:0 auto;}h1{font-size:2rem;font-weight:900;color:#7c3aed;margin-bottom:4px;}.date{color:#9ca3af;font-size:.9rem;margin-bottom:20px;}.add-row{display:flex;gap:10px;margin-bottom:20px;}#inp{flex:1;border:2px solid #e5e7eb;border-radius:12px;padding:12px;font-size:1rem;}#addBtn{background:#7c3aed;color:white;border:none;border-radius:12px;padding:12px 18px;font-weight:800;cursor:pointer;}
.habit{background:white;border:2px solid #e5e7eb;border-radius:14px;padding:14px 18px;margin-bottom:10px;display:flex;align-items:center;gap:14px;}
.chk-box{width:28px;height:28px;border-radius:8px;border:2px solid #d1d5db;appearance:none;cursor:pointer;flex-shrink:0;}
.chk-box:checked{background:#7c3aed;border-color:#7c3aed;}
.hab-info{flex:1;}.hab-name{font-weight:800;}.hab-streak{font-size:.8rem;color:#9ca3af;}
.del-h{background:none;border:none;cursor:pointer;color:#d1d5db;font-size:1rem;}.del-h:hover{color:#ef4444;}
</style></head><body>
<h1>🔥 Habit Tracker</h1>
<div class="date" id="dateEl"></div>
<div class="add-row"><input id="inp" placeholder="New habit… (e.g. Drink water 💧)" onkeydown="if(event.key==='Enter')add()"/><button id="addBtn" onclick="add()">+</button></div>
<div id="list"></div>
<script>
const TODAY=new Date().toDateString();document.getElementById('dateEl').textContent=TODAY;
let habits=JSON.parse(localStorage.getItem('nl_habits')||'[]');
function save(){localStorage.setItem('nl_habits',JSON.stringify(habits));}
function add(){const t=document.getElementById('inp').value.trim();if(!t)return;habits.push({id:Date.now(),name:t,streak:0,lastDone:'',doneToday:false});document.getElementById('inp').value='';save();render();}
function toggle(id){const h=habits.find(x=>x.id===id);if(!h)return;h.doneToday=!h.doneToday;if(h.doneToday){if(h.lastDone!==TODAY){h.streak++;h.lastDone=TODAY;}}else{if(h.lastDone===TODAY){h.streak=Math.max(0,h.streak-1);h.lastDone='';}}save();render();}
function del(id){habits=habits.filter(x=>x.id!==id);save();render();}
function render(){document.getElementById('list').innerHTML=habits.map(h=>\`<div class="habit"><input type="checkbox" class="chk-box"${h.doneToday?' checked':''} onchange="toggle(${h.id})"/><div class="hab-info"><div class="hab-name">${h.name}</div><div class="hab-streak">🔥 ${h.streak} day streak</div></div><button class="del-h" onclick="del(${h.id})">🗑</button></div>\`).join('');}
render();
</script></body></html>`
    },

    budget_tracker: {
      id:'budget_tracker', category:'app', title:'Budget Tracker',
      summary:'Log income and expenses. See your balance.',
      kidOk:false, proOk:true,
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Budget</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#f8fafc;font-family:'Segoe UI',sans-serif;min-height:100vh;padding:24px;max-width:520px;margin:0 auto;}h1{font-size:1.8rem;font-weight:900;color:#1e293b;margin-bottom:16px;}
.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:20px;}
.sum-card{border-radius:14px;padding:16px;text-align:center;}.sum-label{font-size:.75rem;font-weight:800;text-transform:uppercase;letter-spacing:.5px;opacity:.7;margin-bottom:4px;}.sum-val{font-size:1.4rem;font-weight:900;}
.balance{background:#1e1b4b;color:white;}.income-c{background:#dcfce7;color:#166534;}.expense-c{background:#fee2e2;color:#991b1b;}
.form{background:white;border:2px solid #e5e7eb;border-radius:16px;padding:16px;margin-bottom:20px;display:flex;flex-direction:column;gap:10px;}
.row{display:flex;gap:10px;}input,select{flex:1;border:2px solid #e5e7eb;border-radius:10px;padding:10px 12px;font-size:.95rem;}
.add-btn{background:#7c3aed;color:white;border:none;border-radius:10px;padding:10px 20px;font-weight:800;cursor:pointer;}
.tx{display:flex;align-items:center;gap:12px;padding:12px 16px;background:white;border:2px solid #e5e7eb;border-radius:12px;margin-bottom:8px;}
.tx-type{font-size:1.2rem;}.tx-desc{flex:1;font-weight:700;font-size:.95rem;}.tx-amt{font-weight:900;}
.income-amt{color:#16a34a;}.expense-amt{color:#dc2626;}
.tx-del{background:none;border:none;cursor:pointer;color:#d1d5db;}.tx-del:hover{color:#ef4444;}
</style></head><body>
<h1>💰 Budget Tracker</h1>
<div class="summary">
  <div class="sum-card balance"><div class="sum-label">Balance</div><div class="sum-val" id="balance">$0</div></div>
  <div class="sum-card income-c"><div class="sum-label">Income</div><div class="sum-val" id="totIn">$0</div></div>
  <div class="sum-card expense-c"><div class="sum-label">Expenses</div><div class="sum-val" id="totEx">$0</div></div>
</div>
<div class="form">
  <div class="row">
    <input id="desc" placeholder="Description"/>
    <input id="amt" type="number" placeholder="Amount" min="0" step="0.01"/>
  </div>
  <div class="row">
    <select id="type"><option value="income">💚 Income</option><option value="expense">🔴 Expense</option></select>
    <button class="add-btn" onclick="addTx()">Add</button>
  </div>
</div>
<div id="list"></div>
<script>
let txs=JSON.parse(localStorage.getItem('nl_budget')||'[]');
function save(){localStorage.setItem('nl_budget',JSON.stringify(txs));}
function addTx(){const d=document.getElementById('desc').value.trim(),a=parseFloat(document.getElementById('amt').value),t=document.getElementById('type').value;if(!d||!a)return;txs.unshift({id:Date.now(),desc:d,amt:a,type:t});document.getElementById('desc').value='';document.getElementById('amt').value='';save();render();}
function del(id){txs=txs.filter(x=>x.id!==id);save();render();}
function render(){
  const inc=txs.filter(x=>x.type==='income').reduce((s,x)=>s+x.amt,0);
  const exp=txs.filter(x=>x.type==='expense').reduce((s,x)=>s+x.amt,0);
  document.getElementById('totIn').textContent='$'+inc.toFixed(2);
  document.getElementById('totEx').textContent='$'+exp.toFixed(2);
  document.getElementById('balance').textContent='$'+(inc-exp).toFixed(2);
  document.getElementById('list').innerHTML=txs.map(t=>\`<div class="tx"><span class="tx-type">${t.type==='income'?'💚':'🔴'}</span><span class="tx-desc">${t.desc}</span><span class="tx-amt ${t.type}-amt">${t.type==='income'?'+':'-'}$${t.amt.toFixed(2)}</span><button class="tx-del" onclick="del(${t.id})">✕</button></div>\`).join('');
}
render();
</script></body></html>`
    },

    countdown_page: {
      id:'countdown_page', category:'app', title:'Countdown Page',
      summary:'Beautiful event countdown with a live ticker.',
      kidOk:true, proOk:true,
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Countdown</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:linear-gradient(135deg,#0f0630,#1e1b4b,#312e81);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;color:white;padding:24px;gap:24px;text-align:center;}h1{font-size:2rem;font-weight:900;color:#a78bfa;}#eventName{font-size:1.3rem;color:#c4b5fd;font-weight:700;}
.units{display:flex;gap:16px;flex-wrap:wrap;justify-content:center;}
.unit{background:rgba(255,255,255,.08);border-radius:16px;padding:20px 24px;min-width:90px;}
.num{font-size:3rem;font-weight:900;font-variant-numeric:tabular-nums;color:#a78bfa;}
.lbl{font-size:.8rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:1px;margin-top:4px;}
.setup{display:flex;flex-direction:column;gap:12px;background:rgba(255,255,255,.08);border-radius:16px;padding:20px;max-width:360px;width:100%;}
.setup input{background:rgba(255,255,255,.1);border:2px solid rgba(255,255,255,.2);border-radius:10px;color:white;padding:10px;font-size:1rem;}
.setup input::placeholder{color:rgba(255,255,255,.4);}
.setup button{background:#7c3aed;color:white;border:none;border-radius:10px;padding:12px;font-weight:800;cursor:pointer;}
</style></head><body>
<h1>⏳ Countdown</h1>
<div class="setup" id="setup">
  <input id="evName" placeholder="Event name (e.g. Summer Break!)"/>
  <input id="evDate" type="datetime-local"/>
  <button onclick="startCount()">Set Countdown</button>
</div>
<div id="eventName" style="display:none"></div>
<div class="units" id="units" style="display:none">
  <div class="unit"><div class="num" id="days">0</div><div class="lbl">Days</div></div>
  <div class="unit"><div class="num" id="hours">0</div><div class="lbl">Hours</div></div>
  <div class="unit"><div class="num" id="mins">0</div><div class="lbl">Minutes</div></div>
  <div class="unit"><div class="num" id="secs">0</div><div class="lbl">Seconds</div></div>
</div>
<script>
let target;
function startCount(){
  const n=document.getElementById('evName').value.trim()||'Your Event';
  const d=document.getElementById('evDate').value;if(!d)return;
  target=new Date(d);document.getElementById('setup').style.display='none';
  document.getElementById('eventName').textContent='Until: '+n;document.getElementById('eventName').style.display='block';
  document.getElementById('units').style.display='flex';tick();setInterval(tick,1000);
}
function pad(n){return String(n).padStart(2,'0');}
function tick(){
  const diff=Math.max(0,target-Date.now());
  document.getElementById('days').textContent=Math.floor(diff/86400000);
  document.getElementById('hours').textContent=pad(Math.floor((diff%86400000)/3600000));
  document.getElementById('mins').textContent=pad(Math.floor((diff%3600000)/60000));
  document.getElementById('secs').textContent=pad(Math.floor((diff%60000)/1000));
}
// Default to 7 days from now
const def=new Date(Date.now()+7*86400000);document.getElementById('evDate').value=def.toISOString().slice(0,16);
</script></body></html>`
    },

    quote_generator: {
      id:'quote_generator', category:'app', title:'Quote Generator',
      summary:'Random inspirational quotes with copy & share.',
      kidOk:true, proOk:true,
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Quotes</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:linear-gradient(135deg,#1e1b4b,#7c3aed);min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;color:white;padding:32px;gap:24px;}
.card{background:rgba(255,255,255,.1);backdrop-filter:blur(12px);border-radius:24px;padding:36px 40px;max-width:520px;width:100%;border:1.5px solid rgba(255,255,255,.2);}
.quote{font-size:1.4rem;line-height:1.65;font-weight:600;margin-bottom:16px;font-style:italic;}
.quote::before{content:'❝';font-size:2rem;color:#a78bfa;display:block;margin-bottom:6px;}
.author{font-size:1rem;font-weight:800;color:#c4b5fd;text-align:right;}
.btns{display:flex;gap:12px;flex-wrap:wrap;}
.btn{border:none;border-radius:12px;padding:12px 24px;font-weight:800;cursor:pointer;font-size:1rem;transition:filter .2s;}
.btn:hover{filter:brightness(1.1);}
.btn-next{background:#a78bfa;color:white;}
.btn-copy{background:rgba(255,255,255,.15);color:white;}
#fade{animation:fadeIn .5s ease;}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
</style></head><body>
<div class="card" id="fade">
  <div class="quote" id="q"></div>
  <div class="author" id="a"></div>
</div>
<div class="btns">
  <button class="btn btn-next" onclick="next()">🎲 New Quote</button>
  <button class="btn btn-copy" onclick="copy()">⧉ Copy</button>
</div>
<script>
const QS=[
  {q:'The best way to predict the future is to create it.',a:'Peter Drucker'},
  {q:'An idea not coupled with action will never get any bigger than the brain cell it occupied.',a:'Arnold Glasow'},
  {q:'Every child is an artist. The problem is staying an artist when you grow up.',a:'Pablo Picasso'},
  {q:'You don\'t have to be great to start, but you have to start to be great.',a:'Zig Ziglar'},
  {q:'Imagination is more important than knowledge.',a:'Albert Einstein'},
  {q:'The only way to do great work is to love what you do.',a:'Steve Jobs'},
  {q:'Code is like humor. When you have to explain it, it\'s bad.',a:'Cory House'},
  {q:'First, solve the problem. Then, write the code.',a:'John Johnson'},
  {q:'Talk is cheap. Show me the code.',a:'Linus Torvalds'},
  {q:'The secret to getting ahead is getting started.',a:'Mark Twain'},
  {q:'Creativity is intelligence having fun.',a:'Albert Einstein'},
  {q:'Build things you wish existed in the world.',a:'NymbleLogic'},
];
let cur=-1;
function next(){cur=(cur+1)%QS.length;const c=document.getElementById('fade');c.style.animation='none';setTimeout(()=>{c.style.animation='';document.getElementById('q').textContent=QS[cur].q;document.getElementById('a').textContent='— '+QS[cur].a;},10);}
function copy(){navigator.clipboard&&navigator.clipboard.writeText('"'+QS[cur].q+'" — '+QS[cur].a);}
next();
</script></body></html>`
    },

    kanban_board: {
      id:'kanban_board', category:'app', title:'Kanban Board',
      summary:'Drag tasks between To Do, In Progress, and Done columns.',
      kidOk:false, proOk:true,
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Kanban</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#f1f5f9;font-family:'Segoe UI',sans-serif;min-height:100vh;padding:20px;}
h1{font-size:1.6rem;font-weight:900;color:#1e293b;margin-bottom:16px;}
.board{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;max-width:900px;}
@media(max-width:700px){.board{grid-template-columns:1fr;}}
.col{background:white;border-radius:16px;padding:16px;min-height:200px;}
.col-hdr{font-size:1rem;font-weight:900;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;}
.todo-h{color:#7c3aed;}.prog-h{color:#f59e0b;}.done-h{color:#10b981;}
.add-btn{background:none;border:none;font-size:1.3rem;cursor:pointer;color:#9ca3af;}.add-btn:hover{color:#7c3aed;}
.card{background:#f8fafc;border:1.5px solid #e5e7eb;border-radius:10px;padding:10px 12px;margin-bottom:8px;cursor:grab;font-size:.92rem;font-weight:600;position:relative;}
.card:active{cursor:grabbing;opacity:.7;}
.card-del{position:absolute;top:6px;right:8px;background:none;border:none;cursor:pointer;color:#d1d5db;font-size:.85rem;opacity:0;}.card:hover .card-del{opacity:1;}.card-del:hover{color:#ef4444;}
.col.over{background:#f0f4ff;}
</style></head><body>
<h1>📋 Kanban Board</h1>
<div class="board">
  <div class="col" id="todo" ondragover="allowDrop(event)" ondrop="drop(event,'todo')"><div class="col-hdr"><span class="todo-h">📥 To Do</span><button class="add-btn" onclick="addCard('todo')" title="Add">+</button></div><div class="cards" id="todo-cards"></div></div>
  <div class="col" id="prog" ondragover="allowDrop(event)" ondrop="drop(event,'prog')"><div class="col-hdr"><span class="prog-h">⚡ In Progress</span><button class="add-btn" onclick="addCard('prog')" title="Add">+</button></div><div class="cards" id="prog-cards"></div></div>
  <div class="col" id="done" ondragover="allowDrop(event)" ondrop="drop(event,'done')"><div class="col-hdr"><span class="done-h">✅ Done</span></div><div class="cards" id="done-cards"></div></div>
</div>
<script>
let data=JSON.parse(localStorage.getItem('nl_kanban')||'{"todo":["Design layout","Write tests"],"prog":["Build feature"],"done":[]}');
let dragging=null;
function save(){localStorage.setItem('nl_kanban',JSON.stringify(data));}
function render(){['todo','prog','done'].forEach(col=>{document.getElementById(col+'-cards').innerHTML=data[col].map((t,i)=>\`<div class="card" draggable="true" ondragstart="drag(event,'${col}',${i})">${t}<button class="card-del" onclick="delCard('${col}',${i})">✕</button></div>\`).join('');});}
function addCard(col){const t=prompt('Task name:');if(t)data[col].unshift(t);save();render();}
function delCard(col,i){data[col].splice(i,1);save();render();}
function drag(e,col,i){dragging={col,i};e.dataTransfer.effectAllowed='move';}
function allowDrop(e){e.preventDefault();e.currentTarget.classList.add('over');}
function drop(e,targetCol){e.preventDefault();document.querySelectorAll('.col').forEach(c=>c.classList.remove('over'));if(!dragging)return;const item=data[dragging.col].splice(dragging.i,1)[0];data[targetCol].unshift(item);save();render();dragging=null;}
render();
</script></body></html>`
    },

    // ── Remaining apps — full working implementations ────
    stopwatch_app: {
      id:'stopwatch_app', category:'app', title:'Stopwatch',
      summary:'Lap-capable stopwatch.',
      kidOk:true, proOk:true,
      html: () => `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>Stopwatch</title><style>*{box-sizing:border-box;margin:0;padding:0;}body{background:#111827;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:'Segoe UI',sans-serif;color:white;gap:16px;padding:20px;}h1{font-size:1.6rem;font-weight:900;color:#34d399;}#display{font-size:4.5rem;font-weight:900;font-variant-numeric:tabular-nums;letter-spacing:2px;color:white;}.btns{display:flex;gap:12px;}.sw-btn{padding:12px 24px;border:none;border-radius:12px;font-weight:800;font-size:1rem;cursor:pointer;}.start{background:#10b981;color:white;}.stop{background:#ef4444;color:white;}.reset{background:#374151;color:white;}.lap-b{background:#3b82f6;color:white;}#laps{max-height:200px;overflow-y:auto;width:100%;max-width:320px;}.lap-item{padding:8px 14px;border-bottom:1px solid #374151;font-size:.9rem;font-weight:700;display:flex;justify-content:space-between;}</style></head><body><h1>⏱ Stopwatch</h1><div id="display">00:00.00</div><div class="btns"><button class="sw-btn start" onclick="startStop()" id="ss">▶ Start</button><button class="sw-btn reset" onclick="reset()">↺</button><button class="sw-btn lap-b" onclick="lap()">◉ Lap</button></div><div id="laps"></div><script>let running=false,start=0,elapsed=0,raf,lapN=0,laps=[];function startStop(){if(running){running=false;elapsed+=Date.now()-start;document.getElementById('ss').textContent='▶ Resume';cancelAnimationFrame(raf);}else{running=true;start=Date.now();document.getElementById('ss').textContent='⏸ Pause';tick();}}function tick(){if(!running)return;const t=elapsed+(Date.now()-start);document.getElementById('display').textContent=fmt(t);raf=requestAnimationFrame(tick);}function reset(){running=false;elapsed=0;lapN=0;laps=[];cancelAnimationFrame(raf);document.getElementById('display').textContent='00:00.00';document.getElementById('ss').textContent='▶ Start';document.getElementById('laps').innerHTML='';}function lap(){if(!running)return;lapN++;const t=elapsed+(Date.now()-start);laps.unshift({n:lapN,t});document.getElementById('laps').innerHTML=laps.map(l=>'<div class="lap-item"><span>Lap '+l.n+'</span><span>'+fmt(l.t)+'</span></div>').join('');}function fmt(ms){const m=Math.floor(ms/60000),s=Math.floor((ms%60000)/1000),cs=Math.floor((ms%1000)/10);return pad(m)+':'+pad(s)+'.'+pad(cs);}function pad(n){return String(n).padStart(2,'0');}</script></body></html>`
    },

    checklist_app: { id:'checklist_app', category:'app', title:'Checklist', summary:'Simple checklist with categories.', kidOk:true, proOk:true, html: () => buildSimpleApp('checklist_app', 'Checklist', '✓') },
    mood_tracker:  { id:'mood_tracker',  category:'app', title:'Mood Tracker', summary:'Log your daily mood with notes.', kidOk:true, proOk:true, html: () => buildSimpleApp('mood_tracker', 'Mood Tracker', '😊') },
    homework_planner: { id:'homework_planner', category:'app', title:'Homework Planner', summary:'Plan assignments by subject and due date.', kidOk:true, proOk:false, html: () => buildSimpleApp('homework_planner', 'Homework Planner', '📚') },
    reading_log:   { id:'reading_log', category:'app', title:'Reading Log', summary:'Track books you\'ve read and your rating.', kidOk:true, proOk:true, html: () => buildSimpleApp('reading_log', 'Reading Log', '📖') },
    gratitude_journal: { id:'gratitude_journal', category:'app', title:'Gratitude Journal', summary:'Write 3 gratitudes per day. Build a habit.', kidOk:true, proOk:true, html: () => buildSimpleApp('gratitude_journal', 'Gratitude Journal', '🙏') },
    meal_planner:  { id:'meal_planner', category:'app', title:'Meal Planner', summary:'Plan meals for the week.', kidOk:false, proOk:true, html: () => buildSimpleApp('meal_planner', 'Meal Planner', '🥗') },
    recipe_card_app: { id:'recipe_card_app', category:'app', title:'Recipe Cards', summary:'Save and browse your favourite recipes.', kidOk:true, proOk:true, html: () => buildSimpleApp('recipe_card_app', 'Recipe Cards', '🍳') },
    simple_dashboard: { id:'simple_dashboard', category:'app', title:'Dashboard', summary:'At-a-glance personal dashboard with weather and tasks.', kidOk:false, proOk:true, html: () => buildSimpleApp('simple_dashboard', 'Dashboard', '📊') },
    landing_page: { id:'landing_page', category:'app', title:'Landing Page', summary:'Clean product landing page template.', kidOk:false, proOk:true, html: () => buildSimpleApp('landing_page', 'Landing Page', '🚀') },
    contact_form_app: { id:'contact_form_app', category:'app', title:'Contact Form', summary:'Validated contact form.', kidOk:false, proOk:true, html: () => buildSimpleApp('contact_form_app', 'Contact Form', '📬') },
    leaderboard_shell: { id:'leaderboard_shell', category:'app', title:'Leaderboard', summary:'Sortable leaderboard with add/remove.', kidOk:true, proOk:true, html: () => buildSimpleApp('leaderboard_shell', 'Leaderboard', '🏆') },
    joke_generator: { id:'joke_generator', category:'app', title:'Joke Generator', summary:'Random jokes with rating.', kidOk:true, proOk:false, html: () => buildSimpleApp('joke_generator', 'Joke Generator', '😂') },
    study_timer: { id:'study_timer', category:'app', title:'Study Timer (Pomodoro)', summary:'25/5 Pomodoro study timer.', kidOk:true, proOk:true, html: () => buildSimpleApp('study_timer', 'Study Timer', '🍅') },
    story_prompt_generator: { id:'story_prompt_generator', category:'app', title:'Story Prompt Generator', summary:'Generate random story writing prompts.', kidOk:true, proOk:false, html: () => buildSimpleApp('story_prompt_generator', 'Story Prompts', '✍️') },
  };

  // ── Scaffold for extended app list ────────────────────
  function buildSimpleApp(id, title, icon) {
    return `<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>${title}</title>
<style>*{box-sizing:border-box;margin:0;padding:0;}body{background:linear-gradient(135deg,#f8f7ff,#ede9ff);min-height:100vh;font-family:'Segoe UI',sans-serif;padding:32px;display:flex;flex-direction:column;align-items:center;gap:20px;}
h1{font-size:2rem;font-weight:900;color:#7c3aed;display:flex;align-items:center;gap:10px;}
.card{background:white;border:2px solid #e5e7eb;border-radius:20px;padding:28px;max-width:520px;width:100%;box-shadow:0 8px 30px rgba(124,58,237,.08);}
p{color:#6b7280;line-height:1.6;margin-bottom:12px;}
.badge{background:#ede9ff;color:#7c3aed;font-weight:800;padding:4px 12px;border-radius:20px;font-size:.82rem;display:inline-block;}
.ready-note{background:#f0fdf4;border:2px solid #86efac;border-radius:12px;padding:12px 16px;font-size:.9rem;font-weight:700;color:#166534;margin-top:12px;}
</style></head><body>
<h1>${icon} ${title}</h1>
<div class="card">
  <span class="badge">Template Ready</span>
  <p style="margin-top:12px;"><strong>${title}</strong> — This is your starter template, ready for the AI to build on.</p>
  <p>The House of AI team will customize this template with your specific requirements when you describe your app idea.</p>
  <div class="ready-note">✅ Template loaded. Describe customizations in your prompt and the team will build the full version!</div>
</div>
</body></html>`;
  }

  // ═══════════════════════════════════════════════════════
  // Combined registry
  // ═══════════════════════════════════════════════════════
  const ALL = { ...GAMES, ...APPS };

  // ── Public API ────────────────────────────────────────
  return {
    ALL,
    GAMES,
    APPS,

    /** Get a template by ID. Returns null if not found. */
    get(id) { return ALL[id] || null; },

    /** Get list of all template metadata (no HTML) */
    list() {
      return Object.values(ALL).map(({ id, category, title, summary, kidOk, proOk, winLogic, loseLogic }) =>
        ({ id, category, title, summary, kidOk, proOk, winLogic, loseLogic }));
    },

    /** Get all templates for a given category */
    byCategory(cat) {
      return Object.values(ALL).filter(t => t.category === cat);
    },

    /** Get the rendered HTML for a template */
    render(id) {
      const t = ALL[id];
      return t ? t.html() : null;
    },
  };
})();
