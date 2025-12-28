<script setup lang="ts">
import { ref, watch, computed, onBeforeUnmount } from 'vue'
import type { MailAccount, MailGroup } from '@/services/mail'

type QuotaSuffix = 'M' | 'G' | 'T'

interface Props {
  isOpen: boolean
  account?: MailAccount | null
  mode: 'add' | 'edit'
  existingEmails?: string[]
  existingUsernames?: string[]
  errorMessage?: string
  groups?: MailGroup[]
  selectedGroupIds?: number[]
}

interface Emits {
  (e: 'update:isOpen', value: boolean): void
  (e: 'save', data: AccountFormData): void
}

interface AccountFormData {
  email: string
  username: string
  first_name: string
  last_name: string
  password?: string
  is_admin: boolean
  quotaValue: number | null
  quotaSuffix: QuotaSuffix
  groupIds: number[]
}

const props = withDefaults(defineProps<Props>(), {
  existingEmails: () => [],
  existingUsernames: () => [],
  errorMessage: '',
})
const emit = defineEmits<Emits>()

const formData = ref<AccountFormData>({
  email: '',
  username: '',
  first_name: '',
  last_name: '',
  password: '',
  is_admin: false,
  quotaValue: null,
  quotaSuffix: 'G',
  groupIds: [],
})

const isSaving = ref(false)
const passwordRequirements = ref<string[]>([])
const isLoadingRequirements = ref(false)
const copyState = ref<'idle' | 'copied' | 'error'>('idle')
const showPassword = ref(false)
let copyTimer: ReturnType<typeof setTimeout> | null = null

const dialogTitle = computed(() => {
  return props.mode === 'add' ? 'Add Mail Account' : 'Edit Mail Account'
})

const showPasswordField = computed(() => {
  return props.mode === 'add'
})

const normalize = (value?: string | null) => (value || '').trim().toLowerCase()
const existingEmailsNormalized = computed(() => props.existingEmails.map(email => normalize(email)))
const existingUsernamesNormalized = computed(() => props.existingUsernames.map(username => normalize(username)))

const normalizedCurrentEmail = computed(() => normalize(props.account?.email))
const normalizedCurrentUsername = computed(() => normalize(props.account?.username))

const filteredEmails = computed(() => {
  if (props.mode === 'edit') {
    return existingEmailsNormalized.value.filter(email => email !== normalizedCurrentEmail.value)
  }
  return existingEmailsNormalized.value
})

const filteredUsernames = computed(() => {
  if (props.mode === 'edit') {
    return existingUsernamesNormalized.value.filter(username => username !== normalizedCurrentUsername.value)
  }
  return existingUsernamesNormalized.value
})

const quotaSuffixOptions: QuotaSuffix[] = ['M', 'G', 'T']
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const requiredRule = (value: string) => value?.trim().length ? true : 'This field is required'
const emailRules = [
  requiredRule,
  (value: string) => emailPattern.test(value.trim()) ? true : 'Enter a valid email',
  (value: string) => filteredEmails.value.includes(normalize(value)) ? 'Email already exists' : true,
]
const usernameRules = [
  requiredRule,
  (value: string) => filteredUsernames.value.includes(normalize(value)) ? 'Username already exists' : true,
]
const firstNameRules = [requiredRule]
const quotaRules = [
  (value: number | null) => {
    if (value === null) return true
    return Number.isInteger(value) && value > 0 ? true : 'Enter a positive integer'
  },
]
const passwordRules = [
  requiredRule,
  (value: string) => value?.length >= 12 ? true : 'Password must be at least 12 characters',
  (value: string) => /[a-z]/.test(value) && /[A-Z]/.test(value) && /\d/.test(value) && /[^A-Za-z0-9]/.test(value)
    ? true
    : 'Include upper, lower, number, and symbol characters',
]
const isPasswordValid = computed(() => runRules(passwordRules, formData.value.password || ''))

const runRules = (rules: Array<(value: any) => true | string>, value: any) => {
  return rules.every(rule => rule(value) === true)
}

const parseQuota = (quota?: string | null) => {
  const defaultResult = { quotaValue: null, quotaSuffix: 'G' as QuotaSuffix }
  if (!quota) return defaultResult
  const match = /^(\d+)\s*([MGT])$/i.exec(quota.trim())
  if (!match) return defaultResult
  return {
    quotaValue: Number(match[1]),
    quotaSuffix: match[2].toUpperCase() as QuotaSuffix,
  }
}

const groupOptions = computed(() => props.groups || [])

