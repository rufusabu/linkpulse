import styles from "./URLInput.module.css";

export default function URLInput({ value, onChange, disabled }) {
  return (
    <div className={styles.wrapper}>
      <input
        className={styles.input}
        type="url"
        name="url"
        value={value}
        placeholder="Paste a URL to shorten…"
        disabled={disabled}
        autoComplete="off"
        spellCheck={false}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
