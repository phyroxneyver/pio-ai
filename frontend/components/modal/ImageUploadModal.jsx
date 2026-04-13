"use client";
import { useState } from "react";

export default function ImageUploadModal({ onClose }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [progress, setProgress] = useState(0);

  const handleFile = (selectedFile) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    handleFile(e.dataTransfer.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/upload");

    xhr.upload.onprogress = (e) => {
      const percent = Math.round((e.loaded * 100) / e.total);
      setProgress(percent);
    };

    xhr.onload = () => {
      if (xhr.status === 200) {
        alert("Imagen subida");
        onClose();
      } else {
        alert("Error");
      }
    };

    xhr.send(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex justify-center items-center">
      <div className="bg-white p-5 rounded-lg w-[400px]">
        <h2>Añadir Imagen</h2>

        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className="border-2 border-dashed p-4 text-center"
        >
          <input
            type="file"
            accept="image/*"
            onChange={(e) => handleFile(e.target.files[0])}
          />
          <p>Arrastra o selecciona una imagen</p>
        </div>

        {preview && (
          <img src={preview} className="mt-2 w-full h-40 object-cover" />
        )}

        {progress > 0 && (
          <div className="mt-2">
            <progress value={progress} max="100" />
            <p>{progress}%</p>
          </div>
        )}

        <div className="mt-3 flex gap-2">
          <button onClick={handleUpload}>Subir</button>
          <button onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  );
}