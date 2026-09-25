import React, {type ReactNode} from 'react';

// "ENCLAVA.DEV" wordmark with the cyan dot, as on enclava.dev.
export default function EnclavaWordmark(): ReactNode {
  return (
    <span className="enclava-brand__wordmark">
      ENCLAVA<span className="enclava-brand__dot">.</span>DEV
    </span>
  );
}
