<script setup lang="ts">
import { ref, computed } from 'vue'

interface Email {
  id: number
  from: string
  fromEmail: string
  subject: string
  preview: string
  body: string
  date: string
  time: string
  read: boolean
  starred: boolean
  attachments?: Array<{ name: string; size: string }>
}

interface Mailbox {
  id: number
  name: string
  email: string
  imapHost: string
  imapPort: number
  imapSecurity: 'None' | 'SSL/TLS' | 'STARTTLS'
  smtpHost: string
  smtpPort: number
  smtpSecurity: 'None' | 'SSL/TLS' | 'STARTTLS'
  username: string
  password: string
  color: string
  isActive: boolean
  hasError?: boolean
  errorMessage?: string
}

const drawer = ref(true)
const selectedFolder = ref('inbox')
const selectedMailboxId = ref(1)
const selectedEmail = ref<Email | null>(null)
const searchQuery = ref('')
const composeDialog = ref(false)
const draggedIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)
const mailboxDialog = ref(false)
const mailboxSettingsDialog = ref(false)
const editingMailbox = ref<Mailbox | null>(null)
const expandedMailboxes = ref<number[]>([1])
const showFilters = ref(false)
const filterHasAttachments = ref(false)
const filterUnreadOnly = ref(false)
const filterStarredOnly = ref(false)
const showCc = ref(false)
const showBcc = ref(false)
const replyDialog = ref(false)
const forwardDialog = ref(false)
const showCcReply = ref(false)
const showBccReply = ref(false)
const showCcForward = ref(false)
const showBccForward = ref(false)
const mailboxFormValid = ref(false)
const mailboxFormErrors = ref({
  name: false,
  email: false,
  imapHost: false,
  imapPort: false,
  smtpHost: false,
  smtpPort: false,
  username: false,
  password: false,
})

const mailboxes = ref<Mailbox[]>([
  {
    id: 1,
    name: 'Work Gmail',
    email: 'work@gmail.com',
    imapHost: 'imap.gmail.com',
    imapPort: 993,
    imapSecurity: 'SSL/TLS',
    smtpHost: 'smtp.gmail.com',
    smtpPort: 587,
    smtpSecurity: 'STARTTLS',
    username: 'work@gmail.com',
    password: '',
    color: 'primary',
    isActive: true,
  },
  {
    id: 2,
    name: 'Personal Outlook',
    email: 'personal@outlook.com',
    imapHost: 'outlook.office365.com',
    imapPort: 993,
    imapSecurity: 'SSL/TLS',
    smtpHost: 'smtp.office365.com',
    smtpPort: 587,
    smtpSecurity: 'STARTTLS',
    username: 'personal@outlook.com',
    password: '',
    color: 'success',
    isActive: false,
    hasError: true,
    errorMessage: 'Invalid credentials',
  },
])

const selectedMailbox = computed(() =>
  mailboxes.value.find(m => m.id === selectedMailboxId.value) || mailboxes.value[0]
)

const newMailbox = ref<Mailbox>({
  id: 0,
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
  isActive: false,
})

const folders = ref([
  { icon: 'ri-inbox-line', text: 'Inbox', value: 'inbox', count: 12 },
  { icon: 'ri-star-line', text: 'Starred', value: 'starred', count: 3 },
  { icon: 'ri-send-plane-line', text: 'Sent', value: 'sent', count: 0 },
  { icon: 'ri-draft-line', text: 'Drafts', value: 'drafts', count: 2 },
  { icon: 'ri-archive-line', text: 'Archive', value: 'archive', count: 15 },
  { icon: 'ri-spam-line', text: 'Spam', value: 'spam', count: 5 },
  { icon: 'ri-delete-bin-line', text: 'Trash', value: 'trash', count: 8 },
])

const mockEmails: Email[] = [
  {
    id: 1,
    from: 'Sarah Johnson',
    fromEmail: 'sarah.j@company.com',
    subject: 'Q4 Financial Report Review',
    preview: 'Hi team, I have reviewed the Q4 financial reports and have some feedback...',
    body: 'Hi team,\n\nI have reviewed the Q4 financial reports and have some feedback. Overall, the numbers look great, but I think we need to discuss the marketing budget allocation.\n\nCan we schedule a meeting this week?\n\nBest regards,\nSarah',
    date: 'Today',
    time: '10:30 AM',
    read: false,
    starred: true,
    attachments: [
      { name: 'Q4_Report.pdf', size: '2.4 MB' },
      { name: 'Budget_Analysis.xlsx', size: '856 KB' },
    ],
  },
  {
    id: 2,
    from: 'Michael Chen',
    fromEmail: 'mchen@techstartup.io',
    subject: 'Project Timeline Update',
    preview: 'Following up on our discussion about the new feature timeline...',
    body: 'Hi,\n\nFollowing up on our discussion about the new feature timeline. We are making good progress but may need an additional week for testing.\n\nLet me know your thoughts.\n\nMichael',
    date: 'Today',
    time: '9:15 AM',
    read: false,
    starred: false,
  },
  {
    id: 3,
    from: 'Emily Rodriguez',
    fromEmail: 'emily.r@design.co',
    subject: 'Design Mockups for Review',
    preview: 'Attached are the latest design mockups for the mobile app...',
    body: 'Hello,\n\nAttached are the latest design mockups for the mobile app. I have incorporated all the feedback from our last meeting.\n\nPlease review and let me know if any changes are needed.\n\nThanks,\nEmily',
    date: 'Yesterday',
    time: '4:22 PM',
    read: true,
    starred: true,
    attachments: [
      { name: 'App_Mockups_v3.fig', size: '12.1 MB' },
    ],
  },
  {
    id: 4,
    from: 'David Park',
    fromEmail: 'david@example.com',
    subject: 'Weekend Hiking Trip',
    preview: 'Hey! Are you still interested in the hiking trip this weekend?',
    body: 'Hey!\n\nAre you still interested in the hiking trip this weekend? We are planning to leave Saturday morning around 7 AM.\n\nLet me know!\n\nDavid',
    date: 'Yesterday',
    time: '2:10 PM',
    read: true,
    starred: false,
  },
  {
    id: 5,
    from: 'LinkedIn',
    fromEmail: 'notifications@linkedin.com',
    subject: 'You have 3 new connection requests',
    preview: 'John Smith, Maria Garcia, and 1 other want to connect...',
    body: 'You have new connection requests on LinkedIn.\n\nJohn Smith, Maria Garcia, and 1 other want to connect with you.\n\nView all connections.',
    date: '2 days ago',
    time: '11:45 AM',
    read: true,
    starred: false,
  },
]

