/**
 * Prepare a profile photo in the browser: decode whatever image the browser
 * understands, crop the centre square, scale to `size`×`size` and re-encode as
 * JPEG. Re-encoding drops all metadata (EXIF, GPS) and keeps uploads tiny.
 */
export async function squareJpeg(file: File, size = 256, quality = 0.9): Promise<Blob> {
  if (!file.type.startsWith("image/")) throw new Error("Choose an image file.");
  if (file.size > 15 * 1024 * 1024) throw new Error("That image is too large (max 15 MB).");
  const bitmap = await createImageBitmap(file).catch(() => {
    throw new Error("This image format can't be read. Try a PNG or JPEG.");
  });
  const side = Math.min(bitmap.width, bitmap.height);
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Your browser can't process images.");
  context.imageSmoothingQuality = "high";
  context.drawImage(bitmap, (bitmap.width - side) / 2, (bitmap.height - side) / 2, side, side, 0, 0, size, size);
  bitmap.close();
  return new Promise((resolve, reject) =>
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("Could not encode the image."))), "image/jpeg", quality),
  );
}
