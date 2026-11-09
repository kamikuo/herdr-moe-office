// Moe Office: every agent is a coworker with a desk of their own, drawn as a girl cut from character videos (doll.js).
// Working: typing at the desk. Idle: chatting at the water cooler; after a while she takes
// turns napping on the couch, chatting, getting a drink of water and a snack at the counter. Blocked: hand up (after five minutes she cries for help). Done: cheering,
// a happy face on the screen, until you look. New agents come in the door; closed ones leave with a box.
// Sub-agents sit by their parent's desk as interns. Three finishes in five minutes and a cake
// arrives for tea time. A cat lives here. Lights go down after dark.
// Hover anyone to see what they're working on; click them to go to their terminal.
import { View, div } from "gpui-kit";
import { agents, terminals, spaces, panes, shared, run, setAgentOrder, settings } from "herdr";
import { dollSprite, warmup, frameTick, hash, castOf, setPresent, BOX, PERSON } from "./doll.js";
import * as S from "./scene.js";
import * as Debug from "./debug.js";
import { t, setLang } from "./i18n.js";

// Walking speed in scene units per ms, so a girl covers the same share of her height per step at
// any size (about 0.28 px/ms at the default 250 px block). Walks are linear: the walk cycle plays at
// one pace, so easing in and out made her feet slide at the start and the end.
const WALK_SPEED = 0.075;
const CAT_SPEED = 0.03; // about two-thirds of her length per step
const CAT_HOP = 0.1; // up onto a desk or down from it
const CAT_SIZE = 0.8; // of her art
const NAP_AFTER = 10 * 60 * 1000;
// After NAP_AFTER, a long idler takes turns: each LOUNGE_FOR she does the next thing on her
// list (where she starts on it comes from her address, so they don't all move at once).
// Naps are half of it. The couch has COUCH_SEATS; a girl it has no room for chats instead.
const LOUNGE_FOR = 3 * 60 * 1000;
const LOUNGE = ["nap", "nap", "snack", "chat", "nap", "water"];
const ALARM_AFTER = 5 * 60 * 1000;
const WATER_EVERY = 60, WATER_FOR = 3; // a water reminder at the cooler: the first WATER_FOR minutes of every hour
const WALL_GAP = 40; // units: another window goes up on the wall only if the gaps stay this wide
const WATER_KEY = "moe-office.water"; // when you last pressed "I drank it!"
const PARTY_FINISHES = 3, PARTY_WINDOW = 5 * 60 * 1000, PARTY_LENGTH = 8 * 60 * 1000;
const GRAD_BOW = 2500;
const COUCH_SEATS = 3;
const MIN_DESKS = 3;
const TICK = 110; // ms between redraws at most; sooner while she plays faster frames (frameTick)
const TERM_LINE = 500, TERM_FRESH = 130; // the working screen: ms per line; how long a new line stays empty (over one redraw)
const RESIZE_SETTLE = 250; // ms the size must hold still before the office redraws at it

const CODE = ["#9be3c9", "#ffd977", "#b9b0ff", "#ffb3c9"];
const STATUS = { working: "#7fb6ff", blocked: "#ff8a9a", done: "#79c9ad", idle: "#cbb8f0" };
const SCREEN = { working: "#3d3f6b", blocked: "#6b3b52", done: "#2f5b4f", idle: "#4a4560" };
// The sidebar's space colours (mods/my-spaces), by stored name.
const MARK = { ansi6: "#22a99a", ansi3: "#e3814f", ansi4: "#5b8def", ansi5: "#8b7cf6", ansi2: "#3fae6a", ansi1: "#d9649a" };
// Done: a happy face on the screen, cycling.
const HAPPY = ["(≧▽≦)", "(≧▽≦)♡", "ヽ(>▽<)ノ", "(*^▽^*)"];
// Stuck: a puzzled face; stuck too long: crying, the screen flashing pink.
const PUZZLED = ["(・_・?)", "(・・?)", "(°ー°〃)", "(・_・;)"];
const CRYING = ["(╥_╥)", "(T_T)", "(ToT)/", "(;_;)"];

function sky(hour) {
  if (hour < 5 || hour >= 21) return { top: "#3b3f7a", bottom: "#6a6aa8", stars: true };
  if (hour < 7) return { top: "#bcd7f5", bottom: "#ffd0b0" };
  if (hour < 17) return { top: "#a9d8ff", bottom: "#e1f2ff" };
  if (hour < 19) return { top: "#ffd6a8", bottom: "#ffb3a0" };
  return { top: "#7a6fb0", bottom: "#ff9fa8" };
}
const lightsDown = (hour) => hour >= 20 || hour < 6;

const rotate = (list, n) => list.map((_, i) => list[(i + n) % list.length]);
const remote = (address) => address.includes("/");
// Live sub-agents under `addr`, however deep.
const descendants = (all, addr) =>
  all.filter((k) => k.parent === addr && k.state === "live").flatMap((k) => [k, ...descendants(all, k.address)]);

export default class Office extends View {
  init(props, cx) {
    this.lang = props?.lang; // the layout's language: "en" (default), "zh-TW" or "ja"
    this.scene = props?.scene; // the layout's scene: "pastel" (default) or "jirai"
    this.size = { width: 1400, height: 220 };
    this.desk = {}; // address -> desk index, kept while the agent lives
    this.at = {}; // walker -> { spot, x, y, fromX, until, dur, face }
    this.seen = {}; // address -> last status
    this.idleSince = {};
    this.blockedSince = {};
    this.finishes = [];
    this.party = null;
    this.leaving = {}; // address -> true: closed agents on their way out
    this.kids = {}; // intern address -> { x, y, p } where it sat last render
    this.grads = {}; // intern address -> { x, y, p, start }
    this.away = [];
    this.hovered = null;
    this.started = false;
    this.cat = { goal: "sit", desk: null, since: Date.now() };
    this.now = new Date();
    this.debug = Debug.load();
    cx.timer.every(30000, (cx) => { this.now = new Date(); cx.notify(); });
    cx.timer.every(9000, (cx) => { if (this.wanderCat()) cx.notify(); });
  }

