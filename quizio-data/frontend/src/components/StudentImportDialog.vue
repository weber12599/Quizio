<template>
    <el-dialog
        v-model="visible"
        :title="
            step === 'config'
                ? $t('students.import_students')
                : $t('students.import.result_title')
        "
        width="600px"
        @update:model-value="handleClose"
    >
        <!-- Config Phase -->
        <div v-if="step === 'config'" class="import-config">
            <!-- File Upload -->
            <div class="form-section">
                <label class="section-label">{{
                    $t('students.import.upload_button')
                }}</label>
                <el-upload
                    :auto-upload="false"
                    :show-file-list="false"
                    accept=".xlsx,.xls,.csv"
                    :on-change="handleFileChange"
                >
                    <template #default>
                        <el-button>
                            <el-icon><Upload /></el-icon>
                            {{
                                fileLoaded
                                    ? fileName
                                    : $t('students.import.upload_button')
                            }}
                        </el-button>
                    </template>
                </el-upload>
            </div>

            <!-- Sheet Selection -->
            <div v-if="fileLoaded" class="form-section">
                <label class="section-label">{{
                    $t('students.import.sheet')
                }}</label>
                <el-select v-model="selectedSheet" @change="loadSheet">
                    <el-option
                        v-for="sheet in sheetNames"
                        :key="sheet"
                        :label="sheet"
                        :value="sheet"
                    />
                </el-select>
            </div>

            <!-- Row Range -->
            <div v-if="fileLoaded" class="form-section">
                <label class="section-label">{{
                    $t('students.import.row_range')
                }}</label>
                <div class="row-range-inputs">
                    <el-input-number
                        v-model="rowStart"
                        :min="1"
                        :max="Math.max(allRows.length, 1)"
                        :disabled="!fileLoaded"
                        @change="validateRowRange"
                    />
                    <span class="range-separator">{{
                        $t('students.import.row_range_to')
                    }}</span>
                    <el-input-number
                        v-model="rowEnd"
                        :min="1"
                        :max="Math.max(allRows.length, 1)"
                        :disabled="!fileLoaded"
                        @change="validateRowRange"
                    />
                </div>
                <div class="preview-text">
                    {{
                        $t('students.import.preview_rows', {
                            count: selectedRowCount
                        })
                    }}
                </div>
            </div>

            <!-- Password Policy -->
            <div v-if="fileLoaded" class="form-section">
                <label class="section-label">{{
                    $t('students.import.password_policy')
                }}</label>
                <el-radio-group v-model="passwordPolicy">
                    <el-radio value="last4">
                        {{ $t('students.import.password_last4') }}
                    </el-radio>
                    <el-radio value="random">
                        {{ $t('students.import.password_random') }}
                    </el-radio>
                </el-radio-group>
            </div>

            <!-- Column Mapping -->
            <div v-if="fileLoaded" class="form-section">
                <label class="section-label">{{
                    $t('students.import.column_mapping')
                }}</label>
                <div class="column-mapping">
                    <!-- Student ID (required) -->
                    <div class="mapping-row">
                        <span class="mapping-label">
                            {{ $t('students.import.col_student_id') }}
                        </span>
                        <el-select
                            v-model="columnMap.student_id"
                            class="mapping-select"
                            :disabled="!fileLoaded"
                        >
                            <el-option
                                v-for="col in columnOptions"
                                :key="col"
                                :label="col"
                                :value="col"
                            />
                        </el-select>
                        <span v-if="!columnMap.student_id" class="error-text"
                            >{{ $t('common.error_required') }}</span
                        >
                    </div>

                    <!-- Name (required) -->
                    <div class="mapping-row">
                        <span class="mapping-label">
                            {{ $t('students.import.col_name') }}
                        </span>
                        <el-select
                            v-model="columnMap.name"
                            class="mapping-select"
                            :disabled="!fileLoaded"
                        >
                            <el-option
                                v-for="col in columnOptions"
                                :key="col"
                                :label="col"
                                :value="col"
                            />
                        </el-select>
                        <span v-if="!columnMap.name" class="error-text"
                            >{{ $t('common.error_required') }}</span
                        >
                    </div>

                    <!-- Email (optional) -->
                    <div class="mapping-row">
                        <span class="mapping-label">{{
                            $t('students.import.col_email')
                        }}</span>
                        <el-select
                            v-model="columnMap.email"
                            class="mapping-select"
                            :disabled="!fileLoaded"
                            clearable
                        >
                            <el-option
                                :label="$t('students.import.not_mapped')"
                                :value="''"
                            />
                            <el-option
                                v-for="col in columnOptions"
                                :key="col"
                                :label="col"
                                :value="col"
                            />
                        </el-select>
                    </div>

                    <!-- Admission Year (optional) -->
                    <div class="mapping-row">
                        <span class="mapping-label">{{
                            $t('students.import.col_admission_year')
                        }}</span>
                        <el-select
                            v-model="columnMap.admission_year"
                            class="mapping-select"
                            :disabled="!fileLoaded"
                            clearable
                        >
                            <el-option
                                :label="$t('students.import.not_mapped')"
                                :value="''"
                            />
                            <el-option
                                v-for="col in columnOptions"
                                :key="col"
                                :label="col"
                                :value="col"
                            />
                        </el-select>
                        <span v-if="yearColumnError" class="error-text">
                            ⚠️ {{ yearColumnError }}
                        </span>
                    </div>

                    <!-- Class (optional) -->
                    <div class="mapping-row">
                        <span class="mapping-label">{{
                            $t('students.import.col_class')
                        }}</span>
                        <el-select
                            v-model="columnMap.class_name"
                            class="mapping-select"
                            :disabled="!fileLoaded"
                            clearable
                        >
                            <el-option
                                :label="$t('students.import.not_mapped')"
                                :value="''"
                            />
                            <el-option
                                v-for="col in columnOptions"
                                :key="col"
                                :label="col"
                                :value="col"
                            />
                        </el-select>
                    </div>
                </div>
            </div>

            <!-- Batch Overrides -->
            <div v-if="fileLoaded" class="form-section">
                <label class="section-label">{{
                    $t('students.import.batch_settings')
                }}</label>
                <div class="batch-overrides">
                    <!-- Batch Year -->
                    <div class="mapping-row">
                        <span class="mapping-label">{{
                            $t('students.import.batch_year')
                        }}</span>
                        <el-input-number
                            v-model="batchYear"
                            clearable
                            :placeholder="
                                $t('students.import.batch_year_placeholder')
                            "
                            align="left"
                            :controls="false"
                            :style="{ width: '100%' }"
                        />
                    </div>

                    <!-- Batch Class -->
                    <div class="mapping-row">
                        <span class="mapping-label">{{
                            $t('students.import.batch_class')
                        }}</span>
                        <el-input
                            v-model="batchClass"
                            clearable
                            :placeholder="
                                $t('students.import.batch_class_placeholder')
                            "
                        />
                    </div>
                </div>
            </div>

            <!-- Preview -->
            <div v-if="fileLoaded" class="form-section">
                <label class="section-label">{{
                    $t('students.import.preview')
                }}</label>
                <el-table
                    :data="previewPayload"
                    border
                    style="width: 100%"
                    max-height="300"
                >
                    <el-table-column
                        prop="student_id"
                        label="Student ID"
                        width="100"
                    />
                    <el-table-column prop="name" label="Name" width="120" />
                    <el-table-column prop="email" label="Email" width="150" />
                    <el-table-column
                        prop="admission_year"
                        label="Year"
                        width="80"
                    />
                    <el-table-column
                        prop="class_name"
                        label="Class"
                        width="80"
                    />
                </el-table>
                <div class="preview-count">
                    {{
                        $t('students.import.preview_count', {
                            count: fullPayload.length
                        })
                    }}
                </div>
            </div>
        </div>

        <!-- Result Phase -->
        <div v-else class="import-result">
            <div class="result-summary">
                {{
                    $t('students.import.result_summary', {
                        created: importResult.created.length,
                        updated: importResult.updated.length,
                        failed: importResult.failed.length
                    })
                }}
            </div>

            <!-- Created Table -->
            <div v-if="importResult.created.length > 0" class="result-section">
                <h4>
                    {{
                        $t('students.import.result_created', {
                            count: importResult.created.length
                        })
                    }}
                </h4>
                <el-table
                    :data="importResult.created"
                    border
                    style="width: 100%"
                >
                    <el-table-column
                        prop="student_id"
                        :label="$t('students.import.result_col_student_id')"
                        width="150"
                    />
                    <el-table-column
                        prop="name"
                        :label="$t('students.import.result_col_name')"
                        min-width="150"
                    />
                </el-table>
            </div>

            <!-- Updated Table -->
            <div v-if="importResult.updated.length > 0" class="result-section">
                <h4>
                    {{
                        $t('students.import.result_updated', {
                            count: importResult.updated.length
                        })
                    }}
                </h4>
                <el-table
                    :data="importResult.updated"
                    border
                    style="width: 100%"
                >
                    <el-table-column
                        prop="student_id"
                        :label="$t('students.import.result_col_student_id')"
                        width="150"
                    />
                    <el-table-column
                        prop="name"
                        :label="$t('students.import.result_col_name')"
                        min-width="150"
                    />
                </el-table>
            </div>

            <!-- Failed Table -->
            <div v-if="importResult.failed.length > 0" class="result-section">
                <h4>
                    {{
                        $t('students.import.result_failed', {
                            count: importResult.failed.length
                        })
                    }}
                </h4>
                <el-table
                    :data="importResult.failed"
                    border
                    style="width: 100%"
                >
                    <el-table-column
                        prop="student_id"
                        :label="$t('students.import.result_col_student_id')"
                        width="150"
                    />
                    <el-table-column
                        prop="name"
                        :label="$t('students.import.result_col_name')"
                        min-width="120"
                    />
                    <el-table-column
                        prop="reason"
                        :label="$t('students.import.result_col_reason')"
                        min-width="150"
                        :formatter="formatReason"
                    />
                </el-table>
            </div>
        </div>

        <!-- Footer -->
        <template #footer>
            <span v-if="step === 'config'" class="dialog-footer">
                <el-button @click="handleClose">{{
                    $t('common.cancel')
                }}</el-button>
                <el-button
                    type="primary"
                    :disabled="!canImport"
                    :loading="importing"
                    @click="handleImport"
                >
                    {{ $t('students.import.import_button') }}
                </el-button>
            </span>
            <span v-else class="dialog-footer">
                <el-button type="primary" @click="handleCloseResult">
                    {{ $t('common.confirm') }}
                </el-button>
            </span>
        </template>
    </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'
