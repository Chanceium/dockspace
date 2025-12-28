<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { mailService } from '@/services/mail'
import { authService } from '@/services/auth'
import type { MailAccount, MailAlias, MailGroup } from '@/services/mail'
import AccountsTable from '@/components/management/AccountsTable.vue'
import AliasesTable from '@/components/management/AliasesTable.vue'
import GroupsTable from '@/components/management/GroupsTable.vue'
import DeleteConfirmDialog from '@/components/management/DeleteConfirmDialog.vue'
import AccountDialog from '@/components/management/AccountDialog.vue'
import AliasDialog from '@/components/management/AliasDialog.vue'
import GroupDialog from '@/components/management/GroupDialog.vue'
import AccountDetailsDialog from '@/components/management/AccountDetailsDialog.vue'
import GroupDetailsDialog from '@/components/management/GroupDetailsDialog.vue'

// State
const accounts = ref<MailAccount[]>([])
const aliases = ref<MailAlias[]>([])
const groups = ref<MailGroup[]>([])
const isLoadingAccounts = ref(false)
const isLoadingAliases = ref(false)
const isLoadingGroups = ref(false)
const accountError = ref('')
const selectedAccountGroupIds = ref<number[]>([])
const groupError = ref('')
const currentUserEmail = ref('')
const isResetPasswordOpen = ref(false)
const isResettingPassword = ref(false)
const resetPasswordValue = ref('')
const resetPasswordError = ref('')
const accountToReset = ref<MailAccount | null>(null)
const showResetPassword = ref(false)
const resetPasswordCopyState = ref<'idle' | 'copied' | 'error'>('idle')
let resetPasswordCopyTimer: ReturnType<typeof setTimeout> | null = null

// Dialog state
const isAccountDialogOpen = ref(false)
const isAliasDialogOpen = ref(false)
const isGroupDialogOpen = ref(false)
const accountDialogMode = ref<'add' | 'edit'>('add')
const groupDialogMode = ref<'add' | 'edit'>('add')
const selectedAccount = ref<MailAccount | null>(null)
const selectedGroup = ref<MailGroup | null>(null)

// Delete confirmation state
const isDeleteAccountOpen = ref(false)
const isDeleteAliasOpen = ref(false)
const isDeleteGroupOpen = ref(false)
const isDeletingAccount = ref(false)
const isDeletingAlias = ref(false)
const isDeletingGroup = ref(false)
const accountToDelete = ref<MailAccount | null>(null)
const aliasToDelete = ref<MailAlias | null>(null)
const groupToDelete = ref<MailGroup | null>(null)

// Details dialogs
const accountDetails = ref<MailAccount | null>(null)
const accountDetailsAliases = ref<MailAlias[]>([])
const accountDetailsGroups = ref<MailGroup[]>([])
const isAccountDetailsOpen = ref(false)
const groupDetails = ref<MailGroup | null>(null)
const groupDetailsMembers = ref<MailAccount[]>([])
const isGroupDetailsOpen = ref(false)

const existingEmails = computed(() => accounts.value.map(account => account.email))
const existingUsernames = computed(() => accounts.value.map(account => account.username))

// Load data from API
const loadAccounts = async () => {
  isLoadingAccounts.value = true
  const response = await mailService.listAccounts()
  if (response.success && response.accounts) {
    accounts.value = response.accounts
  }
  isLoadingAccounts.value = false
}

const loadAliases = async () => {
  isLoadingAliases.value = true
  const response = await mailService.listAliases()
  if (response.success && response.aliases) {
    aliases.value = response.aliases
  }
  isLoadingAliases.value = false
}

const loadGroups = async () => {
  isLoadingGroups.value = true
  const response = await mailService.listGroups()
  if (response.success && response.groups) {
    groups.value = response.groups
  }
  isLoadingGroups.value = false
}

// Account handlers
const handleAddAccount = () => {
  accountDialogMode.value = 'add'
  selectedAccount.value = null
  accountError.value = ''
  selectedAccountGroupIds.value = []
  isAccountDialogOpen.value = true
}

