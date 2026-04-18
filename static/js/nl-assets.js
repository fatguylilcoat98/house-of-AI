/**
 * NymbleLogic Asset Library v1.0
 * The Good Neighbor Guard — Christopher Hughes
 *
 * Reusable SVG + CSS asset packs for template injection.
 * Each pack returns { emoji, svg, css, colors, bg, name }
 */

window.NL_ASSETS = (() => {
  'use strict';

  // ── Core SVG primitives ───────────────────────────────
  const SVG = {
    star:    `<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"><polygon points="20,2 25,14 38,14 28,22 32,35 20,27 8,35 12,22 2,14 15,14" fill="#f59e0b" stroke="#d97706" stroke-width="1.5"/></svg>`,
    heart:   `<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"><path d="M20 35 C20 35 4 24 4 13 C4 7 9 3 14 3 C17 3 20 6 20 6 C20 6 23 3 26 3 C31 3 36 7 36 13 C36 24 20 35 20 35Z" fill="#f43f5e" stroke="#e11d48" stroke-width="1"/></svg>`,
    coin:    `<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"><circle cx="20" cy="20" r="17" fill="#f59e0b" stroke="#d97706" stroke-width="2"/><circle cx="20" cy="20" r="13" fill="#fbbf24"/><text x="20" y="25" text-anchor="middle" font-size="14" font-weight="bold" fill="#92400e">$</text></svg>`,
    gem:     `<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"><polygon points="20,4 36,16 30,36 10,36 4,16" fill="#8b5cf6" stroke="#6d28d9" stroke-width="1.5"/><polygon points="20,4 36,16 20,12" fill="#a78bfa" opacity="0.6"/></svg>`,
    balloon: `<svg viewBox="0 0 40 50" xmlns="http://www.w3.org/2000/svg"><ellipse cx="20" cy="18" rx="15" ry="18" fill="#f43f5e"/><ellipse cx="15" cy="12" rx="4" ry="5" fill="rgba(255,255,255,0.3)"/><polygon points="20,36 18,40 22,40" fill="#f43f5e"/><line x1="20" y1="40" x2="20" y2="50" stroke="#6b7280" stroke-width="1.5"/></svg>`,
    rocket:  `<svg viewBox="0 0 40 60" xmlns="http://www.w3.org/2000/svg"><ellipse cx="20" cy="20" rx="10" ry="18" fill="#7c3aed"/><polygon points="20,2 10,20 30,20" fill="#6d28d9"/><rect x="12" y="35" width="16" height="10" fill="#7c3aed"/><polygon points="10,40 4,50 16,46" fill="#ef4444"/><polygon points="30,40 36,50 24,46" fill="#ef4444"/><circle cx="20" cy="20" r="4" fill="#a5f3fc"/><polygon points="16,45 20,55 24,45" fill="#f97316" opacity="0.9"/></svg>`,
    cat:     `<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"><circle cx="20" cy="22" r="14" fill="#f97316"/><polygon points="8,12 4,2 14,10" fill="#f97316"/><polygon points="32,12 36,2 26,10" fill="#f97316"/><circle cx="15" cy="20" r="3" fill="white"/><circle cx="25" cy="20" r="3" fill="white"/><circle cx="15.5" cy="20" r="1.5" fill="#1f2937"/><circle cx="25.5" cy="20" r="1.5" fill="#1f2937"/><ellipse cx="20" cy="27" rx="4" ry="2.5" fill="#fda4af"/><line x1="10" y1="26" x2="2" y2="24" stroke="#374151" stroke-width="1.5"/><line x1="10" y1="28" x2="2" y2="28" stroke="#374151" stroke-width="1.5"/><line x1="30" y1="26" x2="38" y2="24" stroke="#374151" stroke-width="1.5"/><line x1="30" y1="28" x2="38" y2="28" stroke="#374151" stroke-width="1.5"/></svg>`,
    dog:     `<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"><circle cx="20" cy="22" r="13" fill="#92400e"/><ellipse cx="11" cy="16" rx="5" ry="7" fill="#92400e"/><ellipse cx="29" cy="16" rx="5" ry="7" fill="#78350f"/><circle cx="16" cy="21" r="2.5" fill="white"/><circle cx="24" cy="21" r="2.5" fill="white"/><circle cx="16.5" cy="21" r="1.2" fill="#111"/><circle cx="24.5" cy="21" r="1.2" fill="#111"/><ellipse cx="20" cy="28" rx="5" ry="3" fill="#fde68a"/><ellipse cx="20" cy="27.5" rx="2.5" ry="1.5" fill="#f43f5e"/></svg>`,
    robot:   `<svg viewBox="0 0 40 50" xmlns="http://www.w3.org/2000/svg"><rect x="8" y="12" width="24" height="20" rx="4" fill="#6b7280"/><rect x="12" y="16" width="6" height="4" rx="1" fill="#34d399"/><rect x="22" y="16" width="6" height="4" rx="1" fill="#34d399"/><rect x="14" y="24" width="12" height="3" rx="1" fill="#9ca3af"/><rect x="10" y="2" width="20" height="10" rx="3" fill="#4b5563"/><line x1="20" y1="2" x2="20" y2="0" stroke="#6b7280" stroke-width="2"/><circle cx="20" cy="0" r="2" fill="#f59e0b"/><rect x="4" y="14" width="4" height="14" rx="2" fill="#6b7280"/><rect x="32" y="14" width="4" height="14" rx="2" fill="#6b7280"/><rect x="12" y="32" width="7" height="16" rx="3" fill="#4b5563"/><rect x="21" y="32" width="7" height="16" rx="3" fill="#4b5563"/></svg>`,
    dino:    `<svg viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg"><ellipse cx="30" cy="30" rx="15" ry="12" fill="#10b981"/><circle cx="38" cy="18" r="9" fill="#10b981"/><circle cx="42" cy="15" r="2.5" fill="white"/><circle cx="43" cy="15" r="1.2" fill="#111"/><polygon points="38,9 36,2 42,8" fill="#059669"/><polygon points="42,7 40,0 46,6" fill="#059669"/><polygon points="20,38 15,50 25,48" fill="#10b981"/><polygon points="34,40 30,50 38,48" fill="#10b981"/><polygon points="45,28 50,22 50,30" fill="#059669"/><polygon points="45,24 50,18 50,26" fill="#059669"/></svg>`,
    alien:   `<svg viewBox="0 0 40 50" xmlns="http://www.w3.org/2000/svg"><ellipse cx="20" cy="22" rx="16" ry="20" fill="#a78bfa"/><ellipse cx="13" cy="18" rx="5" ry="6" fill="white"/><ellipse cx="27" cy="18" rx="5" ry="6" fill="white"/><ellipse cx="13" cy="19" rx="3" ry="4" fill="#1d4ed8"/><ellipse cx="27" cy="19" rx="3" ry="4" fill="#1d4ed8"/><ellipse cx="20" cy="30" rx="5" ry="2" fill="#7c3aed" opacity="0.5"/><line x1="6" y1="10" x2="2" y2="4" stroke="#a78bfa" stroke-width="2"/><circle cx="2" cy="3" r="2" fill="#c4b5fd"/><line x1="34" y1="10" x2="38" y2="4" stroke="#a78bfa" stroke-width="2"/><circle cx="38" cy="3" r="2" fill="#c4b5fd"/></svg>`,
    pizza:   `<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"><polygon points="20,4 36,36 4,36" fill="#fbbf24"/><polygon points="20,4 36,36 4,36" fill="#fde68a" opacity="0.5"/><circle cx="16" cy="28" r="3" fill="#ef4444"/><circle cx="24" cy="24" r="3" fill="#ef4444"/><circle cx="20" cy="32" r="2" fill="#ef4444"/><circle cx="18" cy="20" r="2" fill="#16a34a"/><circle cx="26" cy="30" r="2" fill="#92400e"/><path d="M4,36 Q20,32 36,36" fill="#d97706"/></svg>`,
    cupcake: `<svg viewBox="0 0 40 50" xmlns="http://www.w3.org/2000/svg"><rect x="10" y="28" width="20" height="16" rx="4" fill="#fde68a"/><ellipse cx="20" cy="24" rx="16" ry="10" fill="#f43f5e"/><ellipse cx="20" cy="18" rx="12" ry="8" fill="#fda4af"/><circle cx="20" cy="14" r="4" fill="#f43f5e"/><circle cx="20" cy="10" r="2" fill="#7c3aed"/><circle cx="16" cy="16" r="2" fill="#fff" opacity="0.7"/><circle cx="24" cy="16" r="2" fill="#fff" opacity="0.7"/></svg>`,
    candy:   `<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"><circle cx="20" cy="18" r="14" fill="#f43f5e"/><circle cx="20" cy="18" r="14" fill="none" stroke="white" stroke-width="4" stroke-dasharray="8,6"/><rect x="18" y="30" width="4" height="14" rx="2" fill="#f97316"/><path d="M22,44 Q26,46 26,42" fill="none" stroke="#f97316" stroke-width="3" stroke-linecap="round"/></svg>`,
    chest:   `<svg viewBox="0 0 50 40" xmlns="http://www.w3.org/2000/svg"><rect x="4" y="18" width="42" height="22" rx="3" fill="#92400e"/><rect x="4" y="14" width="42" height="8" rx="3" fill="#78350f"/><rect x="20" y="14" width="10" height="26" fill="#d97706"/><circle cx="25" cy="27" r="3" fill="#f59e0b"/><path d="M4,22 L46,22" stroke="#78350f" stroke-width="2"/><rect x="2" y="14" width="4" height="26" rx="2" fill="#6b3a10"/><rect x="44" y="14" width="4" height="26" rx="2" fill="#6b3a10"/></svg>`,
    rabbit:  `<svg viewBox="0 0 40 50" xmlns="http://www.w3.org/2000/svg"><ellipse cx="20" cy="32" rx="13" ry="14" fill="#f3f4f6"/><ellipse cx="12" cy="14" rx="5" ry="12" fill="#f3f4f6"/><ellipse cx="28" cy="14" rx="5" ry="12" fill="#f3f4f6"/><ellipse cx="12" cy="12" rx="2.5" ry="8" fill="#fda4af"/><ellipse cx="28" cy="12" rx="2.5" ry="8" fill="#fda4af"/><circle cx="16" cy="28" r="3" fill="white"/><circle cx="24" cy="28" r="3" fill="white"/><circle cx="16.5" cy="28" r="1.5" fill="#374151"/><circle cx="24.5" cy="28" r="1.5" fill="#374151"/><ellipse cx="20" cy="34" rx="3" ry="2" fill="#fda4af"/><ellipse cx="20" cy="44" rx="6" ry="3" fill="#e5e7eb"/></svg>`,
    monster: `<svg viewBox="0 0 40 45" xmlns="http://www.w3.org/2000/svg"><ellipse cx="20" cy="26" rx="16" ry="18" fill="#7c3aed"/><polygon points="6,12 4,4 10,10" fill="#6d28d9"/><polygon points="14,8 12,0 18,8" fill="#6d28d9"/><polygon points="22,8 26,0 28,8" fill="#6d28d9"/><polygon points="30,12 36,4 32,12" fill="#6d28d9"/><circle cx="14" cy="22" r="5" fill="#fde68a"/><circle cx="26" cy="22" r="5" fill="#fde68a"/><circle cx="14" cy="22" r="2.5" fill="#111"/><circle cx="26" cy="22" r="2.5" fill="#111"/><path d="M10,34 L14,38 L18,34 L22,38 L26,34 L30,38 L34,34" fill="none" stroke="#fde68a" stroke-width="2" stroke-linecap="round"/></svg>`,
    spaceship:`<svg viewBox="0 0 60 50" xmlns="http://www.w3.org/2000/svg"><ellipse cx="30" cy="22" rx="24" ry="12" fill="#6b7280"/><ellipse cx="30" cy="20" rx="16" ry="10" fill="#3b82f6"/><ellipse cx="30" cy="18" rx="8" ry="6" fill="#a5f3fc"/><polygon points="10,28 4,40 16,36" fill="#4b5563"/><polygon points="50,28 56,40 44,36" fill="#4b5563"/><circle cx="22" cy="26" r="3" fill="#fbbf24"/><circle cx="38" cy="26" r="3" fill="#fbbf24"/><ellipse cx="30" cy="30" rx="6" ry="3" fill="#ef4444" opacity="0.7"/></svg>`,
    cloud:   `<svg viewBox="0 0 60 40" xmlns="http://www.w3.org/2000/svg"><ellipse cx="30" cy="28" rx="25" ry="12" fill="white"/><circle cx="18" cy="22" r="12" fill="white"/><circle cx="30" cy="16" r="14" fill="white"/><circle cx="42" cy="20" r="11" fill="white"/></svg>`,
    shield_s:`<svg viewBox="0 0 40 48" xmlns="http://www.w3.org/2000/svg"><path d="M20 4 L36 12 L36 26 C36 35 20 44 20 44 C20 44 4 35 4 26 L4 12 Z" fill="#3b82f6" stroke="#1d4ed8" stroke-width="2"/><path d="M14 24 L18 28 L26 18" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>`,
  };

  // ── Theme backgrounds ─────────────────────────────────
  const BG = {
    space:     `background: linear-gradient(180deg, #0a0015 0%, #0f0630 50%, #1a0a4a 100%);`,
    sky:       `background: linear-gradient(180deg, #38bdf8 0%, #7dd3fc 60%, #bfdbfe 100%);`,
    grass:     `background: linear-gradient(180deg, #38bdf8 0%, #7dd3fc 50%, #86efac 50%, #22c55e 100%);`,
    ocean:     `background: linear-gradient(180deg, #0ea5e9 0%, #0284c7 40%, #164e63 100%);`,
    forest:    `background: linear-gradient(180deg, #166534 0%, #15803d 40%, #14532d 100%);`,
    castle:    `background: linear-gradient(180deg, #7c3aed 0%, #5b21b6 40%, #1c1038 100%);`,
    classroom: `background: linear-gradient(180deg, #fef3c7 0%, #fde68a 100%);`,
    candy:     `background: linear-gradient(135deg, #fda4af 0%, #f9a8d4 50%, #c4b5fd 100%);`,
    dark:      `background: #111827;`,
    light:     `background: #f8fafc;`,
    purple:    `background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);`,
    teal:      `background: linear-gradient(135deg, #134e4a 0%, #0d9488 100%);`,
  };

  // ── Color palettes per theme ──────────────────────────
  const COLORS = {
    space:     { primary: '#a78bfa', accent: '#06b6d4', text: '#e2e8f0', ui: '#1e1b4b' },
    sky:       { primary: '#0ea5e9', accent: '#f59e0b', text: '#1e3a5f', ui: 'white' },
    grass:     { primary: '#16a34a', accent: '#f59e0b', text: '#14532d', ui: '#dcfce7' },
    ocean:     { primary: '#0ea5e9', accent: '#34d399', text: 'white', ui: '#0c4a6e' },
    forest:    { primary: '#22c55e', accent: '#f59e0b', text: '#f0fdf4', ui: '#166534' },
    castle:    { primary: '#a78bfa', accent: '#f59e0b', text: '#ede9fe', ui: '#2e1065' },
    classroom: { primary: '#3b82f6', accent: '#f59e0b', text: '#1e3a5f', ui: '#eff6ff' },
    candy:     { primary: '#f43f5e', accent: '#7c3aed', text: '#831843', ui: '#fdf2f8' },
    dark:      { primary: '#7c3aed', accent: '#10b981', text: '#f1f5f9', ui: '#1e293b' },
    light:     { primary: '#3b82f6', accent: '#f59e0b', text: '#1e293b', ui: 'white' },
  };

  // ── Public API ────────────────────────────────────────
  return {
    SVG,
    BG,
    COLORS,

    /** Get asset SVG by name, returns empty string if not found */
    get(name) { return SVG[name] || ''; },

    /** Get a full theme pack { bg, colors, name } */
    theme(name) {
      return { bg: BG[name] || BG.light, colors: COLORS[name] || COLORS.light, name };
    },

    /** Match a prompt string to the best asset names */
    matchAssets(prompt) {
      const p = prompt.toLowerCase();
      const assets = [];
      const map = [
        [['star','stars','collect','shiny'],   'star'],
        [['heart','love','valentine'],         'heart'],
        [['coin','money','gold','treasure'],   'coin'],
        [['gem','diamond','jewel','crystal'],  'gem'],
        [['balloon','pop','float'],            'balloon'],
        [['rocket','launch','blast'],          'rocket'],
        [['cat','kitten','kitty'],             'cat'],
        [['dog','puppy','pup'],                'dog'],
        [['robot','mech','machine'],           'robot'],
        [['dino','dinosaur','t-rex'],          'dino'],
        [['alien','ufo','space creature'],     'alien'],
        [['pizza','pepperoni'],                'pizza'],
        [['cupcake','cake','baking'],          'cupcake'],
        [['candy','sweet','sugar'],            'candy'],
        [['chest','treasure','loot'],          'chest'],
        [['rabbit','bunny','nym'],             'rabbit'],
        [['monster','creature','villain'],     'monster'],
        [['spaceship','ship','spacecraft'],    'spaceship'],
        [['cloud','sky','weather'],            'cloud'],
      ];
      map.forEach(([keywords, asset]) => {
        if (keywords.some(k => p.includes(k))) assets.push(asset);
      });
      return assets.length ? assets : ['star']; // default
    },

    /** Match a prompt to the best background theme */
    matchTheme(prompt) {
      const p = prompt.toLowerCase();
      if (['space','galaxy','planet','alien','rocket','star'].some(k => p.includes(k))) return 'space';
      if (['ocean','sea','underwater','fish','whale'].some(k => p.includes(k))) return 'ocean';
      if (['forest','jungle','tree','nature'].some(k => p.includes(k))) return 'forest';
      if (['castle','kingdom','knight','medieval'].some(k => p.includes(k))) return 'castle';
      if (['classroom','school','homework','study'].some(k => p.includes(k))) return 'classroom';
      if (['candy','sweet','sugar','cupcake'].some(k => p.includes(k))) return 'candy';
      if (['night','dark','shadow','ninja'].some(k => p.includes(k))) return 'dark';
      if (['sky','cloud','bird','fly','flight'].some(k => p.includes(k))) return 'sky';
      if (['grass','field','garden','outdoor'].some(k => p.includes(k))) return 'grass';
      return 'light'; // default for apps/tools
    },
  };
})();
