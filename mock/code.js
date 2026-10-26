// Draws the Tallyhive landing-page mock that this repo's MCP server reads. Tallyhive is a made-up product.
// Run it once in the Figma desktop app: Plugins → Development → Import plugin from manifest → pick mock/manifest.json → Run.
// One 1440-wide desktop frame, every section in auto layout, three colour styles, four text styles and four icons,
// so the server has real auto layout, styles, text and icons to turn into a layout Claude can build from.
// Running it again replaces the frame and reuses the styles.

const C = {
  ink: { r: 0.067, g: 0.094, b: 0.153 },      // #111827
  muted: { r: 0.376, g: 0.42, b: 0.494 },     // #606B7E
  brand: { r: 0.231, g: 0.361, b: 0.965 },    // #3B5CF6
  brandSoft: { r: 0.925, g: 0.937, b: 0.996 },// #ECEFFE
  line: { r: 0.894, g: 0.906, b: 0.925 },     // #E4E7EC
  white: { r: 1, g: 1, b: 1 },
  page: { r: 0.98, g: 0.98, b: 0.988 },       // #FAFAFC
};
const solid = (c) => [{ type: "SOLID", color: c }];

async function main() {
  await Promise.all([
    figma.loadFontAsync({ family: "Inter", style: "Regular" }),
    figma.loadFontAsync({ family: "Inter", style: "Semi Bold" }),
    figma.loadFontAsync({ family: "Inter", style: "Bold" }),
  ]);

  // ---- styles (what get_tokens reads); a re-run reuses them and replaces the old frame
  const oldPaints = await figma.getLocalPaintStylesAsync();
  const oldTexts = await figma.getLocalTextStylesAsync();
  const paint = (name, c) => { const s = oldPaints.find((x) => x.name === name) || figma.createPaintStyle(); s.name = name; s.paints = solid(c); return s; };
  const PS = { ink: paint("Ink", C.ink), brand: paint("Brand", C.brand), muted: paint("Muted", C.muted) };
  const textStyle = (name, size, style, lh) => {
    const s = oldTexts.find((x) => x.name === name) || figma.createTextStyle(); s.name = name; s.fontName = { family: "Inter", style }; s.fontSize = size;
    s.lineHeight = { unit: "PIXELS", value: lh }; return s;
  };
  const TS = {
    display: textStyle("Display", 56, "Bold", 64),
    heading: textStyle("Heading", 28, "Semi Bold", 36),
    body: textStyle("Body", 18, "Regular", 28),
    label: textStyle("Label", 16, "Semi Bold", 24),
  };

  // ---- helpers
  const box = (name, dir, opts = {}) => {
    const f = figma.createFrame();
    f.name = name;
    f.layoutMode = dir;
    f.itemSpacing = opts.gap ?? 0;
    f.paddingTop = f.paddingBottom = opts.py ?? 0;
    f.paddingLeft = f.paddingRight = opts.px ?? 0;
    f.primaryAxisSizingMode = "AUTO";
    f.counterAxisSizingMode = "AUTO";
    f.primaryAxisAlignItems = opts.justify ?? "MIN";
    f.counterAxisAlignItems = opts.align ?? "MIN";
    f.fills = opts.fill ? solid(opts.fill) : [];
    if (opts.radius) f.cornerRadius = opts.radius;
    if (opts.stroke) { f.strokes = solid(opts.stroke); f.strokeWeight = 1; }
    return f;
  };
  const text = async (chars, style, paintStyle, name) => {
    const t = figma.createText();
    t.name = name ?? chars.slice(0, 24);
    await t.setTextStyleIdAsync(style.id);
    t.characters = chars;
    await t.setFillStyleIdAsync(paintStyle.id);
    return t;
  };
  const add = (parent, child, fill = false) => { parent.appendChild(child); if (fill) child.layoutSizingHorizontal = "FILL"; return child; };
  const button = async (label, primary) => {
    const b = box(`Button / ${label}`, "HORIZONTAL", { px: 24, py: 14, radius: 10, fill: primary ? C.brand : C.white, stroke: primary ? null : C.line, align: "CENTER", justify: "CENTER" });
    const t = await text(label, TS.label, primary ? PS.ink : PS.ink, label);
    if (primary) t.fills = solid(C.white);
    add(b, t);
    return b;
  };

  for (const n of figma.currentPage.children.filter((n) => n.name === "Tallyhive / Landing / Desktop")) n.remove();

  // ---- icons: simple 24px stroke icons drawn as vectors (our own paths)
  const ICONS = {
    bolt: '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"/>',
    bell: '<path d="M6 9a6 6 0 0 1 12 0c0 6 2.5 8 2.5 8h-17S6 15 6 9Z"/><path d="M10 20.5a2.2 2.2 0 0 0 4 0"/>',
    chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    check: '<path d="M4 12.5 9 17.5 20 6.5"/>',
  };
  const icon = (key, size, color) => {
    const hex = "#" + [color.r, color.g, color.b].map((v) => Math.round(v * 255).toString(16).padStart(2, "0")).join("");
    const n = figma.createNodeFromSvg(`<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="${hex}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[key]}</svg>`);
    n.name = `Icon / ${key}`;
    n.resize(size, size);
    return n;
  };

  // ---- the page
  const page = box("Tallyhive / Landing / Desktop", "VERTICAL", { fill: C.page });
  page.resize(1440, 100);
  page.primaryAxisSizingMode = "AUTO";
  page.counterAxisSizingMode = "FIXED";

  // nav
  const nav = add(page, box("Nav", "HORIZONTAL", { px: 120, py: 24, justify: "SPACE_BETWEEN", align: "CENTER", fill: C.white, stroke: C.line }), true);
  add(nav, await text("Tallyhive", TS.heading, PS.brand, "Logo"));
  const links = add(nav, box("Links", "HORIZONTAL", { gap: 40, align: "CENTER" }));
  for (const l of ["Features", "Pricing", "Customers"]) add(links, await text(l, TS.label, PS.muted, `Link / ${l}`));
  add(links, await button("Start free", true));

  // hero
  const hero = add(page, box("Hero", "VERTICAL", { px: 120, py: 112, gap: 28, align: "CENTER" }), true);
  const h1 = add(hero, await text("Invoices your team actually sends on time", TS.display, PS.ink, "Headline"));
  h1.textAlignHorizontal = "CENTER";
  h1.textAutoResize = "HEIGHT"; h1.resize(860, h1.height);
  const sub = add(hero, await text("Tallyhive turns finished work into a sent invoice in two clicks, chases late payers for you, and shows what's owed at a glance.", TS.body, PS.muted, "Subhead"));
  sub.textAlignHorizontal = "CENTER";
  sub.textAutoResize = "HEIGHT"; sub.resize(680, sub.height);
  const ctas = add(hero, box("CTAs", "HORIZONTAL", { gap: 16 }));
  add(ctas, await button("Start free", true));
  add(ctas, await button("Book a demo", false));

  // features
  const features = add(page, box("Features", "HORIZONTAL", { px: 120, py: 40, gap: 32 }), true);
  const FEATS = [
    ["Two-click invoices", "Pick the hours or the milestone, check the total, send. Tallyhive fills in the rest."],
    ["Polite reminders", "Late payers get a friendly nudge on day 3, 7 and 14, so you never have to write one."],
    ["See what's owed", "Every open invoice, who owes what and since when, on a single page."],
  ];
  const FEAT_ICONS = ["bolt", "bell", "chart"];
  for (const [i, [title, body]] of FEATS.entries()) {
    const card = add(features, box(`Feature / ${title}`, "VERTICAL", { px: 32, py: 32, gap: 12, radius: 16, fill: C.white, stroke: C.line }));
    card.layoutGrow = 1;
    card.layoutAlign = "STRETCH"; // equal heights across the row
    const chip = box("Icon chip", "HORIZONTAL", { radius: 12, fill: C.brandSoft, align: "CENTER", justify: "CENTER" }); chip.resize(48, 48);
    chip.primaryAxisSizingMode = "FIXED"; chip.counterAxisSizingMode = "FIXED";
    add(card, chip);
    add(chip, icon(FEAT_ICONS[i], 24, C.brand));
    const t = add(card, await text(title, TS.heading, PS.ink, "Title"), true);
    t.textAutoResize = "HEIGHT";
    const b = add(card, await text(body, TS.body, PS.muted, "Body"), true);
    b.textAutoResize = "HEIGHT";
  }

  // pricing
  const pricing = add(page, box("Pricing", "VERTICAL", { px: 120, py: 96, gap: 40, align: "CENTER" }), true);
  add(pricing, await text("Simple pricing", TS.heading, PS.ink, "Pricing title"));
  const tiers = add(pricing, box("Tiers", "HORIZONTAL", { gap: 32 }), true);
  const TIERS = [
    ["Solo", "$0", ["5 invoices a month", "Email reminders"], false],
    ["Team", "$19", ["Unlimited invoices", "Reminders on your schedule", "Up to 10 people"], true],
    ["Business", "$49", ["Everything in Team", "Approval steps", "Priority support"], false],
  ];
  for (const [name, price, items, featured] of TIERS) {
    const card = add(tiers, box(`Tier / ${name}`, "VERTICAL", { px: 32, py: 32, gap: 16, radius: 16, fill: C.white, stroke: featured ? C.brand : C.line }));
    card.layoutGrow = 1;
    card.layoutAlign = "STRETCH";
    if (featured) card.strokeWeight = 2;
    add(card, await text(name, TS.label, featured ? PS.brand : PS.muted, "Tier name"));
    const p = box("Price", "HORIZONTAL", { gap: 6, align: "MAX" });
    add(card, p);
    add(p, await text(price, TS.display, PS.ink, "Amount"));
    add(p, await text("/ month", TS.body, PS.muted, "Per"));
    for (const it of items) {
      const row = add(card, box("Item", "HORIZONTAL", { gap: 10, align: "CENTER" }));
      add(row, icon("check", 18, C.brand));
      add(row, await text(it, TS.body, PS.ink, "Item text"));
    }
    add(card, await button(featured ? "Start free trial" : "Choose " + name, featured), true);
  }

  // footer
  const footer = add(page, box("Footer", "HORIZONTAL", { px: 120, py: 32, justify: "SPACE_BETWEEN", align: "CENTER", fill: C.ink }), true);
  const brand = add(footer, await text("Tallyhive", TS.label, PS.ink, "Footer logo")); brand.fills = solid(C.white);
  const copy = add(footer, await text("© 2026 Tallyhive. A demo product for a StackSprint video.", TS.body, PS.muted, "Footer note"));

  figma.currentPage.appendChild(page);
  figma.viewport.scrollAndZoomIntoView([page]);
  figma.notify("Tallyhive mock drawn: 1 frame, 3 colour styles, 4 text styles, 4 icons.");
  figma.closePlugin();
}

main().catch((e) => { figma.notify("Mock failed: " + e.message, { error: true }); figma.closePlugin(); });
