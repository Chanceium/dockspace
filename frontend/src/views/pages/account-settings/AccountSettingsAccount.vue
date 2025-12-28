<script lang="ts" setup>
import { useAuthStore } from '@/stores/auth'
import { authService } from '@/services/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const accountData = ref({
  avatarImg: '',
  picture: '',
  username: '',
  createdAt: '',
  role: '',
  status: '',
  firstName: '',
  lastName: '',
  middleName: '',
  email: '',
  phoneNumber: '',
  website: '',
  gender: '',
  birthdate: '',
  timezone: '',
  locale: '',
  streetAddress: '',
  locality: '',
  region: '',
  postalCode: '',
  country: '',
})

const refInputEl = ref<HTMLElement>()
const isAvatarDialogOpen = ref(false)
const isLoading = ref(false)
const isSaving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const accountDataLocal = ref({ ...accountData.value })
const isAccountDeactivated = ref(false)
const isDeactivating = ref(false)
const accountFullName = computed(() => {
  return `${accountDataLocal.value.firstName} ${accountDataLocal.value.lastName}`.trim()
})

const aliasCount = ref(0)
const groupCount = ref(0)
const mailQuota = ref('')
const mailAliases = ref<Array<{ address: string; updatedAt: string }>>([])
const mailGroups = ref<Array<{ name: string; updatedAt: string }>>([])

// Helper function to get CSRF token from authService
const getCsrfToken = (): string => {
  return authService.getCSRFTokenPublic()
}

// Load profile data from API
const loadProfile = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    console.log('[AccountSettings] Fetching profile data...')
    const response = await fetch('/api/profile/', {
      credentials: 'include',
    })

    console.log('[AccountSettings] Response status:', response.status)
    const data = await response.json()
    console.log('[AccountSettings] Response data:', data)

    if (data.success && data.profile) {
      const profile = data.profile
      accountData.value = {
        avatarImg: profile.picture || '',
        picture: profile.picture || '',
        username: profile.username || '',
        createdAt: profile.created_at ? new Date(profile.created_at).toLocaleDateString() : '',
        role: profile.is_admin ? 'Admin' : 'User',
        status: profile.status || 'active',
        firstName: profile.first_name || '',
        lastName: profile.last_name || '',
        middleName: profile.middle_name || '',
        email: profile.email || '',
        phoneNumber: profile.phone_number || '',
        website: profile.website || '',
        gender: profile.gender || '',
        birthdate: profile.birthdate || '',
        timezone: profile.zoneinfo || '',
        locale: profile.locale || '',
        streetAddress: profile.street_address || '',
        locality: profile.locality || '',
        region: profile.region || '',
        postalCode: profile.postal_code || '',
        country: profile.country || '',
      }
      accountDataLocal.value = { ...accountData.value }

      // Set counts and quota
      aliasCount.value = profile.alias_count || 0
      groupCount.value = profile.group_count || 0
      mailQuota.value = profile.quota || 'No quota set'

      console.log('[AccountSettings] Profile loaded successfully:', accountDataLocal.value)

      // Load aliases and groups
      await loadAliasesAndGroups()
    } else {
      console.error('[AccountSettings] Failed to load profile:', data)
      errorMessage.value = data.error || 'Failed to load profile'
    }
  } catch (error) {
    console.error('[AccountSettings] Error loading profile:', error)
    errorMessage.value = 'Failed to load profile data'
  } finally {
    isLoading.value = false
  }
}

// Load aliases and groups for current user
const loadAliasesAndGroups = async () => {
  try {
    // Load aliases
    const aliasResponse = await fetch('/api/mail/aliases/', {
      credentials: 'include',
    })
    const aliasData = await aliasResponse.json()

    if (aliasData.success && aliasData.aliases) {
      mailAliases.value = aliasData.aliases.map((alias: any) => ({
        address: alias.alias_email,
        updatedAt: alias.created_at ? new Date(alias.created_at).toLocaleDateString() : 'N/A'
      }))
    }

    // Load groups
    const groupResponse = await fetch('/api/mail/groups/', {
      credentials: 'include',
    })
    const groupData = await groupResponse.json()

    if (groupData.success && groupData.groups) {
      mailGroups.value = groupData.groups.map((group: any) => ({
        name: group.name,
        updatedAt: group.updated_at ? new Date(group.updated_at).toLocaleDateString() : 'N/A'
      }))
    }
  } catch (error) {
    console.error('[AccountSettings] Error loading aliases and groups:', error)
  }
}

