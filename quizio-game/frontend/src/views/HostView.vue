<template>
    <div class="host-view">
        <ButtonFloatingAction />

        <div v-if="step === 'login'" class="auth-container">
            <el-card
                class="auth-card"
                shadow="hover"
                :body-style="{ padding: '32px' }"
            >
                <template #header>
                    <h2 class="text-center m-0">{{ $t('host.step_login') }}</h2>
                </template>
                <el-form
                    label-position="top"
                    @submit.prevent
                    @keyup.enter="verifyTeacher"
                    class="auth-form"
                >
                    <el-form-item :label="$t('common.username')">
                        <el-input
                            v-model="username"
                            :placeholder="$t('placeholder.username')"
                            clearable
                            size="large"
                        />
                    </el-form-item>
                    <el-form-item :label="$t('common.password')">
                        <el-input
                            v-model="password"
                            type="password"
                            show-password
                            :placeholder="$t('placeholder.password')"
                            size="large"
                        />
                    </el-form-item>
                    <el-button
                        type="primary"
                        class="w-full mt-4"
                        size="large"
                        plain
                        @click="verifyTeacher"
                        :loading="isLoading"
                    >
                        {{
                            isLoading
                                ? $t('common.connecting')
                                : $t('host.btn_login')
                        }}
                    </el-button>
                </el-form>
                <el-alert
                    v-if="errorMessage"
                    :title="errorMessage"
                    type="error"
                    show-icon
                    class="mt-4"
                    :closable="false"
                />
            </el-card>
        </div>

        <div v-else-if="step === 'setup'" class="auth-container">
            <el-card
                class="auth-card setup-card"
                shadow="hover"
                :body-style="{ padding: '32px' }"
            >
                <template #header>
                    <h2 class="text-center m-0">{{ $t('host.step_setup') }}</h2>
                </template>
                <el-form
                    label-position="top"
                    @submit.prevent
                    class="setup-form"
                >
                    <el-form-item :label="$t('common.room_pin')">
                        <el-input
                            v-model="roomPin"
                            size="large"
                            :placeholder="$t('placeholder.pin')"
                        />
                    </el-form-item>
                    <el-form-item :label="$t('host.select_class')">
                        <el-select
                            v-model="selectedClass"
                            filterable
                            clearable
                            size="large"
                            :placeholder="$t('placeholder.class')"
                            class="w-full"
                            @change="fetchExpectedStudents"
                        >
                            <el-option
                                v-for="cls in classes"
                                :key="cls"
                                :label="cls"
                                :value="cls"
                            />
                        </el-select>
                        <div
                            v-if="selectedClass"
                            class="text-muted mt-2 text-sm"
                        >
                            {{ $t('host.num_students') }}:
                            <el-tag type="info" size="small" effect="plain"
                                ><strong>{{
                                    expectedStudents.length
                                }}</strong></el-tag
                            >
                        </div>
                    </el-form-item>
                    <el-form-item>
                        <el-checkbox
                            v-model="allowGuests"
                            border
                            size="large"
                            class="w-full"
                        >
                            {{ $t('host.allow_guests') }}
                        </el-checkbox>
                    </el-form-item>
                    <el-form-item :label="$t('host.select_exam')" required>
                        <el-select
                            v-model="selectedExam"
                            filterable
                            size="large"
                            :placeholder="$t('placeholder.exam')"
                            class="w-full"
                            no-data-text="No exams found"
                        >
                            <el-option
                                v-for="exam in exams"
                                :key="exam.id"
                                :label="exam.title"
                                :value="exam.id"
                            >
                                <span style="float: left">{{
                                    exam.title
                                }}</span>
                                <span class="exam-id-meta"
                                    >ID: {{ exam.id }}</span
                                >
                            </el-option>
                        </el-select>
                    </el-form-item>
                    <el-button
                        type="primary"
                        class="w-full mt-4"
                        size="large"
                        plain
                        @click="startRoom"
                        :disabled="!selectedExam"
                        :loading="isLoading"
                    >
                        {{
                            isLoading
                                ? $t('common.connecting')
                                : $t('host.btn_create')
                        }}
                    </el-button>
                </el-form>
            </el-card>
        </div>

        <div v-else-if="step === 'room'" class="room-container">
            <el-card
                class="dashboard-card"
                shadow="never"
                :body-style="{ padding: '24px 32px' }"
            >
                <div class="dashboard-flex">
                    <div class="dashboard-title">
                        <h2>
                            {{ $t('common.room_pin') }}
                            <span class="text-danger">{{ roomPin }}</span>
                        </h2>
                        <el-tag
                            v-if="playerStats.total_count === 0"
                            type="warning"
                            effect="plain"
                            round
                            size="large"
                        >
                            <span class="flex-align-center gap-2">
                                <span class="pulse-dot mr-2"></span>
                                {{ $t('host.waiting_players') }}
                            </span>
                        </el-tag>
                    </div>

                    <div class="dashboard-stats">
                        <template v-for="(stat, i) in stats" :key="stat.label">
                            <div
                                v-if="stat.condition"
                                class="stat-item"
                                :class="{
                                    'clickable-stat':
                                        stat.label === $t('host.num_students')
                                }"
                                @click="
                                    stat.label === $t('host.num_students')
                                        ? openAttendanceDetails()
                                        : null
                                "
                            >
                                <span class="label">{{ stat.label }}</span>
                                <span class="value">{{ stat.value }}</span>
                            </div>
                            <el-divider
                                v-if="i < stats.length - 1"
                                direction="vertical"
                            />
                        </template>
                    </div>

                    <div class="dashboard-actions gap-3">
                        <el-button
                            :type="
                                isLeaderboardDisplayed ? 'warning' : 'primary'
                            "
                            plain
                            @click="toggleLeaderboard"
                            size="large"
                        >
                            🏆
                            {{
                                isLeaderboardDisplayed
                                    ? $t('host.hide_leaderboard')
                                    : $t('host.show_leaderboard')
                            }}
                        </el-button>
                        <el-button
                            type="danger"
                            plain
                            size="large"
                            @click="leaveRoom"
                            >{{ $t('common.end_game') }}</el-button
                        >
                    </div>
                </div>
            </el-card>

            <el-alert
                v-if="isReconnecting"
                :title="$t('common.network_disconnected')"
                type="warning"
                show-icon
                center
                :closable="false"
                class="mb-4"
            />

            <el-row :gutter="32" class="main-layout-grid">
                <el-col :xs="24" :md="16">
                    <el-card shadow="never" class="pool-card">
                        <template #header>
                            <div class="flex-between px-2">
                                <h3 class="m-0">
                                    {{ $t('host.question_pool') }} ({{
                                        waitingPool.length
                                    }})
                                </h3>
                                <el-button
                                    type="primary"
                                    size="large"
                                    plain
                                    :disabled="selectedQuestionIds.length === 0"
                                    @click="broadcastSelected"
                                >
                                    <el-icon class="mr-1"><Position /></el-icon>
                                    {{ $t('host.broadcast_selected') }} ({{
                                        selectedQuestionIds.length
                                    }})
                                </el-button>
                            </div>
                        </template>

                        <div class="question-list">
                            <el-checkbox-group
                                v-model="selectedQuestionIds"
                                class="flex-col-gap"
                            >
                                <GameQuestionCard
                                    v-for="eq in waitingPool"
                                    :key="eq.question_id"
                                    :question="eq.question"
                                    :index="eq.sort_order"
                                    role="host"
                                    :class="{
                                        'is-broadcasted':
                                            broadcastedIds.includes(
                                                eq.question_id
                                            )
                                    }"
                                    @showOptionDetails="
                                        (idx) =>
                                            openObjectiveDetailsDialog(eq, idx)
                                    "
                                >
                                    <template #header-left>
                                        <div class="flex-align-center gap-4">
                                            <el-checkbox
                                                :value="eq.question_id"
                                                :disabled="
                                                    broadcastedIds.includes(
                                                        eq.question_id
                                                    )
                                                "
                                                size="large"
                                            />
                                            <el-tag
                                                type="info"
                                                effect="plain"
                                                size="large"
                                                >Q{{
                                                    eq.sort_order + 1
                                                }}</el-tag
                                            >
                                            <el-tag
                                                type="info"
                                                plain
                                                size="large"
                                                >{{
                                                    formatQuestionType(
                                                        eq.question.type
                                                    )
                                                }}</el-tag
                                            >

                                            <el-tag
                                                v-if="
                                                    broadcastedIds.includes(
                                                        eq.question_id
                                                    )
                                                "
                                                type="primary"
                                                effect="plain"
                                                round
                                                size="large"
                                                class="cursor-pointer hover-scale"
                                                @click.stop="
                                                    openSubmissionDetails(
                                                        eq.question_id
                                                    )
                                                "
                                            >
                                                {{ $t('common.submitted') }}:
                                                {{
                                                    getSubmissionCount(
                                                        eq.question_id
                                                    )
                                                }}
                                                / {{ playerStats.total_count }}
                                            </el-tag>
                                        </div>
                                    </template>
                                    <template #header-right>
                                        <el-tag
                                            v-if="
                                                broadcastedIds.includes(
                                                    eq.question_id
                                                )
                                            "
                                            type="success"
                                            effect="plain"
                                            round
                                            size="large"
                                        >
                                            {{ $t('host.sent') }}
                                        </el-tag>
                                    </template>
                                    <template #actions>
                                        <div class="flex-between w-full">
                                            <div class="gap-2">
                                                <el-button
                                                    v-if="
                                                        !broadcastedIds.includes(
                                                            eq.question_id
                                                        )
                                                    "
                                                    type="success"
                                                    plain
                                                    @click="quickBroadcast(eq)"
                                                    size="large"
                                                >
                                                    <el-icon class="mr-1"
                                                        ><Position
                                                    /></el-icon>
                                                    {{
                                                        $t(
                                                            'host.quick_broadcast'
                                                        )
                                                    }}
                                                </el-button>

                                                <template v-else>
                                                    <el-button
                                                        type="success"
                                                        class="mr-1"
                                                        plain
                                                        @click="
                                                            openPinAnswersDialog(
                                                                eq
                                                            )
                                                        "
                                                        size="large"
                                                    >
                                                        <el-icon class="mr-1"
                                                            ><View
                                                        /></el-icon>
                                                        {{
                                                            $t(
                                                                'host.preview_answers'
                                                            )
                                                        }}
                                                    </el-button>
                                                    <el-badge
                                                        :value="
                                                            interactionBadge(
                                                                eq.question_id
                                                            )
                                                        "
                                                        :hidden="
                                                            interactionBadge(
                                                                eq.question_id
                                                            ) === 0
                                                        "
                                                    >
                                                        <el-button
                                                            plain
                                                            @click="
                                                                openInteractionDialog(
                                                                    eq
                                                                )
                                                            "
                                                            size="large"
                                                        >
                                                            <el-icon
                                                                class="mr-1"
                                                                ><ChatDotRound
                                                            /></el-icon>
                                                            {{
                                                                $t(
                                                                    'interaction.view_discussion'
                                                                )
                                                            }}
                                                        </el-button>
                                                    </el-badge>
                                                </template>
                                            </div>

                                            <div>
                                                <el-button
                                                    v-if="
                                                        currentDisplayedEq?.question_id !==
                                                        eq.question_id
                                                    "
                                                    type="primary"
                                                    plain
                                                    @click="
                                                        changeDisplayState(
                                                            eq,
                                                            'question'
                                                        )
                                                    "
                                                    size="large"
                                                >
                                                    <el-icon class="mr-1"
                                                        ><Monitor
                                                    /></el-icon>
                                                    {{
                                                        $t(
                                                            'host.display_on_screen'
                                                        )
                                                    }}
                                                </el-button>

                                                <el-button-group v-else>
                                                    <el-button
                                                        :type="
                                                            currentDisplayState ===
                                                            'question'
                                                                ? 'primary'
                                                                : 'default'
                                                        "
                                                        @click="
                                                            changeDisplayState(
                                                                eq,
                                                                'question'
                                                            )
                                                        "
                                                        size="large"
                                                    >
                                                        📝
                                                    </el-button>
                                                    <el-button
                                                        :type="
                                                            currentDisplayState ===
                                                            'stats'
                                                                ? 'primary'
                                                                : 'default'
                                                        "
                                                        @click="
                                                            changeDisplayState(
                                                                eq,
                                                                'stats'
                                                            )
                                                        "
                                                        size="large"
                                                    >
                                                        📊
                                                    </el-button>
                                                    <el-button
                                                        :type="
                                                            currentDisplayState ===
                                                            'answer'
                                                                ? 'primary'
                                                                : 'default'
                                                        "
                                                        @click="
                                                            changeDisplayState(
                                                                eq,
                                                                'answer'
                                                            )
                                                        "
                                                        size="large"
                                                    >
                                                        💡
                                                    </el-button>
                                                    <el-button
                                                        type="danger"
                                                        plain
                                                        @click="stopDisplaying"
                                                        size="large"
                                                    >
                                                        <el-icon
                                                            ><VideoPause
                                                        /></el-icon>
                                                    </el-button>
                                                </el-button-group>
                                            </div>
                                        </div>
                                    </template>
                                </GameQuestionCard>
                            </el-checkbox-group>
                        </div>
                    </el-card>
                </el-col>

                <el-col :xs="24" :md="8">
                    <div class="right-col-content">
                        <el-card
                            shadow="never"
                            :body-style="{ padding: '24px' }"
                        >
                            <template #header>
                                <div class="flex-between">
                                    <strong style="font-size: 1.2rem">{{
                                        $t('host.participants')
                                    }}</strong>
                                    <el-tag
                                        type="info"
                                        round
                                        effect="plain"
                                        size="large"
                                        >{{ playerStats.total_count }}</el-tag
                                    >
                                </div>
                            </template>

                            <el-empty
                                v-if="
                                    Object.keys(roomStats.clients_info || {})
                                        .length === 0
                                "
                                :description="$t('host.no_students_joined')"
                                :image-size="80"
                            />
                            <div v-else class="flex-wrap gap-3">
                                <el-tag
                                    v-for="(
                                        info, playerId
                                    ) in roomStats.clients_info"
                                    :key="playerId"
                                    size="large"
                                    effect="plain"
                                    class="player-tag cursor-pointer hover-scale"
                                    :type="
                                        info.is_guest ? 'warning' : 'primary'
                                    "
                                    @click="
                                        openStudentDrawer(
                                            String(playerId),
                                            info
                                        )
                                    "
                                >
                                    {{ info.name }}
                                </el-tag>
                            </div>
                        </el-card>
                    </div>
                </el-col>
            </el-row>
        </div>

        <el-drawer v-model="isDrawerVisible" size="600px" :with-header="false">
            <div v-if="selectedStudent" class="drawer-header flex-between mb-4">
                <div class="flex-align-center gap-3">
                    <h2 class="m-0">{{ selectedStudent.name }}</h2>
                    <el-tag
                        :type="selectedStudent.is_guest ? 'warning' : 'success'"
                        round
                        effect="plain"
                        size="large"
                    >
                        {{ selectedStudent.is_guest ? 'Guest' : 'Student' }}
                    </el-tag>
                </div>
                <el-tag
                    type="primary"
                    round
                    effect="plain"
                    size="large"
                    class="font-bold text-lg"
                >
                    {{ $t('host.progress') }}:
                    {{ getStudentProgress(selectedStudent.player_id) }}
                </el-tag>
            </div>

            <div v-if="selectedStudent" class="drawer-body flex-col gap-4 pb-4">
                <el-empty
                    v-if="broadcastedQuestionsList.length === 0"
                    :description="$t('host.no_questions_broadcasted')"
                />

                <template
                    v-for="eq in broadcastedQuestionsList"
                    :key="eq.question_id"
                >
                    <el-card
                        v-if="
                            roomStats.answers[eq.question_id]?.[
                                selectedStudent.player_id
                            ] === undefined
                        "
                        shadow="never"
                        class="unanswered-card border-dashed"
                        :body-style="{ padding: '16px 24px' }"
                    >
                        <div class="flex-between">
                            <span class="font-bold text-muted"
                                >Q{{ eq.sort_order + 1 }} -
                                {{ formatQuestionType(eq.question.type) }}</span
                            >
                            <el-tag type="info" effect="plain" size="large">{{
                                $t('host.not_answered')
                            }}</el-tag>
                        </div>
                    </el-card>

                    <GameQuestionCard
                        v-else
                        :question="eq.question"
                        :index="eq.sort_order"
                        role="client"
                        :submittedAnswer="
                            roomStats.answers[eq.question_id][
                                selectedStudent.player_id
                            ]
                        "
                        :gradingResult="
                            roomStats.gradings[eq.question_id]?.[
                                selectedStudent.player_id
                            ]
                        "
                    />
                </template>
            </div>
        </el-drawer>

        <el-dialog
            v-model="attendanceDialogVisible"
            :title="$t('host.attendance_details')"
            width="550px"
        >
            <el-row :gutter="24">
                <el-col :span="12">
                    <h4 class="text-danger mb-3">
                        {{ $t('host.missing_students') }}
                        ({{ attendanceDetails.missing.length }})
                    </h4>
                    <div class="flex-wrap gap-2">
                        <el-tag
                            v-for="student in attendanceDetails.missing"
                            :key="student.id"
                            type="danger"
                            effect="plain"
                            class="mb-2"
                            >{{ student.name }}</el-tag
                        >
                        <span
                            v-if="attendanceDetails.missing.length === 0"
                            class="text-muted"
                            >{{ $t('common.none') }}</span
                        >
                    </div>
                </el-col>
                <el-col :span="12">
                    <h4 class="text-success mb-3">
                        {{ $t('host.joined_students') }} ({{
                            attendanceDetails.joined.length
                        }})
                    </h4>
                    <div class="flex-wrap gap-2">
                        <el-tag
                            v-for="student in attendanceDetails.joined"
                            :key="student.id"
                            type="success"
                            effect="plain"
                            class="mb-2"
                            >{{ student.name }}</el-tag
                        >
                        <span
                            v-if="attendanceDetails.joined.length === 0"
                            class="text-muted"
                            >{{ $t('common.none') }}</span
                        >
                    </div>
                </el-col>
            </el-row>
        </el-dialog>

        <el-dialog
            v-model="submissionDialogVisible"
            :title="$t('host.submission_details')"
            width="550px"
        >
            <el-row :gutter="24">
                <el-col :span="12">
                    <h4 class="text-danger mb-3">
                        {{ $t('host.unsubmitted_list') }} ({{
                            submissionDetails.unsubmitted.length
                        }})
                    </h4>
                    <div class="flex-wrap gap-2">
                        <el-tag
                            v-for="elem in submissionDetails.unsubmitted"
                            :key="elem.player_id"
                            :type="elem.info.is_guest ? 'warning' : 'danger'"
                            effect="plain"
                            class="mb-2 cursor-pointer hover-scale"
                            @click="openStudentDrawer(elem.playerId, elem.info)"
                        >
                            {{ elem.info.name }}
                        </el-tag>
                        <span
                            v-if="submissionDetails.unsubmitted.length === 0"
                            class="text-muted"
                            >{{ $t('common.none') }}</span
                        >
                    </div>
                </el-col>
                <el-col :span="12">
                    <h4 class="text-success mb-3">
                        {{ $t('host.submitted_list') }} ({{
                            submissionDetails.submitted.length
                        }})
                    </h4>
                    <div class="flex-wrap gap-2">
                        <el-tag
                            v-for="elem in submissionDetails.submitted"
                            :key="elem.player_id"
                            :type="elem.info.is_guest ? 'warning' : 'success'"
                            effect="plain"
                            class="mb-2 cursor-pointer hover-scale"
                            @click="openStudentDrawer(elem.playerId, elem.info)"
                        >
                            {{ elem.info.name }}
                        </el-tag>
                        <span
                            v-if="submissionDetails.submitted.length === 0"
                            class="text-muted"
                            >{{ $t('common.none') }}</span
                        >
                    </div>
                </el-col>
            </el-row>
        </el-dialog>

        <el-dialog
            v-model="pinAnswersDialogVisible"
            :title="$t('host.preview_answers')"
            width="600px"
        >
            <template #header>
                <div class="flex-align-center gap-2">
                    <span class="el-dialog__title" style="font-size: 18px">
                        {{ $t('host.preview_answers') }}
                    </span>
                    <el-button type="primary" link @click="refreshPinAnswers">
                        <el-icon size="20"><Refresh /></el-icon>
                    </el-button>
                </div>
            </template>

            <el-alert
                v-if="
                    currentPinnedAnswer &&
                    currentPinnedAnswer.question_id ===
                        currentPinningEq?.question_id
                "
                type="success"
                show-icon
                :closable="false"
                class="mb-4"
            >
                <template #title>
                    {{ $t('host.currently_pinned') }}
                    <strong>{{ currentPinnedAnswer.name }}</strong>
                    {{ $t('host.pinned_on_screen') }}
                    <el-button
                        type="danger"
                        link
                        @click="unpinAnswer"
                        class="ml-2"
                    >
                        {{ $t('host.unpin') }}
                    </el-button>
                </template>
            </el-alert>

            <div class="flex-col gap-3 max-h-[50vh] overflow-y-auto pr-2">
                <el-empty
                    v-if="answersForPinning.length === 0"
                    :description="$t('host.no_student_answers')"
                />
                <el-card
                    v-for="ans in answersForPinning"
                    :key="ans.player_id"
                    shadow="hover"
                    :class="{
                        'border-success':
                            currentPinnedAnswer?.player_id === ans.player_id
                    }"
                >
                    <div class="flex-between mb-2">
                        <el-tag :type="ans.is_guest ? 'warning' : 'primary'">
                            {{ ans.name }}
                        </el-tag>
                        <el-button
                            :type="
                                currentPinnedAnswer?.player_id === ans.player_id
                                    ? 'success'
                                    : 'primary'
                            "
                            plain
                            size="small"
                            @click="
                                currentPinnedAnswer?.player_id ===
                                    ans.player_id &&
                                currentPinnedAnswer?.question_id ===
                                    currentPinningEq?.question_id
                                    ? unpinAnswer()
                                    : pinAnswer(ans)
                            "
                        >
                            {{
                                currentPinnedAnswer?.player_id ===
                                    ans.player_id &&
                                currentPinnedAnswer?.question_id ===
                                    currentPinningEq?.question_id
                                    ? $t('host.pinned')
                                    : $t('host.pin_action')
                            }}
                        </el-button>
                    </div>
                    <div
                        class="text-main markdown-body"
                        style="word-break: break-word"
                        v-html="renderAnswerAsHtml(ans.answer)"
                    ></div>
                </el-card>
            </div>
        </el-dialog>

        <el-dialog v-model="objectiveDialogVisible" width="650px">
            <template #header>
                <div class="flex-align-center gap-2">
                    <span class="el-dialog__title" style="font-size: 18px">
                        {{ $t('host.objective_details') }}
                    </span>
                    <el-button
                        type="primary"
                        link
                        @click="refreshObjectiveDetails"
                    >
                        <el-icon size="20"><Refresh /></el-icon>
                    </el-button>
                </div>
            </template>

            <el-tabs v-model="objectiveDetailsTab" type="border-card">
                <el-tab-pane
                    :label="
                        $t('host.tab_picked_option', {
                            option: getOptionLabel(currentObjectiveOptionIdx),
                            count: optionStudents.length
                        })
                    "
                    name="option"
                >
                    <el-empty
                        v-if="optionStudents.length === 0"
                        :description="$t('host.no_students_picked')"
                    />
                    <div v-else class="student-tag-list">
                        <el-tag
                            v-for="s in optionStudents"
                            :key="s.player_id"
                            :type="s.is_correct ? 'success' : 'danger'"
                            effect="light"
                            size="large"
                        >
                            {{ s.name }}
                        </el-tag>
                    </div>
                </el-tab-pane>

                <el-tab-pane
                    :label="
                        $t('host.tab_correct_list', {
                            count: correctStudents.length
                        })
                    "
                    name="correct"
                >
                    <el-empty
                        v-if="correctStudents.length === 0"
                        :description="$t('host.no_students_correct')"
                    />
                    <div v-else class="student-tag-list">
                        <el-tag
                            v-for="s in correctStudents"
                            :key="s.player_id"
                            type="success"
                            effect="light"
                            size="large"
                        >
                            {{ s.name }}
                        </el-tag>
                    </div>
                </el-tab-pane>

                <el-tab-pane
                    :label="
                        $t('host.tab_incorrect_list', {
                            count: incorrectStudents.length
                        })
                    "
                    name="incorrect"
                >
                    <el-empty
                        v-if="incorrectStudents.length === 0"
                        :description="$t('host.no_students_incorrect')"
                    />
                    <div v-else class="student-tag-list">
                        <el-tag
                            v-for="s in incorrectStudents"
                            :key="s.player_id"
                            type="danger"
                            effect="light"
                            size="large"
                        >
                            {{ s.name }}
                        </el-tag>
                    </div>
                </el-tab-pane>

                <el-tab-pane
                    :label="
                        $t('host.tab_unsubmitted_list', {
                            count: unsubmittedStudents.length
                        })
                    "
                    name="unsubmitted"
                >
                    <el-empty
                        v-if="unsubmittedStudents.length === 0"
                        :description="$t('host.all_submitted')"
                    />
                    <div v-else class="student-tag-list">
                        <el-tag
                            v-for="s in unsubmittedStudents"
                            :key="s.player_id"
                            type="info"
                            effect="light"
                            size="large"
                        >
                            {{ s.name }}
                        </el-tag>
                    </div>
                </el-tab-pane>
            </el-tabs>
        </el-dialog>

        <InteractionDialog
            v-model:visible="interactionDialogVisible"
            :question="currentInteractionQuestion"
            :peer-answers="currentInteractionPeerAnswers"
            :interactions="
                hostInteractions[currentInteractionQuestion?.id ?? 0] ?? {}
            "
            my-player-id="__host__"
            :is-host="true"
            @like="handleHostLike"
            @unlike="handleHostUnlike"
            @comment="handleHostComment"
            @like-comment="handleHostLikeComment"
            @unlike-comment="handleHostUnlikeComment"
        />
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { socket } from '../utils/socket'
import api from '../api'
import ButtonFloatingAction from '../components/ButtonFloatingAction.vue'
import GameQuestionCard from '../components/GameQuestionCard.vue'
import { formatQuestionType } from '../utils/locales'
import { renderMarkdown } from '../utils/markdown'
import {
    Position,
    Monitor,
    VideoPause,
    Refresh,
    ChatDotRound
} from '@element-plus/icons-vue'
import { SocketEvent } from '../types/socket'
import InteractionDialog from '../components/InteractionDialog.vue'
import type { PeerAnswer, QuestionInteractions } from '../types/interaction'

