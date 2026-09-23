import { useRef, useState } from "react";

// A single drag-and-drop / click-to-browse file slot. Used twice, side by
// side, on the upload page (see coding-standards.md #1: pulled out once it
// had a second use).
export default function Dropzone({ label, file, onChange }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) onChange(dropped);
  }

  function handleClear(event) {
    // The file input covers the whole slot, so without this the click would
    // fall through and immediately reopen the file picker.
    event.stopPropagation();
    event.preventDefault();
    // Clearing the input's value matters: without it, picking the SAME file
    // again fires no change event and the slot would stay empty.
    if (inputRef.current) inputRef.current.value = "";
    onChange(null);
  }

  const stateClass = file ? "filled" : dragging ? "dragging" : "";

  return (
    <div
      className={`dropzone ${stateClass}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        onChange={(e) => onChange(e.target.files[0])}
      />
      {file && (
        <button
          type="button"
          className="dropzone-clear"
          onClick={handleClear}
          title="Remove this file"
          aria-label={`Remove ${file.name}`}
        >
          &times;
        </button>
      )}
      <svg
        className="dropzone-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
      >
        {file ? (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
          />
        ) : (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 16.5V9m0 0-3 3m3-3 3 3m-9 6.75h12A2.25 2.25 0 0 0 20.25 15V6.75A2.25 2.25 0 0 0 18 4.5H6a2.25 2.25 0 0 0-2.25 2.25V15A2.25 2.25 0 0 0 6 17.25Z"
          />
        )}
      </svg>
      <span className="dropzone-label">{label}</span>
      {file ? (
        <>
          <span className="dropzone-file">{file.name}</span>
          <span className="dropzone-sub">Wrong file? Click &times; to replace it.</span>
        </>
      ) : (
        <span className="dropzone-sub">Drag &amp; drop or click to browse (PDF)</span>
      )}
    </div>
  );
}