import * as XLSX from 'xlsx'

import dataAPI, { type ApiError } from '../api'
import type { StudentCreate } from '../api/types/students'

const { t } = useI18n()

// Props and Emits
interface Props {
    modelValue: boolean
}

interface ImportResultItem {
    student_id: string
    name: string
}

interface ImportFailureItem extends ImportResultItem {
    reason: string
}

interface ImportResult {
    created: ImportResultItem[]
    updated: ImportResultItem[]
    failed: ImportFailureItem[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
    'update:modelValue': [value: boolean]
    imported: []
}>()

// Dialog visibility
const visible = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val)
})

// Phase tracking
const step = ref<'config' | 'result'>('config')

// File and data
const fileName = ref('')
const fileLoaded = ref(false)
const workbook = ref<XLSX.WorkBook | null>(null)
const sheetNames = ref<string[]>([])
const selectedSheet = ref('')
const allRows = ref<any[][]>([])
const headers = ref<string[]>([])

// Row range
const rowStart = ref(1)
const rowEnd = ref(1000)
const validateRowRange = () => {
    if (rowStart.value > rowEnd.value) {
        rowStart.value = rowEnd.value
    }
}

// Password policy
const passwordPolicy = ref<'last4' | 'random'>('random')

// Column mapping
const columnMap = ref({
    student_id: '',
    name: '',
    email: '',
    admission_year: '',
    class_name: ''
})

