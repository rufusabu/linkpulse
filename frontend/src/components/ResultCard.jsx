import { useState } from "react";
import styles from "./ResultCard.module.css";

const MAX_ORIGINAL_LEN = 72;

function truncate(str) {
  return str.length > MAX_ORIGINAL_LEN
    ? str.slice(0, MAX_ORIGINAL_LEN) + "…"
    : str;
}

export default function ResultCard({ result }) {
  const [copied, setCopied] = useState(false);

  // For the clickable test link, resolve against the current origin
  const testHref = `${window.location.origin}/r/${result.code}`;

  function handleCopy() {
    navigator.clipboard.writeText(result.shortened_url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className={styles.card} role="region" aria-label="Shortened URL">
      <p className={styles.label}>
        <span className={styles.dot} aria-hidden="true" />
        Your link is ready
      </p>

      <div className={styles.linkRow}>
        <a
          href={testHref}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.shortUrl}
          title={result.shortened_url}
        >
          {result.shortened_url}
        </a>

        <button
          className={copied ? styles.copiedBtn : styles.copyBtn}
          onClick={handleCopy}
          aria-label={copied ? "Copied!" : "Copy short URL"}
        >
          {copied ? "✓ Copied" : "Copy"}
        </button>
      </div>

      <p className={styles.originalUrl} title={result.original_url}>
        ↳ {truncate(result.original_url)}
      </p>
    </div>
  );
}