// Save profile changes
const saveProfile = async () => {
  // Validate form
  if (formRef.value) {
    const { valid } = await formRef.value.validate()
    if (!valid) {
      errorMessage.value = 'Please fix the errors before saving'
      return
    }
  }

  isSaving.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const response = await fetch('/api/profile/update/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      credentials: 'include',
      body: JSON.stringify({
        first_name: accountDataLocal.value.firstName,
        last_name: accountDataLocal.value.lastName,
        middle_name: accountDataLocal.value.middleName,
        phone_number: accountDataLocal.value.phoneNumber,
        website: accountDataLocal.value.website,
        gender: accountDataLocal.value.gender,
        birthdate: accountDataLocal.value.birthdate || null,
        zoneinfo: accountDataLocal.value.timezone,
        locale: accountDataLocal.value.locale,
        street_address: accountDataLocal.value.streetAddress,
        locality: accountDataLocal.value.locality,
        region: accountDataLocal.value.region,
        postal_code: accountDataLocal.value.postalCode,
        country: accountDataLocal.value.country,
      }),
    })

    const data = await response.json()

    if (data.success) {
      successMessage.value = 'Profile updated successfully'
      accountData.value = { ...accountDataLocal.value }

      // Update auth store if name changed
      if (authStore.user) {
        authStore.user.first_name = accountDataLocal.value.firstName
        authStore.user.last_name = accountDataLocal.value.lastName
      }
    } else {
      errorMessage.value = data.error || 'Failed to save profile'
    }
  } catch (error) {
    console.error('Error saving profile:', error)
    errorMessage.value = 'Failed to save profile changes'
  } finally {
    isSaving.value = false
  }
}

const resetForm = () => {
  accountDataLocal.value = { ...accountData.value }
  errorMessage.value = ''
  successMessage.value = ''
}

// Load profile on mount
onMounted(() => {
  loadProfile()
})

const isUploadingPhoto = ref(false)
const uploadErrorMessage = ref('')

// Form validation
const formRef = ref()
const firstNameRules = [
  (v: string) => !!v || 'First name is required',
  (v: string) => (v && v.length >= 1) || 'First name must be at least 1 character',
]

const phoneNumberRules = [
  (v: string) => !v || /^\+?[0-9\s\-()]{7,20}$/.test(v) || 'Invalid phone number format (e.g., +1 555-123-4567)',
]

const websiteRules = [
  (v: string) => !v || /^https?:\/\/.+\..+/.test(v) || 'Invalid URL format (must start with http:// or https://)',
]

const birthdateRules = [
  (v: string) => !v || /^\d{4}-\d{2}-\d{2}$/.test(v) || 'Invalid date format (YYYY-MM-DD)',
  (v: string) => {
    if (!v) return true
    const date = new Date(v)
    const now = new Date()
    return date <= now || 'Birthdate cannot be in the future'
  },
]

const postalCodeRules = [
  (v: string) => !v || /^[A-Z0-9\s\-]{3,10}$/i.test(v) || 'Invalid postal/zip code format',
]

// Generate timezone list with UTC offsets
const generateTimezoneList = () => {
  const timezoneIds = Intl.supportedValuesOf('timeZone')

  return timezoneIds.map(tz => {
    try {
      // Get current UTC offset for this timezone
      const now = new Date()
      const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: tz,
        timeZoneName: 'longOffset'
      })

      const parts = formatter.formatToParts(now)
      const offsetPart = parts.find(part => part.type === 'timeZoneName')
      const offset = offsetPart ? offsetPart.value : ''

      return {
        value: tz,
        text: `${tz} (${offset})`
      }
    } catch (e) {
      // Fallback if timezone is not supported
      return {
        value: tz,
        text: tz
      }
    }
  })
}

const timezones = ref(generateTimezoneList())

