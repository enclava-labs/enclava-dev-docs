import React, {type ReactNode} from 'react';
import Link from '@docusaurus/Link';
import EnclavaWordmark from '@site/src/components/EnclavaWordmark';

// Mirrors the footer on enclava.dev (enclava-dev-website/client/src/components/landing/Footer.tsx).

const SOCIAL = [
  {
    href: 'https://x.com/EnclavaLabs',
    label: 'X',
    path: 'M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.74l7.727-8.835L1.254 2.25H8.08l4.253 5.622L18.244 2.25zm-1.161 17.52h1.833L7.084 4.126H5.117z',
  },
  {
    href: 'https://www.linkedin.com/company/enclava-labs/',
    label: 'LinkedIn',
    path: 'M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z',
  },
  {
    href: 'https://github.com/enclava-labs/',
    label: 'GitHub',
    path: 'M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55v-2.01c-3.2.7-3.87-1.37-3.87-1.37-.52-1.32-1.27-1.67-1.27-1.67-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.02 1.75 2.69 1.25 3.34.95.1-.74.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.28 1.18-3.08-.12-.29-.51-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.05 11.05 0 015.79 0c2.21-1.49 3.18-1.18 3.18-1.18.62 1.59.23 2.76.11 3.05.73.8 1.18 1.82 1.18 3.08 0 4.42-2.69 5.4-5.25 5.68.41.36.78 1.05.78 2.12v3.14c0 .31.21.67.8.55C20.21 21.39 23.5 17.08 23.5 12 23.5 5.65 18.35.5 12 .5z',
  },
];

const COLUMNS = [
  {
    title: 'Documentation',
    links: [
      {label: 'Overview', to: '/'},
      {label: 'Quickstart', to: '/getting-started/quickstart'},
      {label: 'Deploy your own image', to: '/getting-started/manual-oci-deploy'},
      {label: 'CLI reference', to: '/reference/cli-reference'},
    ],
  },
  {
    title: 'Resources',
    links: [
      {label: 'Enclava.dev', href: 'https://enclava.dev/'},
      {label: 'Hosted console', href: 'https://app.enclava.dev/'},
      {label: 'GitHub', href: 'https://github.com/enclava-labs/'},
    ],
  },
];

export default function Footer(): ReactNode {
  return (
    <footer className="enclava-footer">
      <div className="container">
        <div className="enclava-footer__grid">
          <div className="enclava-footer__about">
            <Link to="https://enclava.dev/" className="enclava-brand">
              <EnclavaWordmark />
            </Link>
            <p>
              The confidential applications platform. Encrypted in use,
              verifiable by anyone, invisible to the cloud.
            </p>
            <p>
              A product of <a href="https://enclava-labs.com/">Enclava Labs</a>.
            </p>
            <div className="enclava-footer__social">
              {SOCIAL.map((s) => (
                <a key={s.href} href={s.href} target="_blank" rel="me noopener noreferrer" aria-label={s.label}>
                  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                    <path d={s.path} />
                  </svg>
                </a>
              ))}
            </div>
          </div>

          {COLUMNS.map((col, i) => (
            <div key={col.title} className={`enclava-footer__col${i === 0 ? ' enclava-footer__col--first' : ''}`}>
              <h5>{col.title}</h5>
              <ul>
                {col.links.map((l) => (
                  <li key={l.label}>
                    {'to' in l ? <Link to={l.to}>{l.label}</Link> : <a href={l.href}>{l.label}</a>}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="enclava-footer__bottom">
          <p>&copy; {new Date().getFullYear()} Enclava Labs. All rights reserved.</p>
          <div className="enclava-footer__legal">
            <a href="https://enclava.dev/privacy">Privacy Policy</a>
            <a href="https://enclava.dev/terms">Terms of Service</a>
            <span className="enclava-footer__tagline">encrypted in use · AMD SEV-SNP</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
