---
layout: default
title: Finder Sight
description: Find visually similar and duplicate images on your Mac without uploading anything.
nav: home
page_class: landing-page
---

<section class="hero" aria-labelledby="hero-title">
  <div class="hero-copy">
    <p class="eyebrow">
      <span class="status-dot" aria-hidden="true"></span>
      Native macOS · Fully local
    </p>
    <h1 id="hero-title">Find the image.<br><span>Keep it private.</span></h1>
    <p class="hero-lede">
      Finder Sight searches your local image library using perceptual hashes and
      on-device Apple Vision features. Your images never leave your Mac.
    </p>
    <div class="hero-actions">
      <a class="button button-primary" href="{{ site.download_url }}">
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M12 3v12m0 0 5-5m-5 5-5-5M5 19h14" />
        </svg>
        Download for macOS
      </a>
      <a class="button button-secondary" href="{{ '/guide/' | relative_url }}">Read the user guide</a>
    </div>
    <p class="hero-meta">macOS 13 or later · Free and open source · MIT License</p>
  </div>

  <div class="hero-visual">
    <div class="window-frame">
      <div class="window-bar" aria-hidden="true">
        <span class="window-dot window-dot-red"></span>
        <span class="window-dot window-dot-yellow"></span>
        <span class="window-dot window-dot-green"></span>
        <span class="window-title">Finder Sight</span>
      </div>
      <img
        src="{{ '/assets/search-results-page.webp' | relative_url }}"
        width="1600"
        height="1125"
        alt="Finder Sight showing four visually similar image results"
        fetchpriority="high"
      >
    </div>
  </div>
</section>

<section class="trust-strip" aria-label="Privacy guarantees">
  <div>
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M12 3 5 6v5c0 4.8 2.9 8.2 7 10 4.1-1.8 7-5.2 7-10V6l-7-3Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
    <span><strong>No uploads</strong><small>Images stay on your Mac</small></span>
  </div>
  <div>
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M4 17V7m4 10v-5m4 5V9m4 8V5m4 12v-8" />
      <path d="M3 20h18" />
    </svg>
    <span><strong>No telemetry</strong><small>No analytics or tracking</small></span>
  </div>
  <div>
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M8 9 4 12l4 3m8-6 4 3-4 3m-2-9-4 12" />
    </svg>
    <span><strong>Open source</strong><small>Inspect every line of code</small></span>
  </div>
</section>

<section class="section" aria-labelledby="features-title">
  <div class="section-heading">
    <p class="eyebrow">Built for local libraries</p>
    <h2 id="features-title">Search by sight, not by filename</h2>
    <p>Drop in an image and let Finder Sight compare what it looks like—not what it is called.</p>
  </div>

  <div class="feature-grid">
    <article class="feature-card">
      <span class="icon-tile">
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <circle cx="11" cy="11" r="6" />
          <path d="m16 16 4 4M8 11h6m-3-3v6" />
        </svg>
      </span>
      <h3>Visual similarity</h3>
      <p>Find resized, compressed, edited, and visually related images with hybrid matching.</p>
    </article>

    <article class="feature-card">
      <span class="icon-tile">
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <rect x="4" y="4" width="11" height="11" rx="2" />
          <rect x="9" y="9" width="11" height="11" rx="2" />
        </svg>
      </span>
      <h3>Duplicate cleanup</h3>
      <p>Group exact duplicates, keep the best-quality copy, and move the rest to Trash.</p>
    </article>

    <article class="feature-card">
      <span class="icon-tile">
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M12 3 5 6v5c0 4.8 2.9 8.2 7 10 4.1-1.8 7-5.2 7-10V6l-7-3Z" />
          <path d="M9 12h6" />
        </svg>
      </span>
      <h3>Private by design</h3>
      <p>No account, cloud index, hosted backend, advertising, analytics, or background service.</p>
    </article>
  </div>
</section>

<section class="showcase">
  <div class="showcase-copy">
    <p class="eyebrow">Duplicate detection</p>
    <h2>Clean up with confidence</h2>
    <p>
      Finder Sight shows image dimensions, file size, and the recommended keeper before
      anything moves. Removed copies go to the macOS Trash, so cleanup stays recoverable.
    </p>
    <a class="text-link" href="{{ '/guide/#find-duplicates' | relative_url }}">
      Learn about duplicate cleanup
      <span aria-hidden="true">→</span>
    </a>
  </div>
  <div class="showcase-visual">
    <img
      src="{{ '/assets/duplicate-groups-page.webp' | relative_url }}"
      width="1600"
      height="1125"
      alt="Finder Sight duplicate group with keep and move-to-Trash recommendations"
      loading="lazy"
    >
  </div>