// Generate comprehensive language list using Intl.DisplayNames
const generateLanguageList = () => {
  // Common language codes with regional variants
  const languageCodes = [
    'af', 'ar', 'ar-AE', 'ar-SA', 'bg', 'bn', 'ca', 'cs', 'da', 'de', 'de-AT',
    'de-CH', 'de-DE', 'el', 'en', 'en-AU', 'en-CA', 'en-GB', 'en-IN', 'en-NZ',
    'en-US', 'es', 'es-AR', 'es-ES', 'es-MX', 'et', 'fa', 'fi', 'fil', 'fr',
    'fr-BE', 'fr-CA', 'fr-CH', 'fr-FR', 'he', 'hi', 'hr', 'hu', 'id', 'is',
    'it', 'it-CH', 'it-IT', 'ja', 'ko', 'lt', 'lv', 'ms', 'nb', 'nl', 'nl-BE',
    'nl-NL', 'no', 'pl', 'pt', 'pt-BR', 'pt-PT', 'ro', 'ru', 'sk', 'sl', 'sr',
    'sv', 'sw', 'ta', 'te', 'th', 'tr', 'uk', 'ur', 'vi', 'zh', 'zh-CN', 'zh-HK',
    'zh-TW'
  ]

  const languageNames = new Intl.DisplayNames(['en'], { type: 'language' })

  return languageCodes.map(code => ({
    value: code,
    text: languageNames.of(code) || code
  }))
}

const locales = ref(generateLanguageList())

// Generate comprehensive country list using Intl.DisplayNames
const generateCountryList = () => {
  // ISO 3166-1 alpha-2 country codes
  const countryCodes = [
    'AF', 'AX', 'AL', 'DZ', 'AS', 'AD', 'AO', 'AI', 'AQ', 'AG', 'AR', 'AM', 'AW',
    'AU', 'AT', 'AZ', 'BS', 'BH', 'BD', 'BB', 'BY', 'BE', 'BZ', 'BJ', 'BM', 'BT',
    'BO', 'BQ', 'BA', 'BW', 'BV', 'BR', 'IO', 'BN', 'BG', 'BF', 'BI', 'CV', 'KH',
    'CM', 'CA', 'KY', 'CF', 'TD', 'CL', 'CN', 'CX', 'CC', 'CO', 'KM', 'CG', 'CD',
    'CK', 'CR', 'CI', 'HR', 'CU', 'CW', 'CY', 'CZ', 'DK', 'DJ', 'DM', 'DO', 'EC',
    'EG', 'SV', 'GQ', 'ER', 'EE', 'SZ', 'ET', 'FK', 'FO', 'FJ', 'FI', 'FR', 'GF',
    'PF', 'TF', 'GA', 'GM', 'GE', 'DE', 'GH', 'GI', 'GR', 'GL', 'GD', 'GP', 'GU',
    'GT', 'GG', 'GN', 'GW', 'GY', 'HT', 'HM', 'VA', 'HN', 'HK', 'HU', 'IS', 'IN',
    'ID', 'IR', 'IQ', 'IE', 'IM', 'IL', 'IT', 'JM', 'JP', 'JE', 'JO', 'KZ', 'KE',
    'KI', 'KP', 'KR', 'KW', 'KG', 'LA', 'LV', 'LB', 'LS', 'LR', 'LY', 'LI', 'LT',
    'LU', 'MO', 'MG', 'MW', 'MY', 'MV', 'ML', 'MT', 'MH', 'MQ', 'MR', 'MU', 'YT',
    'MX', 'FM', 'MD', 'MC', 'MN', 'ME', 'MS', 'MA', 'MZ', 'MM', 'NA', 'NR', 'NP',
    'NL', 'NC', 'NZ', 'NI', 'NE', 'NG', 'NU', 'NF', 'MK', 'MP', 'NO', 'OM', 'PK',
    'PW', 'PS', 'PA', 'PG', 'PY', 'PE', 'PH', 'PN', 'PL', 'PT', 'PR', 'QA', 'RE',
    'RO', 'RU', 'RW', 'BL', 'SH', 'KN', 'LC', 'MF', 'PM', 'VC', 'WS', 'SM', 'ST',
    'SA', 'SN', 'RS', 'SC', 'SL', 'SG', 'SX', 'SK', 'SI', 'SB', 'SO', 'ZA', 'GS',
    'SS', 'ES', 'LK', 'SD', 'SR', 'SJ', 'SE', 'CH', 'SY', 'TW', 'TJ', 'TZ', 'TH',
    'TL', 'TG', 'TK', 'TO', 'TT', 'TN', 'TR', 'TM', 'TC', 'TV', 'UG', 'UA', 'AE',
    'GB', 'UM', 'US', 'UY', 'UZ', 'VU', 'VE', 'VN', 'VG', 'VI', 'WF', 'EH', 'YE',
    'ZM', 'ZW'
  ]

  const regionNames = new Intl.DisplayNames(['en'], { type: 'region' })

  return countryCodes.map(code => ({
    value: code,
    text: regionNames.of(code) || code
  })).sort((a, b) => a.text.localeCompare(b.text))
}

