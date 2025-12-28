<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMail } from '@/composables/useMail'
import MailSidebar from '@/components/mail/MailSidebar.vue'
import MailList from '@/components/mail/MailList.vue'
import MailDetail from '@/components/mail/MailDetail.vue'
import ComposeDialog from '@/components/mail/ComposeDialog.vue'
import type { Email, Mailbox } from '@/services/mailClient'

// Use mail composable for state management
const {
  mailboxes,
  selectedMailboxId,
  selectedFolder,
  emails,
  folders,
  selectedEmail,
  loading,
  error,
  loadMailboxes,
  loadEmails,
  loadEmailDetail,
  sendEmail,
  createMailbox,
  updateMailbox,
  deleteMailbox,
  clearSelectedEmail,
} = useMail()

// UI state
const composeDialog = ref(false)
const mailboxDialog = ref(false)
const editingMailbox = ref<Partial<Mailbox>>({
  name: '',
  email: '',
  imapHost: '',
  imapPort: 993,
  imapSecurity: 'SSL/TLS',
  smtpHost: '',
  smtpPort: 587,
  smtpSecurity: 'STARTTLS',
  username: '',
  password: '',
  color: 'primary',
  isActive: true,
})
const filterUnreadOnly = ref(false)
const filterStarredOnly = ref(false)
const filterHasAttachments = ref(false)
const composeData = ref({
  to: '',
  subject: '',
  body: '',
  cc: '',
  bcc: '',
})

// Computed
const filteredEmails = computed(() => {
  let filtered = emails.value

  if (filterUnreadOnly.value) {
    filtered = filtered.filter(e => !e.read)
  }

  if (filterStarredOnly.value) {
    filtered = filtered.filter(e => e.starred)
  }

  if (filterHasAttachments.value) {
    filtered = filtered.filter(e => e.hasAttachments)
  }

  return filtered
})

// Methods
async function handleSelectFolder(folder: string) {
  selectedFolder.value = folder
  clearSelectedEmail()
}

async function handleSelectEmail(email: Email) {
  if (!selectedMailboxId.value) return

  await loadEmailDetail(email.uid, selectedFolder.value)
}

async function handleSendEmail(emailData: any) {
  const result = await sendEmail(emailData)

  if (result?.success) {
    composeDialog.value = false
    // Reset compose data
    composeData.value = {
      to: '',
      subject: '',
      body: '',
      cc: '',
      bcc: '',
    }
  }
}

function handleCompose() {
  composeData.value = {
    to: '',
    subject: '',
    body: '',
    cc: '',
    bcc: '',
  }
  composeDialog.value = true
}

function handleReply() {
  if (!selectedEmail.value) return

  composeData.value = {
    to: selectedEmail.value.fromEmail,
    subject: `Re: ${selectedEmail.value.subject}`,
    body: `\n\n---\nOn ${selectedEmail.value.date} at ${selectedEmail.value.time}, ${selectedEmail.value.from} wrote:\n${selectedEmail.value.body}`,
    cc: '',
    bcc: '',
  }
  composeDialog.value = true
}

function handleForward() {
  if (!selectedEmail.value) return

  composeData.value = {
    to: '',
    subject: `Fwd: ${selectedEmail.value.subject}`,
    body: `\n\n---\nForwarded message from ${selectedEmail.value.from}:\n${selectedEmail.value.body}`,
    cc: '',
    bcc: '',
  }
  composeDialog.value = true
}

function handleAddMailbox() {
  editingMailbox.value = {
    name: '',
    email: '',
    imapHost: '',
    imapPort: 993,
    imapSecurity: 'SSL/TLS',
    smtpHost: '',
    smtpPort: 587,
    smtpSecurity: 'STARTTLS',
    username: '',
    password: '',
    color: 'primary',
    isActive: true,
  }
  mailboxDialog.value = true
}

function handleEditMailbox(mailbox: Mailbox) {
  editingMailbox.value = { ...mailbox }
  mailboxDialog.value = true
}

async function handleSaveMailbox(mailboxData: Partial<Mailbox>) {
  let result
  if (mailboxData.id) {
    result = await updateMailbox(mailboxData.id, mailboxData)
  }
  else {
    result = await createMailbox(mailboxData as any)
  }

  // Show connection test results if available
  if (result?.connectionTest) {
    if (!result.connectionTest.success) {
      error.value = `Mailbox saved but connection test failed: ${result.connectionTest.message}`
    }
  }

  if (result?.success) {
    mailboxDialog.value = false
    editingMailbox.value = {
      name: '',
      email: '',
      imapHost: '',
      imapPort: 993,
      imapSecurity: 'SSL/TLS',
      smtpHost: '',
      smtpPort: 587,
      smtpSecurity: 'STARTTLS',
      username: '',
      password: '',
      color: 'primary',
      isActive: true,
    }
  }
}

async function handleDeleteMailbox(mailboxId?: number) {
  if (!mailboxId) return

  if (confirm('Are you sure you want to delete this mailbox?')) {
    await deleteMailbox(mailboxId)
    mailboxDialog.value = false
  }
}

function handleToggleFilter(filter: 'unread' | 'starred' | 'attachments') {
  switch (filter) {
    case 'unread':
      filterUnreadOnly.value = !filterUnreadOnly.value
      break
    case 'starred':
      filterStarredOnly.value = !filterStarredOnly.value
      break
    case 'attachments':
      filterHasAttachments.value = !filterHasAttachments.value
      break
  }
}

function handleRefresh() {
  loadEmails()
}

// Load initial data
onMounted(async () => {
  await loadMailboxes()
})
</script>

