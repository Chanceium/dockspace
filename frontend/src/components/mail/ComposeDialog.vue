<template>
  <v-dialog
    :model-value="modelValue"
    max-width="800"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title class="d-flex align-center pa-4 border-b">
        <span>{{ title }}</span>
        <v-spacer />
        <v-btn
          icon="ri-close-line"
          variant="text"
          @click="$emit('update:modelValue', false)"
        />
      </v-card-title>

      <v-card-text class="pa-4">
        <v-form @submit.prevent="handleSend">
          <v-text-field
            v-model="formData.to"
            label="To"
            :rules="[rules.required, rules.email]"
            density="comfortable"
            class="mb-2"
          />

          <v-expand-transition>
            <v-text-field
              v-if="showCc"
              v-model="formData.cc"
              label="Cc"
              :rules="[rules.email]"
              density="comfortable"
              class="mb-2"
            />
          </v-expand-transition>

          <v-expand-transition>
            <v-text-field
              v-if="showBcc"
              v-model="formData.bcc"
              label="Bcc"
              :rules="[rules.email]"
              density="comfortable"
              class="mb-2"
            />
          </v-expand-transition>

          <div class="d-flex gap-2 mb-2">
            <v-btn
              v-if="!showCc"
              size="small"
              variant="text"
              @click="showCc = true"
            >
              Cc
            </v-btn>
            <v-btn
              v-if="!showBcc"
              size="small"
              variant="text"
              @click="showBcc = true"
            >
              Bcc
            </v-btn>
          </div>

          <v-text-field
            v-model="formData.subject"
            label="Subject"
            :rules="[rules.required]"
            density="comfortable"
            class="mb-2"
          />

          <v-textarea
            v-model="formData.body"
            label="Message"
            rows="12"
            auto-grow
            class="mb-2"
          />

          <div class="d-flex align-center gap-2">
            <v-btn
              color="primary"
              :loading="sending"
              :disabled="!isFormValid"
              @click="handleSend"
            >
              <v-icon start>
                ri-send-plane-line
              </v-icon>
              Send
            </v-btn>

            <v-btn
              variant="text"
              @click="$emit('update:modelValue', false)"
            >
              Discard
            </v-btn>

            <v-spacer />

            <v-btn
              icon="ri-attachment-line"
              variant="text"
            />

            <v-btn
              icon="ri-image-line"
              variant="text"
            />

            <v-btn
              icon="ri-link"
              variant="text"
            />
          </div>
        </v-form>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Props {
  modelValue: boolean
  title?: string
  to?: string
  subject?: string
  body?: string
  cc?: string
  bcc?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: 'New Message',
  to: '',
  subject: '',
  body: '',
  cc: '',
  bcc: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  send: [data: {
    to: string
    subject: string
    body: string
    cc?: string
    bcc?: string
    replyTo?: string
  }]
}>()

const showCc = ref(false)
const showBcc = ref(false)
const sending = ref(false)

const formData = ref({
  to: props.to,
  subject: props.subject,
  body: props.body,
  cc: props.cc,
  bcc: props.bcc,
})

// Watch for prop changes (e.g., when replying/forwarding)
watch(() => props.to, (newVal) => {
  formData.value.to = newVal
})

watch(() => props.subject, (newVal) => {
  formData.value.subject = newVal
})

watch(() => props.body, (newVal) => {
  formData.value.body = newVal
})

watch(() => props.cc, (newVal) => {
  formData.value.cc = newVal
  if (newVal) showCc.value = true
})

watch(() => props.bcc, (newVal) => {
  formData.value.bcc = newVal
  if (newVal) showBcc.value = true
})

const rules = {
  required: (v: string) => !!v || 'This field is required',
  email: (v: string) => {
    if (!v) return true
    const emails = v.split(',').map(e => e.trim())
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emails.every(e => emailPattern.test(e)) || 'Invalid email address'
  },
}

const isFormValid = computed(() => {
  return (
    formData.value.to &&
    formData.value.subject &&
    rules.email(formData.value.to) === true &&
    (!formData.value.cc || rules.email(formData.value.cc) === true) &&
    (!formData.value.bcc || rules.email(formData.value.bcc) === true)
  )
})

async function handleSend() {
  if (!isFormValid.value) return

  sending.value = true
  try {
    const emailData = {
      to: formData.value.to,
      subject: formData.value.subject,
      body: formData.value.body,
      ...(formData.value.cc && { cc: formData.value.cc }),
      ...(formData.value.bcc && { bcc: formData.value.bcc }),
    }

    emit('send', emailData)
  }
  finally {
    sending.value = false
  }
}
</script>
