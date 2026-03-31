<template>
  <div class="questions-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>Question Bank Management</h2>
          <el-button type="primary" @click="openAddDialog">
            <el-icon><Plus /></el-icon> Add Question
          </el-button>
        </div>
      </template>

      <el-form :inline="true" class="filter-bar">
        <el-form-item label="Type">
          <el-select v-model="filterType" placeholder="Any" clearable style="width: 150px;">
            <el-option label="Single Choice" value="single" />
            <el-option label="True/False" value="boolean" />
            <el-option label="Multiple Choice" value="multiple" />
            <el-option label="Short Answer" value="short" />
            <el-option label="Essay" value="essay" />
          </el-select>
        </el-form-item>
        <el-form-item label="Difficulty">
          <el-select v-model="filterDifficulty" placeholder="Any" clearable style="width: 120px;">
            <el-option label="★ 1" :value="1" />
            <el-option label="★★ 2" :value="2" />
            <el-option label="★★★ 3" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="Lesson">
          <el-input v-model="filterLesson" placeholder="e.g., Lesson 1" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon> Search
          </el-button>
          <el-button @click="resetFilters">Reset</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="questions" v-loading="loading" border style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="Type" width="130">
          <template #default="scope">
            <el-tag :type="getTypeConfig(scope.row.type).tagType">
              {{ getTypeConfig(scope.row.type).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="Content" show-overflow-tooltip min-width="250" />
        <el-table-column label="Difficulty" width="120" align="center">
          <template #default="scope">
            <el-rate :model-value="scope.row.difficulty" :max="3" disabled text-color="#ff9900" />
          </template>
        </el-table-column>
        <el-table-column prop="lesson" label="Lesson" width="150" show-overflow-tooltip />
        <el-table-column label="Tags" min-width="150">
          <template #default="scope">
            <el-tag 
              v-for="tag in scope.row.literacy_tags" 
              :key="tag" 
              size="small" 
              class="tag-item"
            >
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="180" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="openEditDialog(scope.row)">
              <el-icon><Edit /></el-icon> Edit
            </el-button>
            <el-button size="small" type="warning" plain @click="handleArchive(scope.row)">
              <el-icon><Box /></el-icon> Archive
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogType === 'add' ? 'Add Question' : 'Edit Question'" 
      width="650px"
      destroy-on-close
    >
      <el-form :model="formData" label-width="140px">
        <el-form-item label="Question Type" required>
          <el-select v-model="formData.type" @change="handleTypeChange" :disabled="dialogType === 'edit'" style="width: 100%;">
            <el-option label="Single Choice (單選)" value="single" />
            <el-option label="True/False (是非)" value="boolean" />
            <el-option label="Multiple Choice (多選)" value="multiple" />
            <el-option label="Short Answer (簡答)" value="short" />
            <el-option label="Essay (申論)" value="essay" />
          </el-select>
        </el-form-item>

        <el-form-item label="Content" required>
          <el-input v-model="formData.content" type="textarea" :rows="3" placeholder="Enter question content..." />
        </el-form-item>

        <template v-if="['single', 'multiple'].includes(formData.type)">
          <el-divider>Options</el-divider>
          <el-form-item label="Options List" required>
            <div class="options-container">
              <div v-for="(opt, index) in formData.options" :key="index" class="option-row">
                <el-input v-model="formData.options[index]" placeholder="Option text...">
                  <template #prepend>{{ String.fromCharCode(65 + index) }}</template> <template #append>
                    <el-button @click="removeOption(index)" :icon="Delete" :disabled="formData.options.length <= 2" />
                  </template>
                </el-input>
              </div>
              <el-button @click="addOption" plain style="margin-top: 10px;">
                <el-icon><Plus /></el-icon> Add Option
              </el-button>
            </div>
          </el-form-item>
        </template>

        <el-divider>Reference Answer</el-divider>
        <el-form-item label="Correct Answer" required>
          <el-radio-group v-if="formData.type === 'single'" v-model="formData.reference_answer">
            <el-radio v-for="(opt, index) in formData.options" :key="index" :label="index">
              Option {{ String.fromCharCode(65 + index) }}
            </el-radio>
          </el-radio-group>

          <el-checkbox-group v-if="formData.type === 'multiple'" v-model="formData.reference_answer">
            <el-checkbox v-for="(opt, index) in formData.options" :key="index" :label="index">
              Option {{ String.fromCharCode(65 + index) }}
            </el-checkbox>
          </el-checkbox-group>

          <el-radio-group v-if="formData.type === 'boolean'" v-model="formData.reference_answer">
            <el-radio :label="true">True (O)</el-radio>
            <el-radio :label="false">False (X)</el-radio>
          </el-radio-group>

          <el-input 
            v-if="['short', 'essay'].includes(formData.type)" 
            v-model="formData.reference_answer" 
            type="textarea" 
            :rows="3" 
            placeholder="Enter reference answer or grading criteria..." 
          />
        </el-form-item>

        <el-divider>Metadata</el-divider>
        <el-form-item label="Difficulty">
          <el-rate v-model="formData.difficulty" :max="3" clearable style="margin-top: 6px;" />
        </el-form-item>
        
        <el-form-item label="Lesson">
          <el-input v-model="formData.lesson" placeholder="e.g., Lesson 1" />
        </el-form-item>

        <el-form-item label="Literacy Tags">
          <el-select
            v-model="formData.literacy_tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="Type and press Enter to create tags"
            style="width: 100%"
          >
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">Cancel</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitLoading">Confirm</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, Box } from '@element-plus/icons-vue'

// Setup axios instance with interceptor for dynamic JWT injection
const api = axios.create({
  baseURL: '/api'
})

api.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

// Define TypeScript interfaces based on schemas.py
interface Question {
  id: number;
  type: 'single' | 'boolean' | 'multiple' | 'short' | 'essay';
  content: string;
  options: string[] | null;
  reference_answer: any;
  difficulty: number | null;
  lesson: string | null;
  literacy_tags: string[] | null;
}

// Component State
const questions = ref<Question[]>([])
const loading = ref(false)
const submitLoading = ref(false)

// Filter State
const filterType = ref<string>('')
const filterDifficulty = ref<number | ''>('')
const filterLesson = ref<string>('')

// Form State
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const formData = ref<any>({
  id: null,
  type: 'single',
  content: '',
  options: ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
  reference_answer: 0,
  difficulty: 1,
  lesson: '',
  literacy_tags: []
})

// Type Configuration Helper
const getTypeConfig = (type: string) => {
  const configs: Record<string, { label: string, tagType: string }> = {
    single: { label: 'Single Choice', tagType: 'primary' },
    boolean: { label: 'True/False', tagType: 'success' },
    multiple: { label: 'Multiple Choice', tagType: 'warning' },
    short: { label: 'Short Answer', tagType: 'info' },
    essay: { label: 'Essay', tagType: 'danger' }
  }
  return configs[type] || { label: 'Unknown', tagType: '' }
}

// Fetch Data
const fetchQuestions = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (filterType.value) params.type = filterType.value
    if (filterDifficulty.value) params.difficulty = filterDifficulty.value
    if (filterLesson.value) params.lesson = filterLesson.value
    
    const response = await api.get('/questions', { params })
    questions.value = response.data
  } catch (error: any) {
    ElMessage.error('Failed to fetch questions.')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  fetchQuestions()
}