<template>
  <div class="mail-page">
    <v-row class="h-100 ma-0">
      <!-- Sidebar -->
      <v-col
        cols="12"
        md="3"
        lg="2"
        class="pa-0"
      >
        <MailSidebar
          :folders="folders"
          :mailboxes="mailboxes"
          :selected-folder="selectedFolder"
          @compose="handleCompose"
          @select-folder="handleSelectFolder"
          @add-mailbox="handleAddMailbox"
          @edit-mailbox="handleEditMailbox"
        />
      </v-col>

      <!-- Email List -->
      <v-col
        cols="12"
        md="4"
        lg="3"
        class="pa-0 border-e"
      >
        <MailList
          :emails="filteredEmails"
          :selected-email="selectedEmail"
          :loading="loading"
          :filter-unread-only="filterUnreadOnly"
          :filter-starred-only="filterStarredOnly"
          :filter-has-attachments="filterHasAttachments"
          @select-email="handleSelectEmail"
          @refresh="handleRefresh"
          @toggle-filter="handleToggleFilter"
        />
      </v-col>

      <!-- Email Detail -->
      <v-col
        cols="12"
        md="5"
        lg="7"
        class="pa-0"
      >
        <MailDetail
          :email="selectedEmail"
          @close="clearSelectedEmail"
          @reply="handleReply"
          @forward="handleForward"
        />
      </v-col>
    </v-row>

    <!-- Compose Dialog -->
    <ComposeDialog
      v-model="composeDialog"
      :to="composeData.to"
      :subject="composeData.subject"
      :body="composeData.body"
      :cc="composeData.cc"
      :bcc="composeData.bcc"
      @send="handleSendEmail"
    />

    <!-- Mailbox Settings Dialog -->
    <v-dialog
      v-model="mailboxDialog"
      max-width="600"
    >
      <v-card>
        <v-card-title class="d-flex align-center pa-4 border-b">
          <span>{{ editingMailbox ? 'Edit Mailbox' : 'Add Mailbox' }}</span>
          <v-spacer />
          <v-btn
            icon="ri-close-line"
            variant="text"
            @click="mailboxDialog = false"
          />
        </v-card-title>

        <v-card-text class="pa-4">
          <v-form>
            <v-text-field
              v-model="editingMailbox.name"
              label="Mailbox Name"
              density="comfortable"
              class="mb-2"
            />

            <v-text-field
              v-model="editingMailbox.email"
              label="Email Address"
              type="email"
              density="comfortable"
              class="mb-2"
            />

            <v-divider class="my-4" />
            <h3 class="text-subtitle-2 mb-2">
              IMAP Settings (Incoming Mail)
            </h3>

            <v-text-field
              v-model="editingMailbox.imapHost"
              label="IMAP Host"
              density="comfortable"
              class="mb-2"
            />

            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model.number="editingMailbox.imapPort"
                  label="IMAP Port"
                  type="number"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="6">
                <v-select
                  v-model="editingMailbox.imapSecurity"
                  label="Security"
                  :items="['None', 'SSL/TLS', 'STARTTLS']"
                  density="comfortable"
                />
              </v-col>
            </v-row>

            <v-divider class="my-4" />
            <h3 class="text-subtitle-2 mb-2">
              SMTP Settings (Outgoing Mail)
            </h3>

            <v-text-field
              v-model="editingMailbox.smtpHost"
              label="SMTP Host"
              density="comfortable"
              class="mb-2"
            />

            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model.number="editingMailbox.smtpPort"
                  label="SMTP Port"
                  type="number"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="6">
                <v-select
                  v-model="editingMailbox.smtpSecurity"
                  label="Security"
                  :items="['None', 'SSL/TLS', 'STARTTLS']"
                  density="comfortable"
                />
              </v-col>
            </v-row>

            <v-divider class="my-4" />
            <h3 class="text-subtitle-2 mb-2">
              Authentication
            </h3>

            <v-text-field
              v-model="editingMailbox.username"
              label="Username"
              density="comfortable"
              class="mb-2"
            />

            <v-text-field
              v-model="editingMailbox.password"
              label="Password"
              type="password"
              density="comfortable"
              class="mb-2"
              autocomplete="new-password"
            />

            <v-divider class="my-4" />
            <h3 class="text-subtitle-2 mb-2">
              Appearance
            </h3>

            <v-select
              v-model="editingMailbox.color"
              label="Mailbox Color"
              :items="[
                { title: 'Blue (Primary)', value: 'primary' },
                { title: 'Green (Success)', value: 'success' },
                { title: 'Orange (Warning)', value: 'warning' },
                { title: 'Red (Error)', value: 'error' },
                { title: 'Cyan (Info)', value: 'info' }
              ]"
              density="comfortable"
            />
          </v-form>
        </v-card-text>

        <v-card-actions class="pa-4 border-t">
          <v-btn
            v-if="editingMailbox.id"
            color="error"
            variant="text"
            @click="handleDeleteMailbox(editingMailbox.id)"
          >
            Delete
          </v-btn>
          <v-spacer />
          <v-btn
            variant="text"
            @click="mailboxDialog = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            @click="handleSaveMailbox(editingMailbox)"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Error Snackbar -->
    <v-snackbar
      :model-value="!!error"
      color="error"
      timeout="5000"
    >
      {{ error }}
    </v-snackbar>
  </div>
</template>

<style scoped>
.mail-page {
  height: 100vh;
  overflow: hidden;
}

.h-100 {
  height: 100%;
}

.border-e {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.border-b {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.border-t {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
</style>
