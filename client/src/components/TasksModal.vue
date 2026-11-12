<template>
  <BaseModal :open="isOpen" :title="t('tasks.title')" max-width="900px" variant="wide" @close="close">
    <div class="modal-body">
      <!-- Add Task Form -->
      <div class="task-form">
        <div class="form-row">
          <div class="form-group flex-1">
            <label for="task-title">{{ t('tasks.taskTitle') }}</label>
            <input
              id="task-title"
              v-model="newTask.title"
              type="text"
              :placeholder="t('tasks.taskTitlePlaceholder')"
              class="task-input"
              @keyup.enter="handleAddTask"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="task-priority">{{ t('tasks.priority') }}</label>
            <BaseSelect id="task-priority" v-model="newTask.priority" size="lg">
              <option value="high">{{ t('priority.high') }}</option>
              <option value="medium">{{ t('priority.medium') }}</option>
              <option value="low">{{ t('priority.low') }}</option>
            </BaseSelect>
          </div>

          <div class="form-group">
            <label for="task-due-date">{{ t('tasks.dueDate') }}</label>
            <input id="task-due-date" v-model="newTask.dueDate" type="date" class="task-input" />
          </div>

          <div class="form-group-btn">
            <button @click="handleAddTask" class="task-add-btn" :disabled="!newTask.title.trim() || !newTask.dueDate">
              {{ t('tasks.addTask') }}
            </button>
          </div>
        </div>
      </div>

      <div class="tasks-divider"></div>

      <!-- Tasks List -->
      <div v-if="sortedTasks.length === 0" class="no-tasks">
        {{ t('tasks.noTasks') }}
      </div>

      <div v-else class="tasks-list">
        <div
          v-for="task in sortedTasks"
          :key="task.id"
          class="task-item"
          :class="[`priority-${task.priority}`, { completed: task.status === 'completed' }]"
        >
          <div class="task-header">
            <div class="task-check-title">
              <input
                type="checkbox"
                :checked="task.status === 'completed'"
                @change="$emit('toggle-task', task.id)"
                class="task-checkbox"
              />
              <span class="task-title" @click="$emit('toggle-task', task.id)">{{ task.title }}</span>
            </div>
            <button @click="$emit('delete-task', task.id)" class="task-delete-btn" title="Delete task">×</button>
          </div>

          <div class="task-footer">
            <span class="priority-badge" :class="task.priority">
              {{ translatePriority(task.priority) }}
            </span>
            <div class="task-due-date">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <rect x="2" y="3" width="10" height="9" rx="1" stroke="currentColor" stroke-width="1.2" />
                <path
                  d="M4.5 1.5V4.5M9.5 1.5V4.5M2 6H12"
                  stroke="currentColor"
                  stroke-width="1.2"
                  stroke-linecap="round"
                />
              </svg>
              {{ formatDueDate(task.dueDate) }}
            </div>
            <span class="status-badge" :class="getStatusClass(task.dueDate, task.status)">
              {{ getStatusText(task.dueDate, task.status) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-footer">
      <button class="btn-secondary" @click="close">{{ t('profileDetails.close') }}</button>
    </div>
  </BaseModal>
</template>

<script>
import { ref, computed } from 'vue'
import BaseSelect from './BaseSelect.vue'
import BaseModal from './BaseModal.vue'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'TasksModal',
  components: { BaseSelect, BaseModal },
  props: {
    isOpen: {
      type: Boolean,
      required: true,
    },
    tasks: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['close', 'add-task', 'delete-task', 'toggle-task'],
  setup(props, { emit }) {
    const { t, currentLocale } = useI18n()
    const newTask = ref({
      title: '',
      priority: 'medium',
      dueDate: '',
    })

    const sortedTasks = computed(() => {
      // Don't sort - just return tasks in their current order (newest first)
      return [...props.tasks]
    })

    const close = () => {
      emit('close')
    }

    const handleAddTask = () => {
      if (newTask.value.title.trim() && newTask.value.dueDate) {
        emit('add-task', {
          title: newTask.value.title.trim(),
          priority: newTask.value.priority,
          dueDate: newTask.value.dueDate,
        })
        newTask.value = {
          title: '',
          priority: 'medium',
          dueDate: '',
        }
      }
    }

    const formatDueDate = (dateString) => {
      const date = new Date(dateString)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const dueDate = new Date(date)
      dueDate.setHours(0, 0, 0, 0)

      const diffTime = dueDate - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      const isJapanese = currentLocale.value === 'ja'

      if (diffDays === 0) return isJapanese ? '今日' : 'today'
      if (diffDays === 1) return isJapanese ? '明日' : 'tomorrow'
      if (diffDays === -1) return isJapanese ? '昨日' : 'yesterday'
      if (diffDays < 0) return isJapanese ? `${Math.abs(diffDays)}日前` : `${Math.abs(diffDays)} days ago`
      if (diffDays < 7) return isJapanese ? `${diffDays}日後` : `in ${diffDays} days`

      const locale = isJapanese ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined,
      })
    }

    const getStatusClass = (dueDate, status) => {
      if (status === 'completed') return 'completed'

      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const due = new Date(dueDate)
      due.setHours(0, 0, 0, 0)

      const diffTime = due - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays < 0) return 'overdue'
      if (diffDays <= 1) return 'urgent'
      return 'upcoming'
    }

    const getStatusText = (dueDate, status) => {
      const isJapanese = currentLocale.value === 'ja'

      if (status === 'completed') return isJapanese ? '完了' : 'Completed'

      const statusClass = getStatusClass(dueDate, status)
      if (statusClass === 'overdue') return isJapanese ? '期限超過' : 'Overdue'
      if (statusClass === 'urgent') return isJapanese ? 'もうすぐ期限' : 'Due Soon'
      return isJapanese ? '予定' : 'Upcoming'
    }

    const translatePriority = (priority) => {
      const priorityMap = {
        high: t('priority.high'),
        medium: t('priority.medium'),
        low: t('priority.low'),
      }
      return priorityMap[priority] || priority
    }

    return {
      t,
      newTask,
      sortedTasks,
      close,
      handleAddTask,
      formatDueDate,
      getStatusClass,
      getStatusText,
      translatePriority,
    }
  },
}
</script>