  // Desks are handed out lowest free first, and nobody swaps seats. Agents that closed head
  // for the door with a box, and their desk goes: the desks after it move up one, in the same
  // order (their girls walk over), so no empty desk is left in the row.
  seat(list, door, cx) {
    const live = new Set(list.map((a) => a.address));
    let gone = false;
    for (const k of Object.keys(this.desk)) {
      if (live.has(k)) continue;
      const at = this.at[k];
      if (this.started && at && this.seen[k]) {
        this.leaving[k] = true;
        this.walk(`leave:${k}`, "door", door.x, door.y, WALK_SPEED, cx, at);
      }
      delete this.desk[k]; delete this.at[k]; delete this.idleSince[k]; delete this.blockedSince[k]; delete this.seen[k];
      gone = true;
    }
    if (gone) Object.entries(this.desk).sort((a, b) => a[1] - b[1]).forEach(([k], i) => { this.desk[k] = i; });
    const taken = new Set(Object.values(this.desk));
    for (const a of list) {
      if (a.address in this.desk) continue;
      let i = 0;
      while (taken.has(i)) i++;
      this.desk[a.address] = i;
      taken.add(i);
    }
  }

  // Since-when for idle and blocked, and finishes for the pizza.
  track(list, now, cx) {
    const changed = {};
    for (const s of spaces()) for (const t of s.tabs ?? []) changed[t.id] = t.changed_at;
    for (const a of list) {
      const was = this.seen[a.address];
      if (a.status !== "idle") delete this.idleSince[a.address];
      else this.idleSince[a.address] ??= changed[a.tab] ?? now;
      if (a.status !== "blocked") delete this.blockedSince[a.address];
      else this.blockedSince[a.address] ??= was === "blocked" || !was ? (changed[a.tab] ?? now) : now;
      if (this.started && a.status === "done" && was && was !== "done" && !a.debug) this.finishes.push(now);
      this.seen[a.address] = a.status;
    }
    this.finishes = this.finishes.filter((t) => now - t < PARTY_WINDOW);
    if (!this.party && this.finishes.length >= PARTY_FINISHES) this.startParty(now, cx);
  }

  // Tea time: a courier brings a cake to the counter and everyone idle gathers there.
  startParty(now, cx, debug = false) {
    const party = (this.party = { start: now, debug });
    this.finishes = [];
    delete this.at.courier;
    cx.timer.after(PARTY_LENGTH + 50, (cx) => { if (this.party === party) { this.party = null; cx.notify(); } });
  }

  // Whether a debug-panel button stamped `this.debug[name]` since the last render.
  pressed(name) {
    this.seen ??= {};
    const v = this.debug[name] ?? null;
    const was = this.seen[name];
    this.seen[name] = v;
    return was !== undefined && v !== null && v !== was;
  }

  // Starts a walk when a walker's spot changes; returns where it is (or is heading).
  // `start`: where a new walker appears (the door), instead of at its spot.
  walk(key, spot, x, y, speed, cx, start) {
    const now = Date.now();
    const fresh = !this.at[key] && Boolean(start);
    const at = this.at[key] ?? (start ? { ...start, spot: null } : null);
    if (!at) return (this.at[key] = { spot, x, y, fromX: x, until: 0, dur: 1 });
    if (at.spot === spot && at.x === x && at.y === y) return at;
    const dur = Math.max(400, Math.hypot(x - at.x, y - at.y) / (speed * this.g.U));
    this.at[key] = { spot, x, y, fromX: at.x, fromY: at.y, until: now + dur, dur, face: at.face };
    if (spot === "door" || fresh) this.doorUntil = Math.max(this.doorUntil ?? 0, now + dur);
    cx.timer.after(dur + 30, (cx) => cx.notify());
    return this.at[key];
  }

  // Where everything goes, in px. U: px per scene unit, from the view's height.
  // Left to right: a plant and the door in the left corner, the lounge (couch, water cooler,
  // counter), the desks, and a bookshelf in the right corner. Visitors coming in meet the couch
  // first. The plant, the door and the bookshelf stay in the corners; the room in between is
  // shared out: the lounge's gaps widen a little (up to 6 units each), the desks spread a
  // little (up to 6 units more apart), and the rest goes evenly on both sides of the desks, so
  // the desks sit in the middle. So resizing stretches everything smoothly.
  geometry(W, H, deskCount) {
    const U = Math.max(2, Math.min(6, H / 68));
    const floorY = H - Math.max(26, 7 * U);
    const wallBottom = floorY - 14 * U;
    const slot = S.SLOT * U;
    const w = (id) => S.artW(id, U);
    const plantL = 3 * U;
    const doorX = plantL + w("plant") + 2 * U;
    const shelfW = w("bookshelf");
    const shelfX0 = W - 3 * U - shelfW;
    const loungeStart = doorX + w("door") + 5 * U; // the couch, with no extra room
    const loungeW = w("couch") + 6 * U + w("cooler") + 6 * U + w("counter");
    const room = shelfX0 - 4 * U - (loungeStart + loungeW + 8 * U); // for the desks and any extra
    // As many desks in the front row as fit; the rest go in a second row behind.
    const FRONT_ROW = Math.max(3, Math.floor(room / slot));
    const front = Math.min(deskCount, FRONT_ROW);
    const back = Math.max(0, deskCount - FRONT_ROW);
    const cols = Math.max(front, back);
    const groupW = (pitch) => Math.max(front ? (front - 1) * pitch + slot : 0, back ? (back - 1) * pitch + pitch / 2 + slot : 0);
    let extra = Math.max(0, room - groupW(slot));
    const lounge = Math.min(extra * 0.06, 6 * U); // added to each of the lounge's three gaps
    extra -= 3 * lounge;
    const spread = cols > 1 ? Math.min((extra * 0.5) / (cols - 1), 6 * U) : 0; // added between desks
    const pitch = slot + spread;
    extra = Math.max(0, room - 3 * lounge - groupW(pitch));
    const couchX = loungeStart + lounge;
    const coolerX = couchX + w("couch") + 6 * U + lounge;
    const zoneX = coolerX + w("cooler") + 6 * U + lounge; // the counter
    const x0 = zoneX + w("counter") + 8 * U + extra / 2;
    const desksW = groupW(pitch);
    const deskPos = (i) => i < FRONT_ROW
      ? { x: x0 + i * pitch, y: floorY, back: false }
      : { x: x0 + (i - FRONT_ROW) * pitch + pitch / 2, y: floorY - 10 * U, back: true };
    return {
      U, floorY, wallBottom, slot, pitch, cols: front, x0, desksW, deskPos, zoneX, coolerX, couchX, doorX, plantL,
      shelfX: Math.max(shelfX0, x0 + desksW + 4 * U),
      door: { x: doorX + 0.5 * U, y: wallBottom + 2 * U },
    };
  }

