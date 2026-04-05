<template>
    <div class="tiptap-wrapper" :class="{ 'is-minimal': minimal }">
        <div class="toolbar" v-if="editor">
            <el-button-group>
                <el-button
                    size="small"
                    @click="editor.chain().focus().toggleBold().run()"
                    :class="{ 'is-active': editor.isActive('bold') }"
                >
                    <span class="font-bold">B</span>
                </el-button>
                <el-button
                    size="small"
                    @click="editor.chain().focus().toggleItalic().run()"
                    :class="{ 'is-active': editor.isActive('italic') }"
                >
                    <span class="italic">I</span>
                </el-button>
                <el-button
                    size="small"
                    @click="editor.chain().focus().toggleStrike().run()"
                    :class="{ 'is-active': editor.isActive('strike') }"
                >
                    <span class="line-through">S</span>
                </el-button>
                <el-button
                    size="small"
                    @click="editor.chain().focus().toggleCodeBlock().run()"
                    :class="{ 'is-active': editor.isActive('codeBlock') }"
                >
                    &lt;/&gt;
                </el-button>
            </el-button-group>

            <el-button-group class="ml-2">
                <el-button
                    size="small"
                    @click="editor.chain().focus().toggleOrderedList().run()"
                >
                    1.
                </el-button>
                <el-button
                    size="small"
                    @click="editor.chain().focus().toggleBulletList().run()"
                >
                    •
                </el-button>
            </el-button-group>

            <el-button
                size="small"
                @click="triggerImageUpload"
                :loading="isUploading"
            >
                🖼️
            </el-button>

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
import { ElMessage } from 'element-plus'

// 引入我們前面實作的工具
import { compressImageToWebP } from '../utils/image'
import { uploadMedia } from '../api/index'
import { getFullMediaUrl } from '../utils/media'

const props = defineProps({
    modelValue: {
        type: String,
        default: ''
    },
    // minimal 模式用來隱藏部分工具列（適合放在選項 options 裡）
    minimal: {
        type: Boolean,
        default: false
    },
    placeholder: {
        type: String,
        default: '輸入題目內容...'
    }
})

const emit = defineEmits(['update:modelValue'])

const isUploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

// 核心：圖片壓縮與上傳流程
const uploadAndInsertImage = async (file: File) => {
    isUploading.value = true
    try {
        // 1. 本機壓縮轉 WebP
        const compressedFile = await compressImageToWebP(file, {
            maxWidth: 1200,
            maxHeight: 1200
        })
        // 2. 呼叫後端代傳至 SeaweedFS
        const res = await uploadMedia(compressedFile)
        // 3. 取得 Nginx 快取網址
        const url = getFullMediaUrl(res.fid)
        // 4. 插入編輯器
        editor.value?.chain().focus().setImage({ src: url }).run()
    } catch (error) {
        console.error('Image upload failed:', error)
        ElMessage.error('圖片上傳失敗')
    } finally {
        isUploading.value = false
    }
}

const handleFileInput = (event: Event) => {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]
    if (file) {
        uploadAndInsertImage(file)
    }
    target.value = '' // Reset input
}

const triggerImageUpload = () => {
    fileInput.value?.click()
}

// 初始化 Tiptap 編輯器
const editor = useEditor({
    extensions: [
        StarterKit,
        Image.configure({
            inline: true,
            allowBase64: true
        }),
        Placeholder.configure({
            placeholder: props.placeholder
        }),
        // Markdown 擴充：讓 Tiptap 能讀懂並輸出 Markdown！
        Markdown
    ],
    content: props.modelValue, // 初始化載入
    onUpdate: ({ editor }) => {
        // 編輯器更新時，取得 Markdown 字串並 emit 給外部的 v-model
        emit('update:modelValue', editor.storage.markdown.getMarkdown())
    },
    editorProps: {
        // 攔截貼上 (Ctrl+V)
        handlePaste(view, event) {
            const items = event.clipboardData?.items
            if (items) {
                for (const item of items) {
                    if (item.type.indexOf('image') === 0) {
                        const file = item.getAsFile()
                        if (file) {
                            uploadAndInsertImage(file)
                            return true // 阻止預設貼上行為
                        }
                    }
                }
            }
            return false
        },
        // 攔截拖曳 (Drag & Drop)
        handleDrop(view, event, slice, moved) {
            if (
                !moved &&
                event.dataTransfer &&
                event.dataTransfer.files &&
                event.dataTransfer.files[0]
            ) {
                const file = event.dataTransfer.files[0]
                if (file.type.indexOf('image') === 0) {
                    uploadAndInsertImage(file)
                    return true
                }
            }
            return false
        }
    }
})

// 監聽外部傳入的 value 改變 (例如點擊編輯不同的題目時)
watch(
    () => props.modelValue,
    (value) => {
        // 避免內部更新觸發循環
        const currentMarkdown = editor.value?.storage.markdown.getMarkdown()
        if (currentMarkdown !== value) {
            editor.value?.commands.setContent(value, false)
        }
    }
)

onBeforeUnmount(() => {
    editor.value?.destroy()
})
</script>

<style scoped>
.tiptap-wrapper {
    border: 1px solid var(--el-border-color);
    border-radius: 4px;
    background-color: var(--el-bg-color);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    width: 100%;
}

.toolbar {
    background-color: var(--el-fill-color-light);
    padding: 8px;
    border-bottom: 1px solid var(--el-border-color);
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: center;
}

.editor-content {
    padding: 12px;
    min-height: 100px;
    cursor: text;
}

.is-minimal .editor-content {
    min-height: 0px;
}

/* 覆寫 Prosemirror 預設輪廓 */
.editor-content :deep(.ProseMirror) {
    outline: none;
    min-height: inherit;
}

/* 佔位符樣式 */
.editor-content :deep(.ProseMirror p.is-editor-empty:first-child::before) {
    content: attr(data-placeholder);
    float: left;
    color: var(--el-text-color-placeholder);
    pointer-events: none;
    height: 0;
}

/* 圖片在編輯器內的預設樣式 */
.editor-content :deep(img) {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 8px 0;
    box-shadow: var(--el-box-shadow-light);
}

.is-active {
    background-color: var(--el-color-primary-light-9) !important;
    color: var(--el-color-primary) !important;
    border-color: var(--el-color-primary-light-5) !important;
}

/* ==========================================
   Tiptap (ProseMirror) 內部排版微調
========================================== */

/* 1. 調整段落換行間距與行高 */
.editor-content :deep(.ProseMirror p) {
    margin: 0.4em 0; /* 大幅縮小預設的上下 margin (原本通常是 1em) */
    line-height: 1.5; /* 保持易讀的舒適行高 */
}

/* 2. 調整列表縮排與整體間距 */
.editor-content :deep(.ProseMirror ul),
.editor-content :deep(.ProseMirror ol) {
    padding-left: 1.5em; /* 將預設過大的縮排 (40px) 縮小為 1.5em */
    margin: 0.4em 0; /* 縮小列表區塊上下的 margin */
}

/* 3. 調整清單項目的間距 */
.editor-content :deep(.ProseMirror li) {
    margin: 0.2em 0;
}

/* 4. 清單項目內的段落不需要額外 margin，避免撐開列表 */
.editor-content :deep(.ProseMirror li p) {
    margin: 0;
}

/* 5. (選配) 針對程式碼區塊的間距與圓角微調 */
.editor-content :deep(.ProseMirror pre) {
    margin: 0.5em 0;
    padding: 0.75em 1em;
    border-radius: 6px;
    background-color: var(--el-fill-color-darker);
    color: var(--el-text-color-primary);
}
</style>