interface Exam {
    id: number
    title: string
    description?: string
    is_locked: boolean
    exam_questions: ExamQuestion[]
}
interface Question {
    id: number
    type: string
    content: string
    options?: any
    reference_answer: any
}
interface ExamQuestion {
    exam_id: number
    question_id: number
    sort_order: number
    question: Question
    score: number
}
interface ObjectiveStudent {
    player_id: string
    name: string
    is_guest: boolean
    answer: any
    is_correct: boolean | null
}

const { t } = useI18n()

// --- State ---
const step = ref<'login' | 'setup' | 'room'>('login')
const username = ref('')
const password = ref('')
const authToken = ref('')

const roomPin = ref('1234')
const classes = ref<string[]>([])
const exams = ref<Exam[]>([])
const selectedClass = ref('')
const allowGuests = ref(true)
const selectedExam = ref<number | null>(null)
const expectedStudents = ref<string[]>([])
const expectedStudentInfo = ref<Record<string, string>>({})
const pinAnswersDialogVisible = ref(false)
const answersForPinning = ref<any[]>([])
const currentPinningEq = ref<ExamQuestion | null>(null)
const currentPinnedAnswer = ref<any>(null)
const objectiveDialogVisible = ref(false)
const currentObjectiveEq = ref<ExamQuestion | null>(null)
const currentObjectiveOptionIdx = ref<number | null>(null)
const objectiveDetailsTab = ref('option')