  // The cat's next stop: a nap on an empty desk, a sit or a nap (half the time) up on a cat
  // shelf on the wall or on top of the bookshelf (perch -1), or a sit somewhere on the floor. Naps last at least a
  // minute, perches half a minute.
  wanderCat() {
    const g = this.g;
    if (!g) return false;
    const c = this.cat, age = Date.now() - c.since;
    if (c.goal === "sleep" && this.away.includes(c.desk) && age < 60000) return false;
    if (c.goal === "perch" && age < 30000) return false;
    const r = Math.random(), perches = (this.catShelves ?? []).length;
    if (this.away.length && r < 0.35) {
      this.cat = { goal: "sleep", desk: this.away[Math.floor(Math.random() * this.away.length)], since: Date.now() };
    } else if (r < 0.7) {
      this.cat = { goal: "perch", perch: Math.floor(Math.random() * (perches + 1)) - 1, nap: Math.random() < 0.5, since: Date.now() };
    } else {
      const from = g.doorX + S.artW("door", g.U), span = g.shelfX - from - S.CAT_W * g.U;
      this.cat = { goal: "sit", desk: null, x: Math.round(from + Math.random() * span), since: Date.now() };
    }
    return true;
  }

  render(cx) {
    if (!this.ticking) { this.ticking = true; cx.timer.after(frameTick(TICK), (cx) => { this.ticking = false; cx.notify(); }); }
    setLang(this.debug.lang ?? this.lang); // the ⚙️ panel's choice, else the layout's
    S.setTheme(this.debug.scene ?? this.scene); // likewise the scene
    const { width: W, height: H } = this.size;
    const list = agents();
    const all = terminals();
    const now = Date.now();
    const allFakes = Debug.fakes(this.debug, now);
    setPresent([...list, ...allFakes].map((a) => a.address));
    const fakes = allFakes.filter((f) => !f.remote);
    // Agents on other machines are working from home: they're on the video call.
    const here = [...list.filter((a) => !remote(a.address)), ...fakes];
    const callers = [...list.filter((a) => remote(a.address)), ...allFakes.filter((f) => f.remote)];
    // Fake coworkers' sub-agents, shaped like terminals.
    all.push(...Debug.fakeKids(this.debug));
    this.live = new Set(all.filter((k) => k.state === "live").map((k) => k.address));
    // The debug panel's tea-time button.
    // The debug panel's tea-time buttons (a press is a new timestamp; the first render only
    // takes note, so a reload doesn't press them again).
    if (this.pressed("party") && !this.party) this.startParty(now, cx, true);
    if (!this.debug.debug && this.party?.debug) this.party = null; // debug mode turned off
    if (this.pressed("partyEnd")) this.party = null;
    setAgentOrder(list.map((a) => a.address));

    const deskCount = Math.max(MIN_DESKS, here.length, ...Object.values(this.desk).map((i) => i + 1));
    const g = (this.g = this.geometry(W, H, deskCount));
    const U = g.U;
    this.seat(here, g.door, cx);
    this.track(here, now, cx);
    for (const f of fakes) {
      if (f.status === "idle") this.idleSince[f.address] = f.action === "sleep" ? 0 : now;
      else delete this.idleSince[f.address];
      if (f.status === "blocked") this.blockedSince[f.address] = f.action === "alarm" ? 0 : now;
      else delete this.blockedSince[f.address];
    }
    const byDesk = {};
    for (const a of here) byDesk[this.desk[a.address]] = a;
    const tabs = {};
    for (const s of spaces()) for (const t of s.tabs ?? []) tabs[t.id] = t;
    const branches = {};
    for (const p of panes()) branches[p.pane] = p.branch;

    // The pizza: the courier walks in, leaves it on the counter, and walks out.
    const party = this.party;
    const counter = { x: g.zoneX + 8 * U, y: g.floorY };
    const courierTrip = party ? Math.max(400, Math.hypot(counter.x - g.door.x, counter.y - g.door.y) / (WALK_SPEED * U)) : 0;
    const pizzaHere = party && now >= party.start + courierTrip;

    // What each idler is doing: chatting at the cooler at first; after NAP_AFTER, her turn on
    // the LOUNGE list (a debug "sleep" coworker always naps). At tea time everyone's at the cake.
    const idle = here.filter((a) => a.status === "idle").sort((a, b) => this.idleSince[a.address] - this.idleSince[b.address]);
    const doing = (a) => {
      if (pizzaHere) return "pizza";
      if (a.debug && a.action === "sleep") return "nap";
      const long = now - this.idleSince[a.address] - NAP_AFTER;
      return long < 0 ? "chat" : LOUNGE[(Math.floor(long / LOUNGE_FOR) + hash(a.address)) % LOUNGE.length];
    };
    const nappers = idle.filter((a) => doing(a) === "nap").slice(0, COUCH_SEATS);
    const place = {};
    nappers.forEach((a, k) => { place[a.address] = { spot: "couch", x: g.couchX + (k * 10 + 1) * U, y: g.floorY, face: 1 }; });
    // The rest gather around the cooler (chatting or drinking) or the counter (a snack, or the
    // cake), alternating sides, further out each pair.
    const cooler = { left: g.coolerX - (PERSON - 2) * U, right: g.coolerX + S.artW("cooler", U) - 2 * U };
    const bar = { left: g.zoneX - 6 * U, right: g.zoneX + S.artW("counter", U) - 6 * U };
    const gather = (list, hub, spotOf) => list.forEach((a, k) => {
      const left = k % 2 === 0;
      const ring = Math.floor(k / 2) * 9 * U;
      place[a.address] = { spot: spotOf(a), x: left ? hub.left - ring : hub.right + ring, y: g.floorY, face: left ? 1 : -1 };
    });
    const rest = idle.filter((a) => !nappers.includes(a));
    const atCounter = (a) => ["pizza", "snack"].includes(doing(a));
    gather(rest.filter((a) => !atCounter(a)), cooler, (a) => (doing(a) === "water" ? "water" : "cooler"));
    gather(rest.filter(atCounter), bar, doing);
    for (const a of here) {
      const d = g.deskPos(this.desk[a.address]);
      place[a.address] ??= { spot: "desk", x: d.x, y: d.y, face: 1 };
    }
    this.away = here.filter((a) => place[a.address].spot !== "desk").map((a) => this.desk[a.address]);
    if (this.cat.goal === "sleep" && !this.away.includes(this.cat.desk)) this.wanderCat();

    const alarmed = here.filter((a) => a.status === "blocked" && now - (this.blockedSince[a.address] ?? now) > ALARM_AFTER);
    const people = here.map((a) => {
      const p = place[a.address];
      const at = this.walk(a.address, p.spot, p.x, p.y, WALK_SPEED, cx, this.started ? g.door : null);
      // Typing at the desk: drawn between the chair and the desk front.
      const seated = p.spot === "desk" && a.status === "working" && now >= at.until;
      return { y: p.y, seated, el: this.person(a, at, g, p.face, tabs[a.tab], alarmed.includes(a)) };
    });
    const row = (back, seated) => people.filter((p) => (p.y < g.floorY) === back && p.seated === seated).map((p) => p.el);
    const desks = Array.from({ length: deskCount }, (_, i) => {
      const pos = g.deskPos(i);
      const a = byDesk[i];
      return { back: pos.back, chair: S.art("chair", pos.x + S.DESK.chair * U, pos.y, U),
        el: this.deskAt(i, pos, g, a, Boolean(a) && alarmed.includes(a)) };
    });
    const deskRow = (back) => desks.filter((d) => d.back === back);

    const hour = this.debug.hour ?? this.now.getHours(); // the debug panel can force the time of day
    const hovered = here.find((a) => a.address === this.hovered);
    this.started = true;

    return div().id("office").size_full().relative().overflow_hidden().bg(S.FLOOR)
      // Sizes come in screen px; what we draw is scaled by the app's zoom. While the block is
      // being dragged to a new size, keep drawing at the old size and redraw once it has stayed
      // put for RESIZE_SETTLE ms: every new size means new scales for every picture (and the
      // girls' frames loading again), which made dragging jerky.
      .on_size_change((size, cx) => {
        const z = settings().zoom || 1;
        const next = { width: size.width / z, height: size.height / z };
        if (next.width === W && next.height === H) { this.nextSize = null; return; }
        const first = !this.sized;
        this.sized = true;
        if (first) { this.size = next; cx.notify(); return; }
        this.nextSize = next;
        this.resizedAt = Date.now();
        cx.timer.after(RESIZE_SETTLE, (cx) => {
          if (!this.nextSize || Date.now() - this.resizedAt < RESIZE_SETTLE - 10) return;
          this.size = this.nextSize;
          this.nextSize = null;
          cx.notify();
        });
      })
      .children([
        ...warmup(), // under the room: loads every frame before she needs it
        ...S.room(W, H, g.wallBottom, U),
        ...this.wall(W, g, sky(hour), list, callers, all, now),
        S.art("rug", g.couchX - 2 * U, g.floorY + 2 * U, U),
        ...deskRow(true).map((d) => d.chair), ...row(true, true), ...deskRow(true).map((d) => d.el), ...row(true, false),
        ...this.props(g, pizzaHere),
        ...deskRow(false).map((d) => d.chair), ...row(false, true), ...deskRow(false).map((d) => d.el),
        ...here.flatMap((a) => this.interns(a, descendants(all, a.address), g)),
        ...this.graduates(g, now, cx),
        ...row(false, false),
        ...this.leavers(g, now),
        ...(party ? [this.courier(party, counter, courierTrip, g, now, cx)] : []),
        this.kitty(g, cx),
        ...(lightsDown(hour) ? this.night(W, H, g, byDesk, deskCount, alarmed) : []),
        ...(this.waterTime(now) ? [this.water(g)] : []),
        ...(hovered && this.at[hovered.address] ? [this.thought(hovered, this.at[hovered.address], g, branches[hovered.pane])] : []),
        ...(here.length ? [] : [this.sign(W, g)]),
        ...Debug.panel(this.debug, W, H, this.scene, Boolean(this.party)),
      ]);
  }

