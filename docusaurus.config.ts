import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Enclava Dev',
  tagline: 'Deploy confidential applications with Enclava PaaS and CAP',
  favicon: 'img/favicon.ico',

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
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: 'ENCLAVA DEV',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docs',
          position: 'left',
          label: 'Documentation',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {label: 'Overview', to: '/'},
            {label: 'Quickstart', to: '/getting-started/quickstart'},
            {label: 'Confidential Computing', to: '/concepts/confidential-computing'},
            {label: 'CAP Architecture', to: '/cap/architecture'},
          ],
        },
        {
          title: 'Resources',
          items: [
            {label: 'Enclava', href: 'https://enclava.dev/'},
            {label: 'Hosted Console', href: 'https://app.enclava.dev/'},
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Enclava Project. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.vsDark,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