const playerStats = ref({ student_count: 0, guest_count: 0, total_count: 0 })
const broadcastedIds = ref<number[]>([])
const currentDisplayedEq = ref<ExamQuestion | null>(null)
const currentDisplayState = ref<'question' | 'stats' | 'answer'>('question')
const selectedQuestionIds = ref<number[]>([])
const optionStudents = ref<ObjectiveStudent[]>([])
const correctStudents = ref<ObjectiveStudent[]>([])
const incorrectStudents = ref<ObjectiveStudent[]>([])
const unsubmittedStudents = ref<ObjectiveStudent[]>([])

// Drawer
const isDrawerVisible = ref(false)
const selectedStudent = ref<{
    player_id: string
    name: string
    is_guest: boolean
} | null>(null)

// Dialogs
const attendanceDialogVisible = ref(false)
const submissionDialogVisible = ref(false)
const selectedQuestionIdForDetails = ref<number | null>(null)

const roomStats = ref<any>({
    target_class: '',
    allow_guests: true,
    expected_students: [],
    answers: {},
    gradings: {},
    clients_info: {}
})

const errorMessage = ref('')
const isConnected = ref(false)
const isLoading = ref(false)
const isReconnecting = ref(false)
const isLeaderboardDisplayed = ref(false)
const recoveredDisplayedId = ref<number | null>(null)