  // Along the wall, clear of the door and the kitchen: a window every third spot, the clock
  // halfway between the first two, and the remote call (when there is one) after the second.
  wall(W, g, sk, list, callers, all, now) {
    const { U, wallBottom, zoneX } = g;
    const top = 8 * U;
    const els = [];
    const remotes = callers.map((a) => ({
      address: a.address, pane: a.debug ? null : a.pane, machine: a.debug ? "debug" : a.address.split("/")[0],
      name: a.space_name, status: a.status, title: a.title || a.tab_name || a.space_name,
    }));
    // Along the wall, from the door to the bookshelf, evenly spaced: a window, the calendar,
    // the clock, a window, the board, the video call (when there are remote agents), then more
    // windows while the gaps stay at least WALL_GAP wide.
    const cU = U * 0.8; // the clock and calendar are a little smaller than the rest, side by side at one height
    const clockY = top + (S.ART.window.h * U - S.ART.clock.h * cU) / 2 - 3 * U;
    const winW = S.artW("window", U), boardW = 44 * U;
    const calls = Math.min(3, remotes.length);
    const real = list.filter((a) => !a.debug);
    const count = (st) => real.filter((a) => a.status === st).length;
    const napping = real.filter((a) => this.at[a.address]?.spot === "couch").length;
    const interns = real.reduce((n, a) => n + descendants(all, a.address).length, 0);
    const items = [
      { w: winW, window: true },
      { w: S.artW("calendar", cU), draw: (x) => S.calendar(x, clockY, cU, this.now, t("months")[this.now.getMonth()], t("weekdays")[this.now.getDay()]) },
      { w: S.artW("clock", cU), draw: (x) => S.clock(x, clockY, cU, this.now) },
      { w: winW, window: true },
      { w: boardW, draw: (x) => S.board(x, top + 6 * U, U, [
        [STATUS.working, t("board.working"), count("working")],
        [STATUS.done, t("board.done"), count("done")],
        [STATUS.blocked, t("board.blocked"), count("blocked")],
        ["#ffd977", t("board.idle"), count("idle") - napping],
        ["#a993dc", t("board.nap"), napping, napping > 0],
        ["#79c9ad", t("board.interns"), interns, interns > 0],
        ["#f28daa", t("board.pizza"), "🍰", Boolean(this.party)],
      ]) },
      ...(calls ? [{ w: calls * 13 * U + (calls - 1) * U + 2 * U, draw: (x) => S.videoWall(x, top, U, remotes) }] : []),
    ];
    const from = g.doorX + S.artW("door", U) + 4 * U, to = g.shelfX - 4 * U;
    const gapOf = (list) => (to - from - list.reduce((n, it) => n + it.w, 0)) / (list.length + 1);
    while (gapOf([...items, { w: winW }]) >= WALL_GAP * U) items.push({ w: winW, window: true });
    const gap = Math.max(2 * U, gapOf(items));
    let x = from + gap;
    for (const it of items) { it.x = x; x += it.w + gap; }
    // One sun (or moon) for the whole view, in the second window.
    const wins = items.filter((it) => it.window);
    const sunX = (wins[1] ?? wins[0]).x + 17 * U;
    for (const it of items) els.push(it.window ? S.window_(it.x, top, U, sk, sunX) : it.draw(it.x));
    // Three cat shelves, in the gaps between them when there's room: the first gap (by the
    // door), the middle one and the last (by the bookshelf), the middle one higher. `y`: the
    // plank's top, where her feet go.
    const shelfW = S.artW("catshelf", U);
    this.catShelves = [];
    if (gap >= shelfW + 4 * U) {
      const starts = [from, ...items.map((it) => it.x + it.w)];
      const picks = [...new Set([0, Math.round((starts.length - 1) / 2), starts.length - 1])];
      picks.map((i) => starts[i]).forEach((x0, i) => {
        const y = top + (i === 1 ? 14 : 20) * U; // above the girls' heads
        this.catShelves.push({ x: x0 + (gap - shelfW) / 2, y: y + 0.6 * U });
        els.push(S.art("catshelf", x0 + (gap - shelfW) / 2, y + S.ART.catshelf.h * U, U));
      });
    }
    els.push(S.door(g.doorX, wallBottom, U, now < (this.doorUntil ?? 0)));
    return els;
  }

