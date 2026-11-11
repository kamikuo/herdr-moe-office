// Coworkers: every agent is one of the characters (frames cut from character videos, chars/),
// with her own hair colour. Each action is a loop of frames; each frame is three layers (see
// tools/build_video.py): the girl without her pink parts, a mask of those parts filled with
// her colour, and the shadows and shine on top.
import { div, image, svg } from "gpui-kit";
import { CHAR as jirai } from "./chars/jirai/char.js";
import { CHAR as intern } from "./chars/intern/char.js";
import { CHAR as designerCute } from "./chars/designer-cute/char.js";
import { CHAR as engineerHoodie } from "./chars/engineer-hoodie/char.js";
import { CHAR as wavyBlouse } from "./chars/wavy-blouse/char.js";
import { CHAR as twintailBlazer } from "./chars/twintail-blazer/char.js";
import { CHAR as bobJacket } from "./chars/bob-jacket/char.js";

// The characters, by folder name in chars/. New ones go at the end: debug coworkers pick
// theirs by index.
const CAST = {
  jirai, intern, "designer-cute": designerCute, "engineer-hoodie": engineerHoodie,
  "wavy-blouse": wavyBlouse, "twintail-blazer": twintailBlazer, "bob-jacket": bobJacket,
};
export const CHARACTERS = Object.keys(CAST);

// A person's box: PERSON units wide, BOX units tall, feet on its bottom edge.
export const PERSON = 16;
export const BOX = 30;
// How tall she stands, in units (head top to soles).
const STAND_U = 27;
// The walk cycle plays faster than it was filmed, to keep up with main.js's WALK_SPEED
// (her feet slid otherwise). Change both together.
const WALK_PACE = 0.6;

// The hair colours (also eyes and ribbon). Keep them about as light as "pink" (the colour in
// the videos): the shading on top only makes them darker or lighter from there.
export const SWATCH = {
  pink: "#f6a6be", rose: "#f39aa9", coral: "#f6a68e", peach: "#f6bb92",
  honey: "#efcf82", lemon: "#e9de8c", lime: "#c4e090", mint: "#93dfbd",
  aqua: "#8dd6dc", sky: "#98c4f0", periwinkle: "#a8b0f2", lilac: "#c6a3ee",
  lavender: "#dcaeea", berry: "#d97ca2", cocoa: "#bb917c", silver: "#c8c5d6",
};
export const COLOURS = Object.keys(SWATCH);

// The same number every time for the same address.
export function hash(address) {
  let h = 2166136261;
  for (const ch of address) h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0;
  return h;
}

// Looks chosen by hand (the debug panel): address -> { colour: index into COLOURS,
// char: index into CHARACTERS }.
export const FIXED = {};

// Which character each agent is, and her hair colour: picked the first time she shows up,
// then kept in localStorage, so she stays the same after Herdr restarts. The character is one
// of those used least so far, so the office stays mixed. The hair colour comes from her
// address, unless someone in the office now (setPresent) is the same character with that
// colour: then she gets one none of them has. Agents first seen before colours were kept
// (the entry is just the character's name) keep the colour from their address.
const CAST_KEY = "moe-office.cast";
const CAST_MAX = 400; // forget the oldest past this many
let cast = null;
let present = [];

// Who's in the office now (agents and debug coworkers), to keep new girls' looks apart.
export function setPresent(addresses) { present = addresses; }

function looks(address) {
  if (!cast) {
    try { cast = JSON.parse(localStorage.getItem(CAST_KEY)) || {}; } catch { cast = {}; }
  }
  const e = cast[address];
  if (typeof e === "string" && e in CAST) return { char: e };
  if (e && e.char in CAST) return e;
  const used = Object.fromEntries(CHARACTERS.map((n) => [n, 0]));
  for (const v of Object.values(cast)) { const n = typeof v === "string" ? v : v?.char; if (n in used) used[n]++; }
  const least = Math.min(...Object.values(used));
  const pick = CHARACTERS.filter((n) => used[n] === least);
  const char = pick[Math.floor(Math.random() * pick.length)];
  // Only those whose looks are settled (two newcomers at once: the second sees the first).
  const settled = (o) => o !== address && (typeof FIXED[o]?.char === "number" || cast[o]);
  const twins = new Set(present.filter((o) => settled(o) && castOf(o) === char).map((o) => colourOf(o)));
  let colour = hash(address) % COLOURS.length;
  if (twins.has(COLOURS[colour])) {
    const free = COLOURS.map((_, i) => i).filter((i) => !twins.has(COLOURS[i]));
    if (free.length) colour = free[Math.floor(Math.random() * free.length)];
  }
  cast[address] = { char, colour };
  const keys = Object.keys(cast);
  for (const k of keys.slice(0, Math.max(0, keys.length - CAST_MAX))) delete cast[k];
  try { localStorage.setItem(CAST_KEY, JSON.stringify(cast)); } catch {}
  return cast[address];
}

