// ponytail: title = first "# Heading"; if docs ever use frontmatter titles, read them here
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const walk = d =>
  readdirSync(d, { withFileTypes: true }).flatMap(e =>
    e.isDirectory() ? walk(join(d, e.name)) : e.name.endsWith('.md') ? [join(d, e.name)] : [],
  );
const title = f => readFileSync(f, 'utf8').match(/^# (.+)$/m)?.[1] ?? f;

const pages = walk('docs').filter(p => p !== 'docs/overview.md').sort();
const section = p => (p.split('/').length === 2 ? 'Docs' : p.split('/')[1]);
const groups = pages.reduce((acc, p) => ((acc[section(p)] ??= []).push(p), acc), {});

let out = `# Enclava Developer Documentation

> Deploy confidential applications with Enclava PaaS and CAP. Append .md to any page URL for raw markdown.
> Agent skills (deploy/operate/troubleshoot procedures for coding agents): https://github.com/enclava-labs/enclava-dev-skills

- [Enclava Developer Documentation](/overview.md)
`;
const cap = { cap: 'CAP', paas: 'PaaS' }; // known acronym sections
for (const [g, files] of Object.entries(groups))
  out += `\n## ${cap[g] ?? g.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}\n${files
    .map(f => `- [${title(f)}](${f.replace(/^docs/, '')})`)
    .join('\n')}\n`;

writeFileSync('build/llms.txt', out);
console.log(`llms.txt: ${pages.length + 1} pages`);
