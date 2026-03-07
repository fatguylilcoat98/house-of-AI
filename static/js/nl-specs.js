/**
 * NymbleLogic — Compact Template Specs v2.0
 * The Good Neighbor Guard — Christopher Hughes
 *
 * DAY-ONE CORE: 20 fully reliable templates (10 games + 10 apps).
 * These specs are what get sent to the Builder — NOT raw HTML.
 * Each spec is ~20-40 lines max.
 */

window.NL_SPECS = (() => {
  'use strict';

  const SPECS = {

    // ═══════════════════════════════════════════
    // GAMES — 10 fully supported day-one templates
    // ═══════════════════════════════════════════

    connect_four: {
      id: 'connect_four',
      tier: 'day-one',
      category: 'game',
      title: 'Connect Four',
      description: 'Two-player (human vs AI) drop-pieces strategy game on a 6x7 grid.',
      mechanics: ['board_grid_6x7', 'ai_opponent_basic', 'win_overlay', 'score_system', 'restart_flow'],
      winCondition: 'First player to connect 4 pieces horizontally, vertically, or diagonally wins.',
      loseCondition: 'AI connects 4 pieces.',
      drawCondition: 'Board fills completely with no winner.',
      onWin: 'Show win overlay with score. Offer replay. Trigger fireworks hook.',
      onLose: 'Show loss overlay. Offer replay.',
      onDraw: 'Show draw overlay. Offer replay.',
      defaultAssets: ['coin', 'star'],
      defaultTheme: 'dark',
      customizableFields: ['piece colors', 'board background color', 'player emoji/icon', 'AI difficulty (easy/hard)', 'theme'],
      safeToModify: ['colors', 'emoji icons', 'grid size (keep 6x7)', 'AI simple vs medium'],
      doNotTouch: ['win detection logic', 'column drop mechanics', 'board array structure'],
      kidSuitable: true,
      baseHtmlKey: 'connect_four',
    },

    tic_tac_toe: {
      id: 'tic_tac_toe',
      tier: 'day-one',
      category: 'game',
      title: 'Tic Tac Toe',
      description: '3x3 grid game. Human (X) vs AI (O). AI uses minimax.',
      mechanics: ['board_grid_3x3', 'ai_opponent_minimax', 'win_overlay', 'score_system', 'restart_flow'],
      winCondition: '3 in a row horizontally, vertically, or diagonally.',
      loseCondition: 'AI gets 3 in a row.',
      drawCondition: 'All 9 cells filled with no winner.',
      onWin: 'Highlight winning cells. Show win overlay. Track score.',
      onLose: 'Show lose overlay. Track score.',
      onDraw: 'Show draw overlay. Track draws.',
      defaultAssets: ['star', 'heart'],
      defaultTheme: 'purple',
      customizableFields: ['X/O symbols (can be emoji)', 'color theme', 'board style', 'cell shape'],
      safeToModify: ['symbols', 'colors', 'cell styling', 'font'],
      doNotTouch: ['minimax AI logic', 'win check function', 'board state array'],
      kidSuitable: true,
      baseHtmlKey: 'tic_tac_toe',
    },

    snake_game: {
      id: 'snake_game',
      tier: 'day-one',
      category: 'game',
      title: 'Snake Game',
      description: 'Classic snake on a 20x20 canvas grid. Arrow keys + swipe to move.',
      mechanics: ['keyboard_movement', 'touch_swipe', 'collision_detection', 'score_system', 'highscore_localstorage', 'restart_flow'],
      winCondition: 'Optional: reach length milestone (default: none — endless scoring).',
      loseCondition: 'Snake hits wall or its own body.',
      drawCondition: 'N/A',
      onWin: 'N/A (endless mode) or show milestone overlay.',
      onLose: 'Show game over overlay with final score vs high score. Offer replay.',
      defaultAssets: ['star', 'rabbit'],
      defaultTheme: 'dark',
      customizableFields: ['snake color', 'food emoji/color', 'grid size', 'speed', 'background theme'],
      safeToModify: ['colors', 'food item appearance', 'speed constant', 'background'],
      doNotTouch: ['grid coordinate system', 'collision logic', 'direction queue'],
      kidSuitable: true,
      baseHtmlKey: 'snake_game',
    },

    dodge_game: {
      id: 'dodge_game',
      tier: 'day-one',
      category: 'game',
      title: 'Dodge Game',
      description: 'Move left/right to dodge falling enemies. Mouse/touch/arrow keys.',
      mechanics: ['keyboard_movement', 'touch_movement', 'mouse_follow', 'enemy_spawner', 'collision_detection', 'lives_system', 'score_system', 'restart_flow'],
      winCondition: 'Optional: survive X seconds. Default: endless with score.',
      loseCondition: 'Player collides with a falling enemy. Loses all 3 lives.',
      drawCondition: 'N/A',
      onWin: 'Show survival win overlay if time target set.',
      onLose: 'Show game over overlay with score. Offer replay.',
      defaultAssets: ['star', 'monster', 'rocket'],
      defaultTheme: 'space',
      customizableFields: ['player character emoji', 'enemy emoji', 'spawn rate', 'speed', 'number of lives', 'theme'],
      safeToModify: ['emojis', 'colors', 'speed multiplier', 'spawn interval', 'lives count'],
      doNotTouch: ['collision rect check', 'requestAnimationFrame loop', 'lives decrement logic'],
      kidSuitable: true,
      baseHtmlKey: 'dodge_game',
    },

    clicker_game: {
      id: 'clicker_game',
      tier: 'day-one',
      category: 'game',
      title: 'Clicker Game',
      description: 'Click a target to earn points. Buy upgrades. Auto-clicker mechanic.',
      mechanics: ['score_system', 'upgrade_system', 'float_particles', 'restart_flow'],
      winCondition: 'Optional: reach score target. Default: endless.',
      loseCondition: 'N/A',
      drawCondition: 'N/A',
      onWin: 'Show milestone celebration overlay if target set.',
      onLose: 'N/A',
      defaultAssets: ['star', 'coin', 'gem'],
      defaultTheme: 'purple',
      customizableFields: ['click target emoji', 'color theme', 'upgrade names', 'score target', 'auto-click rate'],
      safeToModify: ['emoji', 'colors', 'upgrade labels', 'point values', 'upgrade costs'],
      doNotTouch: ['setInterval auto-clicker', 'upgrade state array', 'score accumulation'],
      kidSuitable: true,
      baseHtmlKey: 'clicker_game',
    },

    memory_match: {
      id: 'memory_match',
      tier: 'day-one',
      category: 'game',
      title: 'Memory Match',
      description: 'Flip cards to find matching pairs on a 4x4 grid.',
      mechanics: ['card_flip', 'score_system', 'win_overlay', 'restart_flow'],
      winCondition: 'All 8 pairs matched.',
      loseCondition: 'Optional: timer expires. Default: no time limit.',
      drawCondition: 'N/A',
      onWin: 'Show win overlay with move count. Track best score in localStorage.',
      onLose: 'Show time-up overlay if timed mode.',
      defaultAssets: ['star', 'heart', 'cat', 'dog', 'rabbit', 'pizza', 'balloon', 'alien'],
      defaultTheme: 'sky',
      customizableFields: ['card emoji set', 'grid size (4x4 default)', 'color theme', 'timed mode on/off', 'card back design'],
      safeToModify: ['emojis on cards', 'card colors', 'timer duration', 'grid size'],
      doNotTouch: ['flip lock mechanism', 'match detection logic', 'card state array'],
      kidSuitable: true,
      baseHtmlKey: 'memory_match',
    },

    quiz_game: {
      id: 'quiz_game',
      tier: 'day-one',
      category: 'game',
      title: 'Quiz Game',
      description: '10-question multiple choice quiz. Pass threshold 70%.',
      mechanics: ['score_system', 'timer_system', 'win_overlay', 'restart_flow'],
      winCondition: 'Score >= 70% of questions correct.',
      loseCondition: 'Score < 70% after all questions.',
      drawCondition: 'N/A',
      onWin: 'Show pass overlay with score percentage.',
      onLose: 'Show fail overlay with score and offer retry.',
      defaultAssets: ['star', 'gem'],
      defaultTheme: 'purple',
      customizableFields: ['question set', 'category/topic', 'pass threshold %', 'timer per question', 'color theme'],
      safeToModify: ['all questions and answers', 'topic', 'pass threshold', 'timer on/off', 'colors'],
      doNotTouch: ['answer shuffle logic', 'score calculation', 'question progression flow'],
      kidSuitable: true,
      baseHtmlKey: 'quiz_game',
    },

    breakout_paddle: {
      id: 'breakout_paddle',
      tier: 'day-one',
      category: 'game',
      title: 'Breakout',
      description: 'Paddle + ball destroys brick rows. Mouse/touch/arrow paddle control.',
      mechanics: ['mouse_follow', 'keyboard_movement', 'collision_detection', 'lives_system', 'score_system', 'win_overlay', 'restart_flow'],
      winCondition: 'All bricks cleared.',
      loseCondition: 'Ball falls below paddle. Lose all 3 lives.',
      drawCondition: 'N/A',
      onWin: 'Show win overlay with score.',
      onLose: 'Show game over overlay with score.',
      defaultAssets: ['gem', 'star'],
      defaultTheme: 'dark',
      customizableFields: ['brick colors', 'ball color/size', 'paddle color', 'brick rows/cols', 'ball speed', 'lives count'],
      safeToModify: ['colors', 'brick layout rows/cols', 'speed constant', 'paddle width'],
      doNotTouch: ['ball physics/reflection math', 'brick collision loop', 'requestAnimationFrame loop'],
      kidSuitable: true,
      baseHtmlKey: 'breakout_paddle',
    },

    reaction_timer: {
      id: 'reaction_timer',
      tier: 'day-one',
      category: 'game',
      title: 'Reaction Timer',
      description: 'Tap when screen flashes green. 5 attempts. Average reaction time scored.',
      mechanics: ['timer_system', 'score_system', 'restart_flow'],
      winCondition: 'Average reaction < 250ms.',
      loseCondition: 'Average > 250ms or early click.',
      drawCondition: 'N/A',
      onWin: 'Show speed grade overlay.',
      onLose: 'Show grade + suggestion to retry.',
      defaultAssets: ['star'],
      defaultTheme: 'dark',
      customizableFields: ['number of attempts', 'target color', 'win threshold ms', 'background'],
      safeToModify: ['number of rounds', 'flash color', 'score thresholds', 'theme'],
      doNotTouch: ['Date.now() timing logic', 'early click detection'],
      kidSuitable: true,
      baseHtmlKey: 'reaction_timer',
    },

    drawing_toy: {
      id: 'drawing_toy',
      tier: 'day-one',
      category: 'game',
      title: 'Drawing Toy',
      description: 'Freeform canvas drawing with color picker, brush size, eraser, and save.',
      mechanics: ['mouse_follow', 'touch_draw', 'canvas_save'],
      winCondition: 'N/A — creative toy.',
      loseCondition: 'N/A',
      drawCondition: 'N/A',
      defaultAssets: ['star', 'heart'],
      defaultTheme: 'light',
      customizableFields: ['default colors palette', 'brush sizes', 'background color', 'toolbar style', 'stamp shapes'],
      safeToModify: ['color swatches', 'brush size range', 'background', 'toolbar layout'],
      doNotTouch: ['canvas draw listener chain', 'touch preventDefault', 'toDataURL save'],
      kidSuitable: true,
      baseHtmlKey: 'drawing_toy',
    },

    // ═══════════════════════════════════════════
    // APPS — 10 fully supported day-one templates
    // ═══════════════════════════════════════════

    calculator_app: {
      id: 'calculator_app',
      tier: 'day-one',
      category: 'app',
      title: 'Calculator',
      description: 'Standard calculator with history. Keyboard + button input.',
      mechanics: ['expression_eval', 'history_log'],
      defaultAssets: [],
      defaultTheme: 'dark',
      customizableFields: ['button colors', 'display style', 'add scientific mode', 'add unit conversion', 'theme'],
      safeToModify: ['colors', 'layout', 'adding extra buttons', 'display font'],
      doNotTouch: ['Function() eval expression engine', 'history array logic'],
      kidSuitable: true,
      baseHtmlKey: 'calculator_app',
    },

    timer_app: {
      id: 'timer_app',
      tier: 'day-one',
      category: 'app',
      title: 'Timer',
      description: 'Countdown timer with presets (1/5/10/25 min), pause, and reset.',
      mechanics: ['timer_system', 'localstorage_prefs'],
      defaultAssets: [],
      defaultTheme: 'purple',
      customizableFields: ['preset durations', 'alarm sound', 'color theme', 'add multiple timers', 'label'],
      safeToModify: ['preset values', 'colors', 'label text', 'alarm behavior'],
      doNotTouch: ['setInterval tick logic', 'pause/resume elapsed calculation'],
      kidSuitable: true,
      baseHtmlKey: 'timer_app',
    },

    stopwatch_app: {
      id: 'stopwatch_app',
      tier: 'day-one',
      category: 'app',
      title: 'Stopwatch',
      description: 'Precision stopwatch with lap recording.',
      mechanics: ['timer_system'],
      defaultAssets: [],
      defaultTheme: 'dark',
      customizableFields: ['color theme', 'lap display style', 'font', 'max laps shown'],
      safeToModify: ['colors', 'layout', 'lap list styling'],
      doNotTouch: ['requestAnimationFrame tick', 'lap delta calculation'],
      kidSuitable: true,
      baseHtmlKey: 'stopwatch_app',
    },

    todo_app: {
      id: 'todo_app',
      tier: 'day-one',
      category: 'app',
      title: 'To-Do List',
      description: 'Add/complete/delete tasks. Filter all/active/done. localStorage persistence.',
      mechanics: ['localstorage_persistence', 'filter_system'],
      defaultAssets: [],
      defaultTheme: 'light',
      customizableFields: ['color theme', 'add categories/tags', 'due dates', 'priority levels', 'drag to reorder'],
      safeToModify: ['colors', 'adding tag/category field', 'due date field', 'sorting'],
      doNotTouch: ['localStorage save/load', 'filter state logic', 'task id generation'],
      kidSuitable: true,
      baseHtmlKey: 'todo_app',
    },

    checklist_app: {
      id: 'checklist_app',
      tier: 'day-one',
      category: 'app',
      title: 'Checklist',
      description: 'Simple checklist with progress bar and completion celebration.',
      mechanics: ['localstorage_persistence', 'progress_bar'],
      defaultAssets: [],
      defaultTheme: 'light',
      customizableFields: ['checklist title', 'color theme', 'add sections', 'celebration on 100%'],
      safeToModify: ['title', 'colors', 'adding sections', 'celebration trigger'],
      doNotTouch: ['check state persistence', 'progress percentage calculation'],
      kidSuitable: true,
      baseHtmlKey: 'checklist_app',
    },

    notes_app: {
      id: 'notes_app',
      tier: 'day-one',
      category: 'app',
      title: 'Notes',
      description: 'Sticky notes grid. Create, edit, delete. Random pastel colors. localStorage.',
      mechanics: ['localstorage_persistence'],
      defaultAssets: [],
      defaultTheme: 'light',
      customizableFields: ['color palette', 'note max length', 'add search', 'add categories', 'font'],
      safeToModify: ['colors', 'font', 'adding search bar', 'note categories'],
      doNotTouch: ['note id generation', 'localStorage save/load', 'edit-on-blur flow'],
      kidSuitable: true,
      baseHtmlKey: 'notes_app',
    },

    flashcard_app: {
      id: 'flashcard_app',
      tier: 'day-one',
      category: 'app',
      title: 'Flashcards',
      description: 'Flip card study app. Got it / Missed grading. Progress tracking.',
      mechanics: ['card_flip_css', 'score_system', 'localstorage_progress'],
      defaultAssets: [],
      defaultTheme: 'purple',
      customizableFields: ['card set topic', 'card content', 'color theme', 'add custom card input', 'shuffle mode'],
      safeToModify: ['all card questions and answers', 'topic', 'colors', 'adding shuffle toggle'],
      doNotTouch: ['CSS 3D flip transform', 'grade tracking counters'],
      kidSuitable: true,
      baseHtmlKey: 'flashcard_app',
    },

    habit_tracker: {
      id: 'habit_tracker',
      tier: 'day-one',
      category: 'app',
      title: 'Habit Tracker',
      description: 'Daily habit check-ins with streak counting. localStorage persistence.',
      mechanics: ['localstorage_persistence', 'streak_system'],
      defaultAssets: [],
      defaultTheme: 'light',
      customizableFields: ['color theme', 'add habit categories', 'weekly view', 'streak goal', 'reminder text'],
      safeToModify: ['colors', 'adding category field', 'streak goal display', 'layout'],
      doNotTouch: ['streak calculation logic', 'date-based done-today check', 'localStorage save'],
      kidSuitable: true,
      baseHtmlKey: 'habit_tracker',
    },

    landing_page: {
      id: 'landing_page',
      tier: 'day-one',
      category: 'app',
      title: 'Landing Page',
      description: 'Clean product landing page. Hero, features, CTA, footer.',
      mechanics: ['scroll_animation', 'smooth_scroll'],
      defaultAssets: ['rocket', 'star'],
      defaultTheme: 'light',
      customizableFields: ['product name', 'tagline', 'feature list', 'CTA text', 'color theme', 'hero image/emoji', 'footer links'],
      safeToModify: ['all copy text', 'colors', 'sections', 'CTA button style', 'hero content'],
      doNotTouch: ['scroll event listeners', 'CSS layout grid structure'],
      kidSuitable: false,
      baseHtmlKey: 'landing_page',
    },

    quote_generator: {
      id: 'quote_generator',
      tier: 'day-one',
      category: 'app',
      title: 'Quote Generator',
      description: 'Random inspirational quotes with fade animation and clipboard copy.',
      mechanics: ['random_picker', 'clipboard_api'],
      defaultAssets: ['star'],
      defaultTheme: 'purple',
      customizableFields: ['quote set/topic', 'color theme', 'add favorites', 'add share button', 'font', 'background style'],
      safeToModify: ['all quotes', 'topic', 'colors', 'font', 'adding favorites feature'],
      doNotTouch: ['fade animation timing', 'clipboard.writeText call'],
      kidSuitable: true,
      baseHtmlKey: 'quote_generator',
    },
  };

  // ── Expansion templates (not day-one supported) ──────
  const EXPANSION_IDS = [
    'platform_jumper','maze_runner','collect_and_avoid','endless_runner',
    'catch_the_stars','flappy_flight','whack_a_mole','simon_says',
    'hangman','word_search','trivia_show','drawing_toy','dress_up_toy',
    'sorting_game','shape_match','color_reaction_game',
    'budget_tracker','countdown_page','kanban_board','mood_tracker',
    'homework_planner','reading_log','gratitude_journal','meal_planner',
    'recipe_card_app','simple_dashboard','contact_form_app',
    'leaderboard_shell','joke_generator','study_timer','story_prompt_generator',
  ];

  // ── Public API ────────────────────────────────────────
  return {
    SPECS,
    EXPANSION_IDS,

    get(id) { return SPECS[id] || null; },

    isDayOne(id) { return !!SPECS[id]; },

    list() {
      return Object.values(SPECS).map(({ id, tier, category, title, description, kidSuitable }) =>
        ({ id, tier, category, title, description, kidSuitable }));
    },

    /**
     * Build the compact context string sent to Builder.
     * ~30 lines max. No raw HTML.
     */
    buildCompactContext(id, userPrompt, userContext = '', assets = [], theme = '') {
      const spec = SPECS[id];
      if (!spec) return userContext;

      const lines = [
        `[NYMBLELOGIC TEMPLATE: ${spec.title} — DAY-ONE CORE]`,
        `Description: ${spec.description}`,
        `Category: ${spec.category}`,
        ``,
        `MECHANICS ALREADY BUILT INTO BASE:`,
        spec.mechanics.map(m => `  - ${m}`).join('\n'),
        ``,
        `WIN:  ${spec.winCondition}`,
        `LOSE: ${spec.loseCondition}`,
        `DRAW: ${spec.drawCondition}`,
        ``,
        `ON WIN:  ${spec.onWin || 'Show win overlay, offer replay.'}`,
        `ON LOSE: ${spec.onLose || 'Show lose overlay, offer replay.'}`,
        ``,
        `SAFE TO CUSTOMIZE:`,
        spec.customizableFields.map(f => `  - ${f}`).join('\n'),
        ``,
        `DO NOT TOUCH (working logic — preserve exactly):`,
        spec.doNotTouch.map(d => `  - ${d}`).join('\n'),
        ``,
        `Assets matched: ${(assets.length ? assets : spec.defaultAssets).join(', ')}`,
        `Theme: ${theme || spec.defaultTheme}`,
        ``,
        `USER REQUEST:`,
        userPrompt,
      ];

      if (userContext) lines.push(`\nADDITIONAL CONTEXT:\n${userContext}`);

      return lines.join('\n');
    },
  };
})();
