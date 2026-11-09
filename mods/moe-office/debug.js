// The settings panel behind the ⚙️ in the corner: the language, and for trying things out,
// fake coworkers with a chosen action, look, sub-agents and whether they're remote, a time of
// day, and buttons for tea time and the water reminder. All kept in
// localStorage. Fake coworkers are placed like real agents but don't count on the board and
// can't be clicked through.
import { div } from "gpui-kit";
import { THEMES } from "./scene.js";
import { COLOURS, SWATCH, FIXED, CHARACTERS } from "./doll.js";
import { t, getLang, LANGS } from "./i18n.js";

const KEY = "moe-office.debug";
const MAX = 6;
export const ACTIONS = ["idle", "walk", "typing", "blocked", "alarm", "done", "sleep"];

export function load() {
  try {
    const d = JSON.parse(localStorage.getItem(KEY));
    if (d && Array.isArray(d.dolls)) {
      for (const doll of d.dolls) {
        if (typeof doll.look?.colour !== "number") doll.look = randomLook(); // looks from the paper dolls
        if (typeof doll.look.char !== "number") doll.look.char = randomLook().char; // from before there were characters
      }
      if (!d.debug) clearDebug(d);
      return d;
    }
  } catch {}
  return { open: false, debug: false, next: 1, dolls: [] };
}

// Debug mode off: no fake coworkers, the real time of day, no forced water reminder (and
// main.js ends a tea time started from here).
function clearDebug(d) {
  d.dolls = [];
  d.hour = null;
  delete d.water;
}

export function randomLook() {
  return { colour: Math.floor(Math.random() * COLOURS.length), char: Math.floor(Math.random() * CHARACTERS.length) };
}

// Debug clock: the hour the room pretends it is (null = the real one).
export const TIMES = [null, 12, 18, 22];

// "walk" goes back and forth between the desk and the cooler every 6 s.
const statusOf = (action, now) =>
  action === "walk" ? (Math.floor(now / 6000) % 2 ? "working" : "idle")
  : action === "typing" ? "working" : action === "blocked" || action === "alarm" ? "blocked"
  : action === "done" ? "done" : "idle";

// The fake agents, shaped like herdr's agents.
export function fakes(d, now) {
  for (const k of Object.keys(FIXED)) if (k.startsWith("debug-")) delete FIXED[k];
  return d.dolls.map((doll) => {
    const address = `debug-${doll.id}`;
    FIXED[address] = doll.look;
    const label = t(`act.${doll.action}`);
    return { address, debug: true, remote: Boolean(doll.remote), status: statusOf(doll.action, now), action: doll.action,
      space_name: `Debug ${doll.id}`, tab_name: label, title: `debug · ${label}` };
  });
}

// The fake coworkers' sub-agents, shaped like herdr's terminals: working, idle, stuck.
const KID_STATUS = ["working", "idle", "blocked"];
export function fakeKids(d) {
  return d.dolls.filter((doll) => !doll.remote).flatMap((doll) => Array.from({ length: doll.kids ?? 0 }, (_, k) => ({
    address: `debug-${doll.id}-sub${k}`, parent: `debug-${doll.id}`, state: "live", status: KID_STATUS[k % KID_STATUS.length],
  })));
}

