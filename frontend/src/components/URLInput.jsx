import React, { useState } from "react";
import styles from "./URLInput.module.css";

export default function URLInput() {
  const [urlStr, setUrlStr] = useState("");

  return (
    <div className={styles.wrapper}>
      <input
        className={styles.input}
        name="input_url"
        value={urlStr}
        placeholder="Paste a URL to shorten..."
        onChange={(e) => setUrlStr(e.target.value)}
      />
    </div>
  );
}
