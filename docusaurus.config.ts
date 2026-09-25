import type {PrismTheme} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// github-dark palette, matching the highlight.js theme on enclava.dev.
const githubDark: PrismTheme = {
  plain: {color: '#c9d1d9', backgroundColor: 'hsl(222, 30%, 15%)'},
  styles: [
    {types: ['comment', 'prolog', 'doctype', 'cdata'], style: {color: '#8b949e'}},
    {types: ['punctuation', 'operator', 'entity', 'url'], style: {color: '#c9d1d9'}},
    {types: ['property', 'tag', 'boolean', 'number', 'constant', 'symbol', 'deleted'], style: {color: '#79c0ff'}},
    {types: ['selector', 'attr-name', 'string', 'char', 'builtin', 'inserted'], style: {color: '#a5d6ff'}},
    {types: ['atrule', 'attr-value', 'keyword'], style: {color: '#ff7b72'}},
    {types: ['function', 'class-name'], style: {color: '#d2a8ff'}},
    {types: ['regex', 'important', 'variable', 'parameter'], style: {color: '#ffa657'}},
  ],
};

const config: Config = {
  title: 'Enclava Dev',
  tagline: 'Deploy confidential applications on Enclava',
  favicon: 'img/favicon.ico',
  headTags: [
    {tagName: 'link', attributes: {rel: 'icon', type: 'image/png', sizes: '32x32', href: '/img/favicon-32.png'}},
    {tagName: 'link', attributes: {rel: 'icon', type: 'image/png', sizes: '192x192', href: '/img/icon-192.png'}},
    {tagName: 'link', attributes: {rel: 'apple-touch-icon', sizes: '180x180', href: '/img/apple-touch-icon.png'}},
  ],

  future: {
    v4: true,
  },

  url: 'https://docs.enclava.dev',
  baseUrl: '/',

  organizationName: 'enclava-labs',
  projectName: 'enclava-dev-docs',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
          editUrl: 'https://github.com/enclava-labs/enclava-dev-docs/tree/main/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // enclava.dev is dark-only; the docs follow it.
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: true,
      respectPrefersColorScheme: false,
    },
    navbar: {
      // Brand is rendered by src/theme/Navbar/Logo; footer by src/theme/Footer.
      title: 'Enclava.dev Docs',
      items: [
        {href: 'https://enclava.dev/', label: 'Enclava.dev', position: 'right'},
        {href: 'https://app.enclava.dev/', label: 'Console', position: 'right'},
        {
          href: 'https://github.com/enclava-labs/',
          position: 'right',
          className: 'navbar-github',
          'aria-label': 'GitHub',
          html: '<span class="sr-only">GitHub</span>',
        },
        {
          href: 'https://enclava.dev/get-started',
          label: 'Request access',
          position: 'right',
          className: 'navbar-cta',
        },
      ],
    },
    prism: {
      theme: githubDark,
      darkTheme: githubDark,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