// ── Interaction state ─────────────────────────────────────────────────────
const interactionDialogVisible = ref(false)
const currentInteractionQuestion = ref<Question | null>(null)
const currentInteractionPeerAnswers = ref<PeerAnswer[]>([])
const hostInteractions = ref<Record<number, QuestionInteractions>>({})
const seenInteractionCount = ref<Record<number, number>>({})

// --- Computeds ---
const activeExam = computed(() => {
    if (!selectedExam.value) return null
    return exams.value.find((e) => e.id === selectedExam.value)
})

const stats = computed(() => {
    return [
        {
            condition: !!roomStats.value.target_class,
            label: t('host.target_class'),
            value: roomStats.value.target_class
        },
        {
            condition: true,
            label: t('host.num_students'),
            value: roomStats.value.target_class
                ? `${playerStats.value.student_count} / ${roomStats.value.expected_students?.length || 0}`
                : `${playerStats.value.student_count}`
        },
        {
            condition: !!roomStats.value.allow_guests,
            label: t('host.num_guests'),
            value: playerStats.value.guest_count
        }
    ].filter((stat) => stat.condition)
})

const waitingPool = computed<ExamQuestion[]>(() => {
    return activeExam.value ? activeExam.value.exam_questions : []
})

const broadcastedQuestionsList = computed(() => {
    return waitingPool.value.filter((eq) =>
        broadcastedIds.value.includes(eq.question_id)
    )
})

