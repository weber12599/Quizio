<template>
    <div class="grades-container">
        <h2>Grades Management</h2>

        <el-card class="filter-card">
            <el-form :inline="true" :model="filters" class="filter-form">
                <el-form-item label="Class">
                    <el-select
                        v-model="filters.class_name"
                        placeholder="Select Class"
                        clearable
                        @change="handleClassChange"
                    >
                        <el-option
                            v-for="className in classOptions"
                            :key="className"
                            :label="className"
                            :value="className"
                        />
                    </el-select>
                </el-form-item>

                <el-form-item label="Student ID">
                    <el-select
                        v-model="filters.student_id"
                        placeholder="Select Student"
                        clearable
                        filterable
                    >
                        <el-option
                            v-for="student in studentOptions"
                            :key="student.student_id"
                            :label="`${student.student_id} - ${student.name}`"
                            :value="student.student_id"
                        />
                    </el-select>
                </el-form-item>

                <el-form-item label="Exam Date">
                    <el-date-picker
                        v-model="dateRange"
                        type="daterange"
                        range-separator="To"
                        start-placeholder="Start Date"
                        end-placeholder="End Date"
                        value-format="YYYY-MM-DD"
                    />
                </el-form-item>

                <el-form-item>
                    <el-button
                        type="primary"
                        @click="fetchReport"
                        :loading="loading"
                    >
                        Search
                    </el-button>
                </el-form-item>
            </el-form>
        </el-card>

        <el-card v-loading="loading" class="table-card">
            <el-table
                v-if="reportData && reportData.students.length > 0"
                :data="reportData.students"
                border
                style="width: 100%"
            >
                <el-table-column
                    prop="class_name"
                    label="Class"
                    width="120"
                    fixed="left"
                />
                <el-table-column
                    prop="student_id"
                    label="Student ID"
                    width="150"
                    fixed="left"
                />
                <el-table-column
                    prop="name"
                    label="Name"
                    width="120"
                    fixed="left"
                />

                <el-table-column
                    v-for="exam in reportData.exams"
                    :key="exam.id"
                    :label="`${exam.title} (${exam.target_date || 'No Date'})`"
                    min-width="150"
                    align="center"
                >
                    <template #default="scope">
                        <span
                            :class="{
                                'no-score': scope.row.scores[exam.id] === 0
                            }"
                        >
                            {{ scope.row.scores[exam.id] }}
                        </span>
                    </template>
                </el-table-column>
            </el-table>

            <el-empty
                v-else-if="hasSearched && !loading"
                description="No grade records found for the selected criteria."
            />
            <el-empty
                v-else-if="!hasSearched"
                description="Please select criteria and click Search to view grades."
            />
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
    getTeacherClasses,
    getGradeReport,
    getStudents,
    type GradeReportResponse,
    type Student
} from '../api'

// State for filters
const filters = ref({
    class_name: '',
    student_id: ''
})
const dateRange = ref<[string, string] | null>(null)

// State for dropdown options
const classOptions = ref<string[]>([])
const allStudents = ref<Student[]>([])
const studentOptions = ref<Student[]>([])

// State for table data
const loading = ref(false)
const hasSearched = ref(false)
const reportData = ref<GradeReportResponse | null>(null)

// Fetch initial dropdown data
onMounted(async () => {
    try {
        // Load available classes
        const classRes = await getTeacherClasses()
        classOptions.value = classRes.data

        // Load all students for the student dropdown
        const studentRes = await getStudents()
        allStudents.value = studentRes.data
        studentOptions.value = studentRes.data
    } catch (error) {
        ElMessage.error('Failed to load initial data')
        console.error(error)
    }
})

// Handle class selection change to filter student options
const handleClassChange = (selectedClass: string) => {
    filters.value.student_id = '' // Reset student selection
    if (selectedClass) {
        studentOptions.value = allStudents.value.filter(
            (s) => s.class_name === selectedClass
        )
    } else {
        studentOptions.value = allStudents.value // Show all if no class selected
    }
}

// Fetch the pivot table report
const fetchReport = async () => {
    loading.value = true
    hasSearched.value = true

    try {
        const params: any = {
            class_name: filters.value.class_name || undefined,
            student_id: filters.value.student_id || undefined
        }

        if (dateRange.value && dateRange.value.length === 2) {
            params.date_start = dateRange.value[0]
            params.date_end = dateRange.value[1]
        }

        const res = await getGradeReport(params)
        reportData.value = res.data
    } catch (error) {
        ElMessage.error('Failed to fetch grade report')
        console.error(error)
        reportData.value = null
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
.grades-container {
    padding: 20px;
}

.filter-card {
    margin-bottom: 20px;
}

.table-card {
    min-height: 400px;
}

.no-score {
    color: #909399; /* Light gray for zero scores or absences */
}

/* Set specific widths for the filter form components */
.filter-form .el-select {
    width: 200px;
}

.filter-form .el-date-editor {
    width: 260px;
}

/* Add a bit of bottom margin in case the screen is narrow and items wrap */
.filter-form .el-form-item {
    margin-bottom: 15px;
}
</style>