const emails = ref<Email[]>(mockEmails)

const filteredEmails = computed(() => {
  let filtered = emails.value

  if (selectedFolder.value === 'starred')
    filtered = filtered.filter(email => email.starred)

  // Search by text, email address, or domain
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter((email) => {
      // Check if searching by domain (starts with @)
      if (query.startsWith('@')) {
        const domain = query.substring(1)
        return email.fromEmail.toLowerCase().includes(domain)
      }

      // Check if searching by email address (contains @)
      if (query.includes('@')) {
        return email.fromEmail.toLowerCase().includes(query)
      }

      // Regular text search
      return email.subject.toLowerCase().includes(query)
        || email.from.toLowerCase().includes(query)
        || email.fromEmail.toLowerCase().includes(query)
        || email.preview.toLowerCase().includes(query)
    })
  }

  // Filter by attachments
  if (filterHasAttachments.value)
    filtered = filtered.filter(email => email.attachments && email.attachments.length > 0)

  // Filter by unread
  if (filterUnreadOnly.value)
    filtered = filtered.filter(email => !email.read)

  // Filter by starred
  if (filterStarredOnly.value)
    filtered = filtered.filter(email => email.starred)

  return filtered
})

// Watch email field and auto-fill IMAP, SMTP, and username
watch(() => newMailbox.value.email, (newEmail) => {
  if (newEmail && newEmail.includes('@')) {
    const domain = newEmail.split('@')[1]
    if (domain) {
      // Auto-fill username with email
      newMailbox.value.username = newEmail

      // Auto-fill IMAP host as imap.domain
      newMailbox.value.imapHost = `imap.${domain}`

      // Auto-fill SMTP host as smtp.domain
      newMailbox.value.smtpHost = `smtp.${domain}`
    }
  }
})

function selectEmail(email: Email) {
  selectedEmail.value = email
  if (!email.read) {
    email.read = true
    const folder = folders.value.find(f => f.value === selectedFolder.value)
    if (folder && folder.count > 0)
      folder.count--
  }
}

function toggleStar(email: Email) {
  email.starred = !email.starred
}

function deleteEmail(email: Email) {
  const index = emails.value.findIndex(e => e.id === email.id)
  if (index > -1) {
    emails.value.splice(index, 1)
    selectedEmail.value = null
  }
}

function backToList() {
  selectedEmail.value = null
}

function handleDragStart(index: number) {
  draggedIndex.value = index
}

function handleDragOver(event: DragEvent, index: number) {
  event.preventDefault()
  dragOverIndex.value = index
}

function handleDragLeave() {
  dragOverIndex.value = null
}

function handleDrop(event: DragEvent, dropIndex: number) {
  event.preventDefault()
  if (draggedIndex.value === null || draggedIndex.value === dropIndex)
    return

  const draggedItem = folders.value[draggedIndex.value]
  folders.value.splice(draggedIndex.value, 1)
  folders.value.splice(dropIndex, 0, draggedItem)
  draggedIndex.value = null
  dragOverIndex.value = null
}

function handleDragEnd() {
  draggedIndex.value = null
  dragOverIndex.value = null
}

function toggleMailbox(mailboxId: number) {
  const index = expandedMailboxes.value.indexOf(mailboxId)
  if (index > -1)
    expandedMailboxes.value.splice(index, 1)
  else
    expandedMailboxes.value.push(mailboxId)
}

function selectFolder(mailboxId: number, folder: string) {
  selectedMailboxId.value = mailboxId
  selectedFolder.value = folder
  selectedEmail.value = null
}

function openAddMailbox() {
  editingMailbox.value = null
  newMailbox.value = {
    id: Date.now(),
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
    isActive: false,
  }
  resetValidationErrors()
  mailboxSettingsDialog.value = true
}