const handleEditAccount = (account: MailAccount) => {
  accountDialogMode.value = 'edit'
  selectedAccount.value = account
  accountError.value = ''
  selectedAccountGroupIds.value = []
  isAccountDialogOpen.value = true
  mailService.getAccountGroups(account.id).then(response => {
    if (response.success && response.groups) {
      selectedAccountGroupIds.value = response.groups.map(group => group.id)
    }
  })
}

const handleViewAccount = async (account: MailAccount) => {
  accountDetails.value = account
  accountDetailsAliases.value = aliases.value.filter(alias => alias.user_id === account.id)
  const groupResponse = await mailService.getAccountGroups(account.id)
  if (groupResponse.success && groupResponse.groups) {
    accountDetailsGroups.value = groupResponse.groups.map(g => ({
      id: g.id,
      name: g.name,
      description: '',
      member_count: 0,
      updated_at: null,
      created_at: null,
    }))
  } else {
    accountDetailsGroups.value = []
  }
  isAccountDetailsOpen.value = true
}

const handleDeleteAccount = (account: MailAccount) => {
  accountToDelete.value = account
  isDeleteAccountOpen.value = true
}

const generateResetPassword = () => {
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

  resetPasswordValue.value = required.join('')
  copyResetPasswordToClipboard(resetPasswordValue.value)
}

const setResetPasswordCopyState = (state: 'idle' | 'copied' | 'error') => {
  resetPasswordCopyState.value = state
  if (resetPasswordCopyTimer) {
    clearTimeout(resetPasswordCopyTimer)
    resetPasswordCopyTimer = null
  }
  if (state !== 'idle') {
    resetPasswordCopyTimer = setTimeout(() => {
      resetPasswordCopyState.value = 'idle'
      resetPasswordCopyTimer = null
    }, 1600)
  }
}

const copyResetPasswordToClipboard = async (password: string) => {
  if (!password) return
  if (!(navigator && navigator.clipboard && navigator.clipboard.writeText)) {
    setResetPasswordCopyState('error')
    return
  }
  try {
    await navigator.clipboard.writeText(password)
    setResetPasswordCopyState('copied')
  } catch (error) {
    console.error('Failed to copy password', error)
    setResetPasswordCopyState('error')
  }
}

const handleResetPassword = (account: MailAccount) => {
  accountToReset.value = account
  resetPasswordValue.value = ''
  resetPasswordError.value = ''
  showResetPassword.value = false
  resetPasswordCopyState.value = 'idle'
  isResetPasswordOpen.value = true
}

const submitResetPassword = async () => {
  if (!accountToReset.value) return
  resetPasswordError.value = ''
  isResettingPassword.value = true
  const response = await mailService.resetAccountPassword(accountToReset.value.id, resetPasswordValue.value)
  isResettingPassword.value = false

  if (response.success) {
    isResetPasswordOpen.value = false
    accountToReset.value = null
    resetPasswordValue.value = ''
  } else {
    resetPasswordError.value = response.error || 'Failed to reset password'
  }
}

const handleToggleAccountStatus = async (account: MailAccount) => {
  const nextStatus = account.status.toLowerCase() === 'suspended' ? 'active' : 'suspended'
  const response = await mailService.updateAccount(account.id, { status: nextStatus })
  if (response.success) {
    await loadAccounts()
  } else {
    accountError.value = response.error || 'Failed to update account status'
  }
}

