import React, {type ReactNode} from 'react';

// Thin wrappers that restyle ordinary markdown lists, so the raw .md pages
// served to agents stay readable. Registered globally in src/theme/MDXComponents.

/** A markdown list of links rendered as a grid of numbered cards. */
export function Cards({children}: {children: ReactNode}): ReactNode {
  return <div className="en-cards">{children}</div>;
}

/** An ordered list rendered as a vertical pipeline; the last step is highlighted. */
export function Flow({children}: {children: ReactNode}): ReactNode {
  return <div className="en-flow">{children}</div>;
}

/** A short list rendered as the hero's glowing status chips. */
export function Chips({children}: {children: ReactNode}): ReactNode {
  return <div className="en-chips">{children}</div>;
}

/** Diagram of the TEE boundary: what goes in, what runs inside, what the host can't see. */
export function TeeDiagram(): ReactNode {
  return (
    <figure className="en-tee" aria-label="Diagram: your signed image and secrets enter the TEE; inside, enclava-init verifies, storage and TLS unlock, then your app starts; the host cannot see inside.">
      <div className="en-tee__host">
        <span className="en-tee__label">Host · cloud provider · Enclava infrastructure</span>

        <div className="en-tee__row">
          <div className="en-tee__inputs">
            <div className="en-tee__node">
              <span className="en-tee__node-title">Signed image</span>
              <code>ghcr.io/…@sha256:…</code>
            </div>
            <div className="en-tee__node">
              <span className="en-tee__node-title">Your secrets</span>
              <code>--set-file KEY=…</code>
            </div>
          </div>

          <div className="en-tee__arrow" aria-hidden="true" />

          <div className="en-tee__enclave">
            <span className="en-tee__label en-tee__label--accent">TEE · AMD SEV-SNP · memory encrypted</span>
            <ol className="en-tee__steps">
              <li><span>01</span>enclava-init verifies image, signer, policy, attestation</li>
              <li><span>02</span>Encrypted storage opens · TLS and secrets delivered</li>
              <li><span>03</span>Your app starts</li>
            </ol>
          </div>
        </div>

        <div className="en-tee__blocked">
          <span aria-hidden="true">✕</span> The host can schedule and restart your app, but can't read its memory, storage keys, or secrets.
        </div>
      </div>
    </figure>
  );
}