  props(g, pizzaHere) {
    const { U, floorY, zoneX } = g;
    return [
      S.art("counter", zoneX, floorY, U),
      ...(pizzaHere ? [S.art("cake", zoneX + 10.5 * U, floorY - S.COUNTER_TOP * U + 0.4 * U, U)] : []),
      S.art("cooler", g.coolerX, floorY, U),
      S.art("couch", g.couchX, floorY, U),
      S.art("bookshelf", g.shelfX, floorY, U),
      S.art("plant", g.plantL, floorY, U),
    ];
  }

  // The water reminder: for the first few minutes of every hour (or from the debug panel).
  // "I drank it!" hides it until the next one (kept in localStorage, so a restart remembers).
  waterTime(now) {
    let drank = 0;
    try { drank = Number(localStorage.getItem(WATER_KEY)) || 0; } catch {}
    const d = new Date(now);
    const hourly = d.getMinutes() % WATER_EVERY < WATER_FOR && drank < now - d.getMinutes() * 60000 - d.getSeconds() * 1000;
    const forced = now - (this.debug.water ?? 0) < WATER_FOR * 60000 && drank < this.debug.water;
    return hourly || forced;
  }

  water(g) {
    const U = g.U;
    const drank = (_e, cx) => { try { localStorage.setItem(WATER_KEY, String(Date.now())); } catch {} cx.notify(); };
    return div().absolute().left(g.coolerX - 10 * U).top(g.floorY - 34 * U).px(8).py(4).gap(8).rounded(10).flex().items_center()
      .bg("#eaf6ff").border_2().border_color("#7fb6ff").text_size(Math.max(10, 2.6 * U)).font_bold().text_color("#3b6fb0")
      .whitespace_nowrap().loop("top", { from: g.floorY - 34 * U, to: g.floorY - 35.5 * U, period: 1400 })
      .child(t("water"))
      .child(div().id("water-done").px(8).py(2).rounded(8).bg("#7fb6ff").text_color("#ffffff").cursor_pointer()
        .hover((s) => s.opacity(0.85)).on_click(drank).child(t("waterDone")));
  }

  sign(W, g) {
    return div().absolute().left(W / 2 - 150).top(g.wallBottom - 30).w(300).py(4).rounded(10).bg("#7a617844")
      .text_size(11).text_color("#fffaf3").flex().justify_center().child(t("empty"));
  }

  // A desk front with its monitor, her desk things (a lamp on an empty desk), and the name tag
  // of whoever sits there under it. The chair is drawn separately, behind the doll.
  deskAt(i, pos, g, a, alarmed) {
    const U = g.U;
    const st = a?.status;
    const away = Boolean(a) && this.at[a.address]?.spot !== "desk";
    const H = 34 * U; // the desk's box: from 34 units above the floor down to the floor
    const y = (h) => H - h * U; // px from the box top, for a height above the floor
    const deskTop = 12.6;
    const at = (id, x, h) => S.art(id, x * U, y(h), U);
    const [sx, sy, sw, sh] = S.DESK.screen;
    const monTop = y(deskTop + 13);
    return div().id(`desk-${i}`).absolute().left(pos.x).top(pos.y - H).w(S.SLOT * U).h(H + 28)
      .when(Boolean(a) && !a.debug, (el) => el.cursor_pointer().on_click(() => run("pane.focus", { pane: a.pane })))
      .children([
        this.screen(away ? "idle" : st, !a || away, U, `d${i}`, alarmed).absolute().left(sx * U).top(monTop + sy * U).w(sw * U).h(sh * U),
        at("monitor", S.DESK.monitor, deskTop),
        a ? at(`set_${castOf(a.address)}`, S.DESK.set, deskTop) : at("lamp", S.DESK.lamp, deskTop),
        at("desk", S.DESK.x, 0),
        ...(a ? [this.plate(a, U, alarmed).absolute().left(6 * U).top(pos.back ? y(31) : H + 5)] : []),
      ]);
  }