const resetFilters = () => {
  filterType.value = ''
  filterDifficulty.value = ''
  filterLesson.value = ''
  fetchQuestions()
}

// Dialog Handlers
const openAddDialog = () => {
  dialogType.value = 'add'
  formData.value = {
    id: null,
    type: 'single',
    content: '',
    options: ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
    reference_answer: 0,
    difficulty: 1,
    lesson: '',
    literacy_tags: []
  }
  dialogVisible.value = true
}

const openEditDialog = (row: Question) => {
  dialogType.value = 'edit'
  formData.value = {
    id: row.id,
    type: row.type,
    content: row.content,
    // Provide a default empty array if options are null to prevent UI crash
    options: row.options ? [...row.options] : [],
    // Clone array if multiple to avoid direct mutation
    reference_answer: Array.isArray(row.reference_answer) ? [...row.reference_answer] : row.reference_answer,
    difficulty: row.difficulty || 1,
    lesson: row.lesson || '',
    literacy_tags: row.literacy_tags ? [...row.literacy_tags] : []
  }
  dialogVisible.value = true
}

// Dynamic Form Handlers
const handleTypeChange = (newType: string) => {
  // Reset options and answers based on newly selected type
  if (newType === 'single') {
    formData.value.options = ['Option 1', 'Option 2', 'Option 3', 'Option 4']
    formData.value.reference_answer = 0
  } else if (newType === 'multiple') {
    formData.value.options = ['Option 1', 'Option 2', 'Option 3', 'Option 4']
    formData.value.reference_answer = []
  } else if (newType === 'boolean') {
    formData.value.options = []
    formData.value.reference_answer = true
  } else {
    formData.value.options = []
    formData.value.reference_answer = ''
  }
}

