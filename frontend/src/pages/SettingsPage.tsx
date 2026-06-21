import { useState, useEffect } from 'react'
import apiClient from '@/api/client'
import { useTheme } from '@/context/ThemeContext'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { FormField } from '@/components/ui/FormField'

const SettingsPage = () => {
  const { theme, setTheme } = useTheme()
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences'>('profile')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  // Form states
  const [profile, setProfile] = useState({ first_name: '', last_name: '', email: '' })
  const [preferences, setPreferences] = useState({
    notifications: true,
    dark_mode: theme === 'dark',
    currency: 'USD'
  })

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true)
        // Mocking user profile and preferences fetch
        const response = await apiClient.get('/users/me')
        setProfile({
          first_name: response.data.first_name || '',
          last_name: response.data.last_name || '',
          email: response.data.email || ''
        })
        // Mocking preferences if available from backend
        if (response.data.preferences) {
          setPreferences(response.data.preferences)
          if (response.data.preferences.dark_mode !== undefined) {
            setTheme(response.data.preferences.dark_mode ? 'dark' : 'light')
          }
        }
      } catch (_err: unknown) {
        const err = _err instanceof Error ? _err : new Error(String(_err));
        // If 404, we might just be showing default empty forms
        if (!err.message?.includes('404')) {
          setMessage({ type: 'error', text: 'Failed to load settings data' })
        }
      } finally {
        setLoading(false)
      }
    }
    fetchSettings()
  }, [])

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSaving(true)
      setMessage(null)
      // Mock update call
      await apiClient.put('/users/me', profile)
      setMessage({ type: 'success', text: 'Profile updated successfully!' })
    } catch (_err: unknown) {
        const err = _err instanceof Error ? _err : new Error(String(_err));
      setMessage({ type: 'error', text: err.message || 'Failed to update profile' })
    } finally {
      setSaving(false)
    }
  }

  const handlePreferencesSave = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSaving(true)
      setMessage(null)
      // Mock update call
      await apiClient.put('/users/me/preferences', preferences)
      setTheme(preferences.dark_mode ? 'dark' : 'light')
      setMessage({ type: 'success', text: 'Preferences saved successfully!' })
    } catch (_err: unknown) {
        const err = _err instanceof Error ? _err : new Error(String(_err));
      setMessage({ type: 'error', text: err.message || 'Failed to save preferences' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <i className="ti ti-loader animate-spin text-4xl text-accent"></i>
      </div>
    )
  }

  return (
    <main className="max-w-4xl mx-auto p-6 animate-fade-in">
      <h1 className="heading-xl text-primary mb-8">Settings</h1>

      {message && (
        <div className={`p-4 mb-8 rounded-xl font-medium ${
          message.type === 'success' ? 'bg-accent/10 text-accent border border-accent/20' : 'bg-danger/10 text-danger border border-danger/20'
        }`}>
          {message.text}
        </div>
      )}

      <Card className="flex flex-col md:flex-row p-0 overflow-hidden">
        
        {/* Sidebar Tabs */}
        <div className="md:w-64 bg-white/5 border-r border-white/10 flex-shrink-0">
          <nav className="flex flex-col p-4 space-y-2">
            <button 
              onClick={() => { setActiveTab('profile'); setMessage(null) }}
              className={`px-4 py-3 text-left rounded-xl font-medium transition-all duration-200 ${
                activeTab === 'profile' ? 'bg-accent/20 text-accent' : 'text-slate-400 hover:text-primary hover:bg-white/5'
              }`}
            >
              Profile Settings
            </button>
            <button 
              onClick={() => { setActiveTab('preferences'); setMessage(null) }}
              className={`px-4 py-3 text-left rounded-xl font-medium transition-all duration-200 ${
                activeTab === 'preferences' ? 'bg-accent/20 text-accent' : 'text-slate-400 hover:text-primary hover:bg-white/5'
              }`}
            >
              Preferences
            </button>
          </nav>
        </div>

        {/* Form Content */}
        <div className="p-8 flex-grow">
          {activeTab === 'profile' && (
            <form onSubmit={handleProfileSave} className="space-y-6">
              <h2 className="heading-md text-primary mb-6">Personal Information</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <FormField
                  as="input"
                  fieldId="firstName"
                  label="First Name"
                  type="text"
                  required
                  value={profile.first_name}
                  onChange={(e) => setProfile({...profile, first_name: e.target.value})}
                />
                <FormField
                  as="input"
                  fieldId="lastName"
                  label="Last Name"
                  type="text"
                  required
                  value={profile.last_name}
                  onChange={(e) => setProfile({...profile, last_name: e.target.value})}
                />
              </div>

              <FormField
                as="input"
                fieldId="email"
                label="Email Address"
                type="email"
                required
                value={profile.email}
                onChange={(e) => setProfile({...profile, email: e.target.value})}
              />

              <div className="pt-6 border-t border-white/10 flex justify-end">
                <Button 
                  type="submit" 
                  variant="primary"
                  disabled={saving}
                >
                  {saving ? <i className="ti ti-loader animate-spin mr-2"></i> : null}
                  {saving ? 'Saving...' : 'Save Profile'}
                </Button>
              </div>
            </form>
          )}

          {activeTab === 'preferences' && (
            <form onSubmit={handlePreferencesSave} className="space-y-6">
              <h2 className="heading-md text-primary mb-6">Application Preferences</h2>
              
              <div className="space-y-6">
                <div className="flex items-center justify-between py-3 border-b border-white/5">
                  <div>
                    <h3 className="text-base font-medium text-primary">Email Notifications</h3>
                    <p className="text-sm text-muted">Receive updates and weekly report summaries.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer" 
                      checked={preferences.notifications}
                      onChange={(e) => setPreferences({...preferences, notifications: e.target.checked})}
                    />
                    <div className="w-11 h-6 border-white/20 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-primary after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between py-3 border-b border-white/5">
                  <div>
                    <h3 className="text-base font-medium text-primary">Dark Mode</h3>
                    <p className="text-sm text-muted">Switch application theme to dark mode.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer"
                      checked={preferences.dark_mode}
                      onChange={(e) => setPreferences({...preferences, dark_mode: e.target.checked})}
                    />
                    <div className="w-11 h-6 border-white/20 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-primary after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                  </label>
                </div>

                <div className="py-3">
                  <FormField
                    as="select"
                    fieldId="currency"
                    label="Preferred Currency"
                    value={preferences.currency}
                    onChange={(e) => setPreferences({...preferences, currency: e.target.value})}
                    options={[
                      { value: 'USD', label: 'USD ($)' },
                      { value: 'EUR', label: 'EUR (€)' },
                      { value: 'GBP', label: 'GBP (£)' }
                    ]}
                  />
                </div>
              </div>

              <div className="pt-6 border-t border-white/10 flex justify-end">
                <Button 
                  type="submit" 
                  variant="primary"
                  disabled={saving}
                >
                  {saving ? <i className="ti ti-loader animate-spin mr-2"></i> : null}
                  {saving ? 'Saving...' : 'Save Preferences'}
                </Button>
              </div>
            </form>
          )}
        </div>
      </Card>
    </main>
  )
}

export default SettingsPage
