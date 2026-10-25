import { useEffect } from 'react'
import { SITE_METADATA } from '@/config/seo'

export interface SeoProps {
  title?: string
  description?: string
  path?: string
  image?: string
  imageAlt?: string
  noindex?: boolean
}

function setMetaTag(selector: string, attributeName: string, attributeValue: string, content: string) {
  let element = document.querySelector(selector)
  if (!element) {
    element = document.createElement('meta')
    element.setAttribute(attributeName, attributeValue)
    document.head.appendChild(element)
  }
  element.setAttribute('content', content)
}

function setCanonicalLink(href: string) {
  let element = document.querySelector("link[rel='canonical']")
  if (!element) {
    element = document.createElement('link')
    element.setAttribute('rel', 'canonical')
    document.head.appendChild(element)
  }
  element.setAttribute('href', href)
}

export function Seo({
  title,
  description,
  path = '',
  image,
  imageAlt,
  noindex = false,
}: SeoProps) {
  const fullTitle = title || SITE_METADATA.defaultTitle
  const fullDescription = description || SITE_METADATA.defaultDescription
  const canonicalUrl = `${SITE_METADATA.baseUrl}${path.startsWith('/') ? path : `/${path}`}`
  const relativeImage = image || SITE_METADATA.defaultOgImage
  const absoluteImageUrl = relativeImage.startsWith('http')
    ? relativeImage
    : `${SITE_METADATA.baseUrl}${relativeImage.startsWith('/') ? relativeImage : `/${relativeImage}`}`
  const altText = imageAlt || SITE_METADATA.defaultOgImageAlt

  useEffect(() => {
    // 1. Title
    document.title = fullTitle

    // 2. Lang attribute on html
    if (!document.documentElement.lang) {
      document.documentElement.lang = 'en'
    }

    // 3. Theme color
    setMetaTag("meta[name='theme-color']", 'name', 'theme-color', SITE_METADATA.themeColor)

    // 4. Primary Description
    setMetaTag("meta[name='description']", 'name', 'description', fullDescription)

    // 5. Canonical
    setCanonicalLink(canonicalUrl)

    // 6. Robots / noindex
    const robotsTag = document.querySelector("meta[name='robots']")
    if (noindex) {
      setMetaTag("meta[name='robots']", 'name', 'robots', 'noindex, nofollow')
    } else if (robotsTag) {
      robotsTag.remove()
    }

    // 7. Open Graph tags
    setMetaTag("meta[property='og:type']", 'property', 'og:type', 'website')
    setMetaTag("meta[property='og:site_name']", 'property', 'og:site_name', SITE_METADATA.siteName)
    setMetaTag("meta[property='og:title']", 'property', 'og:title', fullTitle)
    setMetaTag("meta[property='og:description']", 'property', 'og:description', fullDescription)
    setMetaTag("meta[property='og:url']", 'property', 'og:url', canonicalUrl)
    setMetaTag("meta[property='og:image']", 'property', 'og:image', absoluteImageUrl)
    setMetaTag("meta[property='og:image:alt']", 'property', 'og:image:alt', altText)
    setMetaTag("meta[property='og:locale']", 'property', 'og:locale', SITE_METADATA.locale)

    // 8. Twitter Card tags
    setMetaTag("meta[name='twitter:card']", 'name', 'twitter:card', SITE_METADATA.twitterCard)
    setMetaTag("meta[name='twitter:title']", 'name', 'twitter:title', fullTitle)
    setMetaTag("meta[name='twitter:description']", 'name', 'twitter:description', fullDescription)
    setMetaTag("meta[name='twitter:image']", 'name', 'twitter:image', absoluteImageUrl)
    setMetaTag("meta[name='twitter:image:alt']", 'name', 'twitter:image:alt', altText)
  }, [fullTitle, fullDescription, canonicalUrl, absoluteImageUrl, altText, noindex])

  return null
}

export default Seo