const handleSaveAccount = async (data: any) => {
  accountError.value = ''
  if (accountDialogMode.value === 'add') {
    const response = await mailService.createAccount({
      email: data.email,
      username: data.username,
      password: data.password || '',
      first_name: data.first_name,
      last_name: data.last_name,
      is_admin: data.is_admin,
    })

    if (response.success && response.account?.id) {
      const accountId = response.account.id
      if (data.quotaValue && response.account?.id) {
        const quotaResponse = await mailService.createOrUpdateQuota(response.account.id, data.quotaValue, data.quotaSuffix)
        if (!quotaResponse.success) {
          accountError.value = quotaResponse.error || 'Failed to save quota'
          return
        }
      }
      if (data.groupIds?.length) {
        const groupResponse = await mailService.updateAccountGroups(accountId, data.groupIds)
        if (!groupResponse.success) {
          accountError.value = groupResponse.error || 'Failed to save groups'
          return
        }
      }
      isAccountDialogOpen.value = false
      await loadAccounts()
    } else {
      accountError.value = response.error || 'Failed to create account'
    }
  } else if (accountDialogMode.value === 'edit' && selectedAccount.value) {
    const response = await mailService.updateAccount(selectedAccount.value.id, {
      first_name: data.first_name,
      last_name: data.last_name,
      is_admin: data.is_admin,
    })

    if (response.success) {
      if (data.quotaValue) {
        const quotaResponse = await mailService.createOrUpdateQuota(selectedAccount.value.id, data.quotaValue, data.quotaSuffix)
        if (!quotaResponse.success) {
          accountError.value = quotaResponse.error || 'Failed to save quota'
          return
        }
      }
      const groupResponse = await mailService.updateAccountGroups(selectedAccount.value.id, data.groupIds || [])
      if (!groupResponse.success) {
        accountError.value = groupResponse.error || 'Failed to save groups'
        return
      }
      isAccountDialogOpen.value = false
      await loadAccounts()
    } else {
      accountError.value = response.error || 'Failed to update account'
    }
  }
}

const confirmDeleteAccount = async () => {
  if (!accountToDelete.value) return

  isDeletingAccount.value = true
  const response = await mailService.deleteAccount(accountToDelete.value.id)
  isDeletingAccount.value = false

  if (response.success) {
    isDeleteAccountOpen.value = false
    accountToDelete.value = null
    await loadAccounts()
  }
}

// Alias handlers
const handleAddAlias = () => {
  isAliasDialogOpen.value = true
}

const handleDeleteAlias = (alias: MailAlias) => {
  aliasToDelete.value = alias
  isDeleteAliasOpen.value = true
}

const handleSaveAlias = async (data: any) => {
  const response = await mailService.createAlias(
    data.alias_email,
    data.destination_email
  )

  if (response.success) {
    isAliasDialogOpen.value = false
    await loadAliases()
  }
}

const confirmDeleteAlias = async () => {
  if (!aliasToDelete.value) return

  isDeletingAlias.value = true
  const response = await mailService.deleteAlias(aliasToDelete.value.id)
  isDeletingAlias.value = false

  if (response.success) {
    isDeleteAliasOpen.value = false
    aliasToDelete.value = null
    await loadAliases()
  }
}

// Group handlers
const handleAddGroup = () => {
  groupDialogMode.value = 'add'
  selectedGroup.value = null
  groupError.value = ''
  isGroupDialogOpen.value = true
}

const handleEditGroup = (group: MailGroup) => {
  groupDialogMode.value = 'edit'
  selectedGroup.value = group
  groupError.value = ''
  isGroupDialogOpen.value = true
}

const handleDeleteGroup = (group: MailGroup) => {
  groupToDelete.value = group
  isDeleteGroupOpen.value = true
}

const handleSaveGroup = async (data: any) => {
  groupError.value = ''
  if (groupDialogMode.value === 'add') {
    const response = await mailService.createGroup(
      data.name,
      data.description
    )

    if (response.success) {
      isGroupDialogOpen.value = false
      await loadGroups()
    } else {
      groupError.value = response.error || 'Failed to create group'
    }
  } else if (groupDialogMode.value === 'edit' && selectedGroup.value) {
    const response = await mailService.updateGroup(
      selectedGroup.value.id,
      data.name,
      data.description
    )

    if (response.success) {
      isGroupDialogOpen.value = false
      await loadGroups()
    } else {
      groupError.value = response.error || 'Failed to update group'
    }
  }
}

const handleRemoveAlias = (alias: MailAlias) => {
  handleDeleteAlias(alias)
  isAccountDetailsOpen.value = false
}