// Batch overrides
const batchYear = ref<number | null>(null)
const batchClass = ref<string | null>(null)

// Import state
const importing = ref(false)
const importResult = ref<ImportResult>({ created: [], updated: [], failed: [] })

// Computed properties
const fullPayload = computed(() => buildPayload())
const previewPayload = computed(() => fullPayload.value.slice(0, 10))
const selectedRowCount = computed(() => {
    if (rowStart.value > rowEnd.value) return 0
    return rowEnd.value - rowStart.value + 1
})

const canImport = computed(() => {
    return (
        fileLoaded.value &&
        columnMap.value.student_id &&
        columnMap.value.name &&
        rowStart.value <= rowEnd.value
    )
})

const columnOptions = computed(() => {
    if (!fileLoaded.value || allRows.value.length === 0) return []

    const colLengths = allRows.value.map((row) => row.length)
    if (colLengths.length === 0) return []

    const maxCols = Math.max(...colLengths)
    if (maxCols <= 0 || !isFinite(maxCols)) return []

    return Array.from({ length: maxCols }, (_, i) => indexToColLabel(i))
})

// Validate year column
const yearColumnError = computed(() => {
    if (!columnMap.value.admission_year || allRows.value.length < 2) return ''

    const yearIdx = columnCodeToIndex(columnMap.value.admission_year)
    if (yearIdx < 0) return ''

    const dataRows = allRows.value.slice(rowStart.value - 1, rowEnd.value)
    const hasInvalidYear = dataRows.some((row) => {
        const val = row[yearIdx]
        if (!val) return false
        const num = parseInt(val)
        return isNaN(num)
    })

    if (hasInvalidYear) {
        return (
            t('students.import.error_year_format') ||
            'Selected column contains non-numeric values'
        )
    }
    return ''
})

