// ponytail: title = first "# Heading"; if docs ever use frontmatter titles, read them here
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const walk = d =>
  readdirSync(d, { withFileTypes: true }).flatMap(e =>
    e.isDirectory() ? walk(join(d, e.name)) : e.name.endsWith('.md') ? [join(d, e.name)] : [],
  );
const title = f => readFileSync(f, 'utf8').match(/^# (.+)$/m)?.[1] ?? f;

const pos = f => Number(readFileSync(f, 'utf8').match(/^sidebar_position:\s*(\d+)/m)?.[1] ?? 999);
const pages = walk('docs').filter(p => p !== 'docs/overview.md').sort();
const section = p => (p.split('/').length === 2 ? 'Docs' : p.split('/')[1]);
const groups = pages.reduce((acc, p) => ((acc[section(p)] ??= []).push(p), acc), {});
// Order mirrors sidebars.ts: sections in sidebar order, pages by sidebar_position.
const sectionOrder = ['getting-started', 'guides', 'concepts', 'reference'];

let out = `# Enclava Developer Documentation

> Deploy confidential applications on Enclava. Append .md to any page URL for raw markdown.
> Agent skills (deploy/operate/troubleshoot procedures for coding agents): https://github.com/enclava-labs/enclava-dev-skills

- [Enclava Developer Documentation](/overview.md)
`;
const names = { concepts: 'Security Model' }; // sections whose label differs from the folder name
const rank = g => { const i = sectionOrder.indexOf(g); return i === -1 ? 999 : i; };
for (const [g, files] of Object.entries(groups).sort(([a], [b]) => rank(a) - rank(b) || a.localeCompare(b)))
  out += `\n## ${names[g] ?? g.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}\n${files
    .sort((a, b) => pos(a) - pos(b) || a.localeCompare(b))
    .map(f => `- [${title(f)}](${f.replace(/^docs/, '')})`)
    .join('\n')}\n`;

writeFileSync('build/llms.txt', out);
console.log(`llms.txt: ${pages.length + 1} pages`);