  // A desk's screen. `key` keeps each screen's lines apart (their ids must be unique).
  screen(st, screensaver, U, key, alarmed = false) {
    return div().overflow_hidden().rounded(U * 0.6).bg(SCREEN[st] ?? SCREEN.idle)
      .when(st === "working", (el) => el.child(this.terminal(U, key)))
      // A face on the screen; a loop on the screen itself would make it see-through, so the
      // pink flash is a layer of its own.
      .when(st === "blocked", (el) => el.flex().items_center().justify_center().text_size(Math.max(9, 2.6 * U)).font_bold()
        .when(alarmed, (el) => el.child(div().absolute().left(0).top(0).size_full().bg("#ff6b88").loop("opacity", { from: 0.15, to: 0.85, period: 500 })))
        .child(div().text_color(alarmed ? "#ffffff" : "#ff8a9a").frames(alarmed ? CRYING : PUZZLED, alarmed ? 450 : 900)))
      .when(st === "done", (el) => el.flex().items_center().justify_center().text_size(Math.max(9, 2.6 * U)).font_bold().text_color("#ffe08a")
        .child(div().frames(HAPPY, 600))
        .children([[1, 1, "♡"], [8.2, 4.6, "♡"], [8.6, 0.8, "✦"]].map(([hx, hy, c], k) => div().absolute().left(hx * U).top(hy * U)
          .text_size(Math.max(7, 1.8 * U)).text_color("#ffb3c9").child(c).loop("opacity", { from: 0.2, to: 1, period: 700 + k * 230 }))))
      .when(screensaver && st !== "blocked" && st !== "done", (el) => el.child(div().absolute().top(U * 2.6).text_size(Math.max(9, 2.6 * U))
        .text_color("#ffb3c9").child("♡").loop("left", { from: U, to: U * 7.5, period: 5000 })));
  }

  // Working: a terminal filling up. Four lines from the left edge, random lengths; the bottom
  // one types itself out left to right, then everything scrolls up a line and a new one
  // starts. Lines keep their ids so the scroll and the typing are native transitions.
  terminal(U, key) {
    const salt = hash(key);
    const period = TERM_LINE + (salt % 250); // ms per line, a little different on each desk
    const t = Date.now() + salt;
    const n = Math.floor(t / period); // the line being typed
    const fresh = t % period < TERM_FRESH; // just started: draw it empty, then let it grow
    const lineH = 1.5 * U, maxW = 8.6 * U;
    const lines = [];
    for (let j = n - 4; j <= n; j++) {
      const r = hash(`${key}:${j}`);
      const w = j === n && fresh ? 0 : maxW * (0.3 + (r % 1000) / 1000 * 0.7);
      lines.push(div().id(`term-${key}-${j}`).absolute().left(0).top(0.2 * U + (j - n + 3) * lineH).h(0.8 * U).rounded(U)
        .bg(CODE[r % CODE.length]).w(w)
        .transition("top", { duration: 180, easing: "ease-out" })
        .transition("width", { duration: Math.round(period * 0.55), easing: "linear" }));
    }
    return div().absolute().left(U).top(0.8 * U).w(maxW).h(4 * lineH + 0.2 * U).overflow_hidden().children(lines);
  }

  // The space's colour, as in the sidebar (Herdr shares the colours, not the icons).
  spaceTile(id) {
    const c = (shared("space.colors") ?? {})[id] ?? "ansi6";
    return div().size(12).flex_none().rounded(3).bg(c.startsWith("#") ? c : MARK[c] ?? "#22a99a");
  }

  // Her name tag, under the desk (over it in the back row). Flashes pink when she's been stuck
  // too long.
  plate(a, U, alarmed) {
    const focused = a.focused;
    return div().max_w((S.SLOT - 8) * U).h(16).px(5).gap(4).rounded(8).flex().items_center()
      .bg(focused ? "#fffaf3" : "#7a617855").text_size(10).text_color(focused ? "#7a6178" : "#fffaf3")
      .when(alarmed, (el) => el.bg("#ff6b88").loop("opacity", { from: 0.55, to: 1, period: 450 }))
      .when(!a.debug, (el) => el.child(this.spaceTile(a.space)))
      .child(div().truncate().child(a.space_name + (a.tab_name ? ` · ${a.tab_name}` : "")));
  }

  // Sub-agents: small dolls on stools in front of their parent's desk, laptops on their laps.
  interns(a, kids, g) {
    if (!kids.length) return [];
    const U = g.U;
    const p = U * 0.62;
    const pos = g.deskPos(this.desk[a.address]);
    const x0 = pos.x + 22 * U;
    const shown = kids.slice(0, 3);
    const els = shown.map((k, i) => {
      const x = x0 + i * 9 * U;
      this.kids[k.address] = { x, y: pos.y, p };
      const busy = k.status === "working";
      const stuck = k.status === "blocked" || k.status === "error";
      return div().id(`intern-${k.address}`).absolute().left(x).top(pos.y - BOX * p).w(PERSON * p).h(BOX * p)
        .cursor_pointer().on_click(() => run("terminal.peek", { terminal: k.address }))
        .children([
          S.art("stool", 5 * p, BOX * p, p),
          dollSprite(k.address, busy ? "typing" : "idle", 1, p, hash(k.address), busy ? 10 : 8),
          ...(busy ? [S.art("laptop", 13 * p, BOX * p - 9 * p, p)] : []),
          ...(stuck ? [this.bubble(-6, "#e8586f", p).child("!").loop("opacity", { from: 0.5, to: 1, period: 700 })] : []),
        ]);
    });
    if (kids.length > shown.length)
      els.push(div().absolute().left(x0 + 27 * U).top(pos.y - 14 * U).px(4).rounded(6).bg("#7a617866")
        .text_size(10).text_color("#fffaf3").child(`+${kids.length - shown.length}`));
    return els;
  }

