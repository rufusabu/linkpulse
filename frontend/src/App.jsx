import { useEffect, useState } from "react";
import URLInput from "./components/URLInput";
import SubmitButton from "./components/SubmitButton";

export default function App() {
  const [status, setStatus] = useState("checking...");

  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus("unreachable"));
  }, []);

  return (
    <div
      style={{ fontFamily: "system-ui", padding: "3rem", textAlign: "center" }}
    >
      <h1>Welcome to LinkPulse</h1>
      <p>
        API status: <strong>{status}</strong>
      </p>
      <URLInput />
      <SubmitButton />
    </div>
  );
}
