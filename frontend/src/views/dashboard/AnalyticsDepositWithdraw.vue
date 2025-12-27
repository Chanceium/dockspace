<script setup lang="ts">
const deposits = [
  {
    title: 'Gumroad Account',
    subtitle: 'Sell UI Kit',
    amount: '+$4,650',
    icon: 'ri-shopping-bag-line',
    color: '#FF90E8',
  },
  {
    title: 'Mastercard',
    subtitle: 'Wallet deposit',
    amount: '+$92,705',
    icon: 'ri-bank-card-line',
    color: '#EB001B',
  },
  {
    title: 'Stripe Account',
    subtitle: 'iOS Application',
    amount: '+$957',
    icon: 'ri-bank-line',
    color: '#635BFF',
  },
  {
    title: 'American Bank',
    subtitle: 'American Bank',
    amount: '+$6,837',
    icon: 'ri-building-line',
    color: '#00599C',
  },
  {
    title: 'Bank Account',
    subtitle: 'Wallet deposit',
    amount: '+$8,934',
    icon: 'ri-wallet-line',
    color: '#1565C0',
  },
]

const withdraws = [
  {
    title: 'Google Adsense',
    subtitle: 'PayPal deposit',
    amount: '-$145',
    icon: 'ri-google-fill',
    color: '#4285F4',
  },
  {
    title: 'GitHub Enterprise',
    subtitle: 'Security & compliance',
    amount: '-$1870',
    icon: 'ri-github-fill',
    color: '#24292E',
  },
  {
    title: 'Upgrade Slack Plan',
    subtitle: 'Debit card deposit',
    amount: '-$450',
    icon: 'ri-slack-fill',
    color: '#4A154B',
  },
  {
    title: 'DigitalOcean',
    subtitle: 'Cloud Hosting',
    amount: '-$540',
    icon: 'ri-cloud-line',
    color: '#0080FF',
  },
  {
    title: 'AWS Account',
    subtitle: 'Choosing a Cloud Platform',
    amount: '-$21',
    icon: 'ri-server-line',
    color: '#FF9900',
  },
]
</script>

<template>
  <VCard>
    <VRow no-gutters>
      <VCol
        cols="12"
        md="6"
      >
        <VCardItem>
          <VCardTitle>Deposit</VCardTitle>

          <template #append>
            <h6 class="text-h6">
              <a
                href="javascript:void(0)"
                class="text-primary"
              >View All</a>
            </h6>
          </template>
        </VCardItem>

        <VCardText>
          <VList class="card-list">
            <VListItem
              v-for="deposit in deposits"
              :key="deposit.title"
            >
              <template #prepend>
                <VAvatar
                  :color="deposit.color"
                  variant="tonal"
                  size="38"
                  class="me-4"
                >
                  <VIcon
                    :icon="deposit.icon"
                    size="20"
                  />
                </VAvatar>
              </template>

              <VListItemTitle class="font-weight-medium mb-1">
                {{ deposit.title }}
              </VListItemTitle>
              <VListItemSubtitle class="text-body-1">
                {{ deposit.subtitle }}
              </VListItemSubtitle>

              <template #append>
                <VListItemAction class="text-success font-weight-medium">
                  {{ deposit.amount }}
                </VListItemAction>
              </template>
            </VListItem>
          </VList>
        </VCardText>
      </VCol>

      <VDivider :vertical="$vuetify.display.mdAndUp" />

      <VCol
        cols="12"
        md="6"
      >
        <VCardItem>
          <VCardTitle>Withdraw</VCardTitle>

          <template #append>
            <h6 class="text-h6">
              <a
                href="javascript:void(0)"
                class="text-primary"
              >View All</a>
            </h6>
          </template>
        </VCardItem>

        <VCardText>
          <VList class="card-list">
            <VListItem
              v-for="withdraw in withdraws"
              :key="withdraw.title"
            >
              <template #prepend>
                <VAvatar
                  :color="withdraw.color"
                  variant="tonal"
                  size="38"
                  class="me-4"
                >
                  <VIcon
                    :icon="withdraw.icon"
                    size="20"
                  />
                </VAvatar>
              </template>

              <VListItemTitle class="font-weight-medium mb-1">
                {{ withdraw.title }}
              </VListItemTitle>
              <VListItemSubtitle class="text-body-1">
                {{ withdraw.subtitle }}
              </VListItemSubtitle>

              <template #append>
                <VListItemAction>
                  <span class="text-error font-weight-medium">
                    {{ withdraw.amount }}
                  </span>
                </VListItemAction>
              </template>
            </VListItem>
          </VList>
        </VCardText>
      </VCol>
    </VRow>
  </VCard>
</template>

<style lang="scss" scoped>
.card-list {
  --v-card-list-gap: 1.25rem;
}
</style>