const handleRemoveAccountGroup = async (groupId: number) => {
  if (!accountDetails.value) return
  const newGroups = accountDetailsGroups.value.filter(group => group.id !== groupId).map(group => group.id)
  const response = await mailService.updateAccountGroups(accountDetails.value.id, newGroups)
  if (response.success) {
    accountDetailsGroups.value = accountDetailsGroups.value.filter(group => group.id !== groupId)
    await loadAccounts()
  }
}

const handleViewGroup = async (group: MailGroup) => {
  groupDetails.value = group
  const response = await mailService.getGroup(group.id)
  if (response.success && response.group?.members) {
    groupDetailsMembers.value = response.group.members as unknown as MailAccount[]
  } else {
    groupDetailsMembers.value = []
  }
  isGroupDetailsOpen.value = true
}

const handleRemoveMemberFromGroup = async (member: MailAccount) => {
  if (!groupDetails.value) return
  const accountGroups = await mailService.getAccountGroups(member.id)
  if (!accountGroups.success || !accountGroups.groups) return
  const newGroupIds = accountGroups.groups.map(g => g.id).filter(id => id !== groupDetails.value?.id)
  const updateResponse = await mailService.updateAccountGroups(member.id, newGroupIds)
  if (updateResponse.success) {
    groupDetailsMembers.value = groupDetailsMembers.value.filter(m => m.id !== member.id)
    await loadAccounts()
  }
}

const confirmDeleteGroup = async () => {
  if (!groupToDelete.value) return

  isDeletingGroup.value = true
  const response = await mailService.deleteGroup(groupToDelete.value.id)
  isDeletingGroup.value = false

  if (response.success) {
    isDeleteGroupOpen.value = false
    groupToDelete.value = null
    await loadGroups()
  }
}

// Load data on mount
onMounted(() => {
  loadAccounts()
  loadAliases()
  loadGroups()
  authService.checkSession().then(session => {
    if (session.authenticated && session.user?.email) {
      currentUserEmail.value = session.user.email.toLowerCase()
    }
  })
})

onBeforeUnmount(() => {
  if (resetPasswordCopyTimer) {
    clearTimeout(resetPasswordCopyTimer)
    resetPasswordCopyTimer = null
  }
})

// Expose load functions for parent to trigger refresh
defineExpose({
  loadAccounts,
  loadAliases,
  loadGroups,
})
</script>

