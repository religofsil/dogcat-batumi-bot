/** Match server default `max_upload_bytes` (10 MiB) for fallback checks. */
export const CLIENT_UPLOAD_MAX_BYTES = 10_485_760;

/** Skip re-encoding when already small enough (saves CPU, avoids quality loss). */
const PASS_THROUGH_MAX_BYTES = 4_500_000;

const ALLOWED_RAW = new Set(["image/jpeg", "image/jpg", "image/png", "image/webp"]);

function normalizedType(file: File): string {
  return (file.type || "").split(";")[0].trim().toLowerCase();
}

function shouldPassThroughUnchanged(file: File): boolean {
  const ct = normalizedType(file);
  if (!ct) return false;
  if (!ALLOWED_RAW.has(ct)) return false;
  return file.size <= PASS_THROUGH_MAX_BYTES;
}

async function loadBitmap(file: File): Promise<ImageBitmap> {
  try {
    return await createImageBitmap(file);
  } catch {
    return await new Promise<ImageBitmap>((resolve, reject) => {
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        URL.revokeObjectURL(url);
        createImageBitmap(img).then(resolve).catch(reject);
      };
      img.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("Could not decode image"));
      };
      img.src = url;
    });
  }
}

function scaleDimensions(width: number, height: number, maxEdge: number): [number, number] {
  const long = Math.max(width, height);
  if (long <= maxEdge) return [width, height];
  const s = maxEdge / long;
  return [Math.max(1, Math.round(width * s)), Math.max(1, Math.round(height * s))];
}

function canvasToJpegBlob(canvas: HTMLCanvasElement, quality: number): Promise<Blob | null> {
  return new Promise((resolve) => {
    canvas.toBlob((b) => resolve(b), "image/jpeg", quality);
  });
}

/**
 * Downscale and JPEG-compress large or non-web-safe images so uploads stay under the server limit.
 * HEIC/HEIF and other types are normalized to JPEG when the browser can decode them.
 */
export async function compressImageForUpload(file: File): Promise<File> {
  if (shouldPassThroughUnchanged(file)) {
    return file;
  }

  let bitmap: ImageBitmap;
  try {
    bitmap = await loadBitmap(file);
  } catch {
    if (file.size <= CLIENT_UPLOAD_MAX_BYTES) {
      return file;
    }
    throw new Error("Could not read this image. Try JPEG or PNG, or a smaller file.");
  }

  const qualities = [0.92, 0.88, 0.82, 0.76, 0.7, 0.64, 0.58, 0.52, 0.46, 0.4];
  let maxEdge = 2048;

  try {
    while (maxEdge >= 640) {
      const [cw, ch] = scaleDimensions(bitmap.width, bitmap.height, maxEdge);
      const canvas = document.createElement("canvas");
      canvas.width = cw;
      canvas.height = ch;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        throw new Error("Could not prepare image");
      }
      ctx.drawImage(bitmap, 0, 0, cw, ch);

      for (const q of qualities) {
        const blob = await canvasToJpegBlob(canvas, q);
        if (blob && blob.size <= CLIENT_UPLOAD_MAX_BYTES) {
          return new File([blob], "photo.jpg", {
            type: "image/jpeg",
            lastModified: Date.now(),
          });
        }
      }
      maxEdge = Math.floor(maxEdge * 0.75);
    }
  } finally {
    bitmap.close();
  }

  if (file.size <= CLIENT_UPLOAD_MAX_BYTES) {
    return file;
  }
  throw new Error("Image is too large even after compressing. Try a different photo.");
}