// Watch for dialog open and populate form data
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    // Reset saving state when dialog opens
    isSaving.value = false

    if (props.account && props.mode === 'edit') {
      const parsedQuota = parseQuota(props.account.quota)
      formData.value = {
        email: props.account.email,
        username: props.account.username,
        first_name: props.account.first_name,
        last_name: props.account.last_name,
        is_admin: props.account.is_admin,
        quotaValue: parsedQuota.quotaValue,
        quotaSuffix: parsedQuota.quotaSuffix,
        groupIds: props.selectedGroupIds ? [...props.selectedGroupIds] : [],
      }
    } else if (props.mode === 'add') {
      resetForm()
    }

    if (!passwordRequirements.value.length) {
      loadPasswordRequirements()
    }
  }
})

// Auto-populate username from email in add mode
watch(() => formData.value.email, (email) => {
  if (props.mode === 'add' && email) {
    const atIndex = email.indexOf('@')
    if (atIndex > 0) {
      formData.value.username = email.substring(0, atIndex).trim().toLowerCase()
    }
  }
})

const resetForm = () => {
  formData.value = {
    email: '',
    username: '',
    first_name: '',
  last_name: '',
  password: '',
  is_admin: false,
  quotaValue: null,
  quotaSuffix: 'G',
  groupIds: [],
  }
}

const handleClose = () => {
  emit('update:isOpen', false)
  resetForm()
}

const handleSave = () => {
  isSaving.value = true
  emit('save', {
    ...formData.value,
    email: formData.value.email.trim().toLowerCase(),
    username: formData.value.username.trim().toLowerCase(),
    first_name: formData.value.first_name.trim(),
    last_name: formData.value.last_name.trim(),
  })
  // Parent component should handle the API call and close the dialog
}

const generatePassword = () => {
  const upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const lower = 'abcdefghijklmnopqrstuvwxyz'
  const numbers = '0123456789'
  const symbols = '!@#$%^&*()-_=+[]{};:,.<>?'
  const all = upper + lower + numbers + symbols

  const pick = (chars: string) => chars[Math.floor(Math.random() * chars.length)]
  const required = [pick(upper), pick(lower), pick(numbers), pick(symbols)]

  const remainingLength = 16 - required.length
  for (let i = 0; i < remainingLength; i++) {
    required.push(pick(all))
  }

  // shuffle for randomness
  for (let i = required.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[required[i], required[j]] = [required[j], required[i]]
  }

  formData.value.password = required.join('')
  copyPasswordToClipboard(formData.value.password)
}

const loadPasswordRequirements = async () => {
  try {
    isLoadingRequirements.value = true
    const response = await fetch('/api/profile/password-requirements/', {
      credentials: 'include',
    })
    if (!response.ok) return
    const data = await response.json()
    if (data?.success && Array.isArray(data.requirements)) {
      passwordRequirements.value = data.requirements
    }
  } catch (error) {
    console.error('Failed to load password requirements', error)
  } finally {
    isLoadingRequirements.value = false
  }
}

const setCopyState = (state: 'idle' | 'copied' | 'error') => {
  copyState.value = state
  if (copyTimer) {
    clearTimeout(copyTimer)
    copyTimer = null
  }
  if (state !== 'idle') {
    copyTimer = setTimeout(() => {
      copyState.value = 'idle'
      copyTimer = null
    }, 1600)
  }
}

const copyPasswordToClipboard = async (password: string) => {
  if (!password) return
  if (!(navigator && navigator.clipboard && navigator.clipboard.writeText)) {
    setCopyState('error')
    return
  }
  try {
    await navigator.clipboard.writeText(password)
    setCopyState('copied')
  } catch (error) {
    console.error('Failed to copy password', error)
    setCopyState('error')
  }
}

onBeforeUnmount(() => {
  if (copyTimer) {
    clearTimeout(copyTimer)
    copyTimer = null
  }
})

const isFormValid = computed(() => {
  if (props.mode === 'add') {
    return runRules(emailRules, formData.value.email) &&
           runRules(usernameRules, formData.value.username) &&
           runRules(passwordRules, formData.value.password || '') &&
           runRules(firstNameRules, formData.value.first_name) &&
           runRules(quotaRules, formData.value.quotaValue)
  }
  return runRules(emailRules, formData.value.email) &&
         runRules(usernameRules, formData.value.username) &&
         runRules(firstNameRules, formData.value.first_name) &&
         runRules(quotaRules, formData.value.quotaValue)
})
</script>

