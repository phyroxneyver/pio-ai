type MockUploadOptions = {
  onProgress?: (value: number) => void;
  forceError?: boolean;
};

type MockUploadResponse = {
  url: string;
  message: string;
};

export function mockUploadImage(
  file: File,
  options: MockUploadOptions = {},
): Promise<MockUploadResponse> {
  const { onProgress, forceError = false } = options;

  return new Promise((resolve, reject) => {
    let progress = 0;

    onProgress?.(0);

    const interval = window.setInterval(() => {
      progress += Math.floor(Math.random() * 14) + 8;

      if (progress >= 100) {
        progress = 100;
        onProgress?.(progress);
        window.clearInterval(interval);

        window.setTimeout(() => {
          if (forceError) {
            reject(new Error("No se pudo subir la fotografía. Intenta nuevamente."));
            return;
          }

          resolve({
            url: URL.createObjectURL(file),
            message: "Subida completada correctamente.",
          });
        }, 250);

        return;
      }

      onProgress?.(progress);
    }, 180);
  });
}