const countries = ref(generateCountryList())

// changeAvatar function
const changeAvatar = async (file: Event) => {
  const { files } = file.target as HTMLInputElement

  if (files && files.length) {
    const selectedFile = files[0]

    // Validate file size (5MB max)
    const maxSize = 5 * 1024 * 1024
    if (selectedFile.size > maxSize) {
      uploadErrorMessage.value = 'File size exceeds 5MB limit'
      return
    }

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if (!allowedTypes.includes(selectedFile.type)) {
      uploadErrorMessage.value = 'Invalid file type. Only JPEG, PNG, GIF, and WEBP are allowed.'
      return
    }

    // Show preview
    const fileReader = new FileReader()
    fileReader.readAsDataURL(selectedFile)
    fileReader.onload = () => {
      if (typeof fileReader.result === 'string') {
        accountDataLocal.value.avatarImg = fileReader.result
      }
    }

    // Upload to server
    isUploadingPhoto.value = true
    uploadErrorMessage.value = ''

    try {
      const formData = new FormData()
      formData.append('picture', selectedFile)

      const response = await fetch('/api/profile/upload-photo/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
        },
        credentials: 'include',
        body: formData,
      })

      const data = await response.json()

      if (data.success) {
        accountDataLocal.value.picture = data.picture_url || ''
        accountData.value.picture = data.picture_url || ''
        successMessage.value = 'Profile photo updated successfully'
        closeAvatarDialog()

        // Reload profile to get updated data
        await loadProfile()
      } else {
        uploadErrorMessage.value = data.error || 'Failed to upload photo'
        // Reset preview on error
        accountDataLocal.value.avatarImg = accountData.value.avatarImg
      }
    } catch (error) {
      console.error('Error uploading photo:', error)
      uploadErrorMessage.value = 'Failed to upload photo'
      // Reset preview on error
      accountDataLocal.value.avatarImg = accountData.value.avatarImg
    } finally {
      isUploadingPhoto.value = false
    }
  }
}

// reset avatar image
const resetAvatar = () => {
  accountDataLocal.value.avatarImg = accountData.value.avatarImg
  accountDataLocal.value.picture = accountData.value.picture
  uploadErrorMessage.value = ''
}

const clearAvatar = async () => {
  // For now, just clear the local preview
  // You could add a backend endpoint to delete the photo if needed
  accountDataLocal.value.avatarImg = ''
  uploadErrorMessage.value = ''
}

const openAvatarDialog = () => {
  isAvatarDialogOpen.value = true
}

const closeAvatarDialog = () => {
  isAvatarDialogOpen.value = false
}

