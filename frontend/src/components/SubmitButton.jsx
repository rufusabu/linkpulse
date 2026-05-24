import styles from "./SubmitButton.module.css";

export default function SubmitButton({ loading, disabled }) {
  return (
    <button
      type="submit"
      className={styles.button}
      disabled={disabled}
      aria-busy={loading}
    >
      {loading ? <span className={styles.spinner} aria-hidden="true" /> : null}
      {loading ? "Shortening…" : "Shorten"}
    </button>
  );
}