export function castOf(address) {
  const c = FIXED[address]?.char;
  if (typeof c === "number") return CHARACTERS[c % CHARACTERS.length];
  return looks(address).char;
}

function colourOf(address) {
  const c = FIXED[address]?.colour ?? (typeof FIXED[address]?.char === "number" ? undefined : looks(address).colour);
  return COLOURS[(c ?? hash(address)) % COLOURS.length];
}

// The hair colour, for things that match it.
export function outfitColour(address) {
  return SWATCH[colourOf(address)];
}

// A coworker doing `name`, drawn inside a PERSON x BOX box at scale U (px per unit).
// `face` 1 looks right, -1 left. `at`: where her anchor sits, in units from the box's left
// edge (8 standing in the middle; 10 seated at a desk, so the hands reach the keyboard).
export function dollSprite(address, name, face, U, salt = 0, at = 8) {
  const who = castOf(address), CHAR = CAST[who];
  if (!CHAR.anim[name]) name = "idle";
  const a = name === "walk" ? { ...CHAR.anim.walk, ms: Math.round(CHAR.anim.walk.ms * WALK_PACE) } : CHAR.anim[name];
  // A pingpong action plays forwards then backwards: 0 1 .. n-1 n-2 .. 1.
  const step = Math.floor((Date.now() + salt) / a.ms) % (a.pingpong && a.n > 1 ? 2 * a.n - 2 : a.n);
  const i = step < a.n ? step : 2 * a.n - 2 - step;
  const k = (STAND_U * U) / CHAR.stand; // frame px -> px
  const ax = face < 0 ? (PERSON - at) * U : at * U;
  const cx = face < 0 ? a.w - a.cx : a.cx;
  if (!warm.has(`${who} ${U}`)) warm.set(`${who} ${U}`, 0);
  fastest = Math.min(fastest, a.ms);
  return frame(who, name, i, face, U, SWATCH[colourOf(address)])
    .left(ax - cx * k).top(BOX * U - a.feet * k);
}

// How long until the next redraw: the shortest frame time of what was drawn since the last
// call, so every frame shows (a longer wait skips frames unevenly and she looks jerky).
let fastest = Infinity;
export function frameTick(most) {
  const t = Math.min(most, fastest);
  fastest = Infinity;
  return t;
}

// One frame of character `who`, her three layers stacked, at scale U. Each action is one sheet
// per layer and facing (tools/pack_sheets.py): frames in a grid, `cols` across, `pad` px
// apart. Her box shows one cell; changing frames only moves the sheets inside it, so nothing
// new has to load (separate files per frame made her blink out on a slower Mac with many girls).
function frame(who, name, i, face, U, colour) {
  const CHAR = CAST[who], a = CHAR.anim[name];
  const k = (STAND_U * U) / CHAR.stand;
  const W = a.w * k, H = a.h * k;
  const pw = (a.w + CHAR.pad) * k, ph = (a.h + CHAR.pad) * k;
  const rows = Math.ceil(a.n / a.cols);
  const f = `mods/moe-office/chars/${who}/${name}${face < 0 ? "_l" : ""}`;
  const layer = (el) => el.absolute().left(-(i % a.cols) * pw).top(-Math.floor(i / a.cols) * ph).w(a.cols * pw).h(rows * ph);
  return div().absolute().w(W).h(H).overflow_hidden()
    .child(layer(image(`${f}.png`)))
    .child(layer(svg(`${f}_hair.svg`).text_color(colour)))
    .child(layer(image(`${f}_shade.png`)));
}

// Warming up: a sheet drawn for the first time isn't there yet (its files are still loading),
// so she blinks out for a moment. warmup() draws every sheet once (frame 0 of each action and
// facing), a few per render, for each character and scale that has been drawn; put it first
// in the scene, under everything else, where it can't be seen. Once one is done it draws
// nothing more.
const warm = new Map(); // "character scale" -> how many sheets are done
const ALL = Object.fromEntries(CHARACTERS.map((who) => [who, Object.keys(CAST[who].anim).flatMap((name) => [[name, 0, 1], [name, 0, -1]])]));
const WARM_BATCH = 6;

export function warmup() {
  const out = [];
  for (const [key, done] of warm) {
    const [who, U] = key.split(" "), all = ALL[who];
    if (done >= all.length) continue;
    for (const [name, i, face] of all.slice(done, done + WARM_BATCH)) out.push(frame(who, name, i, face, +U, "#000000").left(0).top(0));
    warm.set(key, done + WARM_BATCH);
  }
  return out;
}
