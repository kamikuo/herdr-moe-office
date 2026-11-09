// Every word the office shows, in English, Traditional Chinese and Japanese. The language
// picked in the ⚙️ panel wins; without one, the block's props ({ "lang": "zh-TW" } or "ja");
// without that, English.
// To add a language, add a column to each entry (and its name to LANGS).

export const LANGS = { en: "English", "zh-TW": "繁體中文", ja: "日本語" };

const T = {
  // The team board
  "board.working": { en: "Working", "zh-TW": "工作中", ja: "作業中" },
  "board.done": { en: "Done", "zh-TW": "完成", ja: "完了" },
  "board.blocked": { en: "Stuck", "zh-TW": "卡住", ja: "困り中" },
  "board.idle": { en: "Break", "zh-TW": "休息", ja: "休憩中" },
  "board.nap": { en: "Napping", "zh-TW": "午睡", ja: "お昼寝" },
  "board.interns": { en: "Interns", "zh-TW": "實習生", ja: "インターン" },
  "board.pizza": { en: "Tea time!", "zh-TW": "下午茶!", ja: "お茶会!" },
  // Speech bubbles
  help: { en: "Help!!", "zh-TW": "救命!!", ja: "助けて!!" },
  thanks: { en: "Done~ ♡", "zh-TW": "完成囉～♡", ja: "できた～♡" },
  pizzaHere: { en: "Cake's here 🍰", "zh-TW": "蛋糕來囉 🍰", ja: "ケーキ届いたよ 🍰" },
  chat: {
    en: ["let's do our best today~", "I want something sweet…", "📱…", "sooo sleepy", "nice weather ☀️", "♡", "did you see that?", "one more cup~", "hehe", "after work? 🍰", "my plushie is the cutest", "✨"],
    "zh-TW": ["今天也要加油喔～", "好想吃甜的…", "📱…", "好睏喔", "天氣真好 ☀️", "♡", "你看到了嗎？", "再一杯就好～", "嘿嘿", "下班去吃甜點？🍰", "我的娃娃最可愛", "✨"],
    ja: ["今日もがんばろ～", "甘いもの食べたい…", "📱…", "ねむ～い", "いい天気 ☀️", "♡", "見た見た？", "もう一杯だけ～", "えへへ", "帰りにケーキ？🍰", "うちの子が一番かわいい", "✨"],
  },
  sip: {
    en: ["💧", "gulp gulp", "ahh~ refreshing", "🥤", "so cold!", "staying hydrated ♡"],
    "zh-TW": ["💧", "咕嚕咕嚕", "啊～好清爽", "🥤", "好冰！", "要多喝水 ♡"],
    ja: ["💧", "ごくごく", "ぷは～", "🥤", "つめたい！", "水分補給 ♡"],
  },
  snack: {
    en: ["🍪", "one more cookie…", "☕", "nom nom", "macaron ♡", "🍮", "just a little snack"],
    "zh-TW": ["🍪", "再一塊餅乾就好…", "☕", "嚼嚼", "馬卡龍 ♡", "🍮", "吃一點點就好"],
    ja: ["🍪", "クッキーもう一枚…", "☕", "もぐもぐ", "マカロン ♡", "🍮", "ちょっとだけ"],
  },
  pizzaChat: {
    en: ["🍰", "so good!", "more tea?", "🫖", "best tea time", "strawberry ♡"],
    "zh-TW": ["🍰", "好好吃！", "再來點茶？", "🫖", "最棒的下午茶", "草莓 ♡"],
    ja: ["🍰", "おいしい！", "お茶おかわり？", "🫖", "最高のお茶会", "いちご ♡"],
  },
  waterDone: { en: "I drank it!", "zh-TW": "我喝完了！", ja: "飲んだよ！" },
  water: { en: "💧 Water break! Have a sip~", "zh-TW": "💧 該喝水囉！喝一口吧～", ja: "💧 お水タイム！ひと口どうぞ～" },
  months: {
    en: ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"],
    "zh-TW": ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
    ja: ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
  },
  weekdays: {
    en: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    "zh-TW": ["週日", "週一", "週二", "週三", "週四", "週五", "週六"],
    ja: ["日", "月", "火", "水", "木", "金", "土"],
  },
  // The room
  empty: {
    en: "Nobody's in yet~ Open an agent and she'll walk in.",
    "zh-TW": "還沒有人上班～開一個 agent，她就會走進來。",
    ja: "まだ誰も出社してないよ～ agent を開くと入ってくるよ。",
  },
  thinking: { en: "Thinking…", "zh-TW": "思考中…", ja: "考え中…" },
  remote: { en: "Remote", "zh-TW": "遠端", ja: "リモート" },
  // The settings panel
  "settings.title": { en: "Settings", "zh-TW": "設定", ja: "設定" },
  "settings.debug": { en: "Debug mode", "zh-TW": "Debug 模式", ja: "デバッグモード" },
  "settings.lang": { en: "Language", "zh-TW": "語言", ja: "言語" },
  "settings.scene": { en: "Scene", "zh-TW": "場景", ja: "シーン" },
  "scene.pastel": { en: "Pastel office", "zh-TW": "粉彩辦公室", ja: "パステルオフィス" },
  "scene.jirai": { en: "Jirai-kei", "zh-TW": "地雷系", ja: "地雷系" },
  "scene.gothic": { en: "Gothic lolita (dark)", "zh-TW": "哥德蘿莉（深色）", ja: "ゴスロリ（ダーク）" },
  "debug.title": { en: "Debug: fake coworkers", "zh-TW": "Debug：假角色", ja: "Debug：ダミーの同僚" },
  "debug.char": { en: "Girl", "zh-TW": "角色", ja: "キャラ" },
  "debug.hair": { en: "Hair", "zh-TW": "髮色", ja: "髪色" },
  "debug.add": { en: "+ Add", "zh-TW": "＋ 新增角色", ja: "＋ 追加" },
  "debug.clear": { en: "Clear all", "zh-TW": "全部清除", ja: "全部消す" },
  "debug.kids": { en: "Subs", "zh-TW": "子", ja: "子" },
  "debug.remote": { en: "Remote", "zh-TW": "遠端", ja: "リモート" },
  "debug.party": { en: "🍰 Tea time", "zh-TW": "🍰 下午茶", ja: "🍰 お茶会" },
  "debug.partyEnd": { en: "🍰 End tea time", "zh-TW": "🍰 結束下午茶", ja: "🍰 お茶会おわり" },
  "debug.water": { en: "💧 Water", "zh-TW": "💧 喝水", ja: "💧 お水" },
  "act.idle": { en: "Idle", "zh-TW": "待機", ja: "待機" },
  "act.walk": { en: "Walk", "zh-TW": "走路", ja: "歩く" },
  "act.typing": { en: "Typing", "zh-TW": "打字", ja: "タイピング" },
  "act.blocked": { en: "Stuck", "zh-TW": "卡住", ja: "困り中" },
  "act.alarm": { en: "Alarm", "zh-TW": "警報", ja: "警報" },
  "act.done": { en: "Done", "zh-TW": "完成", ja: "完了" },
  "act.sleep": { en: "Sleep", "zh-TW": "睡覺", ja: "居眠り" },
  "time.auto": { en: "Time: auto", "zh-TW": "時間：自動", ja: "時間：自動" },
  "time.12": { en: "Time: day", "zh-TW": "時間：白天", ja: "時間：昼" },
  "time.18": { en: "Time: dusk", "zh-TW": "時間：黃昏", ja: "時間：夕方" },
  "time.22": { en: "Time: night", "zh-TW": "時間：夜晚", ja: "時間：夜" },
};

let lang = "en";

// Unknown names fall back to English.
export function setLang(name) {
  lang = name in LANGS ? name : "en";
}

export function getLang() {
  return lang;
}

// The text for `key` in the current language (a string, or a list for chat lines).
export function t(key) {
  const e = T[key];
  return e ? e[lang] ?? e.en : key;
}
