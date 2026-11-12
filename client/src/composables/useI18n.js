import { ref, computed } from 'vue'
import en from '../locales/en'

// English is bundled (it is the fallback for every key); other locales are code-split
// and fetched on demand, so the main bundle only carries one language.
const translations = { en }
const localeLoaders = {
  ja: () => import('../locales/ja'),
}
const SUPPORTED_LOCALES = ['en', ...Object.keys(localeLoaders)]

// Ensure a locale's messages are in `translations` (no-op for en / already loaded)
const loadLocale = async (locale) => {
  if (translations[locale] || !localeLoaders[locale]) return
  translations[locale] = (await localeLoaders[locale]()).default
}

// Keep <html lang> in sync so screen readers pick the right pronunciation
const applyDocumentLang = (locale) => {
  document.documentElement.lang = locale
}

// Load saved locale from localStorage, default to 'en'. Until its messages are loaded
// we stay on 'en' so there is never a frame with missing keys.
const savedLocale = localStorage.getItem('app-locale')
const initialLocale = SUPPORTED_LOCALES.includes(savedLocale) ? savedLocale : 'en'
const currentLocale = ref('en')
applyDocumentLang('en')

// Awaited in main.js before mount: resolves once the saved locale is ready and applied
export const i18nReady = loadLocale(initialLocale)
  .then(() => {
    currentLocale.value = initialLocale
    applyDocumentLang(initialLocale)
  })
  .catch(() => {
    // Chunk failed to load: keep English rather than blocking the app
  })

// Currency is automatically set based on locale (en -> USD, ja -> JPY)
const currentCurrency = computed(() => {
  return currentLocale.value === 'ja' ? 'JPY' : 'USD'
})

export function useI18n() {
  const t = (key, params = {}) => {
    const keys = key.split('.')
    let value = translations[currentLocale.value]

    for (const k of keys) {
      if (value && typeof value === 'object') {
        value = value[k]
      } else {
        // If translation not found, try English as fallback
        if (currentLocale.value !== 'en') {
          let fallback = translations.en
          for (const fk of keys) {
            if (fallback && typeof fallback === 'object') {
              fallback = fallback[fk]
            } else {
              break
            }
          }
          if (fallback && typeof fallback === 'string') {
            return replacePlaceholders(fallback, params)
          }
        }
        // If still not found, return the key itself
        return key
      }
    }

    if (typeof value === 'string') {
      return replacePlaceholders(value, params)
    }

    return key
  }

  const replacePlaceholders = (text, params) => {
    return text.replace(/\{(\w+)\}/g, (match, key) => {
      return params[key] !== undefined ? params[key] : match
    })
  }

  // Loads the locale chunk first, then switches, so the UI never renders with missing keys
  const setLocale = async (locale) => {
    if (!SUPPORTED_LOCALES.includes(locale)) return
    try {
      await loadLocale(locale)
    } catch {
      return // network failure: stay on the current locale
    }
    currentLocale.value = locale
    localStorage.setItem('app-locale', locale)
    applyDocumentLang(locale)
  }

  const availableLocales = computed(() => SUPPORTED_LOCALES)

  const localeName = computed(() => {
    const names = {
      en: 'English',
      ja: '日本語',
    }
    return names[currentLocale.value] || currentLocale.value
  })

  // Translate product names
  const translateProductName = (productName) => {
    if (currentLocale.value === 'ja' && translations.ja?.productNames[productName]) {
      return translations.ja?.productNames[productName]
    }
    return productName
  }

  // Translate customer names
  const translateCustomerName = (customerName) => {
    if (currentLocale.value === 'ja' && translations.ja?.customerNames[customerName]) {
      return translations.ja?.customerNames[customerName]
    }
    return customerName
  }

  // Translate warehouse names
  const translateWarehouse = (warehouseName) => {
    if (currentLocale.value === 'ja') {
      // Handle city names
      const cityMap = {
        'San Francisco': 'サンフランシスコ',
        London: 'ロンドン',
        Tokyo: '東京',
      }

      if (cityMap[warehouseName]) {
        return cityMap[warehouseName]
      }

      // Handle "Warehouse X-##" pattern
      if (warehouseName.startsWith('Warehouse ')) {
        return warehouseName.replace('Warehouse ', '倉庫')
      }

      return warehouseName
    }
    return warehouseName
  }

  return {
    t,
    setLocale,
    currentLocale: computed(() => currentLocale.value),
    currentCurrency,
    availableLocales,
    localeName,
    translateProductName,
    translateCustomerName,
    translateWarehouse,
  }
}