  // Interns that finished: a bow where they sat, then out the door.
  graduates(g, now, cx) {
    const live = this.live;
    for (const [k, info] of Object.entries(this.kids)) {
      if (live.has(k)) continue;
      delete this.kids[k];
      if (!this.started) continue;
      this.grads[k] = { ...info, start: now };
      cx.timer.after(GRAD_BOW + 20, (cx) => cx.notify());
    }
    return Object.entries(this.grads).flatMap(([k, gr]) => {
      const box = (el, x, y) => div().id(`grad-${k}`).absolute().left(x).top(y - BOX * gr.p).w(PERSON * gr.p).h(BOX * gr.p).child(el);
      if (now < gr.start + GRAD_BOW)
        return [box(dollSprite(k, "cheer", -1, gr.p, hash(k)), gr.x, gr.y).child(this.bubble(-8, "#7a6178", gr.p).child(t("thanks")))];
      const at = this.walk(`grad:${k}`, "door", g.door.x, g.door.y, WALK_SPEED, cx, { x: gr.x, y: gr.y });
      if (now >= at.until && at.until > 0) { delete this.grads[k]; delete this.at[`grad:${k}`]; return []; }
      return [box(dollSprite(k, "walk", -1, gr.p, hash(k)), at.x, at.y)
        .transition("left", { duration: at.dur, easing: "linear" }).transition("top", { duration: at.dur, easing: "linear" })];
    });
  }

  // A walking doll carrying something (`thing`: an ART id held at the chest).
  carrier(address, face, U, thing) {
    const a = S.ART[thing];
    const x = face < 0 ? (PERSON / 2 - 4 - a.w / 2) * U : (PERSON / 2 + 4 - a.w / 2) * U;
    return div().absolute().size_full().children([
      dollSprite(address, "walk", face, U, hash(address)),
      S.art(thing, x, (BOX - 11) * U, U),
    ]);
  }

  // Closed agents carrying their box out.
  leavers(g, now) {
    return Object.keys(this.leaving).flatMap((k) => {
      const at = this.at[`leave:${k}`];
      if (!at || now >= at.until) { delete this.leaving[k]; delete this.at[`leave:${k}`]; return []; }
      return [div().id(`leave-${k}`).absolute().left(at.x).top(at.y - BOX * g.U).w(PERSON * g.U).h(BOX * g.U)
        .transition("left", { duration: at.dur, easing: "linear" }).transition("top", { duration: at.dur, easing: "linear" })
        .child(this.carrier(k, Math.sign(at.x - at.fromX) || -1, g.U, "box"))];
    });
  }

  courier(party, counter, trip, g, now, cx) {
    const stay = 2500;
    const leaving = now >= party.start + trip + stay;
    if (now >= party.start + 2 * trip + stay + 100) return div();
    if (!leaving) cx.timer.after(party.start + trip + stay - now + 20, (cx) => cx.notify());
    const goal = leaving ? g.door : counter;
    const at = this.walk("courier", leaving ? "door" : "counter", goal.x, goal.y, WALK_SPEED, cx, g.door);
    const walking = now < at.until;
    const face = walking ? Math.sign(at.x - at.fromX) || 1 : 1;
    const body = walking
      ? (leaving ? dollSprite("courier", "walk", face, g.U) : this.carrier("courier", face, g.U, "cakeCarry"))
      : dollSprite("courier", "cheer", 1, g.U);
    return div().id("courier").absolute().left(at.x).top(at.y - BOX * g.U).w(PERSON * g.U).h(BOX * g.U)
      .transition("left", { duration: at.dur, easing: "linear" }).transition("top", { duration: at.dur, easing: "linear" })
      .child(body).when(!walking, (el) => el.child(this.bubble(-6, "#f28daa", g.U).child(t("pizzaHere"))));
  }

  person(a, at, g, placeFace, tab, alarmed) {
    const U = g.U;
    const napping = at.spot === "couch";
    const walking = Date.now() < at.until;
    const face = walking ? Math.sign(at.x - at.fromX) || 1 : placeFace;
    at.face = face;
    const st = a.status;
    const salt = hash(a.address);
    const doll = (name, f = 1, x = 8) => dollSprite(a.address, name, f, U, salt, x);
    const wrap = (el, bob) => div().absolute().size_full().child(el).when(Boolean(bob), (d) => d.loop("top", bob));
    let body;
    if (walking) body = doll("walk", face);
    else if (["cooler", "water", "pizza", "snack"].includes(at.spot)) body = doll("idle", face);
    else if (napping) body = doll("sleep");
    else if (st === "working") body = doll("typing", 1, 10); else if (alarmed) body = wrap(doll("blocked"), { from: 0, to: -4, period: 420 });
    else if (st === "done") body = doll("cheer");
    else body = doll("blocked");

    const top = -2 * U;
    const n = salt % 997;
    let bubble = null;
    if (walking) bubble = null;
    else if (at.spot === "pizza") bubble = this.bubble(top, "#f28daa", U).frames(rotate(t("pizzaChat"), n % t("pizzaChat").length), 1800 + (n % 900));
    else if (at.spot === "snack") bubble = this.bubble(top, "#f28daa", U).frames(rotate(t("snack"), n % t("snack").length), 2000 + (n % 1200));
    else if (at.spot === "water") bubble = this.bubble(top, "#6fb3e0", U).frames(rotate(t("sip"), n % t("sip").length), 2000 + (n % 1200));
    else if (at.spot === "cooler") bubble = this.bubble(top, "#7a6178", U).frames(rotate(t("chat"), n % t("chat").length), 2200 + (n % 1500));
    else if (napping) bubble = this.bubble(top + 4 * U, "#a993dc", U).frames(["z", "zZ", "zZz", "zZ"], 900);
    else if (alarmed) bubble = this.bubble(top - 6, "#e8586f", U).h(22).px(9).text_size(14).child(`😭 ${t("help")}`).loop("opacity", { from: 0.6, to: 1, period: 400 });
    else if (st === "blocked") bubble = this.bubble(top, "#e8586f", U).child("!").loop("opacity", { from: 0.5, to: 1, period: 700 });
    else if (st === "done") bubble = this.bubble(top, "#f06b97", U).child("♡");

    return div().id(`person-${a.address}`).absolute().left(at.x).top(at.y - BOX * U).w(PERSON * U).h(BOX * U)
      .transition("left", { duration: at.dur, easing: "linear" })
      .transition("top", { duration: at.dur, easing: "linear" })
      .when(!a.debug, (el) => el.cursor_pointer().on_click(() => run("pane.focus", { pane: a.pane })))
      .on_hover((h, cx) => {
        if (h) this.hovered = a.address;
        else if (this.hovered === a.address) this.hovered = null;
        cx.notify();
      })
      .children([body, ...(bubble ? [bubble] : [])]);
  }

