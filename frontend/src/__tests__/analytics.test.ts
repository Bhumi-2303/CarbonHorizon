import { describe, it, expect, vi, beforeEach } from 'vitest'
import { track, initAnalytics } from '@/analytics'

describe('Privacy-Friendly Analytics Module (Task 19)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    window.plausible = vi.fn()
    const script = document.getElementById('plausible-script')
    if (script) script.remove()
  })

  it('drops tracking if user has NOT consented (canTrackAnalytics === false)', () => {
    track('signup_started', { source: 'hero' }, { canTrackAnalytics: false, isChildProfile: false })
    expect(window.plausible).not.toHaveBeenCalled()
  })

  it('strictly NEVER tracks events for Little Explorer / child profiles', () => {
    // Even if consent was mistakenly marked true, child profile rule overrides it
    track('cta_clicked', { cta_label: 'Calculate', location: 'hero' }, {
      canTrackAnalytics: true,
      isChildProfile: true,
    })
    expect(window.plausible).not.toHaveBeenCalled()
  })

  it('emits typed analytics event when user consented and is not a child profile', () => {
    track('cta_clicked', { cta_label: 'Calculate my carbon footprint', location: 'hero' }, {
      canTrackAnalytics: true,
      isChildProfile: false,
    })
    expect(window.plausible).toHaveBeenCalledWith('cta_clicked', {
      props: {
        cta_label: 'Calculate my carbon footprint',
        location: 'hero',
      },
    })
  })

  it('sanitizes and strips personal data or message text before sending', () => {
    const rawProps: any = {
      category: 'energy',
      message: 'Sensitive user chat message about high energy bills',
      email: 'user@example.com',
      password: 'SecretPassword123!',
      user_id: 'user-uuid-1234',
    }

    track('coach_question_asked', rawProps, {
      canTrackAnalytics: true,
      isChildProfile: false,
    })

    expect(window.plausible).toHaveBeenCalledWith('coach_question_asked', {
      props: {
        category: 'energy',
      },
    })
  })

  it('initAnalytics does not inject script if isChildProfile is true or consent is false', () => {
    initAnalytics(false, false)
    expect(document.getElementById('plausible-script')).toBeNull()

    initAnalytics(true, true)
    expect(document.getElementById('plausible-script')).toBeNull()
  })
})