const deactivateAccount = async () => {
  if (!isAccountDeactivated.value) return
  isDeactivating.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const response = await fetch('/api/profile/deactivate/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
      },
      credentials: 'include',
    })
    const data = await response.json()
    if (data.success) {
      await authStore.logout()
      await router.replace('/login')
    } else {
      errorMessage.value = data.error || 'Failed to deactivate account'
    }
  } catch (error) {
    errorMessage.value = 'Failed to deactivate account'
  } finally {
    isDeactivating.value = false
  }
}
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard title="Profile details">
        <VCardText v-if="isLoading" class="text-center py-8">
          <VProgressCircular
            indeterminate
            color="primary"
          />
          <div class="mt-4 text-body-2 text-disabled">
            Loading profile...
          </div>
        </VCardText>
        <VCardText v-if="!isLoading" class="d-flex flex-wrap gap-6 align-center">
          <div class="avatar-picker cursor-pointer" @click="openAvatarDialog">
            <VAvatar
              v-if="accountData.avatarImg"
              rounded="lg"
              size="100"
              :image="accountData.avatarImg"
            />
            <VAvatar
              v-else
              rounded="lg"
              size="100"
              color="primary"
              variant="tonal"
            >
              <AppAvatar
                :name="accountFullName"
                variant="avataaars"
              />
            </VAvatar>
            <div class="avatar-picker__icon">
              <VIcon
                icon="ri-camera-line"
                size="18"
              />
            </div>
          </div>

          <div class="d-flex flex-wrap gap-6 text-body-2">
            <div>
              <div class="text-caption text-disabled">
                Role
              </div>
              <div>
                <VChip
                  color="primary"
                  size="small"
                  variant="tonal"
                >
                  {{ accountData.role }}
                </VChip>
              </div>
            </div>
            <div>
              <div class="text-caption text-disabled">
                Name
              </div>
              <div class="font-weight-medium">
                {{ accountData.firstName }} {{ accountData.lastName }}
              </div>
            </div>
            <div>
              <div class="text-caption text-disabled">
                Username
              </div>
              <div class="font-weight-medium">
                {{ accountData.username }}
              </div>
            </div>
            <div>
              <div class="text-caption text-disabled">
                Email
              </div>
              <div class="font-weight-medium">
                {{ accountData.email }}
              </div>
            </div>
            <div>
              <div class="text-caption text-disabled">
                Created
              </div>
              <div class="font-weight-medium">
                {{ accountData.createdAt }}
              </div>
            </div>
            <div>
              <div class="text-caption text-disabled">
                Timezone
              </div>
              <div class="font-weight-medium">
                {{ accountData.timezone || '—' }}
              </div>
            </div>
          </div>

          <input
            ref="refInputEl"
            type="file"
            name="file"
            accept=".jpeg,.png,.jpg,GIF"
            hidden
            @input="changeAvatar"
          >
        </VCardText>

        <VCardText class="pt-0">
          <VRow class="text-body-2">
            <VCol cols="12" sm="3">
              <div class="text-caption text-disabled">
                Aliases
              </div>
              <div class="font-weight-medium">
                {{ aliasCount }}
              </div>
            </VCol>
            <VCol cols="12" sm="3">
              <div class="text-caption text-disabled">
                Groups
              </div>
              <div class="font-weight-medium">
                {{ groupCount }}
              </div>
            </VCol>
            <VCol cols="12" sm="3">
              <div class="text-caption text-disabled">
                Mail quota
              </div>
              <div class="font-weight-medium">
                {{ mailQuota }}
              </div>
            </VCol>
          </VRow>
        </VCardText>

        <VCardText>
          <VExpansionPanels variant="accordion">
            <VExpansionPanel>
              <VExpansionPanelTitle>
                Edit Profile Details
              </VExpansionPanelTitle>
              <VExpansionPanelText>
                <VForm ref="formRef" class="mt-2" @submit.prevent="saveProfile">
                  <VRow>
                    <!-- Error/Success messages -->
                    <VCol v-if="errorMessage" cols="12">
                      <VAlert
                        type="error"
                        variant="tonal"
                        closable
                        @click:close="errorMessage = ''"
                      >
                        {{ errorMessage }}
                      </VAlert>
                    </VCol>
                    <VCol v-if="successMessage" cols="12">
                      <VAlert
                        type="success"
                        variant="tonal"
                        closable
                        @click:close="successMessage = ''"
                      >
                        {{ successMessage }}
                      </VAlert>
                    </VCol>
                    <!-- 👉 First Name -->
                    <VCol
                      md="6"
                      cols="12"
                    >
                      <VTextField
                        v-model="accountDataLocal.firstName"
                        :rules="firstNameRules"
                        placeholder="Chance"
                        label="First name *"
                        required
                      />
                    </VCol>

                    <!-- 👉 Last Name -->
                    <VCol
                      md="6"
                      cols="12"
                    >
                      <VTextField
                        v-model="accountDataLocal.lastName"
                        placeholder="Page"
                        label="Last name"
                      />
                    </VCol>

                    <!-- 👉 Middle Name -->
                    <VCol
                      md="6"
                      cols="12"
                    >
                      <VTextField
                        v-model="accountDataLocal.middleName"
                        placeholder="Middle name"
                        label="Middle name"
                      />
                    </VCol>

                    <!-- 👉 Phone Number -->
                    <VCol
                      cols="12"
                      md="6"
                    >
                      <VTextField
                        v-model="accountDataLocal.phoneNumber"
                        :rules="phoneNumberRules"
                        label="Phone number"
                        placeholder="+15551234567"
                      />
                    </VCol>

                    <!-- 👉 Website -->
                    <VCol
                      cols="12"
                      md="6"
                    >
                      <VTextField
                        v-model="accountDataLocal.website"
                        :rules="websiteRules"
                        label="Website"
                        placeholder="https://example.com"
                      />
                    </VCol>

                    <!-- 👉 Gender -->
                    <VCol
                      cols="12"
                      md="6"
                    >
                      <VTextField
                        v-model="accountDataLocal.gender"
                        label="Gender"
                        placeholder="OIDC gender claim (string)"
                      />
                    </VCol>

                    <!-- 👉 Birthdate -->
                    <VCol
                      cols="12"
                      md="6"
                    >
                      <VTextField
                        v-model="accountDataLocal.birthdate"
                        :rules="birthdateRules"
                        label="Birthdate"
                        placeholder="YYYY-MM-DD"
                        type="date"
                      />
                    </VCol>

                    <!-- 👉 Timezone -->
                    <VCol
                      cols="12"
                      md="6"
                    >
                      <VSelect
                        v-model="accountDataLocal.timezone"
                        :items="timezones"
                        item-title="text"
                        item-value="value"
                        label="Timezone"
                        placeholder="Select timezone"
                        clearable
                      />
                    </VCol>

                    <!-- 👉 Language -->
                    <VCol
                      cols="12"
                      md="6"
                    >
                      <VSelect
                        v-model="accountDataLocal.locale"
                        :items="locales"
                        item-title="text"
                        item-value="value"
                        label="Language"
                        placeholder="Select language"
                        clearable
                      />
                    </VCol>

                    <!-- 👉 Street Address -->
                    <VCol
                      cols="12"
                      md="6"
                    >
                      <VTextField
                        v-model="accountDataLocal.streetAddress"
                        label="Street address"
                        placeholder="Street address"
                      />
                    </VCol>

                    <!-- 👉 City -->
                    <VCol
                      cols="12"
                      md="6"
                    >
                      <VTextField
                        v-model="accountDataLocal.locality"
                        label="City"
                        placeholder="City"
                      />
                    </VCol>

                    <!-- 👉 Region -->
                    <VCol
                      cols="12"
                      md="6"
                    >
                      <VTextField
                        v-model="accountDataLocal.region"
                        label="Region"
                        placeholder="Region"
                      />
                    </VCol>

                    <!-- 👉 Postal/Zip -->
                    <VCol
                      cols="12"
                      md="6"
                    >
                      <VTextField
                        v-model="accountDataLocal.postalCode"
                        :rules="postalCodeRules"
                        label="Postal/Zip"
                        placeholder="12345 or A1B 2C3"
                      />
                    </VCol>

                    <!-- 👉 Country -->
                    <VCol
                      cols="12"
                      md="6"
                    >
                      <VSelect
                        v-model="accountDataLocal.country"
                        :items="countries"
                        item-title="text"
                        item-value="value"
                        label="Country"
                        placeholder="Select country"
                        clearable
                      />
                    </VCol>

                    <!-- 👉 Form Actions -->
                    <VCol
                      cols="12"
                      class="d-flex flex-wrap gap-4"
                    >
                      <VBtn
                        type="submit"
                        :loading="isSaving"
                        :disabled="isSaving"
                      >
                        Save changes
                      </VBtn>

                      <VBtn
                        color="secondary"
                        variant="outlined"
                        type="reset"
                        :disabled="isSaving"
                        @click.prevent="resetForm"
                      >
                        Reset
                      </VBtn>
                    </VCol>
                  </VRow>
                </VForm>
              </VExpansionPanelText>
            </VExpansionPanel>
          </VExpansionPanels>
        </VCardText>

        <VCardText class="pt-0">
          <VRow>
            <VCol cols="12" md="6">
              <VCard
                variant="outlined"
                title="Mail aliases"
              >
                <VCardText>
                  <div class="d-flex flex-column gap-4 list-scroll">
                    <div
                      v-for="alias in mailAliases"
                      :key="alias.address"
                      class="d-flex align-center justify-space-between"
                    >
                      <div class="font-weight-medium">
                        {{ alias.address }}
                      </div>
                      <div class="text-caption text-disabled">
                        Updated {{ alias.updatedAt }}
                      </div>
                    </div>
                  </div>
                </VCardText>
              </VCard>
            </VCol>
            <VCol cols="12" md="6">
              <VCard
                variant="outlined"
                title="Mail groups"
              >
                <VCardText>
                  <div class="d-flex flex-column gap-4 list-scroll">
                    <div
                      v-for="group in mailGroups"
                      :key="group.name"
                      class="d-flex align-center justify-space-between"
                    >
                      <div class="font-weight-medium">
                        {{ group.name }}
                      </div>
                      <div class="text-caption text-disabled">
                        Updated {{ group.updatedAt }}
                      </div>
                    </div>
                  </div>
                </VCardText>
              </VCard>
            </VCol>
          </VRow>
        </VCardText>

        <VDivider />
      </VCard>
    </VCol>

    <VCol cols="12">
      <!-- 👉 Deactivate Account -->
      <VCard title="Deactivate Account">
        <VCardText>
          <div>
            <VCheckbox
              v-model="isAccountDeactivated"
              label="I confirm my account deactivation"
            />
          </div>

          <VBtn
            :disabled="!isAccountDeactivated || isDeactivating"
            color="error"
            class="mt-3"
            :loading="isDeactivating"
            @click="deactivateAccount"
          >
            Deactivate Account
          </VBtn>
        </VCardText>
      </VCard>
    </VCol>

    <VDialog
      v-model="isAvatarDialogOpen"
      max-width="420"
    >
      <VCard>
        <VCardTitle>Update profile picture</VCardTitle>
        <VCardText>
          <p class="text-body-2 mb-4">
            Choose a new image or clear the current one. Maximum file size: 5MB. Supported formats: JPEG, PNG, GIF, WEBP.
          </p>

          <!-- Error message -->
          <VAlert
            v-if="uploadErrorMessage"
            type="error"
            variant="tonal"
            closable
            class="mb-4"
            @click:close="uploadErrorMessage = ''"
          >
            {{ uploadErrorMessage }}
          </VAlert>

          <!-- Upload progress -->
          <div v-if="isUploadingPhoto" class="text-center mb-4">
            <VProgressCircular
              indeterminate
              color="primary"
            />
            <div class="mt-2 text-body-2">
              Uploading photo...
            </div>
          </div>

          <div v-else class="d-flex justify-center mb-4">
            <VAvatar
              v-if="accountDataLocal.avatarImg"
              rounded="lg"
              size="96"
              :image="accountDataLocal.avatarImg"
            />
            <VAvatar
              v-else
              rounded="lg"
              size="96"
              color="primary"
              variant="tonal"
            >
              <AppAvatar
                :name="accountFullName"
                variant="avataaars"
              />
            </VAvatar>
          </div>
          <div class="d-flex flex-column gap-3">
            <VBtn
              color="primary"
              prepend-icon="ri-upload-cloud-line"
              :disabled="isUploadingPhoto"
              @click="refInputEl?.click()"
            >
              Upload new image
            </VBtn>
            <VBtn
              color="error"
              variant="outlined"
              prepend-icon="ri-delete-bin-line"
              :disabled="(!accountDataLocal.avatarImg && !accountDataLocal.picture) || isUploadingPhoto"
              @click="clearAvatar"
            >
              Clear image
            </VBtn>
          </div>
        </VCardText>
        <VCardActions class="justify-end">
          <VBtn
            variant="text"
            :disabled="isUploadingPhoto"
            @click="closeAvatarDialog"
          >
            Done
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </VRow>
</template>

<style scoped lang="scss">
.avatar-picker {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;

  &:hover .avatar-picker__icon {
    opacity: 1;
  }
}

.avatar-picker__icon {
  position: absolute;
  inset-block-end: -4px;
  inset-inline-end: -4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  inline-size: 28px;
  block-size: 28px;
  border-radius: 999px;
  background-color: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-primary));
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.18);
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.list-scroll {
  max-block-size: 12rem;
  overflow-y: auto;
  padding-inline-end: 0.25rem;
}
</style>