function fillGmailSettings() {
  newMailbox.value.imapHost = 'imap.gmail.com'
  newMailbox.value.imapPort = 993
  newMailbox.value.imapSecurity = 'SSL/TLS'
  newMailbox.value.smtpHost = 'smtp.gmail.com'
  newMailbox.value.smtpPort = 587
  newMailbox.value.smtpSecurity = 'STARTTLS'
}

function fillOutlookSettings() {
  newMailbox.value.imapHost = 'outlook.office365.com'
  newMailbox.value.imapPort = 993
  newMailbox.value.imapSecurity = 'SSL/TLS'
  newMailbox.value.smtpHost = 'smtp.office365.com'
  newMailbox.value.smtpPort = 587
  newMailbox.value.smtpSecurity = 'STARTTLS'
}

function fillYahooSettings() {
  newMailbox.value.imapHost = 'imap.mail.yahoo.com'
  newMailbox.value.imapPort = 993
  newMailbox.value.imapSecurity = 'SSL/TLS'
  newMailbox.value.smtpHost = 'smtp.mail.yahoo.com'
  newMailbox.value.smtpPort = 587
  newMailbox.value.smtpSecurity = 'STARTTLS'
}

function openEditMailbox(mailbox: Mailbox) {
  editingMailbox.value = mailbox
  newMailbox.value = { ...mailbox }
  resetValidationErrors()
  mailboxSettingsDialog.value = true
}

function resetValidationErrors() {
  mailboxFormErrors.value = {
    name: false,
    email: false,
    imapHost: false,
    imapPort: false,
    smtpHost: false,
    smtpPort: false,
    username: false,
    password: false,
  }
}

function validateMailboxForm() {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

  mailboxFormErrors.value.name = !newMailbox.value.name || newMailbox.value.name.trim() === ''
  mailboxFormErrors.value.email = !newMailbox.value.email || !emailRegex.test(newMailbox.value.email)
  mailboxFormErrors.value.imapHost = !newMailbox.value.imapHost || newMailbox.value.imapHost.trim() === ''
  mailboxFormErrors.value.imapPort = !newMailbox.value.imapPort || newMailbox.value.imapPort < 1 || newMailbox.value.imapPort > 65535
  mailboxFormErrors.value.smtpHost = !newMailbox.value.smtpHost || newMailbox.value.smtpHost.trim() === ''
  mailboxFormErrors.value.smtpPort = !newMailbox.value.smtpPort || newMailbox.value.smtpPort < 1 || newMailbox.value.smtpPort > 65535
  mailboxFormErrors.value.username = !newMailbox.value.username || newMailbox.value.username.trim() === ''
  mailboxFormErrors.value.password = !newMailbox.value.password || newMailbox.value.password.trim() === ''

  return !Object.values(mailboxFormErrors.value).some(error => error)
}

function saveMailbox() {
  if (!validateMailboxForm()) {
    return
  }

  if (editingMailbox.value) {
    const index = mailboxes.value.findIndex(m => m.id === editingMailbox.value!.id)
    if (index > -1)
      mailboxes.value[index] = { ...newMailbox.value }
  }
  else {
    mailboxes.value.push({ ...newMailbox.value })
  }
  mailboxSettingsDialog.value = false
}

function deleteMailbox(mailbox: Mailbox) {
  const index = mailboxes.value.findIndex(m => m.id === mailbox.id)
  if (index > -1) {
    mailboxes.value.splice(index, 1)
    if (selectedMailboxId.value === mailbox.id && mailboxes.value.length > 0)
      selectedMailboxId.value = mailboxes.value[0].id
  }
}

function getAvatarColor(name: string) {
  const colors = ['primary', 'secondary', 'success', 'info', 'warning', 'error']
  const firstChar = name.charAt(0).toUpperCase()
  const index = firstChar.charCodeAt(0) % colors.length
  return colors[index]
}

function openReply() {
  replyDialog.value = true
}

function openForward() {
  forwardDialog.value = true
}

function archiveEmail(email: Email) {
  // Archive functionality - could move email to archive folder
  // For now, just remove from current view
  const index = emails.value.indexOf(email)
  if (index > -1) {
    emails.value.splice(index, 1)
    if (selectedEmail.value?.id === email.id)
      selectedEmail.value = null
  }
}
</script>

