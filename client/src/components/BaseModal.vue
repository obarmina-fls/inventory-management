<script>
// Shared accessible dialog shell. Module scope so these are shared across all open modals.
let uid = 0
// Stack of open dialogs (topmost last): only the topmost one reacts to Escape/Tab.
const openStack = []
let lockCount = 0
let prevBodyOverflow = ''

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
</script>

<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { useI18n } from '../composables/useI18n'

const props = defineProps({
  // Whether the dialog is shown. Parents pass their existing `isOpen && data` condition.
  open: { type: Boolean, default: false },
  title: { type: String, required: true },
  // Max width of the dialog, any CSS length
  maxWidth: { type: String, default: '700px' },
  // 'default' = standard modal, 'wide' = roomier header/footer used by the Tasks modal
  variant: { type: String, default: 'default', validator: (v) => ['default', 'wide'].includes(v) },
})

const emit = defineEmits(['close'])

const { t } = useI18n()
const titleId = `base-modal-title-${++uid}`
const dialogRef = ref(null)
const token = {}
let opener = null

const requestClose = () => emit('close')

const getFocusable = () =>
  dialogRef.value
    ? [...dialogRef.value.querySelectorAll(FOCUSABLE)].filter(
        (el) => el.offsetParent !== null || el === document.activeElement
      )
    : []

const onKeydown = (e) => {
  // Ignore if another dialog is stacked above this one
  if (openStack[openStack.length - 1] !== token) return

  if (e.key === 'Escape') {
    e.stopPropagation()
    requestClose()
    return
  }

  if (e.key !== 'Tab' || !dialogRef.value) return
  const items = getFocusable()
  // Nothing focusable: keep focus on the dialog itself
  if (!items.length) {
    e.preventDefault()
    dialogRef.value.focus()
    return
  }
  const first = items[0]
  const last = items[items.length - 1]
  const active = document.activeElement
  const inside = dialogRef.value.contains(active) && active !== dialogRef.value
  // Wrap at the ends; also pull focus back in if it somehow escaped (or sits on the dialog container)
  if (e.shiftKey && (active === first || !inside)) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && (active === last || !inside)) {
    e.preventDefault()
    first.focus()
  }
}

const activate = async () => {
  opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
  openStack.push(token)
  document.addEventListener('keydown', onKeydown)
  if (lockCount++ === 0) {
    prevBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
  }
  // Wait for the dialog to render before moving focus into it
  await nextTick()
  if (!dialogRef.value) return
  const [first] = getFocusable()
  ;(first || dialogRef.value).focus()
}

const deactivate = () => {
  const i = openStack.indexOf(token)
  if (i === -1) return
  openStack.splice(i, 1)
  document.removeEventListener('keydown', onKeydown)
  if (--lockCount === 0) document.body.style.overflow = prevBodyOverflow
  // Return focus to whatever opened the dialog (if it is still in the document)
  if (opener && document.contains(opener)) opener.focus()
  opener = null
}

watch(
  () => props.open,
  (isOpen) => (isOpen ? activate() : deactivate()),
  { immediate: true }
)

onBeforeUnmount(deactivate)
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-overlay" :class="`modal-overlay--${variant}`" @click="requestClose">
        <div
          ref="dialogRef"
          class="modal-container"
          :class="`modal-container--${variant}`"
          :style="{ maxWidth }"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          tabindex="-1"
          @click.stop
        >
          <div class="modal-header">
            <h3 :id="titleId" class="modal-title">{{ title }}</h3>
            <button type="button" class="close-button" :aria-label="t('common.close')" @click="requestClose">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true" focusable="false">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
              </svg>
            </button>
          </div>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-4);
}

.modal-container {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* The dialog itself is only a programmatic focus target; the ring would be noise */
.modal-container:focus {
  outline: none;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-6);
  border-bottom: 1px solid var(--border);
}

.modal-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  transition: all var(--duration) var(--ease);
}

.close-button:hover {
  background: var(--surface-muted);
  color: var(--text);
}

/* Wide variant (Tasks): no overlay padding, narrower-than-viewport width, roomier header */
.modal-overlay--wide {
  padding: 0;
}
.modal-container--wide {
  width: 90%;
  max-height: 85vh;
}
.modal-container--wide .modal-header {
  padding: var(--space-6) var(--space-8);
  border-bottom-width: 2px;
}
.modal-container--wide .modal-title {
  font-size: var(--text-2xl);
  font-weight: 600;
  margin: 0;
  letter-spacing: normal;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--duration) var(--ease);
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--duration) var(--ease);
}
.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