// --- Attendance Logic ---
const openAttendanceDetails = () => {
    attendanceDialogVisible.value = true
}

const attendanceDetails = computed(() => {
    const clients = roomStats.value.clients_info || {}

    const joinedIds = Object.keys(clients)
        .filter((id) => !clients[id].is_guest)
        .map((id) => String(id))

    const joined = joinedIds.map((id) => ({
        id: String(id),
        name: clients[String(id)].name
    }))

    const missing = expectedStudents.value
        .filter((id) => !joinedIds.includes(String(id)))
        .map((id) => ({
            id: String(id),
            name: expectedStudentInfo.value[String(id)] || String(id)
        }))

    return { joined, missing }
})

// --- Submission Logic  ---
const openSubmissionDetails = (qId: number) => {
    selectedQuestionIdForDetails.value = qId
    submissionDialogVisible.value = true
}

const submissionDetails = computed(() => {
    const qId = selectedQuestionIdForDetails.value
    if (qId === null) return { submitted: [], unsubmitted: [] }

    const answers = roomStats.value.answers?.[qId] || {}
    const clients = roomStats.value.clients_info || {}

    const submitted: any[] = []
    const unsubmitted: any[] = []

    for (const [playerId, info] of Object.entries(clients)) {
        if (answers[playerId] !== undefined) {
            submitted.push({
                playerId: playerId,
                info: info
            })
        } else {
            unsubmitted.push({
                playerId: playerId,
                info: info
            })
        }
    }
    return { submitted, unsubmitted }
})

// --- Methods ---
const verifyTeacher = async () => {
    if (!username.value || !password.value) {
        errorMessage.value = 'Please fill in all fields'
        return
    }
    isLoading.value = true
    errorMessage.value = ''
    try {
        const formData = new URLSearchParams()
        formData.append('username', username.value)
        formData.append('password', password.value)

        const data: any = await api.post('/auth/login', formData.toString(), {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })

        authToken.value = data.access_token
        localStorage.setItem('host_token', data.access_token)

        const [classRes, examRes] = await Promise.all([
            api.get('/students/classes'),
            api.get('/exams/?is_locked=true&is_deleted=false')
        ])

        classes.value = classRes as unknown as string[]
        exams.value = examRes as any
        step.value = 'setup'
    } catch (error: any) {
        errorMessage.value = error.response?.data?.detail || 'Login failed.'
    } finally {
        isLoading.value = false
    }
}

const fetchExpectedStudents = async () => {
    if (!selectedClass.value) {
        expectedStudents.value = []
        expectedStudentInfo.value = {}
        return
    }
    try {
        const res: any = await api.get(
            `/students/?class_name=${selectedClass.value}`
        )
        expectedStudents.value = res.map((s: any) => String(s.student_id))

        const infoMap: Record<string, string> = {}
        res.forEach((s: any) => {
            infoMap[String(s.student_id)] = s.name
        })
        expectedStudentInfo.value = infoMap
    } catch (e) {
        console.error('Failed to fetch expected students', e)
    }
}

const startRoom = () => {
    isLoading.value = true
    socket.off('connect')
    socket.on('connect', () => {
        socket.emit('host_join_room', {
            room_pin: roomPin.value,
            token: authToken.value,
            exam_id: Number(selectedExam.value),
            target_class: selectedClass.value,
            allow_guests: allowGuests.value,
            expected_students: expectedStudents.value
        })

        isConnected.value = true
        isLoading.value = false
        step.value = 'room'
        isReconnecting.value = false
        localStorage.setItem(
            'setup_data',
            JSON.stringify({
                room_pin: roomPin.value,
                exam_id: selectedExam.value,
                target_class: selectedClass.value,
                allow_guests: allowGuests.value,
                expected_students: expectedStudents.value,
                expected_student_info: expectedStudentInfo.value
            })
        )
    })

    socket.off('disconnect')
    socket.on('disconnect', (reason) => {
        if (
            reason === 'io server disconnect' ||
            reason === 'io client disconnect'
        ) {
            isConnected.value = false
            isReconnecting.value = false
        } else {
            isReconnecting.value = true
        }
    })
    socket.connect()
}

const leaveRoom = () => {
    if (isConnected.value)
        socket.emit('end_game', {
            room_pin: roomPin.value
        })
    localStorage.removeItem('setup_data')
    localStorage.removeItem('host_token')
    isConnected.value = false
    isReconnecting.value = false
    authToken.value = ''
    selectedClass.value = ''
    selectedExam.value = null
    broadcastedIds.value = []
    selectedQuestionIds.value = []
    currentDisplayedEq.value = null
    isLeaderboardDisplayed.value = false
    step.value = 'login'
    setTimeout(() => socket.disconnect(), 100)
}