// A gear button in the corner opens the panel.
export function panel(d, W, H, scene, partyOn) {
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(d)); } catch {} };
  const act = (fn) => (_e, cx) => { fn(); save(); cx.notify(); };
  const btn = (id, label, fn, bg = "#7a6178") => div().id(id).flex_none().h(16).px(5).rounded(4).flex().items_center()
    .bg(bg).text_color("#fffaf3").cursor_pointer().hover((s) => s.opacity(0.8)).on_click(act(fn)).child(label);
  const toggle = div().id("debug-toggle").absolute().left(W - 26).top(4).size(20).rounded(6).flex().items_center().justify_center()
    .text_size(12).bg(d.open ? "#7a6178" : "#00000014").cursor_pointer().on_click(act(() => { d.open = !d.open; }))
    .child(d.open ? "✕" : "⚙️");
  if (!d.open) return [toggle];
  const cycle = (n, v) => (v + 1) % n;
  const rows = d.dolls.map((doll) => {
    const L = doll.look, id = doll.id;
    return div().flex().items_center().gap(3).children([
      div().w(30).flex_none().child(`#${id}`),
      btn(`dbg-act-${id}`, `▶ ${t(`act.${doll.action}`)}`, () => {
        doll.action = ACTIONS[(ACTIONS.indexOf(doll.action) + 1) % ACTIONS.length];
      }, "#5b8def"),
      btn(`dbg-char-${id}`, `${t("debug.char")} ${(L.char % CHARACTERS.length) + 1}`, () => { L.char = cycle(CHARACTERS.length, L.char); }, "#c27ba0"),
      btn(`dbg-colour-${id}`, t("debug.hair"), () => { L.colour = cycle(COLOURS.length, L.colour ?? 0); },
        SWATCH[COLOURS[(L.colour ?? 0) % COLOURS.length]]),
      btn(`dbg-rnd-${id}`, "🎲", () => { doll.look = randomLook(); }),
      btn(`dbg-kids-${id}`, `${t("debug.kids")} ${doll.kids ?? 0}`, () => { doll.kids = cycle(4, doll.kids ?? 0); }, "#3f9a7a"),
      btn(`dbg-remote-${id}`, `${doll.remote ? "☑" : "☐"} ${t("debug.remote")}`, () => { doll.remote = !doll.remote; }, "#8b7cf6"),
      btn(`dbg-del-${id}`, "✕", () => { d.dolls = d.dolls.filter((x) => x !== doll); }, "#e8586f"),
    ]);
  });
  const ti = Math.max(0, TIMES.indexOf(d.hour ?? null));
  const langs = Object.keys(LANGS);
  const li = langs.indexOf(getLang());
  const scenes = Object.keys(THEMES);
  const si2 = Math.max(0, scenes.indexOf(d.scene ?? scene));
  const footer = div().flex().gap(3).children([
    btn("dbg-time", t(`time.${TIMES[ti] ?? "auto"}`), () => { d.hour = TIMES[(ti + 1) % TIMES.length]; }, "#e0a050"),
    partyOn ? btn("dbg-party-end", t("debug.partyEnd"), () => { d.partyEnd = Date.now(); }, "#c27ba0")
      : btn("dbg-party", t("debug.party"), () => { d.party = Date.now(); }, "#f28daa"),
    btn("dbg-water", t("debug.water"), () => { d.water = Date.now(); }, "#7fb6ff"),
    ...(d.dolls.length < MAX ? [btn("dbg-add", t("debug.add"), () => {
      d.dolls.push({ id: d.next++, action: "idle", look: randomLook() });
    }, "#3f9a7a")] : []),
    ...(d.dolls.length ? [btn("dbg-clear", t("debug.clear"), () => { d.dolls = []; }, "#e8586f")] : []),
  ]);
  const panelW = d.debug ? 530 : 300;
  const box = div().id("debug-panel").absolute().left(Math.max(4, W - panelW - 30)).top(28).w(panelW).max_h(H - 32).p(6).rounded(8)
    .bg("#fffaf3f2").border_1().border_color("#7a6178").text_size(10).text_color("#7a6178")
    .flex().flex_col().gap(3)
    .children([
      div().font_bold().child(t("settings.title")),
      div().flex().items_center().gap(3).children([
        div().child(t("settings.lang")),
        btn("dbg-lang", `🌐 ${LANGS[getLang()]}`, () => { d.lang = langs[(li + 1) % langs.length]; }, "#5b8def"),
        div().ml(8).child(t("settings.scene")),
        btn("dbg-scene", `🏠 ${t(`scene.${scenes[si2]}`)}`, () => { d.scene = scenes[(si2 + 1) % scenes.length]; }, "#c27ba0"),
      ]),
      div().mt(4).flex().items_center().gap(3).child(
        btn("dbg-on", `${d.debug ? "☑" : "☐"} ${t("settings.debug")}`, () => { d.debug = !d.debug; if (!d.debug) clearDebug(d); }, "#7a6178")),
      ...(d.debug ? [div().font_bold().child(t("debug.title")), ...rows, footer] : []),
    ]);
  return [box, toggle];
}