// Methods
const handleFileChange = (uploadFile: UploadFile) => {
    const file = uploadFile.raw
    if (!file) return

    // Reset state before loading new file
    fileLoaded.value = false
    allRows.value = []
    headers.value = []
    columnMap.value = {
        student_id: '',
        name: '',
        email: '',
        admission_year: '',
        class_name: ''
    }
    rowStart.value = 1
    rowEnd.value = 1000

    fileName.value = file.name
    const reader = new FileReader()

    reader.onload = (e) => {
        try {
            const data = new Uint8Array(e.target?.result as ArrayBuffer)
            const wb = XLSX.read(data, { type: 'array' })

            workbook.value = wb
            sheetNames.value = wb.SheetNames
            selectedSheet.value = wb.SheetNames[0]

            fileLoaded.value = true
            loadSheet()
        } catch (err) {
            console.error('File read error:', err)
            ElMessage.error(t('common.error'))
            fileLoaded.value = false
            allRows.value = []
        }
    }

    reader.onerror = () => {
        ElMessage.error(t('common.error'))
        fileLoaded.value = false
        allRows.value = []
    }

    reader.readAsArrayBuffer(file)
}

const loadSheet = () => {
    if (!workbook.value) return

    const sheet = workbook.value.Sheets[selectedSheet.value]
    if (!sheet) {
        ElMessage.error(t('common.error'))
        return
    }

    try {
        const rows: any[][] = []
        const range = XLSX.utils.decode_range(sheet['!ref'] || 'A1')

        for (let R = range.s.r; R <= range.e.r; ++R) {
            const row: any[] = []
            for (let C = range.s.c; C <= range.e.c; ++C) {
                const cellAddress = XLSX.utils.encode_cell({ r: R, c: C })
                const cell = sheet[cellAddress]
                let value = ''

                if (cell && cell.v !== undefined && cell.v !== null) {
                    value = String(cell.v).trim()
                }
                row.push(value)
            }
            rows.push(row)
        }

        allRows.value = rows
        headers.value = (rows[0] ?? [])
            .map((h) => String(h || ''))
            .filter((h) => h.trim() !== '')

        rowStart.value = 1
        rowEnd.value = rows.length

        // Reset column mapping when sheet changes
        columnMap.value = {
            student_id: '',
            name: '',
            email: '',
            admission_year: '',
            class_name: ''
        }
    } catch (err) {
        console.error('Sheet parsing error:', err)
        ElMessage.error(t('common.error'))
    }
}

const getPassword = (studentId: string): string => {
    if (passwordPolicy.value === 'last4') {
        const digits = studentId.replace(/\D/g, '')
        return digits.slice(-4).padStart(4, '0')
    }
    return String(Math.floor(1000 + Math.random() * 9000))
}

// Converts 0-based index to Excel column label: 0→A, 25→Z, 26→AA, 27→AB
const indexToColLabel = (i: number): string => {
    let result = ''
    let n = i + 1
    while (n > 0) {
        const rem = (n - 1) % 26
        result = String.fromCharCode(65 + rem) + result
        n = Math.floor((n - 1) / 26)
    }
    return result
}

// Inverse: 'A'→0, 'Z'→25, 'AA'→26, 'AB'→27
const columnCodeToIndex = (code: string): number => {
    if (!code) return -1
    let result = 0
    for (let i = 0; i < code.length; i++) {
        result = result * 26 + (code.charCodeAt(i) - 64)
    }
    return result - 1
}