<template>
  <VDialog
    :model-value="isOpen"
    max-width="600"
    @update:model-value="handleClose"
  >
    <VCard>
      <VCardTitle class="d-flex align-center justify-space-between pa-4">
        <span>{{ dialogTitle }}</span>
        <VBtn
          icon="ri-close-line"
          variant="text"
          size="small"
          @click="handleClose"
        />
      </VCardTitle>

      <VDivider />

      <VCardText class="pa-6">
        <VAlert
          v-if="errorMessage"
          type="error"
          variant="tonal"
          class="mb-4"
        >
          {{ errorMessage }}
        </VAlert>

        <VAlert
          v-if="passwordRequirements.length && !isPasswordValid && (formData.password?.length || 0) > 0"
          type="info"
          variant="tonal"
          class="mb-4"
        >
          <div class="text-subtitle-2 mb-2">Password requirements</div>
          <ul class="ps-5 mb-0">
            <li v-for="req in passwordRequirements" :key="req">{{ req }}</li>
          </ul>
        </VAlert>

        <VRow>
          <VCol cols="12" md="6">
            <VTextField
              v-model="formData.first_name"
              label="First Name *"
              placeholder="John"
              :rules="firstNameRules"
              required
              :disabled="isSaving"
            />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField
              v-model="formData.last_name"
              label="Last Name"
              placeholder="Doe"
              :disabled="isSaving"
            />
          </VCol>
          <VCol cols="12">
            <VTextField
              v-model="formData.email"
              label="Email Address *"
              type="email"
              placeholder="john.doe@example.com"
              :rules="emailRules"
              required
              :disabled="isSaving || mode === 'edit'"
              :hint="mode === 'edit' ? 'Email cannot be changed' : ''"
              persistent-hint
            />
          </VCol>
          <VCol cols="12">
            <VTextField
              v-model="formData.username"
              label="Username *"
              placeholder="johndoe"
              :rules="usernameRules"
              required
              :disabled="isSaving || mode === 'edit'"
              :hint="mode === 'edit' ? 'Username cannot be changed' : ''"
              persistent-hint
            />
          </VCol>
          <VCol cols="12">
            <VSelect
              v-model="formData.groupIds"
              label="Groups"
              :items="groupOptions"
              item-title="name"
              item-value="id"
              multiple
              chips
              closable-chips
              clearable
              :disabled="isSaving || !groupOptions.length"
              hint="Optional: assign this account to one or more groups"
              persistent-hint
            />
          </VCol>
          <VCol v-if="showPasswordField" cols="12" md="8">
            <VTextField
              v-model="formData.password"
              label="Password *"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Enter password"
              :rules="passwordRules"
              required
              :disabled="isSaving"
              hint="Min 12 chars with upper, lower, number, and symbol"
              persistent-hint
              :append-inner-icon="showPassword ? 'ri-eye-off-line' : 'ri-eye-line'"
              @click:append-inner="showPassword = !showPassword"
            />
          </VCol>
          <VCol v-if="showPasswordField" cols="12" md="4">
            <VBtn
              color="primary"
              variant="outlined"
              block
              height="50"
              @click="generatePassword"
            >
              Generate
            </VBtn>
            <div v-if="copyState === 'copied' || copyState === 'error'" class="v-input__details">
              <div class="v-messages">
                <div class="v-messages__message">
                  {{ copyState === 'copied' ? 'Copied to clipboard' : 'Copy failed' }}
                </div>
              </div>
            </div>
          </VCol>
          <VCol cols="12" md="8">
            <VTextField
              v-model.number="formData.quotaValue"
              label="Storage Quota"
              placeholder="10"
              type="number"
              min="1"
              step="1"
              :rules="quotaRules"
              :disabled="isSaving"
              hint="Enter a numeric value and choose a unit"
              persistent-hint
            />
          </VCol>
          <VCol cols="12" md="4">
            <VSelect
              v-model="formData.quotaSuffix"
              label="Unit"
              :items="quotaSuffixOptions"
              :disabled="isSaving"
              hint="M=MiB, G=GiB, T=TiB"
              persistent-hint
            />
          </VCol>
          <VCol cols="12">
            <VCheckbox
              v-model="formData.is_admin"
              label="Administrator privileges"
              :disabled="isSaving"
            />
          </VCol>
        </VRow>
      </VCardText>

      <VDivider />

      <VCardActions class="pa-4">
        <VSpacer />
        <VBtn
          variant="outlined"
          @click="handleClose"
          :disabled="isSaving"
        >
          Cancel
        </VBtn>
        <VBtn
          color="primary"
          @click="handleSave"
          :disabled="!isFormValid || isSaving"
          :loading="isSaving"
        >
          {{ mode === 'add' ? 'Create Account' : 'Save Changes' }}
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>
