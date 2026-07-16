import fs from "fs";
import path from "path";
import { marked } from "marked";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const mdPath = path.join(root, "content", "alltra-report.md");
const outDir = path.join(root, "public", "reports");
const htmlPath = path.join(outDir, "alltra-report.html");

const markdown = fs.readFileSync(mdPath, "utf8");
const body = marked.parse(markdown);

const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Alltra Tokens, Funds &amp; Liquidity Report</title>
  <style>
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: #1a1f2b;
      background: #fff;
      line-height: 1.65;
    }
    .wrap { max-width: 52rem; margin: 0 auto; padding: 2.5rem 1.5rem 4rem; }
    h1, h2, h3 { font-family: "Segoe UI", Arial, sans-serif; line-height: 1.25; }
    h1 { font-size: 2rem; margin: 0 0 1rem; }
    h2 { font-size: 1.35rem; margin: 2.5rem 0 0.75rem; color: #6b5424; border-bottom: 1px solid #ddd; padding-bottom: 0.35rem; }
    h3 { font-size: 1.1rem; margin: 1.75rem 0 0.5rem; }
    p, li { font-size: 1rem; }
    a { color: #6b5424; }
    table { width: 100%; border-collapse: collapse; margin: 1rem 0 1.5rem; font-size: 0.92rem; }
    th, td { border: 1px solid #ddd; padding: 0.55rem 0.65rem; text-align: left; vertical-align: top; }
    th { background: #f6f1e8; }
    code { font-family: Consolas, monospace; background: #f4f4f4; padding: 0.1rem 0.35rem; font-size: 0.9em; }
    pre { background: #f4f4f4; padding: 1rem; overflow-x: auto; border: 1px solid #ddd; }
    hr { border: 0; border-top: 1px solid #ddd; margin: 2rem 0; }
    .banner {
      font-family: "Segoe UI", Arial, sans-serif;
      background: #f6f1e8;
      border: 1px solid #d9c9a5;
      padding: 1rem 1.25rem;
      margin-bottom: 2rem;
      font-size: 0.95rem;
    }
    @media print {
      .banner { background: #f6f1e8; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      .wrap { padding: 0.5in; }
      a { color: #000; text-decoration: none; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="banner">
      <strong>Alltra Tokens, Funds &amp; Liquidity Report</strong><br />
      Art City AI Studio · Research document · 16 July 2026
    </div>
    ${body}
  </div>
</body>
</html>`;

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(htmlPath, html, "utf8");
console.log(`Wrote ${htmlPath}`);
