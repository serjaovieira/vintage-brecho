/**
 * Image compression and Supabase storage upload service.
 * Downscales high-resolution camera photos to ~300KB via browser Canvas.
 */

export interface CompressionResult {
  blob: Blob;
  file: File;
  dataUrl: string;
  originalSizeKB: number;
  compressedSizeKB: number;
  width: number;
  height: number;
}

/**
 * Compresses an image file using an HTML5 Canvas.
 * Target resolution: max 1200px along the longest edge.
 * Quality: 0.8 JPEG (~200KB - 350KB typical for smartphone photos).
 */
export async function compressImage(
  file: File,
  maxDimension = 1200,
  quality = 0.8
): Promise<CompressionResult> {
  const originalSizeKB = Math.round(file.size / 1024);

  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (readerEvent) => {
      const img = new Image();
      img.onload = () => {
        let width = img.width;
        let height = img.height;

        if (width > maxDimension || height > maxDimension) {
          if (width > height) {
            height = Math.round((height * maxDimension) / width);
            width = maxDimension;
          } else {
            width = Math.round((width * maxDimension) / height);
            height = maxDimension;
          }
        }

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('Falha ao obter contexto 2D do Canvas'));
          return;
        }

        // Draw image smoothed
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(new Error('Erro ao converter Canvas para Blob'));
              return;
            }

            const compressedFile = new File([blob], file.name.replace(/\.[^/.]+$/, '.jpg'), {
              type: 'image/jpeg',
              lastModified: Date.now(),
            });

            const dataUrl = canvas.toDataURL('image/jpeg', quality);
            const compressedSizeKB = Math.round(blob.size / 1024);

            resolve({
              blob,
              file: compressedFile,
              dataUrl,
              originalSizeKB,
              compressedSizeKB,
              width,
              height,
            });
          },
          'image/jpeg',
          quality
        );
      };

      img.onerror = (err) => reject(err);
      img.src = readerEvent.target?.result as string;
    };

    reader.onerror = (err) => reject(err);
    reader.readAsDataURL(file);
  });
}

/**
 * Uploads an image to Supabase Storage bucket 'brecho-photos'.
 * Uses anon key for authorization.
 * Falls back to data URL if remote bucket is missing or unauthenticated.
 */
export async function uploadToSupabaseStorage(
  fileOrBlob: File | Blob,
  customFileName?: string
): Promise<string> {
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://umxkyzmccpmqazsldage.supabase.co';
  const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';
  const bucket = import.meta.env.VITE_SUPABASE_BUCKET || 'brecho-photos';

  const ext = fileOrBlob.type === 'image/png' ? 'png' : 'jpg';
  const timestamp = Date.now();
  const randomStr = Math.random().toString(36).substring(2, 8);
  const fileName = customFileName || `vintage_${timestamp}_${randomStr}.${ext}`;

  const uploadEndpoint = `${supabaseUrl}/storage/v1/object/${bucket}/${fileName}`;
  const publicUrl = `${supabaseUrl}/storage/v1/object/public/${bucket}/${fileName}`;

  try {
    const response = await fetch(uploadEndpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${supabaseKey}`,
        'apikey': supabaseKey,
        'Content-Type': fileOrBlob.type || 'image/jpeg',
        'x-upsert': 'true',
      },
      body: fileOrBlob,
    });

    if (response.ok) {
      return publicUrl;
    }

    console.warn(`Supabase storage returned status ${response.status}. Attempting fallback.`);
  } catch (err) {
    console.warn('Direct Supabase upload error:', err);
  }

  // Graceful fallback: Convert blob to base64 Data URL so the product can still be registered
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      resolve(reader.result as string);
    };
    reader.readAsDataURL(fileOrBlob);
  });
}