<style scoped>
.modal-body {
  padding: var(--space-8);
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: var(--space-6) var(--space-8);
  border-top: 2px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-4);
}

.btn-secondary {
  padding: var(--space-3) var(--space-6);
  background: var(--surface-muted);
  color: var(--text-secondary);
  border: none;
  border-radius: var(--radius-lg);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration) var(--ease);
}

.btn-secondary:hover {
  background: var(--border);
}

/* Task Form */
.task-form {
  background: var(--surface-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  margin-bottom: var(--space-6);
}

.form-row {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex: 1;
}

.form-group.flex-1 {
  flex: 1;
}

.form-group-btn {
  display: flex;
  align-items: flex-end;
}

label {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-secondary);
}

.task-input {
  padding: var(--space-3);
  border: 2px solid var(--border);
  border-radius: var(--radius-lg);
  font-size: var(--text-md);
  transition: border-color var(--duration) var(--ease);
  font-family: inherit;
}

.task-input:focus {
  outline: none;
  border-color: var(--accent);
}

.task-add-btn {
  padding: var(--space-3) var(--space-6);
  background: var(--accent);
  color: var(--accent-ink);
  border: none;
  border-radius: var(--radius-lg);
  font-weight: 600;
  cursor: pointer;
  transition:
    transform var(--duration) var(--ease),
    opacity var(--duration) var(--ease);
  white-space: nowrap;
  height: fit-content;
}

.task-add-btn:hover:not(:disabled) {
  transform: none;
}

.task-add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tasks-divider {
  height: 1px;
  background: var(--border);
  margin: var(--space-8) 0;
}

.no-tasks {
  text-align: center;
  padding: var(--space-12);
  color: var(--text-muted);
  font-size: var(--text-xl);
  font-style: italic;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.task-item {
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-4) var(--space-5);
  transition: all var(--duration) var(--ease);
}

.task-item:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.task-item.priority-high {
  border-left: 4px solid var(--danger);
}

.task-item.priority-medium {
  border-left: 4px solid var(--warning);
}

.task-item.priority-low {
  border-left: 4px solid var(--info);
}

.task-item.completed {
  opacity: 0.6;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-3);
  gap: var(--space-4);
}

.task-check-title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
}

.task-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--accent);
  flex-shrink: 0;
}

.task-title {
  flex: 1;
  cursor: pointer;
  user-select: none;
  color: var(--text);
  font-size: var(--text-lg);
  font-weight: 600;
  line-height: 1.4;
}

.task-item.completed .task-title {
  text-decoration: line-through;
  color: var(--text-subtle);
}

.task-delete-btn {
  width: 28px;
  height: 28px;
  background: var(--danger);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-xl);
  line-height: 1;
  cursor: pointer;
  transition: all var(--duration) var(--ease);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  flex-shrink: 0;
}

.task-delete-btn:hover {
  background: var(--danger);
  transform: scale(1.1);
}

.task-footer {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.priority-badge {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  letter-spacing: 0.025em;
}

.priority-badge.high {
  background: var(--danger-soft);
  color: var(--danger-ink);
}

.priority-badge.medium {
  background: var(--warning-soft);
  color: var(--warning-ink);
}

.priority-badge.low {
  background: var(--info-soft);
  color: var(--info-ink);
}

.task-due-date {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.task-due-date svg {
  color: var(--text-subtle);
}

.status-badge {
  font-size: var(--text-xs);
  font-weight: 600;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  margin-left: auto;
}

.status-badge.overdue {
  background: var(--danger-soft);
  color: var(--danger-ink);
}

.status-badge.urgent {
  background: var(--warning-soft);
  color: var(--warning-ink);
}

.status-badge.upcoming {
  background: var(--info-soft);
  color: var(--info-ink);
}

.status-badge.completed {
  background: var(--success-soft);
  color: var(--success-ink);
}
</style>
