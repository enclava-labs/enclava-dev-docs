import React, {type ReactNode} from 'react';
import Link from '@docusaurus/Link';
import EnclavaWordmark from '@site/src/components/EnclavaWordmark';

export default function NavbarLogo(): ReactNode {
  return (
    <Link to="/" className="navbar__brand enclava-brand" aria-label="Enclava.dev documentation home">
      <EnclavaWordmark />
      <span className="enclava-brand__tag">Docs</span>
    </Link>
  );
}
