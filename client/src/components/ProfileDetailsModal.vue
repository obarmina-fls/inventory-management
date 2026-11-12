<template>
  <BaseModal :open="isOpen" :title="t('profileDetails.title')" max-width="600px" @close="close">
    <div class="modal-body">
      <div class="profile-section">
        <div class="avatar-section">
          <div class="avatar-xl">
            {{ getInitials(currentUser.name) }}
          </div>
          <h4 class="profile-name">{{ currentUser.name }}</h4>
          <p class="profile-job-title">{{ currentUser.jobTitle }}</p>
        </div>

        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">{{ t('profileDetails.email') }}</div>
            <div class="info-value">{{ currentUser.email }}</div>
          </div>

          <div class="info-item">
            <div class="info-label">{{ t('profileDetails.department') }}</div>
            <div class="info-value">{{ currentUser.department }}</div>
          </div>

          <div class="info-item">
            <div class="info-label">{{ t('profileDetails.location') }}</div>
            <div class="info-value">{{ currentUser.location }}</div>
          </div>

          <div class="info-item">
            <div class="info-label">{{ t('profileDetails.phone') }}</div>
            <div class="info-value">{{ currentUser.phone }}</div>
          </div>

          <div class="info-item">
            <div class="info-label">{{ t('profileDetails.joinDate') }}</div>
            <div class="info-value">{{ formatDate(currentUser.joinDate) }}</div>
          </div>

          <div class="info-item">
            <div class="info-label">{{ t('profileDetails.employeeId') }}</div>
            <div class="info-value">CC-{{ currentUser.id.toString().padStart(5, '0') }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-footer">
      <button class="btn-secondary" @click="close">{{ t('profileDetails.close') }}</button>
    </div>
  </BaseModal>
</template>

<script setup>
import { useAuth } from '../composables/useAuth'
import BaseModal from './BaseModal.vue'
import { useI18n } from '../composables/useI18n'

const { currentUser, getInitials } = useAuth()
const { t, currentLocale } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
  return date.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>

<style scoped>
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-8);
}

.profile-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--border);
}

.avatar-xl {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: var(--accent);
  color: var(--accent-ink);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: var(--text-3xl);
  letter-spacing: 0.025em;
  box-shadow: var(--shadow-md);
}

.profile-name {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text);
  margin: 0;
}

.profile-job-title {
  font-size: var(--text-lg);
  color: var(--text-muted);
  margin: 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--space-6);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.info-label {
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.info-value {
  font-size: var(--text-md);
  color: var(--text);
  font-weight: 500;
}

.modal-footer {
  padding: var(--space-6);
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.btn-secondary {
  padding: var(--space-2) var(--space-5);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  font-weight: 500;
  font-size: var(--text-base);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration) var(--ease);
  font-family: inherit;
}

.btn-secondary:hover {
  background: var(--border);
  border-color: var(--border-strong);
}
</style>
