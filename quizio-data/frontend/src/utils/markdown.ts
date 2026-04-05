import MarkdownIt from 'markdown-it'

// 初始化 MarkdownIt，開啟 HTML 支援（讓 Tiptap 產生的少數 HTML 標籤能正常顯示）
const md = new MarkdownIt({
    html: true,
    breaks: true, // 將 \n 轉換為 <br>
    linkify: true // 自動將 URL 轉為超連結
})

/**
 * 將 Markdown 字串轉換為 HTML 字串
 */
export const renderMarkdown = (text: string | null | undefined): string => {
    if (!text) return ''
    return md.render(text)
}
