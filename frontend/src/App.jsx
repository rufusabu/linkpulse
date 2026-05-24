import { useState } from "react";
import axios from "axios";
import URLInput from "./components/URLInput";
import SubmitButton from "./components/SubmitButton";
import ResultCard from "./components/ResultCard";
import styles from "./App.module.css";

export default function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const { data } = await axios.post("/api/url", { original_url: trimmed });
      setResult(data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      // Pydantic validation errors come back as an array
      const msg = Array.isArray(detail)
        ? detail[0]?.msg ?? "Invalid input."
        : detail ?? "Something went wrong. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <main className={styles.card}>
        <header className={styles.brand}>
          <div className={styles.logoMark}>⚡</div>
          <h1 className={styles.wordmark}>LinkPulse</h1>
          <p className={styles.tagline}>Shorten links. Track every click.</p>
        </header>

        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <URLInput value={url} onChange={setUrl} disabled={loading} />
          <SubmitButton loading={loading} disabled={loading || !url.trim()} />
        </form>

        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}

        {result && <ResultCard result={result} />}
      </main>

      <p className={styles.footer}>Made with ⚡ by LinkPulse</p>
    </div>
  );
}