const quickBroadcast = (eq: ExamQuestion) => {
    if (broadcastedIds.value.includes(eq.question_id)) return

    const questionsToBroadcast = [{ ...eq.question, score: eq.score }]
    socket.emit('host_broadcast_questions', {
        room_pin: roomPin.value,
        questions: questionsToBroadcast
    })
    broadcastedIds.value.push(eq.question_id)
}

const broadcastSelected = () => {
    if (selectedQuestionIds.value.length === 0) return
    const questionsToBroadcast = waitingPool.value
        .filter((eq) => selectedQuestionIds.value.includes(eq.question_id))
        .map((eq) => {
            return { ...eq.question, score: eq.score }
        })

    socket.emit('host_broadcast_questions', {
        room_pin: roomPin.value,
        questions: questionsToBroadcast
    })
    broadcastedIds.value.push(...selectedQuestionIds.value)
    selectedQuestionIds.value = []
}

const changeDisplayState = (
    eq: ExamQuestion,
    state: 'question' | 'stats' | 'answer'
) => {
    currentPinnedAnswer.value = null
    socket.emit('host_pin_answer', {
        room_pin: roomPin.value,
        question_id: eq.question_id,
        pinned_answer: null
    })

    currentDisplayedEq.value = eq
    currentDisplayState.value = state
    isLeaderboardDisplayed.value = false
    socket.emit('host_display_question', {
        room_pin: roomPin.value,
        question: eq.question,
        display_state: state
    })
}

const stopDisplaying = () => {
    currentDisplayedEq.value = null
    currentPinnedAnswer.value = null
    socket.emit('host_display_question', {
        room_pin: roomPin.value,
        question: null
    })
}

const toggleLeaderboard = () => {
    if (isLeaderboardDisplayed.value) {
        isLeaderboardDisplayed.value = false
        socket.emit('host_display_question', {
            room_pin: roomPin.value,
            question: null
        })
    } else {
        isLeaderboardDisplayed.value = true
        currentDisplayedEq.value = null
        socket.emit('host_show_leaderboard', { room_pin: roomPin.value })
    }
}

const getSubmissionCount = (qId: number) => {
    if (!roomStats.value.answers || !roomStats.value.answers[qId]) return 0
    return Object.keys(roomStats.value.answers[qId]).length
}

const openStudentDrawer = (playerId: string, info: any) => {
    selectedStudent.value = { player_id: playerId, ...info }
    isDrawerVisible.value = true
}

const openObjectiveDetailsDialog = (eq: ExamQuestion, idx: number) => {
    currentObjectiveEq.value = eq
    currentObjectiveOptionIdx.value = idx
    objectiveDetailsTab.value = 'option'
    refreshObjectiveDetails()
    objectiveDialogVisible.value = true
}

const refreshObjectiveDetails = () => {
    if (!currentObjectiveEq.value) return

    const qId = currentObjectiveEq.value.question_id
    const answers = roomStats.value.answers?.[qId] || {}
    const gradings = roomStats.value.gradings?.[qId] || {}
    const clients = roomStats.value.clients_info || {}

    optionStudents.value = []
    correctStudents.value = []
    incorrectStudents.value = []
    unsubmittedStudents.value = []

    Object.entries(clients).forEach(([playerId, clientInfo]: [string, any]) => {
        const ans = answers[playerId]
        const grading = gradings[playerId]

        const studentObj: ObjectiveStudent = {
            player_id: playerId,
            name: clientInfo.name || 'Unknown',
            is_guest: clientInfo.is_guest || false,
            answer: ans,
            is_correct: grading?.is_correct ?? null
        }

        if (ans === undefined || ans === null) {
            unsubmittedStudents.value.push(studentObj)
            return
        }

        if (studentObj.is_correct === true)
            correctStudents.value.push(studentObj)
        else if (studentObj.is_correct === false)
            incorrectStudents.value.push(studentObj)

        if (currentObjectiveOptionIdx.value !== null) {
            const targetIdx = currentObjectiveOptionIdx.value
            let picked = false
            if (Array.isArray(ans)) {
                picked = ans.some((a) => Number(a) === targetIdx)
            } else {
                picked = Number(ans) === targetIdx
            }
            if (picked) optionStudents.value.push(studentObj)
        }
    })
}

const getOptionLabel = (idx: number | null) => {
    if (idx === null || !currentObjectiveEq.value) return ''
    const isBoolean = currentObjectiveEq.value.question.type === 'boolean'
    if (isBoolean)
        return idx === 0 ? t('common.true_option') : t('common.false_option')
    return String.fromCharCode(65 + idx)
}

const openPinAnswersDialog = (eq: ExamQuestion) => {
    currentPinningEq.value = eq
    refreshPinAnswers()
    pinAnswersDialogVisible.value = true
}

const refreshPinAnswers = () => {
    if (currentPinningEq.value === null) {
        return
    }

    const answers =
        roomStats.value.answers?.[currentPinningEq.value.question_id] || {}
    const clients = roomStats.value.clients_info || {}

    answersForPinning.value = Object.entries(answers).map(
        ([playerId, answer]) => {
            return {
                player_id: playerId,
                name: clients[playerId]?.name || 'Unknown',
                is_guest: clients[playerId]?.is_guest || false,
                answer: answer
            }
        }
    )
}

const formatPreviewAnswer = (answer: any) => {
    const question = currentPinningEq.value?.question
    if (!question) {
        return answer
    }

    const qType = question.type
    const isBoolean = qType === 'boolean'
    const isChoice = ['single', 'multiple', 'boolean'].includes(qType)

    if (isChoice) {
        const formatItem = (val: any) => {
            const idx = Number(val)
            if (isBoolean) {
                return idx === 0
                    ? t('common.true_option')
                    : t('common.false_option')
            }
            return String.fromCharCode(65 + idx)
        }

        if (Array.isArray(answer)) {
            return answer.map(formatItem).join(', ')
        }
        return formatItem(answer)
    }

    return answer
}

const renderAnswerAsHtml = (answer: any) => {
    const question = currentDisplayedEq.value?.question
    const formattedText = formatPreviewAnswer(answer)

    if (question && ['single', 'multiple', 'boolean'].includes(question.type)) {
        return formattedText
    }

    return renderMarkdown(formattedText || '')
}

const pinAnswer = (studentAnswerInfo: any) => {
    if (!currentPinningEq.value) {
        return
    }

    if (
        currentDisplayedEq.value?.question_id !==
            currentPinningEq.value.question_id ||
        currentDisplayState.value !== 'question'
    ) {
        changeDisplayState(currentPinningEq.value, 'question')
    }

    const payload = {
        ...studentAnswerInfo,
        question_id: currentPinningEq.value.question_id
    }
    currentPinnedAnswer.value = payload

    socket.emit('host_pin_answer', {
        room_pin: roomPin.value,
        question_id: currentPinningEq.value.question_id,
        pinned_answer: payload
    })
}

const unpinAnswer = () => {
    if (!currentPinningEq.value) {
        return
    }

    if (currentDisplayState.value !== 'question') {
        changeDisplayState(currentDisplayedEq.value!, 'question')
    }

    currentPinnedAnswer.value = null
    socket.emit('host_pin_answer', {
        room_pin: roomPin.value,
        question_id: currentPinningEq.value.question_id,
        pinned_answer: null
    })
}

