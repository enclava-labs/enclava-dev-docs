import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docs: [
    'overview',
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/quickstart',
        'getting-started/hosted-template',
        'getting-started/manual-oci-deploy',
        'getting-started/examples',
      ],
    },
    {
      type: 'category',
      label: 'Guides',
      items: [
        'guides/console',
        'guides/attestation-in-your-app',
        'guides/storage-and-recovery',
        'guides/security-checklist',
        'guides/custom-domains',
      ],
    },
    {
      type: 'category',
      label: 'Security Model',
      items: [
        'concepts/confidential-computing',
        'concepts/threat-model',
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      items: [
        'reference/cli-reference',
        'reference/glossary',
      ],
    },
  ],
};

export default sidebars;
