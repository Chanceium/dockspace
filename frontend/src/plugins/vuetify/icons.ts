import type { IconAliases, IconProps } from 'vuetify'

/* eslint-disable regex/invalid */
const customIcons: Record<string, string> = {
  'mdi-checkbox-blank-outline': 'ri-checkbox-blank-line',
  'mdi-checkbox-marked': 'ri-checkbox-fill',
  'mdi-minus-box': 'ri-checkbox-indeterminate-line',
  'mdi-radiobox-marked': 'ri-radio-button-fill',
  'mdi-radiobox-blank': 'ri-radio-button-line',
}

const aliases: Partial<IconAliases> = {
  info: 'ri-error-warning-line',
  success: 'ri-checkbox-circle-line',
  warning: 'ri-alert-line',
  error: 'ri-error-warning-line',
  calendar: 'ri-calendar-2-line',
  collapse: 'ri-arrow-up-s-line',
  complete: 'ri-check-line',
  cancel: 'ri-close-line',
  close: 'ri-close-line',
  delete: 'ri-close-circle-fill',
  clear: 'ri-close-line',
  prev: 'ri-arrow-left-s-line',
  next: 'ri-arrow-right-s-line',
  delimiter: 'ri-circle-line',
  sort: 'ri-arrow-up-line',
  expand: 'ri-arrow-down-s-line',
  menu: 'ri-menu-line',
  subgroup: 'ri-arrow-down-s-fill',
  dropdown: 'ri-arrow-down-s-line',
  edit: 'ri-pencil-line',
  ratingEmpty: 'ri-star-line',
  ratingFull: 'ri-star-fill',
  ratingHalf: 'ri-star-half-line',
  loading: 'ri-refresh-line',
  first: 'ri-skip-back-mini-line',
  last: 'ri-skip-forward-mini-line',
  unfold: 'ri-split-cells-vertical',
  file: 'ri-attachment-2',
  plus: 'ri-add-line',
  minus: 'ri-subtract-line',
  sortAsc: 'ri-arrow-up-line',
  sortDesc: 'ri-arrow-down-line',
}
/* eslint-enable */

export const iconify = {
  component: (props: IconProps) => {
    // Map custom icon names to Remix Icons
    let iconClass = props.icon
    if (typeof props.icon === 'string') {
      const mappedIcon = customIcons[props.icon]

      if (mappedIcon)
        iconClass = mappedIcon
    }

    return h(
      props.tag,
      {
        ...props,

        // As we are using class based icons
        class: [iconClass],

        // Remove used props from DOM rendering
        tag: undefined,
        icon: undefined,
      },
    )
  },
}

export const icons = {
  defaultSet: 'iconify',
  aliases,
  sets: {
    iconify,
  },
}
