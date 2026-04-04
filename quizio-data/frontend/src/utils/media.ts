/**
 * 取得圖片的完整相對路徑 (依賴 Vite/Nginx Proxy 轉發)
 * @param fid SeaweedFS 回傳的檔案 ID
 * @returns 給 <img> 標籤使用的相對路徑
 */
export const getFullMediaUrl = (fid: string): string => {
    if (!fid) return ''
    return `/media/${fid}`
}