</section>

<section class="section how-it-works" aria-labelledby="steps-title">
  <div class="section-heading compact">
    <p class="eyebrow">Three simple steps</p>
    <h2 id="steps-title">From folder to match in minutes</h2>
  </div>
  <ol class="steps">
    <li>
      <span>1</span>
      <div><strong>Add folders</strong><p>Choose the image libraries you want Finder Sight to index.</p></div>
    </li>
    <li>
      <span>2</span>
      <div><strong>Drop an image</strong><p>Drag, choose, or paste the picture you want to find.</p></div>
    </li>
    <li>
      <span>3</span>
      <div><strong>Reveal the match</strong><p>Open a result or reveal its exact location in Finder.</p></div>
    </li>
  </ol>
</section>

<section class="security-panel" aria-labelledby="security-title">
  <div class="security-copy">
    <p class="eyebrow">Auditable security</p>
    <h2 id="security-title">Trust the evidence, not a promise</h2>
    <p>
      The source, CI results, security analysis, release checksum, and build provenance
      are public. The only app network request is a manual update check against GitHub Releases.
    </p>
    <div class="security-badges" aria-label="Repository security status">
      <a href="https://github.com/smallyunet/finder-sight/actions/workflows/ci.yml">
        <img src="https://github.com/smallyunet/finder-sight/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI workflow status">
      </a>
      <a href="https://github.com/smallyunet/finder-sight/actions/workflows/codeql.yml">
        <img src="https://github.com/smallyunet/finder-sight/actions/workflows/codeql.yml/badge.svg?branch=main" alt="CodeQL workflow status">
      </a>
      <a href="https://scorecard.dev/viewer/?uri=github.com/smallyunet/finder-sight">
        <img src="https://api.scorecard.dev/projects/github.com/smallyunet/finder-sight/badge" alt="OpenSSF Scorecard result">
      </a>
    </div>
    <div class="security-links">
      <a href="https://github.com/smallyunet/finder-sight/blob/main/PRIVACY.md">Privacy details</a>
      <a href="https://github.com/smallyunet/finder-sight/blob/main/SECURITY.md">Security policy</a>
      <a href="{{ site.repository_url }}">Inspect the source</a>
    </div>
  </div>
  <div class="verification-card">
    <span class="verification-label">Verify a release</span>
    <pre><code>shasum -a 256 -c \
FinderSight-macOS.dmg.sha256

gh attestation verify \
FinderSight-macOS.dmg \
-R smallyunet/finder-sight</code></pre>
  </div>
</section>

<section class="section install-section" aria-labelledby="install-title">
  <div class="section-heading compact">
    <p class="eyebrow">Install Finder Sight</p>
    <h2 id="install-title">Ready when your library is</h2>
  </div>
  <div class="install-grid">
    <div class="install-steps">
      <ol>
        <li><span>1</span>Download the latest DMG.</li>
        <li><span>2</span>Drag Finder Sight into Applications.</li>
        <li><span>3</span>Right-click Finder Sight and choose <strong>Open</strong> the first time.</li>
      </ol>
      <a class="button button-primary" href="{{ site.download_url }}">Download Finder Sight</a>
    </div>
    <aside class="notice" aria-label="Apple signing status">
      <svg aria-hidden="true" viewBox="0 0 24 24">
        <path d="M12 4 3 20h18L12 4Z" />
        <path d="M12 9v5m0 3h.01" />
      </svg>
      <div>
        <strong>Not notarized yet</strong>
        <p>
          Finder Sight is ad-hoc signed because the project does not currently have an Apple
          Developer ID. macOS may show an unidentified-developer warning.
        </p>
      </div>
    </aside>
  </div>
</section>

<section class="final-cta" aria-labelledby="final-cta-title">
  <img src="{{ '/assets/app-icon.webp' | relative_url }}" width="96" height="96" alt="">
  <div>
    <h2 id="final-cta-title">Search your images without sharing them.</h2>
    <p>Native macOS performance. Local Apple Vision analysis. No account required.</p>
  </div>
  <a class="button button-light" href="{{ site.download_url }}">Download for macOS</a>
</section>
