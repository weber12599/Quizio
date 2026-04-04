/**
 * Utility functions for client-side image processing and compression
 */

interface CompressOptions {
    maxWidth?: number
    maxHeight?: number
    quality?: number // 0.0 to 1.0 (壓縮品質，預設 0.8)
}

/**
 * 透過 HTML5 Canvas 將圖片壓縮並轉換為 WebP 格式
 * @param file 原始圖片檔案 (File)
 * @param options 壓縮選項 (最大寬高、品質)
 * @returns 回傳壓縮後的 WebP File Promise
 */
export const compressImageToWebP = (
    file: File,
    options: CompressOptions = {}
): Promise<File> => {
    return new Promise((resolve, reject) => {
        const { maxWidth = 1920, maxHeight = 1080, quality = 0.8 } = options

        // 防呆：確保傳入的是圖片檔
        if (!file.type.startsWith('image/')) {
            return reject(new Error('The provided file is not an image.'))
        }

        const reader = new FileReader()
        reader.readAsDataURL(file)

        reader.onload = (event) => {
            const img = new Image()
            img.src = event.target?.result as string

            img.onload = () => {
                let { width, height } = img

                // 智慧等比例縮放
                if (width > maxWidth || height > maxHeight) {
                    const ratio = Math.min(maxWidth / width, maxHeight / height)
                    width = width * ratio
                    height = height * ratio
                }

                // 建立 Canvas 重繪圖片
                const canvas = document.createElement('canvas')
                canvas.width = width
                canvas.height = height

                const ctx = canvas.getContext('2d')
                if (!ctx) {
                    return reject(new Error('Failed to get canvas context.'))
                }

                ctx.drawImage(img, 0, 0, width, height)

                // 轉換成輕量的 WebP 格式
                canvas.toBlob(
                    (blob) => {
                        if (!blob) {
                            return reject(
                                new Error('Canvas to Blob conversion failed.')
                            )
                        }

                        // 建立新的 WebP File 物件，準備交給 API 上傳
                        const newFilename =
                            file.name.replace(/\.[^/.]+$/, '') + '.webp'
                        const compressedFile = new File([blob], newFilename, {
                            type: 'image/webp',
                            lastModified: Date.now()
                        })
                        resolve(compressedFile)
                    },
                    'image/webp',
                    quality
                )
            }

            img.onerror = (error) => reject(error)
        }

        reader.onerror = (error) => reject(error)
    })
}
