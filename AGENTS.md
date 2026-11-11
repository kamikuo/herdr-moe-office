# Moe Office: development notes

For people (and agents) changing this mod or making a new character. The user guide is README.md.

## Layout

- `mods/moe-office/`: the mod itself; this is the folder that goes into Herdr. The repo is laid out the way Herdr shares mods (herdr.dev/mods): `mods/<name>/`, `RECIPE.md` and `preview.png` at the top, and the repo topic `herdr-mod`.
  - `main.js`: what happens in the office: walking, statuses, tea time, interns, the water reminder, the cat and night.
  - `doll.js`: the characters' frames, where she stands, which agent is which character, and the hair colours.
  - `scene.js`: scene objects, the art table `ART`, and the scene themes `THEMES` (wall, wainscot and floor colours).
  - `i18n.js`: every word on screen, in English, Traditional Chinese and Japanese.
  - `debug.js`: the settings panel behind the ⚙️ in the top right: the language and scene, then, behind a "Debug mode" checkbox (off by default; turning it off clears the fakes, the forced time, the forced water reminder and a tea time started from there), fake coworkers (action, character, hair colour, sub-agents, remote), time of day, and buttons for tea time and the water reminder, so every state can be seen without waiting for it. Kept in localStorage.
  - `chars/<character>/`: the character's frames and their list `char.js`, made by `tools/build_video.py`; don't edit by hand. So far `jirai`, `intern`, `designer-cute`, `engineer-hoodie`, `wavy-blouse`, `twintail-blazer` and `bob-jacket`. New ones go at the end of `CAST` in `doll.js` (debug coworkers pick theirs by index), and each needs its two desk things in `SETS` in `tools/scene_art.py` and a `set_<name>` entry in `ART` in `scene.js`. The names only describe the look; any agent can be any of them.
  - `scene/<theme>/`: the scene's vector art, one folder per theme (`pastel`, `jirai`, `gothic`), made by `tools/scene_art.py`; don't edit by hand.
