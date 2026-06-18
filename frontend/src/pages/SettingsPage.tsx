import { useState, useEffect } from 'react'
import apiClient from '@/api/client'
import { useTheme } from '@/context/ThemeContext'

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
      } catch (err: any) {
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
    } catch (err: any) {
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
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to save preferences' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-gray-500 animate-pulse">Loading settings...</div>
      </div>
    )
  }

  return (
    <main className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8 text-gray-800">Settings</h1>

      {message && (
        <div className={`p-4 mb-8 rounded-lg font-medium ${
          message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          {message.text}
        </div>
      )}

      <div className="bg-deep-ocean rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col md:flex-row">
        
        {/* Sidebar Tabs */}
        <div className="md:w-64 bg-gray-50 border-r border-gray-100 flex-shrink-0">
          <nav className="flex flex-col p-4 space-y-1">
            <button 
              onClick={() => { setActiveTab('profile'); setMessage(null) }}
              className={`px-4 py-3 text-left rounded-lg font-medium transition-colors ${
                activeTab === 'profile' ? 'bg-teal-50 text-teal-700' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Profile Settings
            </button>
            <button 
              onClick={() => { setActiveTab('preferences'); setMessage(null) }}
              className={`px-4 py-3 text-left rounded-lg font-medium transition-colors ${
                activeTab === 'preferences' ? 'bg-teal-50 text-teal-700' : 'text-gray-600 hover:bg-gray-100'
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
              <h2 className="text-xl font-bold text-gray-800 mb-6">Personal Information</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">First Name</label>
                  <input 
                    type="text" 
                    value={profile.first_name}
                    onChange={(e) => setProfile({...profile, first_name: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none transition-shadow"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">Last Name</label>
                  <input 
                    type="text" 
                    value={profile.last_name}
                    onChange={(e) => setProfile({...profile, last_name: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none transition-shadow"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">Email Address</label>
                <input 
                  type="email" 
                  value={profile.email}
                  onChange={(e) => setProfile({...profile, email: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none transition-shadow"
                  required
                />
              </div>

              <div className="pt-6 border-t border-gray-100 flex justify-end">
                <button 
                  type="submit" 
                  disabled={saving}
                  className="bg-teal-600 hover:bg-teal-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Profile'}
                </button>
              </div>
            </form>
          )}

          {activeTab === 'preferences' && (
            <form onSubmit={handlePreferencesSave} className="space-y-6">
              <h2 className="text-xl font-bold text-gray-800 mb-6">Application Preferences</h2>
              
              <div className="space-y-6">
                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <div>
                    <h3 className="text-base font-medium text-gray-800">Email Notifications</h3>
                    <p className="text-sm text-gray-500">Receive updates and weekly report summaries.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer" 
                      checked={preferences.notifications}
                      onChange={(e) => setPreferences({...preferences, notifications: e.target.checked})}
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-teal-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-deep-ocean after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-teal-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <div>
                    <h3 className="text-base font-medium text-gray-800">Dark Mode</h3>
                    <p className="text-sm text-gray-500">Switch application theme to dark mode.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer"
                      checked={preferences.dark_mode}
                      onChange={(e) => setPreferences({...preferences, dark_mode: e.target.checked})}
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-teal-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-deep-ocean after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-teal-600"></div>
                  </label>
                </div>

                <div className="space-y-2 py-3">
                  <label className="block text-sm font-medium text-gray-700">Preferred Currency</label>
                  <select 
                    value={preferences.currency}
                    onChange={(e) => setPreferences({...preferences, currency: e.target.value})}
                    className="w-full md:w-1/2 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none transition-shadow bg-deep-ocean"
                  >
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                  </select>
                </div>
              </div>

              <div className="pt-6 border-t border-gray-100 flex justify-end">
                <button 
                  type="submit" 
                  disabled={saving}
                  className="bg-teal-600 hover:bg-teal-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </main>
  )
}

export default SettingsPage