  // What they're working on, in a thought cloud over their head, with the git branch.
  thought(a, at, g, branch) {
    const U = g.U;
    const text = (a.title || a.tab_name || a.program?.name || t("thinking")).replace(/\s+/g, " ").trim();
    const x = at.x + 8 * U;
    const y = at.y - 30 * U;
    return div().absolute().left(Math.max(4, x - 20)).top(Math.max(2, y - 44))
      .child(div().max_w(260).px(8).py(4).rounded(12).bg("#ffffff").border_1().border_color(S.INK)
        .text_size(10).text_color(S.INK).child(div().truncate().child(`💭 ${text}`))
        .when(Boolean(branch), (el) => el.child(div().truncate().text_size(9).opacity(0.75).child(`⎇ ${branch}`))))
      .child(div().absolute().left(16).top(26).size(7).rounded_full().bg("#ffffff").border_1().border_color(S.INK))
      .child(div().absolute().left(22).top(35).size(4).rounded_full().bg("#ffffff").border_1().border_color(S.INK));
  }

  kitty(g, cx) {
    const U = g.U;
    const c = this.cat;
    const onDesk = c.goal === "sleep";
    const pos = onDesk ? g.deskPos(c.desk) : null;
    // A perch: a cat shelf on the wall, or (-1, or a shelf that's gone after a resize) the top
    // of the bookshelf.
    const shelf = c.goal === "perch" ? (this.catShelves ?? [])[c.perch] : null;
    const napping = onDesk || (c.goal === "perch" && c.nap);
    const onBooks = c.goal === "perch" && !shelf;
    const x = onDesk ? pos.x + 12 * U : shelf ? shelf.x : onBooks ? g.shelfX : (c.x ?? g.couchX - 12 * U);
    const y = onDesk ? pos.y - 12.6 * U : shelf ? shelf.y : onBooks ? g.floorY - S.ART.bookshelf.h * U : g.floorY;
    // She doesn't fly: off a desk she hops straight down first, then walks along the floor to
    // under the next spot, then hops straight up. One leg at a time; the next starts when it ends.
    const key = `${c.goal}-${c.desk}-${c.since}`;
    const cur = this.at.cat, near = (a, b) => Math.abs(a - b) < 0.5 * U;
    let leg = { x, y, spot: key };
    if (cur && !(cur.spot?.startsWith(key) && Date.now() < cur.until)) {
      if (!near(cur.x, x) && !near(cur.y, g.floorY)) leg = { x: cur.x, y: g.floorY, spot: `${key}-down` };
      else if (!near(cur.x, x) && !near(y, g.floorY)) leg = { x, y: g.floorY, spot: `${key}-under` };
    } else if (cur?.spot?.startsWith(key)) leg = cur;
    const hop = cur && near(leg.x, cur.x) && !near(leg.y, cur.y);
    const at = this.walk("cat", leg.spot, leg.x, leg.y, hop ? CAT_HOP : CAT_SPEED, cx);
    const walking = Date.now() < at.until;
    const hopping = walking && near(at.x, at.fromX) && !near(at.y, at.fromY ?? at.y);
    if (walking && !hopping) at.face = Math.sign(at.x - at.fromX) || at.face || 1;
    const face = at.face ?? 1;
    const id = hopping ? "catWalk1" : walking ? `catWalk${Math.floor(Date.now() / 140) % 2}` : napping ? "catSleep" : "catSit";
    // She's drawn at CAT_SIZE of the art's size, centred on her spot (14 units wide, like the shelves).
    const cU = U * CAT_SIZE, h = S.ART[id].h * cU, inset = S.CAT_W * (U - cU) / 2;
    return div().id("cat").absolute().left(at.x + inset).top(at.y - h).w(S.CAT_W * cU).h(h)
      .transition("left", { duration: at.dur, easing: "linear" })
      .transition("top", { duration: at.dur, easing: hopping ? (at.y < at.fromY ? "ease-out" : "ease-in") : "linear" })
      .child(S.art(id, 0, h, cU, undefined, face < 0))
      .when(napping && !walking, (el) => el.child(div().absolute().left(10 * cU).top(-2 * cU).text_size(Math.max(8, 2.4 * cU)).font_bold()
        .text_color("#a993dc").frames(["z", "zz", "zzz", ""], 800)));
  }

  // After dark: the room dims and busy screens glow.
  night(W, H, g, byDesk, deskCount, alarmed) {
    const U = g.U;
    const els = [div().absolute().left(0).top(0).w(W).h(H).bg("#2a2350").opacity(0.42 * S.nightDim())]; // less in a dark scene
    const [sx, sy, sw, sh] = S.DESK.screen;
    for (let i = 0; i < deskCount; i++) {
      const a = byDesk[i];
      if (!a || this.at[a.address]?.spot !== "desk") continue;
      const pos = g.deskPos(i);
      if (a.status !== "idle") {
        const top = pos.y - (12.6 + 13) * U + sy * U;
        els.push(div().absolute().left(pos.x + (sx - 3) * U).top(top - 3 * U).w((sw + 6) * U).h((sh + 6) * U).rounded(6 * U)
          .bg(STATUS[a.status] ?? STATUS.idle).opacity(0.2));
        els.push(this.screen(a.status, false, U, `n${i}`, alarmed.includes(a)).absolute().left(pos.x + sx * U).top(top).w(sw * U).h(sh * U));
      }
    }
    return els;
  }

  bubble(top, color, U = 3) {
    return div().absolute().left((PERSON * U) / 2 - 4).top(top).px(6).h(16).flex().items_center().rounded(8)
      .bg("#fffaf3").border_1().border_color(S.INK).text_size(10).font_bold().text_color(color).whitespace_nowrap();
  }
}
