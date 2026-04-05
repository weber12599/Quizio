import MarkdownIt from 'markdown-it'

// Initialize MarkdownIt with HTML support
const md = new MarkdownIt({
    html: true,
    breaks: true, // Convert \n to <br>
    linkify: true // Auto-convert URLs to links
})

/**
 * Render Markdown string to HTML string
 */
export const renderMarkdown = (text: string | null | undefined): string => {
    if (!text) return ''
    return md.render(text)
}
