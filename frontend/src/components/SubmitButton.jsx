import React from "react";
import styles from "./SubmitButton.module.css";

function SubmitButton() {
  return (
    <div className={styles.wrapper}>
      <button type="submit" className={styles.button}>
        Shorten
      </button>
    </div>
  );
}

export default SubmitButton;
