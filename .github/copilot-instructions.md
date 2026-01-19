# Copilot instructions for tarzan-jump-game

Purpose: Short, actionable guidance so coding agents can be immediately productive working on this small pygame prototype.

- **Repo type:** single-file pygame prototype. Entry point: [main.py](main.py).
- **Run locally:** ensure Python 3.x and `pygame` installed, then run `python main.py`.

Key code areas and patterns
- `main.py` contains all logic: classes `World`, `Particle`, `Rope`, `CeilingMap`, `SpikeFloor`, and `AppMain` (game loop).
- Physics: gravity is applied in `Particle.update()` via `self.vel += self.world.gravity * self.world.dt`. Speed is clamped to 10.
- Rope constraint: when player-anchor distance > rope length, the player position is snapped to `anchor + normalized_diff * length` and radial velocity removed via projection. See `Rope.update()`.
- Camera/scroll: `scroll_x` follows `player.x - world.width/3` with smoothing factor `0.1` (in `AppMain.update()`).
- Level generation: `CeilingMap` builds ceiling `pygame.Rect` segments up to ~12000px; check `get_ceiling_y(x)` to find attachment points.
- Input & states: simple state machine strings `"READY"`, `"PLAYING"`, `"GAMEOVER"`, `"GOAL"`. Left mouse: fire rope; release: detach. ESC posts `QUIT`.

Config & tuning
- Top-level constants in `main.py` are the intended tweak points: `ROPE_ANGLE`, `KICK_STRENGTH`, `GOAL_X` — prefer changing these for game-balance adjustments rather than invasive refactors.
- Positions use `pygame.Vector2`; `Particle` exposes `x,y,vx,vy` as properties (backwards-compatibility).

Common tasks and examples
- To test a physics tweak (e.g., rope boost): edit `KICK_STRENGTH` and run:

```powershell
python -m pip install pygame
python main.py
```

- To find where rope attachment is computed: inspect `AppMain.get_rope_target()` and `CeilingMap.get_ceiling_y()` (both in [main.py](main.py)).
- To change the visible goal distance, edit `GOAL_X` at the top of [main.py](main.py).

Developer conventions (discoverable)
- Single-file prototype: avoid adding deep modularization unless adding tests or multiple modules — keep changes focused and minimal.
- Visual/debugging: drawing and logic are entangled; prefer small, localized changes (constants or small helper functions) for quick iteration.

Integration & dependencies
- Only external dependency: `pygame`. No network or build system integrations.

Editing guidance for AI agents
- Prefer minimal, reversible edits: change constants or small functions; when larger refactors are required, propose a migration plan first.
- Use the state strings and camera smoothing when adding features that affect gameplay pacing.
- Preserve the random ceiling generation behavior unless the change intends to replace procedural generation.

No existing agent guidance files were found in the repository; create pull requests for larger changes and include a short demo GIF or recorded run when modifying core gameplay.

If anything above is unclear or you want more examples (line references, small refactor PR), tell me which area to expand.
