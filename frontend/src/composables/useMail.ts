/**
 * Mail composable for managing mail state and operations
 */
import { ref, computed, watch } from 'vue'
import { mailClientService, type Mailbox, type Email, type EmailDetail, type Folder } from '@/services/mailClient'

const mailboxes = ref<Mailbox[]>([])
const selectedMailboxId = ref<number | null>(null)
const selectedFolder = ref('INBOX')
const emails = ref<Email[]>([])
const folders = ref<Folder[]>([])
const selectedEmail = ref<EmailDetail | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

export function useMail() {
  const selectedMailbox = computed(() =>
    mailboxes.value.find(m => m.id === selectedMailboxId.value) || null
  )

  /**
   * Load all mailboxes for current user
   */
  async function loadMailboxes() {
    loading.value = true
    error.value = null

    try {
      const result = await mailClientService.listMailboxes()

      if (result.success && result.mailboxes) {
        mailboxes.value = result.mailboxes

        // Auto-select first mailbox if none selected
        if (!selectedMailboxId.value && result.mailboxes.length > 0) {
          selectedMailboxId.value = result.mailboxes[0].id
        }
      }
      else {
        // Don't show auth errors as they're expected when not logged in
        if (!result.error?.includes('Authentication required')) {
          error.value = result.error || 'Failed to load mailboxes'
        }
      }
    }
    catch (err) {
      error.value = 'Network error loading mailboxes'
      console.error(err)
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Load folders for selected mailbox
   */
  async function loadFolders(mailboxId?: number) {
    const id = mailboxId || selectedMailboxId.value
    if (!id)
      return

    loading.value = true
    error.value = null

    try {
      const result = await mailClientService.listFolders(id)

      if (result.success && result.folders) {
        folders.value = result.folders
      }
      else {
        error.value = result.error || 'Failed to load folders'
      }
    }
    catch (err) {
      error.value = 'Network error loading folders'
      console.error(err)
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Load emails from current folder
   */
  async function loadEmails(folder?: string, limit = 50, offset = 0) {
    if (!selectedMailboxId.value)
      return

    const folderName = folder || selectedFolder.value
    loading.value = true
    error.value = null

    try {
      const result = await mailClientService.fetchEmails(
        selectedMailboxId.value,
        folderName,
        limit,
        offset
      )

      if (result.success && result.emails) {
        emails.value = result.emails
      }
      else {
        error.value = result.error || 'Failed to load emails'
      }
    }
    catch (err) {
      error.value = 'Network error loading emails'
      console.error(err)
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Load full email details
   */
  async function loadEmailDetail(emailId: string, folder?: string) {
    if (!selectedMailboxId.value)
      return

    const folderName = folder || selectedFolder.value
    loading.value = true
    error.value = null

    try {
      const result = await mailClientService.fetchEmailDetail(
        selectedMailboxId.value,
        emailId,
        folderName
      )

      if (result.success && result.email) {
        selectedEmail.value = result.email as EmailDetail
      }
      else {
        error.value = result.error || 'Failed to load email'
      }
    }
    catch (err) {
      error.value = 'Network error loading email'
      console.error(err)
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Send an email
   */
  async function sendEmail(emailData: {
    to: string
    subject: string
    body: string
    cc?: string
    bcc?: string
    replyTo?: string
  }) {
    if (!selectedMailboxId.value)
      return { success: false, error: 'No mailbox selected' }

    loading.value = true
    error.value = null

    try {
      const result = await mailClientService.sendEmail(selectedMailboxId.value, emailData)

      if (!result.success) {
        error.value = result.error || 'Failed to send email'
      }

      return result
    }
    catch (err) {
      error.value = 'Network error sending email'
      console.error(err)
      return { success: false, error: 'Network error' }
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Create a new mailbox
   */
  async function createMailbox(mailboxData: Omit<Mailbox, 'id' | 'hasError' | 'errorMessage' | 'lastSync'>) {
    loading.value = true
    error.value = null

    try {
      const result = await mailClientService.createMailbox(mailboxData)

      if (result.success && result.mailbox) {
        mailboxes.value.push(result.mailbox)

        // Auto-select if first mailbox
        if (mailboxes.value.length === 1) {
          selectedMailboxId.value = result.mailbox.id
        }
      }
      else {
        error.value = result.error || 'Failed to create mailbox'
      }

      return result
    }
    catch (err) {
      error.value = 'Network error creating mailbox'
      console.error(err)
      return { success: false, error: 'Network error' }
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Update a mailbox
   */
  async function updateMailbox(mailboxId: number, updates: Partial<Mailbox>) {
    loading.value = true
    error.value = null

    try {
      const result = await mailClientService.updateMailbox(mailboxId, updates)

      if (result.success && result.mailbox) {
        const index = mailboxes.value.findIndex(m => m.id === mailboxId)
        if (index > -1) {
          mailboxes.value[index] = result.mailbox
        }
      }
      else {
        error.value = result.error || 'Failed to update mailbox'
      }

      return result
    }
    catch (err) {
      error.value = 'Network error updating mailbox'
      console.error(err)
      return { success: false, error: 'Network error' }
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Delete a mailbox
   */
  async function deleteMailbox(mailboxId: number) {
    loading.value = true
    error.value = null

    try {
      const result = await mailClientService.deleteMailbox(mailboxId)

      if (result.success) {
        const index = mailboxes.value.findIndex(m => m.id === mailboxId)
        if (index > -1) {
          mailboxes.value.splice(index, 1)
        }

        // Select another mailbox if deleted was selected
        if (selectedMailboxId.value === mailboxId) {
          selectedMailboxId.value = mailboxes.value.length > 0 ? mailboxes.value[0].id : null
        }
      }
      else {
        error.value = result.error || 'Failed to delete mailbox'
      }

      return result
    }
    catch (err) {
      error.value = 'Network error deleting mailbox'
      console.error(err)
      return { success: false, error: 'Network error' }
    }
    finally {
      loading.value = false
    }
  }

  /**
   * Select a mailbox and folder
   */
  function selectMailboxAndFolder(mailboxId: number, folder: string) {
    selectedMailboxId.value = mailboxId
    selectedFolder.value = folder
    selectedEmail.value = null
  }

  /**
   * Clear selected email
   */
  function clearSelectedEmail() {
    selectedEmail.value = null
  }

  // Watch for mailbox changes and reload folders/emails
  watch(selectedMailboxId, async (newId) => {
    if (newId) {
      await loadFolders(newId)
      await loadEmails()
    }
  })

  watch(selectedFolder, async () => {
    if (selectedMailboxId.value) {
      await loadEmails()
    }
  })

  return {
    // State
    mailboxes,
    selectedMailboxId,
    selectedMailbox,
    selectedFolder,
    emails,
    folders,
    selectedEmail,
    loading,
    error,

    // Actions
    loadMailboxes,
    loadFolders,
    loadEmails,
    loadEmailDetail,
    sendEmail,
    createMailbox,
    updateMailbox,
    deleteMailbox,
    selectMailboxAndFolder,
    clearSelectedEmail,
  }
}
