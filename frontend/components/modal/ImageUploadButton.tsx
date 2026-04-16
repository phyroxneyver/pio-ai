"use client";

import { useState } from "react";
import ImageUploadModal from "./ImageUploadModal";

export default function ImageUploadButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="primary-button rounded-2xl px-4 py-3 text-sm font-semibold"
      >
        Añadir imagen
      </button>

      {open && (
        <ImageUploadModal onClose={() => setOpen(false)} />
      )}
    </>
  );
}