- `tools/`: the scripts that make the art.
- `art-src/video/<character>/`: the character videos, two per character. Not in git (they're only needed to make the frames again, and would make every install download about 60 MB more): get them from `art-src.zip` attached to the latest [release](https://github.com/kamikuo/herdr-moe-office/releases) and unzip it at the top of the repo. A new character's videos go in a new `art-src.zip` on the next release.
  - `setA.mp4`: idle, walk, typing.
  - `setB.mp4`: asking for help, cheering, dozing.

## Setup

The art scripts need Python 3 (Pillow, NumPy, SciPy), ffmpeg and Real-ESRGAN:

```
python3 -m venv .venv && .venv/bin/pip install pillow numpy scipy && brew install ffmpeg
```

Real-ESRGAN: download [the macOS build of realesrgan-ncnn-vulkan](https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-macos.zip) and unpack it as `.tools/realesrgan/` (with `realesrgan-ncnn-vulkan` and `models/` inside). `.tools/` is not in git.

For type hints in your editor you need Herdr's `gpui-kit.d.ts`. It's Herdr's file, so it isn't in the repo; copy it over:

```
cp ~/.config/herdr-app/gpui-kit.d.ts mods/moe-office/
```

## Commands

Install into Herdr (replaces `~/.config/herdr-app/mods/moe-office` and runs `herdr-app check`):

```
./install.sh
```

After changing a character video or how it's cut, make the frames again (about 2 to 3 minutes):

```
rm -rf mods/moe-office/chars/jirai && .venv/bin/python -I tools/build_video.py jirai
```

To add a character: put its two videos in `art-src/video/<name>/` (and in the next release's `art-src.zip`), add it to `CHARS` in `tools/build_video.py`, build it, then import its `char.js` in `mods/moe-office/doll.js` and add it to `CAST`.

Make the scene art again:

```
rm -rf mods/moe-office/scene && .venv/bin/python -I tools/scene_art.py mods/moe-office/scene
```

## Languages

- All text on screen comes from `t(key)` in `mods/moe-office/i18n.js`. Add new text there in all three languages, never as a literal in the code.
- The language: the one picked with 🌐 in the ⚙️ panel (saved); else the block's props (`{ "lang": "zh-TW" }`); else English.
- To add a language: add it to `LANGS` and a column to every entry. Missing entries fall back to English.
- Translate for the feel, not word for word: these are short, playful office lines.

## Character videos

- Two videos per character, made with image-to-video from the same character picture: 10 seconds, 16:9, locked camera, plain background, facing 45 degrees to the right the whole time.
- The actions are split into two sets because with all six in one video each action is too short to loop. Walking is followed by typing, which gives the walk its "hurrying to the computer" bounce.
- Each character's settings are in `CHARS` in `tools/build_video.py`: white or green background, which stretch each action uses (first frame, loop end, every Nth frame), how fast each plays (`speed`), and the standing frames used to measure her height (hands below her head). With a new video, find the loops again: pick the stretch whose first and last frames look most alike. Idle is different (`pingpong`): it plays a gentle sway forwards then backwards, so pick a stretch that starts and ends where she turns around, with no head turns. A short idle loop of near-still frames only shows the video's noise and looks like shaking.
- **Real-ESRGAN first, on every frame**: video compression adds noise and keeps colour at half resolution, so edges pick up the background colour and lines go soft. Real-ESRGAN's anime video model (`realesr-animevideov3`) at 2x removes the noise and sharpens the lines, and the key leaves almost no green fringe. The downside: very fine strokes (like the hatching on her blush) get smoothed away. The processed frames live in a temporary folder and are deleted afterwards (about 500 MB per character).
- **The key must not touch opaque pixels**: her outline is a dark line around the edge; only the half-transparent edge pixels may be corrected, or the outline gets wiped and everything turns blurry. Real-ESRGAN leaves a lighter green ring around her, so the greenness threshold is strict (`0.7`) to count that ring as background.
- **No dithering in the 256-colour PNGs**: dithering breaks thin lines into specks.
- **Green screen is easier than white**: green is the background, so there's no guessing about enclosed gaps, and white clothes and highlights don't get cut out. The half-transparent edge pixels have the green taken out, then her whole body has green capped at red or blue (despill), so there's no green fringe. She must have no green on her. The green-screen prompt must say: the character picture is 16:9, she fills about 60% of the frame height, and her whole body stays in frame at all times; otherwise she often jumps out of frame or only her upper body is shown.
- White background: white touching the border is background; white gaps enclosed by hair, arms and body are background too. Only white within `HEAD` px below the top of her head, smaller than `EYE_MAX` px, and ringed by a dark outline is kept as eye whites. The gaps often sit next to black clothes or socks, so a dark ring alone isn't enough. For a character with bigger eye whites, adjust these two. Half-transparent edge pixels have the white taken out, so there's no white fringe on the dark night background.
- **Hair colour is set when she's drawn**: each frame is three layers drawn on top of each other, and all colours share the same files.
  - `<action>.png`: everything that isn't pink (face, clothes, outline).
  - `<action>_hair.svg`: where the hair, eyes and ribbon are, as a PNG mask inside an SVG. The mod draws it with `svg()`, filled with her colour.
  - `<action>_shade.png`: black (shadow) and white (shine) on top of the colour. Each pixel gets as much black as it is darker than the video's base hair colour (`HAIR`), or as much white as it is lighter, so every colour keeps its depth.
  - The colours are `SWATCH` in `mods/moe-office/doll.js`. A new colour should be about as light as `pink`, since the shading goes up and down from there.
  - The pink is only the pixels with a hue of 335 to 351 degrees and enough chroma. Skin (5 to 27 degrees) and blush (355 to 10 degrees) stay out, so her blush keeps its colour. Measure these again for a new character.
- **One sheet per action**: each of those files holds all of the action's frames, in a grid `cols` across with `pad` px of nothing between them (both in `char.js`); `frame()` in `doll.js` shows one cell by moving the sheets inside a clipped box. `build_video.py` writes every frame on its own, then runs `tools/pack_sheets.py`, which puts them together and deletes the single frames. Separate files per frame meant three new files at every frame change: with 8 or more girls (every character at once) an M1 MacBook Pro couldn't keep them all ready, and girls blinked out for a moment. Now each character is 36 files, loaded once.
- **File size**: the base is a 256-colour PNG; the mask and shading keep only 16 levels of transparency, and the shading is a 32-colour PNG. No visible difference, about 3 to 4 MB per character.
- Frames facing left are a mirrored copy saved as `_l`, since elements can't be flipped.
- **Which agent is which character**: picked at random the first time an agent shows up (among the characters used least so far), and kept in localStorage (`moe-office.cast`, the newest 400), so she stays the same after Herdr restarts. The hair colour comes from the address instead. In the ⚙️ panel each fake coworker can switch character.
- **One prompt for every character**: all the characters' pink (hair, eyes, one accessory) measured the same, hue 336 to 348 and about the same `HAIR`, so `PINK` and `HAIR` are shared. Check again for a new character.

## Scene themes

- A theme is the same set of pieces at the same sizes in other colours and trimmings, so the layout, seats and desk tops stay put.
- In `tools/scene_art.py`, `THEMES` gives each theme's colours by role (LAV: desks, couch, clock; MINT: door, counter, lamp, leaves; and so on), `J` adds lace (`lace()`) and bows (`bow()`) to the jirai and gothic themes, and `G` the gothic theme's crosses (`cross()`) and roses (`rose()`). In `mods/moe-office/scene.js`, `THEMES` has the colours drawn as divs: wall, wainscot, rail, floor, baseboard, outline, board pins, whether the wainscot gets a lace trim, and how much the room dims at night (`night`: a dark scene is dark already).
- Readability: keep the background (wall, wainscot, floor) low in contrast and far from the furniture's tone, light or dark, so the furniture and the girls stand out. A busy black-and-pink floor made the first jirai try unreadable.
- Which theme: the one picked in the ⚙️ panel (saved); else the block's props (`{ "scene": "jirai" }`); else `pastel`.
- To add a theme: add it to both `THEMES`, an i18n entry `scene.<name>`, and make the art again.

## Desk things

- Each character has her own two things on the desk (`set_<character>` in `scene_art.py` `SETS` and in `ART`, 8 × 10 U), drawn at `DESK.set`: a small one in front of the monitor's corner, a taller one beside it. Keep it to two: more made the desks look cluttered. An empty desk keeps the lamp. A new character needs a set too.

## Swapping vector art for pictures

- Every scene object is listed in the `ART` table in `mods/moe-office/scene.js`, each with a file name and a size.
- Sizes are in scene units, turned into pixels from the panel's height when drawn.
- To swap one for a picture:
  - Draw a PNG with the same aspect ratio and put it in `mods/moe-office/scene/<theme>/`.
  - Change that entry's `src` to the new file name.
- Things that turn around (only the cat so far) also need a mirrored `<name>_l.png`.
- The clock hands are one file per angle in `scene/<theme>/clock/`: hour hand `h_0` to `h_47`, one per 15 minutes; minute hand `m_0` to `m_59`, one per minute.
- Careful: `scene_art.py` deletes `mods/moe-office/scene` first, so keep your pictures somewhere else, or don't run it again after swapping.

## Pitfalls

- **Zoom**: the panel reports its size in screen pixels, and what's drawn is scaled again by Herdr's zoom, so divide by `settings().zoom` first.
- **`loop` always goes back and forth**: things that fall or drift one way (snow, rain, clouds, confetti, sweat) can't use `loop`; work out their position from the time.
- **Elements can't be rotated**: that's why the clock hands are pre-drawn at every angle. Inside an SVG, don't use `transform` either: Herdr skipped a rotated ellipse (the calendar's bunny ears) without a word.
- **A picture blinks the first time it's drawn**: its file is still loading, so that frame is empty. Herdr has no preload API, so `warmup()` in `doll.js` draws every sheet once under the room (where it can't be seen), 6 per redraw, done in a few redraws. SVGs are rasterised at the size they're drawn, so each size she has appeared at (staff, interns) gets its own round.
- **Redraw as fast as the animation**: the view redraws on a timer; if that's longer than a frame, frames get skipped unevenly and she looks jerky. `frameTick()` in `doll.js` sets the next redraw to the shortest frame time among the actions drawn this time (110 ms at most). Each action's playback speed is `speed` in `build_video.py`.
- **Resizing redraws at the end**: every new size means new scales for every picture, and the girls' frames load again at the new scale, so redrawing at each step of a drag was jerky. `on_size_change` keeps the old size until the new one has held still for `RESIZE_SETTLE` ms (main.js).
- **`herdr-app check` needs the full path**: given just a name, it looks in the current folder.
- **Don't name a variable `t`**: it's the translator from `i18n.js`. The video wall once had `const t = 13 * U`, and broke the moment a remote agent showed up.
- **A reload during `install.sh` can leave the mod half-copied** (no `main.js`): the view shows "not a function" or "no main.js" in `herdr-app status`. Run `./install.sh` again.
- **The wall is a row of its own**: `wall()` in main.js lines up window, calendar, clock, window, board (video call), then extra windows, from the door to the bookshelf with equal gaps. It used to be a 40-unit grid with some spots skipped, and every resize changed which spot got a window, so things jumped around; now a resize only stretches the gaps, except when an extra window fits (gaps of `WALL_GAP` units or more). The corners are fixed (plant and door left, bookshelf right) and the floor in between is shared out in `geometry()`.
- **The view out of the windows is one landscape**: `window_()` gets the room x of the sun or moon and draws each window's own stretch of the skyline and clouds, so there is only one sun however many windows there are.