const interactionBadge = (qId: number): number => {
    if (
        interactionDialogVisible.value &&
        currentInteractionQuestion.value?.id === qId
    )
        return 0
    const ia = hostInteractions.value[qId] ?? {}
    const total = Object.values(ia).reduce(
        (sum, x) => sum + x.likes.length + x.comments.length,
        0
    )
    return Math.max(0, total - (seenInteractionCount.value[qId] ?? 0))
}

const openInteractionDialog = (eq: ExamQuestion) => {
    currentInteractionQuestion.value = eq.question
    const answers = roomStats.value.answers?.[eq.question_id] || {}
    const clients = roomStats.value.clients_info || {}
    currentInteractionPeerAnswers.value = Object.entries(answers).map(
        ([playerId, answer]) => ({
            player_id: playerId,
            name: clients[playerId]?.name || 'Unknown',
            is_guest: clients[playerId]?.is_guest || false,
            answer,
            question_id: eq.question_id
        })
    )
    const ia = hostInteractions.value[eq.question_id] ?? {}
    seenInteractionCount.value[eq.question_id] = Object.values(ia).reduce(
        (sum, x) => sum + x.likes.length + x.comments.length,
        0
    )
    interactionDialogVisible.value = true
}

const handleHostLike = (ownerId: string) => {
    const qId = currentInteractionQuestion.value?.id
    if (!qId) return
    if (!hostInteractions.value[qId]) hostInteractions.value[qId] = {}
    const ia = hostInteractions.value[qId][ownerId] ?? {
        likes: [],
        comments: []
    }
    ia.likes.push({ from_id: '__host__', name: username.value })
    hostInteractions.value[qId][ownerId] = ia
    socket.emit(SocketEvent.LIKE_ANSWER, {
        room_pin: roomPin.value,
        question_id: qId,
        answer_owner_id: ownerId
    })
}

const handleHostUnlike = (ownerId: string) => {
    const qId = currentInteractionQuestion.value?.id
    if (!qId) return
    const ia = hostInteractions.value[qId]?.[ownerId]
    if (ia) ia.likes = ia.likes.filter((l) => l.from_id !== '__host__')
    socket.emit(SocketEvent.UNLIKE_ANSWER, {
        room_pin: roomPin.value,
        question_id: qId,
        answer_owner_id: ownerId
    })
}

const handleHostComment = (ownerId: string, content: string) => {
    const qId = currentInteractionQuestion.value?.id
    if (!qId) return
    if (!hostInteractions.value[qId]) hostInteractions.value[qId] = {}
    const ia = hostInteractions.value[qId][ownerId] ?? {
        likes: [],
        comments: []
    }
    ia.comments.push({
        id: `local-${Date.now()}`,
        from_id: '__host__',
        name: username.value,
        content,
        is_host: true,
        likes: []
    })
    hostInteractions.value[qId][ownerId] = ia
    socket.emit(SocketEvent.COMMENT_ANSWER, {
        room_pin: roomPin.value,
        question_id: qId,
        answer_owner_id: ownerId,
        content
    })
}

const handleHostLikeComment = (ownerId: string, commentId: string) => {
    const qId = currentInteractionQuestion.value?.id
    if (!qId) return
    const comment = hostInteractions.value[qId]?.[ownerId]?.comments.find(
        (c) => c.id === commentId
    )
    if (comment) {
        if (!comment.likes) comment.likes = []
        comment.likes.push({ from_id: '__host__', name: username.value })
    }
    socket.emit(SocketEvent.LIKE_COMMENT, {
        room_pin: roomPin.value,
        question_id: qId,
        answer_owner_id: ownerId,
        comment_id: commentId
    })
}

const handleHostUnlikeComment = (ownerId: string, commentId: string) => {
    const qId = currentInteractionQuestion.value?.id
    if (!qId) return
    const comment = hostInteractions.value[qId]?.[ownerId]?.comments.find(
        (c) => c.id === commentId
    )
    if (comment?.likes) {
        comment.likes = comment.likes.filter((l) => l.from_id !== '__host__')
    }
    socket.emit(SocketEvent.UNLIKE_COMMENT, {
        room_pin: roomPin.value,
        question_id: qId,
        answer_owner_id: ownerId,
        comment_id: commentId
    })
}

const getStudentProgress = (playerId: string) => {
    if (broadcastedIds.value.length === 0) return '0 / 0'
    let answered = 0
    broadcastedIds.value.forEach((qId) => {
        if (
            roomStats.value.answers[qId] &&
            roomStats.value.answers[qId][playerId] !== undefined
        ) {
            answered++
        }
    })
    return `${answered} / ${broadcastedIds.value.length}`
}

// --- Lifecycle ---
onMounted(() => {
    const savedToken = localStorage.getItem('host_token')
    let savedSetupData = undefined
    try {
        const jsonStr = localStorage.getItem('setup_data')
        if (jsonStr) savedSetupData = JSON.parse(jsonStr)
    } catch {}

    if (savedToken && savedSetupData && !isConnected.value) {
        authToken.value = savedToken
        roomPin.value = savedSetupData.room_pin
        selectedExam.value = savedSetupData.exam_id
        selectedClass.value = savedSetupData.target_class
        allowGuests.value = savedSetupData.allow_guests
        expectedStudents.value = savedSetupData.expected_students
        expectedStudentInfo.value = savedSetupData.expected_student_info || {}

        Promise.all([
            api.get('/students/classes'),
            api.get('/exams/?is_locked=true&is_deleted=false')
        ]).then(([classRes, examRes]) => {
            classes.value = classRes as unknown as string[]
            exams.value = examRes as any
            startRoom()
        })
    }

    socket.on('room_state', async (data) => {
        if (data.player_stats) playerStats.value = data.player_stats
        await nextTick()
    })

    socket.on('host_room_stats', (data) => {
        roomStats.value = data
    })

    socket.on(SocketEvent.INTERACTION_UPDATE, (data) => {
        if (!hostInteractions.value[data.question_id])
            hostInteractions.value[data.question_id] = {}
        hostInteractions.value[data.question_id][data.answer_owner_id] =
            data.answer_interactions
    })

    socket.on('host_recovered_state', (data) => {
        broadcastedIds.value = data.broadcasted_ids
        isLeaderboardDisplayed.value = data.is_leaderboard_displayed
        recoveredDisplayedId.value = data.displayed_question_id
        currentDisplayState.value =
            (data.display_state as 'question' | 'stats' | 'answer') ||
            'question'
        currentPinnedAnswer.value = data.pinned_answer || null

        if (recoveredDisplayedId.value && waitingPool.value.length > 0) {
            currentDisplayedEq.value =
                waitingPool.value.find(
                    (q) => q.question_id === recoveredDisplayedId.value
                ) || null
        } else {
            currentDisplayedEq.value = null
        }
    })
})

onUnmounted(() => {
    socket.disconnect()
    socket.off('room_state')
    socket.off('host_room_stats')
    socket.off('host_recovered_state')
    socket.off('connect')
    socket.off('disconnect')
    socket.off(SocketEvent.INTERACTION_UPDATE)
})
</script>

