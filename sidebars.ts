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
      ],
    },
    {
      type: 'category',
      label: 'Core Concepts',
      items: [
        'concepts/confidential-computing',
        'concepts/threat-model',
        'concepts/deployment-model',
      ],
    },
    {
      type: 'category',
      label: 'Enclava PaaS',
      items: [
        'paas/overview',
        'paas/cli-and-console',
        'paas/hosted-templates',
      ],
    },
    {
      type: 'category',
      label: 'CAP',
      items: [
        'cap/overview',
        'cap/architecture',
        'cap/cli-reference',
        'cap/runtime-verification',
      ],
    },
    {
      type: 'category',
      label: 'Operations',
      items: [
        'operations/production-checklist',
        'operations/security-checklist',
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      items: [
        'reference/api-surface',
        'reference/glossary',
      ],
    },
  ],
};

export default sidebars;
