import { render } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { Seo } from '../Seo'
import { SEO_PAGES, SITE_METADATA } from '@/config/seo'

describe('Seo Component (Task 6)', () => {
  beforeEach(() => {
    document.title = ''
    document.head.innerHTML = ''
    document.documentElement.lang = ''
  })

  it('updates document.title and description from config', () => {
    render(<Seo {...SEO_PAGES.landing} />)

    expect(document.title).toBe(SEO_PAGES.landing.title)
    expect(document.documentElement.lang).toBe('en')

    const desc = document.querySelector("meta[name='description']")
    expect(desc?.getAttribute('content')).toBe(SEO_PAGES.landing.description)

    const canonical = document.querySelector("link[rel='canonical']")
    expect(canonical?.getAttribute('href')).toBe(`${SITE_METADATA.baseUrl}/`)
  })

  it('sets open graph and twitter card metadata including default og:image', () => {
    render(<Seo {...SEO_PAGES.privacy} />)

    const ogTitle = document.querySelector("meta[property='og:title']")
    expect(ogTitle?.getAttribute('content')).toBe(SEO_PAGES.privacy.title)

    const ogImage = document.querySelector("meta[property='og:image']")
    expect(ogImage?.getAttribute('content')).toBe(`${SITE_METADATA.baseUrl}/og-image.png`)

    const ogImageAlt = document.querySelector("meta[property='og:image:alt']")
    expect(ogImageAlt?.getAttribute('content')).toBe(SITE_METADATA.defaultOgImageAlt)

    const twitterCard = document.querySelector("meta[name='twitter:card']")
    expect(twitterCard?.getAttribute('content')).toBe('summary_large_image')
  })

  it('sets robots noindex when noindex is specified', () => {
    render(<Seo {...SEO_PAGES.notFound} />)

    const robots = document.querySelector("meta[name='robots']")
    expect(robots?.getAttribute('content')).toBe('noindex, nofollow')
  })

  it('removes robots noindex when rendering a public indexable page', () => {
    // First render notFound with noindex
    const { unmount } = render(<Seo {...SEO_PAGES.notFound} />)
    expect(document.querySelector("meta[name='robots']")).not.toBeNull()

    unmount()
    // Now render public page
    render(<Seo {...SEO_PAGES.landing} />)
    expect(document.querySelector("meta[name='robots']")).toBeNull()
  })
})