<style scoped>
/* --------------------------------------
   Base Layout & Overrides
--------------------------------------- */
.host-view {
    padding: 32px 24px;
    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
    color: var(--el-text-color-primary);

    height: 100dvh;
    max-height: 100dvh;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}
.w-full {
    width: 100%;
}
.m-0 {
    margin: 0;
}
.mb-4 {
    margin-bottom: 24px;
}
.mt-2 {
    margin-top: 12px;
}
.mt-4 {
    margin-top: 24px;
}
.px-2 {
    padding-left: 8px;
    padding-right: 8px;
}
.mr-1 {
    margin-right: 8px;
}
.pb-4 {
    padding-bottom: 24px;
}
.text-center {
    text-align: center;
}
.text-right {
    text-align: right;
}
.text-muted {
    color: var(--el-text-color-secondary);
}
.text-danger {
    color: var(--el-color-danger);
}
.text-success {
    color: var(--el-color-success);
    font-weight: bold;
}
.text-sm {
    font-size: 0.95rem;
}
.text-lg {
    font-size: 1.15rem;
}
.font-bold {
    font-weight: bold;
}

.flex-between {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.flex-align-center {
    display: flex;
    align-items: center;
}
.flex-wrap {
    display: flex;
    flex-wrap: wrap;
}
.flex-col {
    display: flex;
    flex-direction: column;
}
.gap-2 {
    gap: 8px;
}
.gap-3 {
    gap: 16px;
}
.gap-4 {
    gap: 24px;
}
.flex-col-gap {
    display: flex;
    flex-direction: column;
    gap: 32px;
}

/* --------------------------------------
   Auth & Setup Panels
--------------------------------------- */
.auth-container {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow-y: auto;
}
.auth-card {
    width: 100%;
    max-width: 520px;
    border-radius: 12px;
    background-color: var(--el-bg-color-overlay);
    margin: auto;
}
.auth-form .el-form-item,
.setup-form .el-form-item {
    margin-bottom: 28px;
}
.exam-id-meta {
    float: right;
    color: var(--el-text-color-placeholder);
    font-size: 0.9rem;
}

/* --------------------------------------
   Dashboard UI (Room State)
--------------------------------------- */
.room-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 24px;
    min-height: 0;
    height: 100%;
}
.dashboard-card {
    flex-shrink: 0;
    border-radius: 12px;
    background-color: var(--el-bg-color-overlay);
}
.dashboard-flex {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}
.dashboard-title h2 {
    margin: 0;
    font-size: 1.5rem;
    display: flex;
    align-items: center;
    gap: 20px;
}
.dashboard-stats {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.stat-item .label {
    font-size: 0.8rem;
    color: var(--el-text-color-secondary);
    text-transform: uppercase;
    font-weight: bold;
    letter-spacing: 0.5px;
}
.stat-item .value {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--el-text-color-primary);
    margin-top: 6px;
}

/* --------------------------------------
   Main Grid (Left: Pool, Right: Participants)
--------------------------------------- */
.main-layout-grid {
    flex: 1;
    min-height: 0;
    height: 100%;
}
.main-layout-grid > .el-col {
    display: flex;
    flex-direction: column;
    min-height: 0;
    height: 100%;
}
.pool-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-radius: 12px;
    background-color: var(--el-bg-color-overlay);
    min-height: 0;
    height: 100%;
}
.pool-card :deep(.el-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 0;
    min-height: 0;
    height: 100%;
}

.question-list {
    flex: 1;
    overflow-y: auto;
    height: 100%;
    padding: 32px;
    background-color: var(--el-fill-color-light);
    border-radius: 0 0 12px 12px;
    -ms-overflow-style: none;
    scrollbar-width: none;
}
question-list::-webkit-scrollbar {
    display: none;
}

.question-list :deep(.game-question-card) {
    background-color: var(--el-bg-color-overlay);
}
.question-list :deep(.game-question-card.is-broadcasted) {
    border-left-color: var(--el-color-success);
}
.question-list :deep(.el-checkbox__label) {
    display: none;
}

.right-col-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    height: 100%;
}
.right-col-content .el-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-radius: 12px;
    background-color: var(--el-bg-color-overlay);
    min-height: 0;
    height: 100%;
}
.right-col-content .el-card :deep(.el-card__body) {
    flex: 1;
    overflow-y: auto;
    height: 100%;
    padding: 24px;
}

.player-tag {
    font-size: 1.1rem;
    padding: 20px 18px;
    border-radius: 8px;
}
.cursor-pointer {
    cursor: pointer;
}
.hover-scale {
    transition:
        transform 0.2s cubic-bezier(0.2, 0, 0, 1),
        box-shadow 0.2s;
}
.hover-scale:hover {
    transform: translateY(-3px);
    box-shadow: var(--el-box-shadow-light);
}
.clickable-stat {
    cursor: pointer;
    transition:
        transform 0.2s cubic-bezier(0.2, 0, 0, 1),
        opacity 0.2s;
}
.clickable-stat:hover {
    transform: translateY(-3px);
    opacity: 0.8;
}

/* --------------------------------------
   Drawer & Pulse Styles
--------------------------------------- */
.drawer-header {
    padding: 20px 24px 20px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);
}
.border-dashed {
    border-style: dashed;
    border-color: var(--el-border-color);
    background-color: var(--el-fill-color-light);
}
.unanswered-card {
    border-radius: 12px;
}

.pulse-dot {
    width: 6px;
    height: 6px;
    background-color: var(--el-color-warning);
    border-radius: 50%;
    animation: pulse 1.5s infinite;
    display: inline-block;
}
@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(230, 162, 60, 0.5);
    }
    70% {
        box-shadow: 0 0 0 6px rgba(230, 162, 60, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(230, 162, 60, 0);
    }
}

/* --------------------------------------
   RWD (Mobile View)
--------------------------------------- */
@media (max-width: 992px) {
    /* 手機版：解開鎖死的 100dvh，讓整頁可以自然捲動 */
    .host-view {
        height: 100dvh !important;
        overflow-y: auto !important;
    }
    .main-layout-grid {
        flex-direction: column;
        flex-wrap: wrap; /* 手機版允許換行 */
        gap: 24px;
    }

    /* 解除所有強制的 height: 100% 限制，讓子元件自由生長 */
    .room-container,
    .main-layout-grid,
    .main-layout-grid > .el-col,
    .pool-card,
    .pool-card :deep(.el-card__body),
    .right-col-content,
    .right-col-content .el-card,
    .right-col-content .el-card :deep(.el-card__body),
    .question-list {
        flex: none !important;
        min-height: auto !important;
        height: auto !important;
    }

    /* 為了避免手機版清單無限拉長，給予這兩區一個最大高度的內部捲軸 */
    .question-list {
        max-height: 50vh;
        overflow-y: auto !important;
    }
    .right-col-content .el-card :deep(.el-card__body) {
        max-height: 40vh;
        overflow-y: auto !important;
    }

    .dashboard-flex {
        flex-direction: column;
        align-items: flex-start;
    }
    .dashboard-stats {
        width: 100%;
        justify-content: space-around;
        padding: 16px 0;
    }
    .dashboard-actions {
        width: 100%;
        display: flex;
        justify-content: flex-end;
    }
}
</style>
