/**
 * NymbleLogic Prompt Router v2.0
 * The Good Neighbor Guard — Christopher Hughes
 *
 * Routes prompts to templates. Builds compact spec context (not HTML dumps).
 * Day-one core templates → nl-specs.js compact context (~30 lines).
 * Expansion templates    → light routing hint only.
 * No match               → pass user context as-is to agents.
 */

window.NL_ROUTER = (() => {
  'use strict';

  // ── Routing table ─────────────────────────────────────
  const ROUTES = [
    // GAMES
    [['connect four','connect 4','four in a row','drop pieces'],         'connect_four'],
    [['tic tac toe','tic-tac-toe','noughts and crosses','xs and os'],    'tic_tac_toe'],
    [['snake game','snake','grow the snake','collect food','eat apples'],'snake_game'],
    [['dodge','avoid falling','dodge enemies','escape falling'],         'dodge_game'],
    [['clicker','idle game','cookie clicker','tap to earn','tapper'],    'clicker_game'],
    [['memory match','flip cards','card matching','pair cards','match'], 'memory_match'],
    [['quiz','multiple choice','trivia quiz','test my knowledge'],       'quiz_game'],
    [['breakout','brick breaker','paddle ball','break bricks'],          'breakout_paddle'],
    [['reaction','reaction time','how fast','tap when green'],           'reaction_timer'],
    [['drawing','paint','doodle','draw','canvas art','sketch'],          'drawing_toy'],
    [['platform','jump across','jumping game','platformer'],             'platform_jumper'],
    [['maze','find the exit','labyrinth','navigate maze'],               'maze_runner'],
    [['endless run','side scroll runner','keep running','runner game'],  'endless_runner'],
    [['flappy','fly through','flap','bird game'],                        'flappy_flight'],
    [['whack','mole','tap mole','hit mole'],                             'whack_a_mole'],
    [['simon says','color sequence','repeat sequence'],                  'simon_says'],
    [['hangman','guess the word','word guessing'],                       'hangman'],
    [['catch stars','collect falling','basket catch'],                   'catch_the_stars'],
    [['color reaction','color speed','tap the color'],                   'color_reaction_game'],
    [['sorting','drag to sort','sort items'],                            'sorting_game'],
    // APPS
    [['calculator','math app','compute','arithmetic'],                   'calculator_app'],
    [['countdown timer','kitchen timer','set a timer','timer app'],      'timer_app'],
    [['stopwatch','lap timer','split times'],                            'stopwatch_app'],
    [['to do','todo','task list','task manager','my tasks'],             'todo_app'],
    [['checklist','check off items','to-do checklist'],                  'checklist_app'],
    [['notes','sticky notes','note pad','note taking'],                  'notes_app'],
    [['flashcard','flash cards','study cards','flip study'],             'flashcard_app'],
    [['habit','streak','daily habit','habit track'],                     'habit_tracker'],
    [['landing page','product page','hero section','startup page'],      'landing_page'],
    [['quote','inspirational quote','random quote'],                     'quote_generator'],
    [['budget','expense tracker','money tracker','spending log'],        'budget_tracker'],
    [['countdown','days until','event countdown'],                       'countdown_page'],
    [['kanban','task board','project board'],                            'kanban_board'],
    [['mood','mood log','how i feel','mood tracker'],                    'mood_tracker'],
    [['homework','assignment planner','school planner'],                 'homework_planner'],
    [['reading log','book tracker','books read'],                        'reading_log'],
    [['gratitude','grateful','thankful journal'],                        'gratitude_journal'],
    [['meal plan','weekly meals','food planner'],                        'meal_planner'],
    [['recipe','cooking app','recipe card'],                             'recipe_card_app'],
    [['leaderboard','high score board','ranking'],                       'leaderboard_shell'],
    [['joke','funny app','pun generator'],                               'joke_generator'],
    [['pomodoro','study timer','focus timer'],                           'study_timer'],
    [['story prompt','writing prompt','story idea'],                     'story_prompt_generator'],
  ];

  // Score one prompt against one keyword list
  function score(prompt, keywords) {
    const p = prompt.toLowerCase();
    return keywords.reduce((acc, kw) => p.includes(kw) ? acc + kw.split(' ').length : acc, 0);
  }

  // ── Classify ──────────────────────────────────────────
  function classify(prompt) {
    if (!prompt || !prompt.trim()) {
      return { templateId: null, confidence: 0, isDayOne: false, assets: [], theme: 'light' };
    }
    let best = null, bestScore = 0;
    for (const [kws, id] of ROUTES) {
      const s = score(prompt, kws);
      if (s > bestScore) { bestScore = s; best = id; }
    }
    const confidence = Math.min(1, bestScore / 3);
    // isDayOne = template exists in nl-specs.js day-one core
    const isDayOne   = best ? (window.NL_SPECS ? NL_SPECS.isDayOne(best) : false) : false;
    const assets     = window.NL_ASSETS ? NL_ASSETS.matchAssets(prompt) : [];
    const theme      = window.NL_ASSETS ? NL_ASSETS.matchTheme(prompt)  : 'light';
    const category   = best && window.NL_TEMPLATES ? (NL_TEMPLATES.get(best) || {}).category || 'unknown' : 'unknown';

    return { templateId: best, confidence, isDayOne, assets, theme, category };
  }

  // ── Build context for backend agents ──────────────────
  // Day-one: compact spec (~30 lines) — safe path, low token load
  // Expansion: light routing hint only — no HTML dump
  // No match: raw user context only
  function buildContext(classification, userPrompt, userContext) {
    const { templateId, confidence, isDayOne, assets, theme } = classification;
    userContext = userContext || '';

    // No confident match — agents build from scratch
    if (!templateId || confidence < 0.25) return userContext;

    // Day-one template — compact spec (the right path)
    if (isDayOne && window.NL_SPECS) {
      return NL_SPECS.buildCompactContext(templateId, userPrompt, userContext, assets, theme);
    }

    // Expansion template — light hint only, no HTML wall
    const spec = window.NL_TEMPLATES ? NL_TEMPLATES.get(templateId) : null;
    const hint = [
      `[TEMPLATE HINT: ${templateId} — expansion template, not day-one core]`,
      `Build a complete, working, single-file HTML ${(spec ? spec.title : templateId.replace(/_/g,' '))}.`,
      `Theme: ${theme}. Assets/style: ${assets.join(', ')}.`,
      `Match confidence: ${Math.round(confidence * 100)}%.`,
    ];
    if (userContext) hint.push(`\nUSER CONTEXT:\n${userContext}`);
    return hint.join('\n');
  }

  // ── Instant preview (before backend responds) ─────────
  function getInstantPreview(templateId) {
    if (!templateId || !window.NL_TEMPLATES) return null;
    return NL_TEMPLATES.render(templateId);
  }

  return { classify, buildContext, getInstantPreview };
})();
