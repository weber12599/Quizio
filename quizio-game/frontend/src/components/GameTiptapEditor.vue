<template>
    <div class="tiptap-wrapper">
        <div class="toolbar" v-if="editor">
            <button
                class="tool-btn"
                @click="editor.chain().focus().toggleBold().run()"
                :class="{ 'is-active': editor.isActive('bold') }"
            >
                <b>B</b>
            </button>
            <button
                class="tool-btn"
                @click="editor.chain().focus().toggleItalic().run()"
                :class="{ 'is-active': editor.isActive('italic') }"
            >
                <i>I</i>
            </button>
            <button
                class="tool-btn"
                @click="editor.chain().focus().toggleStrike().run()"
                :class="{ 'is-active': editor.isActive('strike') }"
            >
                <s>S</s>
            </button>
            <div class="divider"></div>
            <button
                class="tool-btn"
                @click="editor.chain().focus().toggleOrderedList().run()"
            >
                1.
            </button>
            <button
                class="tool-btn"
                @click="editor.chain().focus().toggleBulletList().run()"
            >
                •
            </button>
            <div class="divider"></div>
            <button
                class="tool-btn"
                @click="triggerImageUpload"
                :disabled="isUploading"
            >
                <span v-if="isUploading">⏳</span>
                <span v-else>🖼️</span>
            </button>

            <input
                type="file"
                ref="fileInput"
                accept="image/*"
                style="display: none"
                @change="handleFileInput"
            />
        </div>

        <editor-content :editor="editor" class="editor-content" />
    </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'
import { Markdown } from 'tiptap-markdown'

const props = defineProps({
    modelValue: { type: String, default: '' },
    placeholder: { type: String, default: '請輸入作答內容...' }
})
const emit = defineEmits(['update:modelValue'])

const isUploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

// 透過 Game Backend Proxy 上傳圖片
const uploadAndInsertImage = async (file: File) => {
    isUploading.value = true
    try {
        const token = localStorage.getItem('quizio_upload_token')
        if (!token) throw new Error('未取得上傳權限')

        const formData = new FormData()
        formData.append('file', file)

        // 呼叫我們在 game-backend 寫好的 proxy 路由
        const res = await fetch('/api/media/upload', {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`
            },
            body: formData
        })

        if (!res.ok) throw new Error('圖片上傳失敗')
        const data = await res.json()

        const imageUrl = `/media${data.url}`

        editor.value?.chain().focus().setImage({ src: imageUrl }).run()
    } catch (error) {
        console.error(error)
        alert('圖片上傳失敗，請確認登入狀態')
    } finally {
        isUploading.value = false
    }
}

const handleFileInput = (event: Event) => {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]
    if (file) uploadAndInsertImage(file)
    target.value = ''
}

const triggerImageUpload = () => fileInput.value?.click()

const editor = useEditor({
    extensions: [
        StarterKit,
        Image.configure({ inline: true, allowBase64: true }),
        Placeholder.configure({ placeholder: props.placeholder }),
        Markdown
    ],
    content: props.modelValue,
    onUpdate: ({ editor }) => {
        emit('update:modelValue', editor.storage.markdown.getMarkdown())
    },
    editorProps: {
        handlePaste(view, event) {
            const items = event.clipboardData?.items
            if (items) {
                for (const item of items) {
                    if (item.type.indexOf('image') === 0) {
                        const file = item.getAsFile()
                        if (file) {
                            uploadAndInsertImage(file)
                            return true
                        }
                    }
                }
            }
            return false
        }
    }
})

watch(
    () => props.modelValue,
    (value) => {
        const currentMarkdown = editor.value?.storage.markdown.getMarkdown()
        if (currentMarkdown !== value) {
            editor.value?.commands.setContent(value, false)
        }
    }
)

onBeforeUnmount(() => editor.value?.destroy())
</script>

<style scoped>
.tiptap-wrapper {
    border: 2px solid var(--border-color);
    border-radius: 10px;
    background-color: var(--input-bg);
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.toolbar {
    background-color: var(--chip-bg);
    padding: 8px;
    border-bottom: 2px solid var(--border-color);
    display: flex;
    gap: 6px;
    align-items: center;
}

.tool-btn {
    background: transparent;
    border: none;
    color: var(--text-main);
    padding: 6px 10px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1rem;
    transition: background 0.2s;
}

.tool-btn:hover {
    background: rgba(0, 0, 0, 0.05);
}
.tool-btn.is-active {
    background: var(--primary-light);
    color: var(--primary-color);
}

.divider {
    width: 2px;
    height: 20px;
    background-color: var(--border-color);
    margin: 0 4px;
}

.editor-content {
    padding: 16px;
    min-height: 120px;
    color: var(--text-main);
    font-size: 1.1rem;
}

/* 移除預設黑框與設定 Placeholder */
.editor-content :deep(.ProseMirror) {
    outline: none;
}
.editor-content :deep(.ProseMirror p.is-editor-empty:first-child::before) {
    content: attr(data-placeholder);
    float: left;
    color: #9ca3af;
    pointer-events: none;
    height: 0;
}
.editor-content :deep(img) {
    max-width: 100%;
    border-radius: 8px;
    margin: 8px 0;
}
</style>