const buildPayload = (): StudentCreate[] => {
    const {
        student_id: sidCol,
        name: nameCol,
        email: emailCol,
        admission_year: yearCol,
        class_name: classCol
    } = columnMap.value
    const dataRows = allRows.value.slice(rowStart.value - 1, rowEnd.value)

    const sidIdx = columnCodeToIndex(sidCol)
    const nameIdx = columnCodeToIndex(nameCol)
    const emailIdx = columnCodeToIndex(emailCol)
    const yearIdx = columnCodeToIndex(yearCol)
    const classIdx = columnCodeToIndex(classCol)

    return dataRows
        .filter((row) => {
            return row[sidIdx] && row[nameIdx]
        })
        .map((row) => {
            const studentId = String(row[sidIdx] || '').trim()
            let year = null as number | null
            if (batchYear.value !== null) {
                year = batchYear.value
            } else if (yearIdx >= 0 && row[yearIdx]) {
                year = parseInt(row[yearIdx]) || null
            }

            let klass = null as string | null
            if (batchClass.value) {
                klass = batchClass.value
            } else if (classIdx >= 0 && row[classIdx]) {
                klass = String(row[classIdx]).trim() || null
            }

            return {
                student_id: studentId,
                name: String(row[nameIdx] || '').trim(),
                password: getPassword(studentId),
                email:
                    emailIdx >= 0
                        ? row[emailIdx]
                            ? String(row[emailIdx]).trim()
                            : null
                        : null,
                admission_year: year,
                class_name: klass
            }
        })
}

const handleImport = async () => {
    importing.value = true
    const payload = buildPayload()

    try {
        const res = await dataAPI.bulkUpsertStudents(payload)
        importResult.value = {
            created: res.data.created,
            updated: res.data.updated,
            failed: res.data.failed
        }
        step.value = 'result'
        if (res.data.created.length > 0 || res.data.updated.length > 0) {
            ElMessage.success(t('common.success'))
        }
    } catch (err) {
        const error = err as ApiError
        ElMessage.error(error.response?.data?.detail || t('common.error'))
    } finally {
        importing.value = false
    }
}

const formatReason = (row: ImportFailureItem) => {
    if (row.reason === 'student_id_conflict') {
        return t('students.import.reason_conflict')
    } else if (row.reason === 'error') {
        return t('students.import.reason_error')
    }
    return t('students.import.reason_unknown')
}

const handleCloseResult = () => {
    if (
        importResult.value.created.length > 0 ||
        importResult.value.updated.length > 0
    ) {
        emit('imported')
    }
    handleClose()
}

const handleClose = () => {
    visible.value = false
    step.value = 'config'
    fileLoaded.value = false
    fileName.value = ''
    headers.value = []
    allRows.value = []
    workbook.value = null
    columnMap.value = {
        student_id: '',
        name: '',
        email: '',
        admission_year: '',
        class_name: ''
    }
    batchYear.value = null
    batchClass.value = null
    importResult.value = { created: [], updated: [], failed: [] }
}
</script>

<style scoped>
.import-config,
.import-result {
    padding: 10px 0;
}

.form-section {
    margin-bottom: 20px;
}

.section-label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: var(--el-text-color-primary);
}

.row-range-inputs {
    display: flex;
    gap: 8px;
    align-items: center;
}

.row-range-inputs :deep(.el-input-number) {
    flex: 0 0 100px;
}

.range-separator {
    color: var(--el-text-color-secondary);
}

.preview-text {
    margin-top: 6px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
}

.batch-overrides,
.column-mapping {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.mapping-row {
    display: flex;
    align-items: center;
    gap: 8px;
}

.mapping-label {
    min-width: 120px;
    font-size: 14px;
}

.mapping-select {
    flex: 1;
}

.error-text {
    color: var(--el-color-danger);
    font-size: 12px;
}

.result-summary {
    margin-bottom: 16px;
    padding: 10px 12px;
    background-color: var(--el-fill-color-light);
    border-radius: 4px;
    font-weight: 500;
}

.result-section {
    margin-bottom: 20px;
}

.result-section h4 {
    margin: 12px 0 8px 0;
    font-size: 14px;
    color: var(--el-text-color-primary);
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}
</style>