<template>
  <VRow>
    <!-- Mail Accounts -->
    <VCol cols="12">
      <AccountsTable
        :accounts="accounts"
        :loading="isLoadingAccounts"
        :current-user-email="currentUserEmail"
        @view="handleViewAccount"
        @edit="handleEditAccount"
        @toggle-status="handleToggleAccountStatus"
        @reset-password="handleResetPassword"
        @delete="handleDeleteAccount"
      >
        <template #actions>
          <VBtn
            color="primary"
            variant="outlined"
            @click="handleAddAccount"
          >
            Add account
          </VBtn>
        </template>
      </AccountsTable>
    </VCol>

    <!-- Mail Groups -->
    <VCol cols="12">
      <GroupsTable
        :groups="groups"
        :loading="isLoadingGroups"
        @view="handleViewGroup"
        @edit="handleEditGroup"
        @delete="handleDeleteGroup"
      >
        <template #actions>
          <VBtn
            color="primary"
            variant="outlined"
            @click="handleAddGroup"
          >
            Add group
          </VBtn>
        </template>
      </GroupsTable>
    </VCol>

    <!-- Mail Aliases -->
    <VCol cols="12">
      <AliasesTable
        :aliases="aliases"
        :loading="isLoadingAliases"
        @delete="handleDeleteAlias"
      >
        <template #actions>
          <VBtn
            color="primary"
            variant="outlined"
            @click="handleAddAlias"
          >
            Add alias
          </VBtn>
        </template>
      </AliasesTable>
    </VCol>
  </VRow>

  <!-- Dialogs -->
  <AccountDialog
    v-model:is-open="isAccountDialogOpen"
    :mode="accountDialogMode"
    :account="selectedAccount"
    :existing-emails="existingEmails"
    :existing-usernames="existingUsernames"
    :error-message="accountError"
    :groups="groups"
    :selected-group-ids="selectedAccountGroupIds"
    @save="handleSaveAccount"
  />

  <AliasDialog
    v-model:is-open="isAliasDialogOpen"
    :accounts="accounts"
    @save="handleSaveAlias"
  />

  <GroupDialog
    v-model:is-open="isGroupDialogOpen"
    :mode="groupDialogMode"
    :group="selectedGroup"
    :error-message="groupError"
    @save="handleSaveGroup"
  />

  <AccountDetailsDialog
    v-model:is-open="isAccountDetailsOpen"
    :account="accountDetails"
    :aliases="accountDetailsAliases"
    :groups="accountDetailsGroups"
    @remove-alias="handleRemoveAlias"
    @remove-group="handleRemoveAccountGroup"
  />

  <GroupDetailsDialog
    v-model:is-open="isGroupDetailsOpen"
    :group="groupDetails"
    :members="groupDetailsMembers"
    @remove-member="handleRemoveMemberFromGroup"
  />

  <!-- Delete Confirmations -->
  <DeleteConfirmDialog
    v-model:is-open="isDeleteAccountOpen"
    title="Delete Account"
    :message="`Are you sure you want to delete ${accountToDelete?.email}? This action cannot be undone.`"
    :is-deleting="isDeletingAccount"
    @confirm="confirmDeleteAccount"
  />

  <DeleteConfirmDialog
    v-model:is-open="isDeleteAliasOpen"
    title="Delete Alias"
    :message="`Are you sure you want to delete ${aliasToDelete?.alias_email}? This action cannot be undone.`"
    :is-deleting="isDeletingAlias"
    @confirm="confirmDeleteAlias"
  />

  <DeleteConfirmDialog
    v-model:is-open="isDeleteGroupOpen"
    title="Delete Group"
    :message="`Are you sure you want to delete ${groupToDelete?.name}? This action cannot be undone.`"
    :is-deleting="isDeletingGroup"
    @confirm="confirmDeleteGroup"
  />

  <!-- Reset Password Dialog -->
  <VDialog
    v-model="isResetPasswordOpen"
    max-width="600"
  >
    <VCard>
      <VCardTitle class="d-flex align-center justify-space-between pa-4">
        <span>Reset Password</span>
        <VBtn
          icon="ri-close-line"
          variant="text"
          size="small"
          @click="isResetPasswordOpen = false"
        />
      </VCardTitle>

      <VDivider />

      <VCardText class="pa-6">
        <div class="mb-4">
          Set a new password for <strong>{{ accountToReset?.email }}</strong>.
          Passwords must be at least 12 characters.
        </div>

        <VRow>
          <VCol cols="12" md="8">
            <VTextField
              v-model="resetPasswordValue"
              label="New Password"
              :type="showResetPassword ? 'text' : 'password'"
              :error-messages="resetPasswordError"
              :append-inner-icon="showResetPassword ? 'ri-eye-off-line' : 'ri-eye-line'"
              @click:append-inner="showResetPassword = !showResetPassword"
            />
          </VCol>

          <VCol cols="12" md="4">
            <VBtn
              color="primary"
              variant="outlined"
              block
              height="50"
              @click="generateResetPassword"
            >
              Generate
            </VBtn>
            <div v-if="resetPasswordCopyState === 'copied' || resetPasswordCopyState === 'error'" class="v-input__details">
              <div class="v-messages">
                <div class="v-messages__message">
                  {{ resetPasswordCopyState === 'copied' ? 'Copied to clipboard' : 'Copy failed' }}
                </div>
              </div>
            </div>
          </VCol>
        </VRow>
      </VCardText>

      <VDivider />

      <VCardActions class="pa-4">
        <VSpacer />
        <VBtn variant="outlined" @click="isResetPasswordOpen = false">
          Cancel
        </VBtn>
        <VBtn
          color="primary"
          :loading="isResettingPassword"
          :disabled="!resetPasswordValue"
          @click="submitResetPassword"
        >
          Reset Password
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>