const addOption = () => {
  formData.value.options.push(`Option ${formData.value.options.length + 1}`)
}

const removeOption = (index: number) => {
  formData.value.options.splice(index, 1)
  // Ensure reference_answer stays valid if an option is removed
  if (formData.value.type === 'single' && formData.value.reference_answer >= formData.value.options.length) {
    formData.value.reference_answer = 0
  } else if (formData.value.type === 'multiple') {
    formData.value.reference_answer = formData.value.reference_answer.filter((ans: number) => ans !== index).map((ans: number) => ans > index ? ans - 1 : ans)
  }
}

// Submit Data
const submitForm = async () => {
  if (!formData.value.content) {
    ElMessage.warning('Question content is required.')
    return
  }

  submitLoading.value = true
  try {
    // Prepare payload, ensuring redundant data is stripped based on type
    const payload = { ...formData.value }
    delete payload.id // ID goes in URL for PUT, not needed for POST

    if (!['single', 'multiple'].includes(payload.type)) {
      payload.options = null // Strip options for non-choice questions
    }
    
    // Clean up empty strings
    if (payload.lesson === '') payload.lesson = null
    if (payload.literacy_tags.length === 0) payload.literacy_tags = null
    if (!payload.difficulty) payload.difficulty = 1

    if (dialogType.value === 'add') {
      await api.post('/questions', payload)
      ElMessage.success('Question added successfully')
    } else {
      await api.put(`/questions/${formData.value.id}`, payload)
      ElMessage.success('Question updated successfully')
    }
    
    dialogVisible.value = false
    fetchQuestions()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Operation failed')
  } finally {
    submitLoading.value = false
  }
}

// Delete Data
const handleArchive = (row: Question) => {
  ElMessageBox.confirm(
    'Are you sure you want to archive this question? It will be hidden from the active question bank, but kept for historical records.',
    'Archive Question',
    {
      confirmButtonText: 'Archive',
      cancelButtonText: 'Cancel',
      type: 'warning',
    }
  ).then(async () => {
    try {
      // 一樣打 DELETE API，因為後端已經改為 Soft Delete
      await api.delete(`/questions/${row.id}`)
      ElMessage.success('Question archived successfully')
      fetchQuestions()
    } catch (error) {
      ElMessage.error('Failed to archive question')
    }
  }).catch(() => {
    // Action cancelled
  })
}

// Initial Fetch
onMounted(() => {
  fetchQuestions()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-header h2 {
  margin: 0;
  font-size: 1.2rem;
  color: #303133;
}
.filter-bar {
  margin-bottom: 20px;
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
}
.tag-item {
  margin-right: 5px;
  margin-bottom: 5px;
}
.options-container {
  display: flex;
  flex-direction: column;
  width: 100%;
}
.option-row {
  margin-bottom: 10px;
  width: 100%;
}
</style>