<template>
  <VRow class="h-100">
    <!-- Sidebar -->
    <VCol
      cols="12"
      md="3"
      lg="2"
      class="d-none d-md-block border-e"
    >
      <!-- Compose Button -->
      <div class="pa-4">
        <VBtn
          block
          color="primary"
          prepend-icon="ri-edit-line"
          @click="composeDialog = true"
        >
          Compose
        </VBtn>
      </div>

      <VDivider />

      <!-- Mailboxes with Folders -->
      <div class="mailbox-list">
        <template
          v-for="mailbox in mailboxes"
          :key="mailbox.id"
        >
          <!-- Mailbox Header -->
          <div
            class="mailbox-header pa-3 d-flex align-center"
            @click="toggleMailbox(mailbox.id)"
          >
            <VAvatar
              v-if="!mailbox.hasError"
              :color="mailbox.color"
              size="24"
              class="me-2"
            >
              <span class="text-caption text-white">{{ mailbox.name.charAt(0) }}</span>
            </VAvatar>
            <VIcon
              v-else
              color="error"
              size="24"
              class="me-2"
            >
              ri-error-warning-fill
            </VIcon>
            <div class="flex-grow-1 text-truncate">
              <div
                class="text-caption font-weight-bold"
                :class="{ 'text-error': mailbox.hasError }"
              >
                {{ mailbox.name }}
              </div>
              <div
                class="text-caption"
                :class="mailbox.hasError ? 'text-error' : 'text-disabled'"
              >
                {{ mailbox.email }}
              </div>
              <div
                v-if="mailbox.hasError && mailbox.errorMessage"
                class="text-caption text-error mt-1"
              >
                {{ mailbox.errorMessage }}
              </div>
            </div>
            <VIcon size="small">
              {{ expandedMailboxes.includes(mailbox.id) ? 'ri-arrow-down-s-line' : 'ri-arrow-right-s-line' }}
            </VIcon>
            <VBtn
              icon="ri-settings-3-line"
              variant="text"
              size="x-small"
              class="ms-1"
              @click.stop="openEditMailbox(mailbox)"
            />
          </div>

          <!-- Folders List (Collapsible) -->
          <VExpandTransition>
            <VList
              v-show="expandedMailboxes.includes(mailbox.id)"
              density="compact"
              class="ps-2"
            >
              <VListItem
                v-for="(folder, index) in folders"
                :key="`${mailbox.id}-${folder.value}`"
                :prepend-icon="folder.icon"
                :title="folder.text"
                :active="selectedMailboxId === mailbox.id && selectedFolder === folder.value"
                :class="{
                  'dragging': draggedIndex === index,
                  'drag-over': dragOverIndex === index && draggedIndex !== index
                }"
                draggable="true"
                @click="selectFolder(mailbox.id, folder.value)"
                @dragstart="handleDragStart(index)"
                @dragover="handleDragOver($event, index)"
                @dragleave="handleDragLeave"
                @drop="handleDrop($event, index)"
                @dragend="handleDragEnd"
              >
                <template #prepend>
                  <VIcon
                    :icon="folder.icon"
                    class="drag-handle me-3"
                    size="small"
                  />
                </template>
                <template #append>
                  <VChip
                    v-if="folder.count > 0"
                    :color="selectedMailboxId === mailbox.id && selectedFolder === folder.value ? 'primary' : ''"
                    size="small"
                  >
                    {{ folder.count }}
                  </VChip>
                </template>
              </VListItem>
            </VList>
          </VExpandTransition>

          <VDivider />
        </template>

        <!-- Add Mailbox Button -->
        <div class="pa-3">
          <VBtn
            block
            variant="outlined"
            prepend-icon="ri-add-line"
            size="small"
            @click="openAddMailbox"
          >
            Add Mailbox
          </VBtn>
        </div>
      </div>
    </VCol>

    <!-- Email List / Detail View -->
    <VCol
      cols="12"
      md="9"
      lg="10"
      class="pa-0"
    >
      <!-- Toolbar -->
      <VSheet class="border-b pa-4">
        <VRow align="center">
          <VCol cols="12" md="6">
            <VTextField
              v-model="searchQuery"
              density="compact"
              placeholder="Search by text, email, or @domain..."
              prepend-inner-icon="ri-search-line"
              variant="outlined"
              hide-details
            >
              <template #append-inner>
                <VBtn
                  :icon="showFilters ? 'ri-filter-fill' : 'ri-filter-line'"
                  :color="showFilters || filterHasAttachments || filterUnreadOnly || filterStarredOnly ? 'primary' : 'default'"
                  variant="text"
                  size="small"
                  @click="showFilters = !showFilters"
                />
              </template>
            </VTextField>
          </VCol>
          <VCol
            cols="12"
            md="6"
            class="text-end"
          >
            <VBtn
              icon="ri-refresh-line"
              variant="text"
              size="small"
            />
            <VBtn
              icon="ri-more-2-line"
              variant="text"
              size="small"
            />
          </VCol>
        </VRow>

        <!-- Filters Row -->
        <VExpandTransition>
          <VRow v-show="showFilters" class="mt-3">
            <VCol cols="12">
              <div class="d-flex flex-wrap gap-2">
                <VChip
                  :variant="filterHasAttachments ? 'flat' : 'outlined'"
                  :color="filterHasAttachments ? 'primary' : 'default'"
                  prepend-icon="ri-attachment-2"
                  @click="filterHasAttachments = !filterHasAttachments"
                >
                  Has attachments
                </VChip>
                <VChip
                  :variant="filterUnreadOnly ? 'flat' : 'outlined'"
                  :color="filterUnreadOnly ? 'primary' : 'default'"
                  prepend-icon="ri-mail-line"
                  @click="filterUnreadOnly = !filterUnreadOnly"
                >
                  Unread only
                </VChip>
                <VChip
                  :variant="filterStarredOnly ? 'flat' : 'outlined'"
                  :color="filterStarredOnly ? 'warning' : 'default'"
                  prepend-icon="ri-star-line"
                  @click="filterStarredOnly = !filterStarredOnly"
                >
                  Starred only
                </VChip>
                <VChip
                  v-if="filterHasAttachments || filterUnreadOnly || filterStarredOnly"
                  variant="text"
                  prepend-icon="ri-close-line"
                  @click="filterHasAttachments = false; filterUnreadOnly = false; filterStarredOnly = false"
                >
                  Clear filters
                </VChip>
              </div>
            </VCol>
          </VRow>
        </VExpandTransition>
      </VSheet>

      <!-- Email List View -->
      <div v-if="!selectedEmail" class="email-list">
        <VList lines="three">
          <template
            v-for="(email, index) in filteredEmails"
            :key="email.id"
          >
            <VListItem
              :class="{ 'bg-grey-lighten-4': !email.read }"
              @click="selectEmail(email)"
            >
              <template #prepend>
                <VAvatar
                  :color="getAvatarColor(email.from)"
                  size="40"
                >
                  <span class="text-white">{{ email.from.charAt(0).toUpperCase() }}</span>
                </VAvatar>
              </template>

              <VListItemTitle class="font-weight-medium">
                <span :class="{ 'font-weight-bold': !email.read }">
                  {{ email.from }}
                </span>
                <VIcon
                  v-if="email.attachments"
                  size="small"
                  class="ms-2"
                >
                  ri-attachment-2
                </VIcon>
              </VListItemTitle>

              <VListItemSubtitle class="mb-1">
                <span :class="{ 'font-weight-bold': !email.read }">
                  {{ email.subject }}
                </span>
              </VListItemSubtitle>

              <VListItemSubtitle class="text-truncate">
                {{ email.preview }}
              </VListItemSubtitle>

              <template #append>
                <div class="d-flex flex-column align-end">
                  <div class="text-caption text-disabled mb-2">
                    {{ email.time }}
                  </div>
                  <div class="d-flex gap-1">
                    <VBtn
                      :icon="email.starred ? 'ri-star-fill' : 'ri-star-line'"
                      :color="email.starred ? 'warning' : 'default'"
                      variant="text"
                      size="x-small"
                      @click.stop="toggleStar(email)"
                    />
                    <VBtn
                      icon="ri-archive-line"
                      variant="text"
                      size="x-small"
                      @click.stop="archiveEmail(email)"
                    />
                  </div>
                </div>
              </template>
            </VListItem>

            <VDivider v-if="index < filteredEmails.length - 1" />
          </template>
        </VList>

        <div
          v-if="filteredEmails.length === 0"
          class="text-center pa-8"
        >
          <VIcon
            size="64"
            color="grey"
          >
            ri-mail-line
          </VIcon>
          <div class="text-h6 mt-4 text-disabled">
            No emails found
          </div>
        </div>
      </div>

      <!-- Email Detail View -->
      <div v-else class="email-detail pa-6">
        <div class="d-flex align-center mb-6">
          <VBtn
            icon="ri-arrow-left-line"
            variant="text"
            @click="backToList"
          />
          <VSpacer />
          <VBtn
            icon="ri-reply-line"
            variant="text"
            class="me-2"
            @click="openReply"
          />
          <VBtn
            icon="ri-share-forward-line"
            variant="text"
            class="me-2"
            @click="openForward"
          />
          <VBtn
            :icon="selectedEmail.starred ? 'ri-star-fill' : 'ri-star-line'"
            :color="selectedEmail.starred ? 'warning' : 'default'"
            variant="text"
            class="me-2"
            @click="toggleStar(selectedEmail)"
          />
          <VBtn
            icon="ri-archive-line"
            variant="text"
            class="me-2"
            @click="archiveEmail(selectedEmail)"
          />
          <VBtn
            icon="ri-delete-bin-line"
            variant="text"
            color="error"
            @click="deleteEmail(selectedEmail)"
          />
        </div>

        <div class="text-h5 font-weight-bold mb-4">
          {{ selectedEmail.subject }}
        </div>

        <div class="d-flex align-center mb-4">
          <VAvatar
            :color="getAvatarColor(selectedEmail.from)"
            size="48"
            class="me-3"
          >
            <span class="text-white text-h6">{{ selectedEmail.from.charAt(0).toUpperCase() }}</span>
          </VAvatar>
          <div>
            <div class="font-weight-bold">
              {{ selectedEmail.from }}
            </div>
            <div class="text-caption text-disabled">
              {{ selectedEmail.fromEmail }}
            </div>
          </div>
          <VSpacer />
          <div class="text-caption text-disabled">
            {{ selectedEmail.date }} at {{ selectedEmail.time }}
          </div>
        </div>

        <VDivider class="my-4" />

        <div class="email-body mb-4" style="white-space: pre-wrap; line-height: 1.8;">
          {{ selectedEmail.body }}
        </div>

        <div v-if="selectedEmail.attachments" class="mt-6">
          <div class="text-subtitle-2 mb-2">
            Attachments ({{ selectedEmail.attachments.length }})
          </div>
          <VChip
            v-for="attachment in selectedEmail.attachments"
            :key="attachment.name"
            prepend-icon="ri-attachment-2"
            class="me-2 mb-2"
            variant="outlined"
          >
            {{ attachment.name }} ({{ attachment.size }})
          </VChip>
        </div>

        <VDivider class="my-6" />

        <VBtn
          color="primary"
          prepend-icon="ri-reply-line"
          class="me-2"
          @click="openReply"
        >
          Reply
        </VBtn>
        <VBtn
          variant="outlined"
          prepend-icon="ri-share-forward-line"
          @click="openForward"
        >
          Forward
        </VBtn>
      </div>
    </VCol>

    <!-- Compose Dialog -->
    <VDialog
      v-model="composeDialog"
      max-width="800"
    >
      <VCard>
        <VCardTitle class="d-flex align-center pa-4">
          <span>New Message</span>
          <VSpacer />
          <VBtn
            icon="ri-close-line"
            variant="text"
            size="small"
            @click="composeDialog = false"
          />
        </VCardTitle>

        <VDivider />

        <VCardText class="pa-4">
          <div class="d-flex align-center mb-4">
            <VTextField
              label="To"
              variant="outlined"
              density="compact"
              class="flex-grow-1"
            />
            <VBtn
              v-if="!showCc"
              variant="text"
              size="small"
              class="ms-2"
              @click="showCc = true"
            >
              Cc
            </VBtn>
            <VBtn
              v-if="!showBcc"
              variant="text"
              size="small"
              class="ms-2"
              @click="showBcc = true"
            >
              Bcc
            </VBtn>
          </div>

          <VExpandTransition>
            <VTextField
              v-show="showCc"
              label="Cc"
              variant="outlined"
              density="compact"
              class="mb-4"
            >
              <template #append-inner>
                <VBtn
                  icon="ri-close-line"
                  variant="text"
                  size="x-small"
                  @click="showCc = false"
                />
              </template>
            </VTextField>
          </VExpandTransition>

          <VExpandTransition>
            <VTextField
              v-show="showBcc"
              label="Bcc"
              variant="outlined"
              density="compact"
              class="mb-4"
            >
              <template #append-inner>
                <VBtn
                  icon="ri-close-line"
                  variant="text"
                  size="x-small"
                  @click="showBcc = false"
                />
              </template>
            </VTextField>
          </VExpandTransition>

          <VTextField
            label="Subject"
            variant="outlined"
            density="compact"
            class="mb-4"
          />
          <VTextarea
            label="Message"
            variant="outlined"
            rows="10"
          />
        </VCardText>

        <VDivider />

        <VCardActions class="pa-4">
          <VBtn
            color="primary"
            prepend-icon="ri-send-plane-line"
          >
            Send
          </VBtn>
          <VBtn
            variant="outlined"
            prepend-icon="ri-attachment-2"
          >
            Attach
          </VBtn>
          <VSpacer />
          <VBtn
            variant="text"
            @click="composeDialog = false"
          >
            Discard
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Reply Dialog -->
    <VDialog
      v-model="replyDialog"
      max-width="800"
    >
      <VCard>
        <VCardTitle class="d-flex align-center pa-4">
          <span>Reply to: {{ selectedEmail?.subject }}</span>
          <VSpacer />
          <VBtn
            icon="ri-close-line"
            variant="text"
            size="small"
            @click="replyDialog = false"
          />
        </VCardTitle>

        <VDivider />

        <VCardText class="pa-4">
          <VTextField
            :model-value="selectedEmail?.fromEmail"
            label="To"
            variant="outlined"
            density="compact"
            readonly
            class="mb-4"
          />

          <div class="d-flex align-center mb-4">
            <VBtn
              v-if="!showCcReply"
              variant="text"
              size="small"
              @click="showCcReply = true"
            >
              Cc
            </VBtn>
            <VBtn
              v-if="!showBccReply"
              variant="text"
              size="small"
              class="ms-2"
              @click="showBccReply = true"
            >
              Bcc
            </VBtn>
          </div>

          <VExpandTransition>
            <VTextField
              v-show="showCcReply"
              label="Cc"
              variant="outlined"
              density="compact"
              class="mb-4"
            >
              <template #append-inner>
                <VBtn
                  icon="ri-close-line"
                  variant="text"
                  size="x-small"
                  @click="showCcReply = false"
                />
              </template>
            </VTextField>
          </VExpandTransition>

          <VExpandTransition>
            <VTextField
              v-show="showBccReply"
              label="Bcc"
              variant="outlined"
              density="compact"
              class="mb-4"
            >
              <template #append-inner>
                <VBtn
                  icon="ri-close-line"
                  variant="text"
                  size="x-small"
                  @click="showBccReply = false"
                />
              </template>
            </VTextField>
          </VExpandTransition>

          <VTextarea
            label="Message"
            variant="outlined"
            rows="10"
            placeholder="Type your reply here..."
            class="mb-4"
          />

          <VDivider class="mb-3" />

          <div class="pa-3 bg-grey-lighten-4 rounded">
            <div class="text-caption text-disabled mb-2">Original Message:</div>
            <div class="font-weight-bold">{{ selectedEmail?.from }}</div>
            <div class="text-caption text-disabled">{{ selectedEmail?.date }} at {{ selectedEmail?.time }}</div>
            <div class="mt-2" style="white-space: pre-wrap">{{ selectedEmail?.body }}</div>
          </div>
        </VCardText>

        <VDivider />

        <VCardActions class="pa-4">
          <VBtn
            color="primary"
            prepend-icon="ri-send-plane-line"
          >
            Send
          </VBtn>
          <VBtn
            variant="outlined"
            prepend-icon="ri-attachment-2"
          >
            Attach
          </VBtn>
          <VSpacer />
          <VBtn
            variant="text"
            @click="replyDialog = false"
          >
            Discard
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Forward Dialog -->
    <VDialog
      v-model="forwardDialog"
      max-width="800"
    >
      <VCard>
        <VCardTitle class="d-flex align-center pa-4">
          <span>Forward: {{ selectedEmail?.subject }}</span>
          <VSpacer />
          <VBtn
            icon="ri-close-line"
            variant="text"
            size="small"
            @click="forwardDialog = false"
          />
        </VCardTitle>

        <VDivider />

        <VCardText class="pa-4">
          <div class="d-flex align-center mb-4">
            <VTextField
              label="To"
              variant="outlined"
              density="compact"
              class="flex-grow-1"
            />
            <VBtn
              v-if="!showCcForward"
              variant="text"
              size="small"
              class="ms-2"
              @click="showCcForward = true"
            >
              Cc
            </VBtn>
            <VBtn
              v-if="!showBccForward"
              variant="text"
              size="small"
              class="ms-2"
              @click="showBccForward = true"
            >
              Bcc
            </VBtn>
          </div>

          <VExpandTransition>
            <VTextField
              v-show="showCcForward"
              label="Cc"
              variant="outlined"
              density="compact"
              class="mb-4"
            >
              <template #append-inner>
                <VBtn
                  icon="ri-close-line"
                  variant="text"
                  size="x-small"
                  @click="showCcForward = false"
                />
              </template>
            </VTextField>
          </VExpandTransition>

          <VExpandTransition>
            <VTextField
              v-show="showBccForward"
              label="Bcc"
              variant="outlined"
              density="compact"
              class="mb-4"
            >
              <template #append-inner>
                <VBtn
                  icon="ri-close-line"
                  variant="text"
                  size="x-small"
                  @click="showBccForward = false"
                />
              </template>
            </VTextField>
          </VExpandTransition>

          <VTextarea
            label="Message"
            variant="outlined"
            rows="10"
            placeholder="Add a message (optional)..."
            class="mb-4"
          />

          <VDivider class="mb-3" />

          <div class="pa-3 bg-grey-lighten-4 rounded">
            <div class="font-weight-bold mb-2">---------- Forwarded message ---------</div>
            <div class="text-body-2"><span class="font-weight-bold">From:</span> {{ selectedEmail?.from }} &lt;{{ selectedEmail?.fromEmail }}&gt;</div>
            <div class="text-body-2"><span class="font-weight-bold">Date:</span> {{ selectedEmail?.date }} at {{ selectedEmail?.time }}</div>
            <div class="text-body-2"><span class="font-weight-bold">Subject:</span> {{ selectedEmail?.subject }}</div>
            <div class="mt-3" style="white-space: pre-wrap">{{ selectedEmail?.body }}</div>
            <div v-if="selectedEmail?.attachments" class="mt-3">
              <div class="font-weight-bold mb-2">Attachments:</div>
              <VChip
                v-for="attachment in selectedEmail.attachments"
                :key="attachment.name"
                size="small"
                class="me-2"
                prepend-icon="ri-attachment-2"
              >
                {{ attachment.name }} ({{ attachment.size }})
              </VChip>
            </div>
          </div>
        </VCardText>

        <VDivider />

        <VCardActions class="pa-4">
          <VBtn
            color="primary"
            prepend-icon="ri-send-plane-line"
          >
            Send
          </VBtn>
          <VBtn
            variant="outlined"
            prepend-icon="ri-attachment-2"
          >
            Attach
          </VBtn>
          <VSpacer />
          <VBtn
            variant="text"
            @click="forwardDialog = false"
          >
            Discard
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Mailbox Settings Dialog -->
    <VDialog
      v-model="mailboxSettingsDialog"
      max-width="600"
      scrollable
    >
      <VCard>
        <VCardTitle class="d-flex align-center pa-4">
          <span>{{ editingMailbox ? 'Edit' : 'Add' }} Mailbox</span>
          <VSpacer />
          <VBtn
            icon="ri-close-line"
            variant="text"
            size="small"
            @click="mailboxSettingsDialog = false"
          />
        </VCardTitle>

        <VDivider />

        <VCardText class="pa-4">
          <VRow>
            <VCol cols="12">
              <div class="text-subtitle-2 mb-2">Quick Setup</div>
              <div class="d-flex gap-2">
                <VBtn
                  size="small"
                  variant="outlined"
                  @click="fillGmailSettings"
                >
                  Gmail
                </VBtn>
                <VBtn
                  size="small"
                  variant="outlined"
                  @click="fillOutlookSettings"
                >
                  Outlook
                </VBtn>
                <VBtn
                  size="small"
                  variant="outlined"
                  @click="fillYahooSettings"
                >
                  Yahoo
                </VBtn>
              </div>
            </VCol>

            <VCol cols="12">
              <VDivider />
            </VCol>

            <VCol cols="12">
              <VTextField
                v-model="newMailbox.name"
                label="Mailbox Name *"
                variant="outlined"
                density="compact"
                placeholder="e.g., Work Gmail"
                :error="mailboxFormErrors.name"
                :error-messages="mailboxFormErrors.name ? 'Mailbox name is required' : ''"
              />
            </VCol>

            <VCol cols="12">
              <VTextField
                v-model="newMailbox.email"
                label="Email Address *"
                variant="outlined"
                density="compact"
                type="email"
                placeholder="your@email.com"
                :error="mailboxFormErrors.email"
                :error-messages="mailboxFormErrors.email ? 'Valid email address is required' : ''"
              />
            </VCol>

            <VCol cols="12">
              <VTextField
                v-model="newMailbox.username"
                label="Username *"
                variant="outlined"
                density="compact"
                placeholder="Usually same as email"
                :error="mailboxFormErrors.username"
                :error-messages="mailboxFormErrors.username ? 'Username is required' : ''"
              />
            </VCol>

            <VCol cols="12">
              <VTextField
                v-model="newMailbox.password"
                label="Password *"
                variant="outlined"
                density="compact"
                type="password"
                placeholder="Your email password or app password"
                :error="mailboxFormErrors.password"
                :error-messages="mailboxFormErrors.password ? 'Password is required' : ''"
              />
            </VCol>

            <VCol cols="12">
              <VDivider />
            </VCol>

            <VCol cols="12">
              <div class="text-subtitle-2 mb-2">IMAP Settings (Incoming)</div>
            </VCol>

            <VCol cols="8">
              <VTextField
                v-model="newMailbox.imapHost"
                label="IMAP Host *"
                variant="outlined"
                density="compact"
                placeholder="imap.gmail.com"
                :error="mailboxFormErrors.imapHost"
                :error-messages="mailboxFormErrors.imapHost ? 'IMAP host is required' : ''"
              />
            </VCol>

            <VCol cols="4">
              <VTextField
                v-model.number="newMailbox.imapPort"
                label="Port *"
                variant="outlined"
                density="compact"
                type="number"
                placeholder="993"
                :error="mailboxFormErrors.imapPort"
                :error-messages="mailboxFormErrors.imapPort ? 'Valid port (1-65535) required' : ''"
              />
            </VCol>

            <VCol cols="12">
              <VSelect
                v-model="newMailbox.imapSecurity"
                label="Security"
                variant="outlined"
                density="compact"
                :items="['None', 'SSL/TLS', 'STARTTLS']"
              />
            </VCol>

            <VCol cols="12">
              <VDivider />
            </VCol>

            <VCol cols="12">
              <div class="text-subtitle-2 mb-2">SMTP Settings (Outgoing)</div>
            </VCol>

            <VCol cols="8">
              <VTextField
                v-model="newMailbox.smtpHost"
                label="SMTP Host *"
                variant="outlined"
                density="compact"
                placeholder="smtp.gmail.com"
                :error="mailboxFormErrors.smtpHost"
                :error-messages="mailboxFormErrors.smtpHost ? 'SMTP host is required' : ''"
              />
            </VCol>

            <VCol cols="4">
              <VTextField
                v-model.number="newMailbox.smtpPort"
                label="Port *"
                variant="outlined"
                density="compact"
                type="number"
                placeholder="587"
                :error="mailboxFormErrors.smtpPort"
                :error-messages="mailboxFormErrors.smtpPort ? 'Valid port (1-65535) required' : ''"
              />
            </VCol>

            <VCol cols="12">
              <VSelect
                v-model="newMailbox.smtpSecurity"
                label="Security"
                variant="outlined"
                density="compact"
                :items="['None', 'SSL/TLS', 'STARTTLS']"
              />
            </VCol>
          </VRow>
        </VCardText>

        <VDivider />

        <VCardActions class="d-flex flex-wrap gap-4 pa-4">
          <VBtn
            color="primary"
            @click="saveMailbox"
          >
            {{ editingMailbox ? 'Save changes' : 'Add mailbox' }}
          </VBtn>
          <VBtn
            color="secondary"
            variant="outlined"
            @click="mailboxSettingsDialog = false"
          >
            Cancel
          </VBtn>
          <VSpacer />
          <VBtn
            v-if="editingMailbox && mailboxes.length > 1"
            color="error"
            variant="outlined"
            prepend-icon="ri-delete-bin-line"
            @click="deleteMailbox(editingMailbox); mailboxSettingsDialog = false"
          >
            Delete mailbox
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </VRow>
</template>

<style scoped>
.email-list {
  height: calc(100vh - 200px);
  overflow-y: auto;
}

.email-detail {
  height: calc(100vh - 200px);
  overflow-y: auto;
}

.mailbox-list {
  overflow-y: auto;
  max-height: calc(100vh - 180px);
}

.mailbox-header {
  cursor: pointer;
  transition: background-color 0.2s;
}

.mailbox-header:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.h-100 {
  height: 100%;
}

.drag-handle {
  cursor: grab;
}

.dragging {
  opacity: 0.5;
  cursor: grabbing !important;
  transform: scale(0.98);
}

.drag-over {
  position: relative;
  background: rgba(var(--v-theme-primary), 0.08) !important;
  border-left: 3px solid rgb(var(--v-theme-primary)) !important;
  animation: pulse 0.6s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    background: rgba(var(--v-theme-primary), 0.08);
  }
  50% {
    background: rgba(var(--v-theme-primary), 0.15);
  }
}

:deep(.v-list-item) {
  cursor: pointer;
  transition: all 0.2s ease;
}

:deep(.v-list-item:hover .drag-handle) {
  cursor: grab;
}
</style>
