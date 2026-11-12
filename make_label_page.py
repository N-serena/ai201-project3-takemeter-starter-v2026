#!/usr/bin/env python3
"""
Build the labelling page from the batch CSVs.

    python make_label_page.py --out label_page.html

The page shows one post at a time and takes a label from a keypress. It runs
as a published Artifact and writes each label to the artifact's own store, so
the labels come back without copy-paste.

Two modes, because the two jobs are different:

**Cold 20** shows the post and nothing else. No suggestion, because a
suggestion is exactly what makes a cold label worthless.

**Pre-labelled 220** shows the existing label and lets it be kept or
overridden. That is a correction pass, and seeing the current value is the
point of it.

The page carries the posts; the labels live in the store. Nothing is seeded
into the page source.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass

LABELS = ["anecdote", "checkable", "assertion"]

BATCHES = [
    ("cold", "Cold 20", "cold_batch.csv", False),
    ("prelabelled", "Pre-labelled 220", "batch_prelabelled.csv", True),
]

TEMPLATE = r"""<title>Evidence Labeller</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@400;500&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
  /* Layout: one reading column. Status rail on top, label keys at the foot of the card. */
  :root {
    --bg: #f3f5f7;
    --surface: #ffffff;
    --fg: #171a1f;
    --muted: #59616d;
    --line: #dde3e9;
    --accent: #3d5a80;
    --tint: rgba(61, 90, 128, 0.09);
    --anecdote: #6b4fbb;
    --checkable: #16676c;
    --assertion: #a8512f;
    --ok: #1d6b45;
    --warn: #9a5b12;
    color-scheme: light;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg: #14171b;
      --surface: #1c2026;
      --fg: #e7eaee;
      --muted: #99a2af;
      --line: #2b323b;
      --accent: #8fb0d8;
      --tint: rgba(143, 176, 216, 0.14);
      --anecdote: #ad92e9;
      --checkable: #5ec2c6;
      --assertion: #e38d69;
      --ok: #6cc294;
      --warn: #dcac5e;
      color-scheme: dark;
    }
  }
  :root[data-theme="dark"] {
    --bg: #14171b;
    --surface: #1c2026;
    --fg: #e7eaee;
    --muted: #99a2af;
    --line: #2b323b;
    --accent: #8fb0d8;
    --tint: rgba(143, 176, 216, 0.14);
    --anecdote: #ad92e9;
    --checkable: #5ec2c6;
    --assertion: #e38d69;
    --ok: #6cc294;
    --warn: #dcac5e;
    color-scheme: dark;
  }

  * { box-sizing: border-box; }
  /* Own this rather than inherit it: .panel and .card set display, which beats
     the attribute on its own. */
  [hidden] { display: none !important; }
  html, body { height: 100%; }
  body {
    background: var(--bg);
    color: var(--fg);
    font-family: "IBM Plex Sans", system-ui, -apple-system, sans-serif;
    font-size: 15px;
    line-height: 1.5;
  }
  .wrap {
    max-width: 720px;
    margin: 0 auto;
    padding-left: max(16px, env(safe-area-inset-left, 0px));
    padding-right: max(16px, env(safe-area-inset-right, 0px));
    padding-block: 0 48px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  /* ---- top rail ---- */
  .rail {
    position: sticky;
    top: env(safe-area-inset-top, 0px);
    z-index: 10;
    background: var(--bg);
    padding-block: 14px 10px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    border-bottom: 1px solid var(--line);
  }
  body::before {
    content: "";
    position: fixed;
    inset: 0 0 auto;
    height: env(safe-area-inset-top, 0px);
    z-index: 10;
    background: var(--bg);
  }
  .rail-top { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
  .modes { display: flex; gap: 4px; }
  .mode {
    font: inherit;
    font-weight: 500;
    color: var(--muted);
    background: none;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 4px 10px;
    cursor: pointer;
  }
  .mode[aria-selected="true"] { background: var(--tint); color: var(--fg); border-color: var(--line); }
  .mode:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .count {
    margin-left: auto;
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
    color: var(--muted);
    font-size: 13px;
  }
  .track { height: 3px; background: var(--line); border-radius: 2px; overflow: hidden; }
  .track > i { display: block; height: 100%; background: var(--accent); width: 0; transition: width .18s ease; }

  /* ---- the post ---- */
  .card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 22px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    min-width: 0;
  }
  .meta {
    display: flex;
    gap: 14px;
    align-items: baseline;
    flex-wrap: wrap;
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-size: 12px;
    color: var(--muted);
  }
  .post {
    font-family: "IBM Plex Serif", Georgia, serif;
    font-size: 17px;
    line-height: 1.62;
    margin: 0;
    min-width: 0;
    overflow-wrap: break-word;
  }
  .held {
    font-size: 13px;
    color: var(--muted);
    border-top: 1px solid var(--line);
    padding-top: 12px;
  }
  .held b { font-weight: 600; }

  /* ---- label keys ---- */
  .keys { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
  @media (max-width: 560px) { .keys { grid-template-columns: 1fr; } }
  .key {
    font: inherit;
    text-align: left;
    background: var(--surface);
    color: var(--fg);
    border: 1px solid var(--line);
    border-left: 3px solid var(--hue);
    border-radius: 8px;
    padding: 12px 14px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }
  .key:hover { background: var(--tint); }
  .key:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .key[aria-pressed="true"] { background: var(--tint); border-color: var(--hue); }
  .key-name { font-weight: 600; color: var(--hue); display: flex; align-items: center; gap: 8px; }
  .cap {
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-size: 11px;
    border: 1px solid var(--line);
    border-radius: 4px;
    padding: 1px 5px;
    color: var(--muted);
  }
  .key-def { font-size: 12.5px; color: var(--muted); line-height: 1.4; }

  .nav { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  .nav button {
    font: inherit;
    font-size: 13px;
    background: none;
    color: var(--muted);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 5px 11px;
    cursor: pointer;
  }
  .nav button:hover { background: var(--tint); color: var(--fg); }
  .nav button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .status {
    margin-left: auto;
    font-size: 12px;
    color: var(--muted);
    font-family: "IBM Plex Mono", ui-monospace, monospace;
  }

  /* ---- distribution ---- */
  .panel {
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    background: var(--surface);
  }
  .panel h2 {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: .07em;
    font-weight: 600;
    color: var(--muted);
    margin: 0;
  }
  .dist { display: flex; flex-direction: column; gap: 9px; }
  .row { display: grid; grid-template-columns: 5.5em 1fr 7.5em; gap: 10px; align-items: center; font-size: 13px; }
  @media (max-width: 480px) { .row { grid-template-columns: 5em 1fr; } .row > .verdict { grid-column: 2; } }
  .row > b { font-weight: 500; color: var(--hue); }
  .bar { position: relative; height: 16px; background: var(--bg); border: 1px solid var(--line); border-radius: 3px; overflow: hidden; }
  .band { position: absolute; top: 0; bottom: 0; left: 25%; width: 20%; background: var(--tint); }
  .fill { position: absolute; top: 0; bottom: 0; left: 0; background: var(--hue); opacity: .75; transition: width .18s ease; }
  .verdict { font-family: "IBM Plex Mono", ui-monospace, monospace; font-variant-numeric: tabular-nums; font-size: 12px; color: var(--muted); }
  .verdict.out { color: var(--warn); }
  .verdict.in { color: var(--ok); }
  .note { font-size: 12.5px; color: var(--muted); margin: 0; }

  details.ref { border: 1px solid var(--line); border-radius: 10px; padding: 12px 16px; background: var(--surface); }
  details.ref summary { cursor: pointer; font-size: 13px; font-weight: 500; }
  details.ref summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  details.ref blockquote {
    margin: 12px 0 8px;
    padding-left: 12px;
    border-left: 2px solid var(--accent);
    font-family: "IBM Plex Serif", Georgia, serif;
    font-size: 14.5px;
  }
  details.ref ul { margin: 8px 0 0; padding-left: 20px; font-size: 13px; color: var(--muted); }
  details.ref li + li { margin-top: 6px; }

  .banner {
    border: 1px solid var(--warn);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    color: var(--fg);
    background: var(--tint);
  }
  .done { display: flex; flex-direction: column; gap: 12px; }
  .done textarea {
    width: 100%;
    min-height: 140px;
    font-family: "IBM Plex Mono", ui-monospace, monospace;
    font-size: 12px;
    background: var(--bg);
    color: var(--fg);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 10px;
    resize: vertical;
  }
  .primary {
    font: inherit;
    font-weight: 500;
    background: var(--accent);
    color: var(--bg);
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    cursor: pointer;
    align-self: flex-start;
  }
  .primary:focus-visible { outline: 2px solid var(--fg); outline-offset: 2px; }
  @media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>

<script id="posts" type="application/json">__POSTS__</script>

<div class="wrap">
  <div class="rail">
    <div class="rail-top">
      <div class="modes" role="tablist" aria-label="Batch"></div>
      <span class="count" id="count"></span>
    </div>
    <div class="track"><i id="trackfill"></i></div>
  </div>

  <div id="banner" hidden></div>

  <div class="card" id="card">
    <div class="meta" id="meta"></div>
    <p class="post" id="post">Loading the batch…</p>
    <div class="held" id="held" hidden></div>
  </div>

  <div class="keys" id="keys"></div>

  <div class="nav">
    <button type="button" id="prev">&larr; Back</button>
    <button type="button" id="next">Skip &rarr;</button>
    <button type="button" id="firstgap">Next unlabelled</button>
    <span class="status" id="status">starting</span>
  </div>

  <div class="panel">
    <h2>Label balance, this batch</h2>
    <div class="dist" id="dist"></div>
    <p class="note">The shaded band is 25–45%, the window criterion 3 asks every label to land in.</p>
  </div>

  <details class="ref">
    <summary>The decision rule</summary>
    <blockquote>Could another reader check this without taking the writer's word for it? If yes, <b>checkable</b>. If not, does it recount a particular incident? Then <b>anecdote</b>. If it is neither, <b>assertion</b>.</blockquote>
    <ul>
      <li>A link is not required. A named law, a public event, a product's documented behaviour, a video everyone in the thread has seen: all <b>checkable</b>, supplied source or not.</li>
      <li>But it has to be named specifically enough to check. "Studies show" and "everyone knows" name nothing, so they stay <b>assertion</b>.</li>
      <li>An anecdote can be about anyone, told from any perspective. It is not a first-person label.</li>
      <li>A preference is not an incident. "Laptops only, thanks" and "I always collapse the top comment" are a taste and a habit, so both are <b>assertion</b>.</li>
    </ul>
  </details>

  <div class="panel done" id="done" hidden>
    <h2>Every post in this batch is labelled</h2>
    <p class="note" id="donenote"></p>
    <textarea id="csv" readonly aria-label="Labels as CSV"></textarea>
    <button type="button" class="primary" id="copy">Copy as CSV</button>
  </div>
</div>

<script>
(function () {
  "use strict";

  var DATA = JSON.parse(document.getElementById("posts").textContent);
  var LABELS = DATA.labels;
  var DEFS = DATA.definitions;
  var BATCHES = DATA.batches;

  var labels = Object.create(null);   // post id -> label
  var store = null;                   // db namespace, when it arrives
  var chains = Object.create(null);   // per-doc write serialisation
  var current = BATCHES[0].key;
  var index = Object.create(null);
  BATCHES.forEach(function (b) { index[b.key] = 0; });

  var el = {
    modes: document.querySelector(".modes"),
    count: document.getElementById("count"),
    fill: document.getElementById("trackfill"),
    meta: document.getElementById("meta"),
    post: document.getElementById("post"),
    held: document.getElementById("held"),
    keys: document.getElementById("keys"),
    dist: document.getElementById("dist"),
    status: document.getElementById("status"),
    banner: document.getElementById("banner"),
    done: document.getElementById("done"),
    donenote: document.getElementById("donenote"),
    csv: document.getElementById("csv"),
    card: document.getElementById("card")
  };

  function batch(key) {
    for (var i = 0; i < BATCHES.length; i++) if (BATCHES[i].key === key) return BATCHES[i];
    return BATCHES[0];
  }
  function posts() { return batch(current).posts; }
  function post() { return posts()[index[current]] || null; }

  // ---- local safety net. The store is the record; this only survives a reload
  // if the store never answered.
  function cache(write) {
    try {
      if (write) localStorage.setItem("takemeter.labels", JSON.stringify(labels));
      else return JSON.parse(localStorage.getItem("takemeter.labels") || "null");
    } catch (e) { /* private window, blocked storage */ }
    return null;
  }

  function setStatus(text) { el.status.textContent = text; }

  function banner(text) {
    if (!text) { el.banner.hidden = true; return; }
    el.banner.textContent = text;
    el.banner.hidden = false;
  }

  // ---- rendering
  function buildModes() {
    BATCHES.forEach(function (b) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "mode";
      btn.id = "mode-" + b.key;
      btn.setAttribute("role", "tab");
      btn.textContent = b.title;
      btn.addEventListener("click", function () { current = b.key; render(); });
      el.modes.appendChild(btn);
    });
  }

  function buildKeys() {
    LABELS.forEach(function (name, i) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "key";
      btn.id = "key-" + name;
      btn.style.setProperty("--hue", "var(--" + name + ")");
      var h = document.createElement("span");
      h.className = "key-name";
      var cap = document.createElement("span");
      cap.className = "cap";
      cap.textContent = String(i + 1);
      h.appendChild(cap);
      h.appendChild(document.createTextNode(name));
      var d = document.createElement("span");
      d.className = "key-def";
      d.textContent = DEFS[name];
      btn.appendChild(h);
      btn.appendChild(d);
      btn.addEventListener("click", function () { assign(name); });
      el.keys.appendChild(btn);
    });
  }

  function render() {
    var b = batch(current);
    var list = b.posts;
    var p = post();

    Array.prototype.forEach.call(el.modes.children, function (btn) {
      btn.setAttribute("aria-selected", btn.id === "mode-" + current ? "true" : "false");
    });

    var done = list.filter(function (q) { return labels[q.id]; }).length;
    el.count.textContent = done + " / " + list.length + " labelled";
    el.fill.style.width = (list.length ? (done / list.length) * 100 : 0) + "%";

    if (p) {
      el.card.hidden = false;
      el.meta.textContent = "";
      [p.id, p.text.trim().split(/\s+/).length + " words",
       "post " + (index[current] + 1) + " of " + list.length].forEach(function (t) {
        var s = document.createElement("span");
        s.textContent = t;
        el.meta.appendChild(s);
      });
      el.post.textContent = p.text;

      var mine = labels[p.id];
      if (b.suggests && p.suggested) {
        el.held.hidden = false;
        el.held.textContent = "";
        var lead = document.createElement("span");
        lead.textContent = "Pre-labelled ";
        var val = document.createElement("b");
        val.textContent = p.suggested;
        el.held.appendChild(lead);
        el.held.appendChild(val);
        el.held.appendChild(document.createTextNode(
          mine ? (mine === p.suggested ? " · you kept it" : " · you changed it to " + mine)
               : " · press Enter to keep it, or 1/2/3 to change it"));
      } else if (mine) {
        el.held.hidden = false;
        el.held.textContent = "";
        el.held.appendChild(document.createTextNode("You labelled this "));
        var v2 = document.createElement("b");
        v2.textContent = mine;
        el.held.appendChild(v2);
      } else {
        el.held.hidden = true;
      }

      Array.prototype.forEach.call(el.keys.children, function (btn) {
        var name = btn.id.slice(4);
        btn.setAttribute("aria-pressed", mine === name ? "true" : "false");
      });
    } else {
      el.card.hidden = true;
    }

    renderDist(list);

    var all = list.length > 0 && done === list.length;
    el.done.hidden = !all;
    if (all) {
      el.donenote.textContent = "All " + list.length + " labelled. They are saved in the artifact's store"
        + (store ? "." : " only in this tab - the store never answered, so copy them out.");
      el.csv.value = csvFor(list);
    }
  }

  function renderDist(list) {
    var labelled = list.filter(function (p) { return labels[p.id]; });
    el.dist.textContent = "";
    LABELS.forEach(function (name) {
      var n = labelled.filter(function (p) { return labels[p.id] === name; }).length;
      var share = labelled.length ? n / labelled.length : 0;

      var row = document.createElement("div");
      row.className = "row";
      row.style.setProperty("--hue", "var(--" + name + ")");

      var nm = document.createElement("b");
      nm.textContent = name;

      var bar = document.createElement("div");
      bar.className = "bar";
      var band = document.createElement("span");
      band.className = "band";
      var fill = document.createElement("span");
      fill.className = "fill";
      fill.style.width = (share * 100).toFixed(1) + "%";
      bar.appendChild(band);
      bar.appendChild(fill);

      var v = document.createElement("span");
      v.className = "verdict";
      if (!labelled.length) {
        v.textContent = "-";
      } else {
        var inBand = share >= 0.25 && share <= 0.45;
        v.classList.add(inBand ? "in" : "out");
        v.textContent = n + "  " + (share * 100).toFixed(0) + "%" + (inBand ? "" : "  !");
      }

      row.appendChild(nm);
      row.appendChild(bar);
      row.appendChild(v);
      el.dist.appendChild(row);
    });
  }

  function csvFor(list) {
    var out = ["id,label"];
    list.forEach(function (p) { if (labels[p.id]) out.push(p.id + "," + labels[p.id]); });
    return out.join("\n");
  }

  // ---- writing
  function save(id, label) {
    cache(true);
    if (!store) { setStatus("not saved"); return; }
    var prior = chains[id] || Promise.resolve();
    chains[id] = prior.then(function () {
      return store.collection("labels").doc(id).set({
        label: label,
        batch: current,
        at: new Date().toISOString()
      });
    }).then(function () {
      setStatus("saved");
    }, function (err) {
      var code = (err && err.code) || "unavailable";
      setStatus("not saved: " + code);
      if (code === "invalid_argument") {
        banner("The store refused the write. Your labels are in this tab only - copy them out when you finish.");
      }
    });
  }

  function assign(label) {
    var p = post();
    if (!p) return;
    if (labels[p.id] !== label) {
      labels[p.id] = label;
      save(p.id, label);
    }
    advance();
  }

  function advance() {
    var list = posts();
    if (index[current] < list.length - 1) index[current]++;
    render();
  }

  function gap() {
    var list = posts();
    for (var i = 0; i < list.length; i++) {
      if (!labels[list[i].id]) { index[current] = i; render(); return; }
    }
    render();
  }

  // ---- input
  document.getElementById("prev").addEventListener("click", function () {
    if (index[current] > 0) index[current]--;
    render();
  });
  document.getElementById("next").addEventListener("click", advance);
  document.getElementById("firstgap").addEventListener("click", gap);

  document.getElementById("copy").addEventListener("click", function () {
    var text = el.csv.value;
    var fallback = function () { el.csv.focus(); el.csv.select(); setStatus("select and copy"); };
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { setStatus("copied"); }, fallback);
      } else { fallback(); }
    } catch (e) { fallback(); }
  });

  document.addEventListener("keydown", function (ev) {
    var t = ev.target;
    if (t && (t.tagName === "TEXTAREA" || t.tagName === "INPUT")) return;
    if (ev.metaKey || ev.ctrlKey || ev.altKey) return;

    if (ev.key === "1" || ev.key === "2" || ev.key === "3") {
      ev.preventDefault();
      assign(LABELS[Number(ev.key) - 1]);
    } else if (ev.key === "Enter") {
      var p = post();
      if (p && batch(current).suggests && p.suggested) { ev.preventDefault(); assign(p.suggested); }
    } else if (ev.key === "ArrowRight") {
      ev.preventDefault(); advance();
    } else if (ev.key === "ArrowLeft") {
      ev.preventDefault();
      if (index[current] > 0) index[current]--;
      render();
    }
  });

  // ---- start
  buildModes();
  buildKeys();
  var local = cache(false);
  if (local) { labels = local; }
  render();
  setStatus("connecting");

  var settled = false;
  var timer = setTimeout(function () {
    if (settled) return;
    setStatus("store not reachable");
    banner("The label store has not answered. You can keep labelling - the page holds them in this tab - but copy them out before you close it.");
  }, 10000);

  if (window.claude && window.claude.use) {
    window.claude.use("db").then(function (db) {
      if (!db) {
        settled = true;
        clearTimeout(timer);
        setStatus("no store");
        banner("Labels cannot be saved from this view. Keep going and use Copy as CSV when you finish.");
        return;
      }
      store = db;
      return db.collection("labels").get().then(function (snap) {
        settled = true;
        clearTimeout(timer);
        banner("");
        snap.docs.forEach(function (d) {
          var body = d.data();
          if (body && typeof body.label === "string") labels[d.id] = body.label;
        });
        cache(true);
        setStatus("ready");
        // Open on the first batch that still has unlabelled posts, so a
        // finished batch isn't what greets you.
        for (var i = 0; i < BATCHES.length; i++) {
          var unlabelled = BATCHES[i].posts.some(function (p) { return !labels[p.id]; });
          if (unlabelled) { current = BATCHES[i].key; break; }
        }
        gap();
      });
    }).catch(function (err) {
      settled = true;
      clearTimeout(timer);
      setStatus("store error: " + ((err && err.code) || "unavailable"));
      banner("The label store could not be read. Keep labelling and copy the results out when you finish.");
    });
  } else {
    settled = true;
    clearTimeout(timer);
    setStatus("no store");
  }
})();
</script>
"""


def read(path):
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="label_page.html", type=Path)
    args = ap.parse_args()

    batches = []
    for key, title, source, suggests in BATCHES:
        rows = read(source)
        if not rows:
            print(f"[warn] {source} is missing or empty, skipping that batch")
            continue
        batches.append({
            "key": key,
            "title": title,
            "suggests": suggests,
            "posts": [
                {
                    "id": r["id"],
                    "text": r["text"],
                    "suggested": (r.get("label") or "").strip() or None,
                }
                for r in rows
            ],
        })
        print(f"  {title}: {len(rows)} posts from {source}")

    if not batches:
        sys.exit("No batches found. Run make_batch.py first.")

    payload = {
        "labels": LABELS,
        "definitions": {
            "anecdote": "Recounts a particular incident, about anyone, from any perspective, that nobody else can verify.",
            "checkable": "Rests on something a reader could verify: a named fact, figure, date, document, event or rule. No link required.",
            "assertion": "No incident, and nothing a reader could check. Opinion, preference, habit, prediction, argument.",
        },
        "batches": batches,
    }

    # `<` escaped so no post can close the script tag early.
    blob = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    args.out.write_text(TEMPLATE.replace("__POSTS__", blob), encoding="utf-8")

    size = args.out.stat().st_size
    print(f"\nwrote {args.out} ({size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
