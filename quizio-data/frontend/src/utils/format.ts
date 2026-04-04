/**
 * 強健版：去除 Markdown 與 HTML 語法，將內容純文字化，非常適合用於單行表格預覽
 */
export const stripMarkdown = (md: string): string => {
    if (!md) return ''

    let text = md

    // 1. 攔截圖片並替換為提示字元 (包含 Markdown 圖片與 HTML 圖片)
    text = text.replace(/!\[.*?\]\(.*?\)/g, '[圖片]')
    text = text.replace(/<img[^>]*>/gi, '[圖片]')

    // 2. 攔截程式碼區塊並替換為提示字元
    text = text.replace(/```[\s\S]*?```/g, '[程式碼]')

    // 3. 去除所有殘留的 HTML 標籤 (例如 <p>, <br>, <strong>)
    text = text.replace(/<[^>]+>/g, ' ')

    // 4. 去除標題井字號 (例如 ### Heading -> Heading)
    text = text.replace(/^#{1,6}\s+/gm, '')

    // 5. 去除區塊引用 (例如 > Quote -> Quote)
    text = text.replace(/^\s*>+\s+/gm, '')

    // 6. 去除列表符號 (包含無序 -, *, + 與有序 1., 2.)
    text = text.replace(/^(\s*[-*+]\s+|\s*\d+\.\s+)/gm, '')

    // 7. 去除粗體、斜體、刪除線 (**text**, *text*, ~~text~~)
    // 這裡使用迴圈替換，確保嵌套樣式 (如 **~~text~~**) 能被拔除乾淨
    text = text.replace(/(\*\*|__|\*|_|~~)(.*?)\1/g, '$2')
    text = text.replace(/(\*\*|__|\*|_|~~)(.*?)\1/g, '$2')

    // 8. 去除超連結，僅保留顯示文字 ([text](url) -> text)
    text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')

    // 9. 去除行內程式碼 (`code` -> code)
    text = text.replace(/`([^`]+)`/g, '$1')

    // 10. 去除水平分隔線 (---, ***, ___)
    text = text.replace(/^[-*_]{3,}\s*$/gm, '')

    // 11. 單行化處理：將所有的換行符號 (\n) 轉換為空白，並壓縮多餘的連續空白
    text = text.replace(/\n+/g, ' ')
    text = text.replace(/\s{2,}/g, ' ')

    return text.trim()
}
