import { useEffect, useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi, type UserProfile, type AgeGroup, type LifestyleType } from '@/api/auth'
import { dashboardApi, type DashboardData } from '@/api/dashboard'
import { useAuth } from '@/context/AuthContext'

export default function Profile() {
  const { logout, setUser } = useAuth()
  const navigate = useNavigate()

  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  // Form State
  const [fullName, setFullName] = useState('')
  const [ageGroup, setAgeGroup] = useState<AgeGroup | ''>('')
  const [lifestyle, setLifestyle] = useState<LifestyleType | ''>('')
  const [city, setCity] = useState('')
  const [country, setCountry] = useState('')

  // Preferences State
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>(
    (localStorage.getItem('ch_theme') as any) || 'dark'
  )
  const [unit, setUnit] = useState<'metric' | 'imperial'>(
    (localStorage.getItem('ch_unit') as any) || 'metric'
  )
  const [notifications, setNotifications] = useState<boolean>(
    localStorage.getItem('ch_notifications') !== 'false'
  )

  // Delete Modal State
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleteStep, setDeleteStep] = useState(1)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    async function loadData() {
      try {
        const [profRes, dashRes] = await Promise.all([
          authApi.getProfile(),
          dashboardApi.getDashboard().catch(() => null)
        ])
        
        setProfile(profRes)
        setDashboard(dashRes)

        setFullName(profRes.full_name || '')
        setAgeGroup(profRes.age_group || '')
        setLifestyle(profRes.lifestyle_type || '')
        setCity(profRes.city || '')
        setCountry(profRes.country || '')
      } catch (err: any) {
        setMessage({ type: 'error', text: 'Failed to load profile data.' })
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const handleProfileSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      const updated = await authApi.updateProfile({
        full_name: fullName,
        age_group: ageGroup ? (ageGroup as AgeGroup) : undefined,
        lifestyle_type: lifestyle ? (lifestyle as LifestyleType) : undefined,
        city,
        country
      })
      setProfile(updated)
      setUser(updated)
      setMessage({ type: 'success', text: 'Profile updated successfully!' })
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to update profile.' })
    } finally {
      setSaving(false)
    }
  }

  const handlePreferencesSave = () => {
    localStorage.setItem('ch_theme', theme)
    localStorage.setItem('ch_unit', unit)
    localStorage.setItem('ch_notifications', String(notifications))
    setMessage({ type: 'success', text: 'Preferences saved successfully!' })
  }

  const handleDeleteAccount = async () => {
    setDeleting(true)
    try {
      await authApi.deleteAccount()
      await logout()
      navigate('/login')
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to delete account.' })
      setShowDeleteModal(false)
    } finally {
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center p-20">
        <i className="ti ti-loader animate-spin text-4xl text-[#2ECC71]"></i>
      </div>
    )
  }

  if (!profile) return null

  // Header Initials
  const initials = profile.full_name 
    ? profile.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
    : 'U'

  // Dashboard Stats
  const carbonScore = dashboard?.latest_assessment?.carbon_score || 0
  const activeGoals = dashboard?.active_goals_count || 0
  const totalAssessments = dashboard?.total_assessments || (dashboard?.latest_assessment ? 1 : 0)

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto space-y-8 animate-fade-in pb-20">
      
      {message && (
        <div className={`p-4 rounded-xl border ${message.type === 'success' ? 'bg-[#2ECC71]/10 border-[#2ECC71]/30 text-[#2ECC71]' : 'bg-red-500/10 border-red-500/30 text-red-500'}`}>
          {message.text}
        </div>
      )}

      {/* 1. Header Profile */}
      <div className="card flex items-center gap-6 p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#2ECC71]/5 rounded-full blur-3xl"></div>
        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-[#2ECC71] to-emerald-700 flex items-center justify-center shadow-lg shadow-[#2ECC71]/20 border-4 border-[#0F172A] z-10">
          <span className="text-3xl font-bold text-[#08121E]">{initials}</span>
        </div>
        <div className="z-10">
          <h1 className="heading-lg text-white mb-1">{profile.full_name}</h1>
          <p className="text-slate-400 mb-2">{profile.email}</p>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#08121E] border border-slate-800 text-xs text-slate-500 font-medium">
            <i className="ti ti-calendar"></i>
            Member since {new Date(profile.created_at).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })}
          </div>
        </div>
      </div>

      {/* 2. Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card text-center py-8">
          <p className="text-xs text-slate-400 uppercase font-medium mb-2 tracking-wider">Carbon Score</p>
          <p className="text-4xl font-[Montserrat] font-bold text-[#2ECC71]">{Math.round(carbonScore)}</p>
        </div>
        <div className="card text-center py-8">
          <p className="text-xs text-slate-400 uppercase font-medium mb-2 tracking-wider">Assessments</p>
          <p className="text-4xl font-[Montserrat] font-bold text-slate-200">{totalAssessments}</p>
        </div>
        <div className="card text-center py-8">
          <p className="text-xs text-slate-400 uppercase font-medium mb-2 tracking-wider">Active Goals</p>
          <p className="text-4xl font-[Montserrat] font-bold text-slate-200">{activeGoals}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* 3. Edit Profile Form */}
        <div className="card">
          <h2 className="heading-md text-white mb-6 flex items-center gap-2">
            <i className="ti ti-user-edit text-[#2ECC71]"></i> Personal Details
          </h2>
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">Full Name</label>
              <input 
                type="text" 
                required 
                value={fullName} 
                onChange={e => setFullName(e.target.value)}
                className="w-full bg-[#08121E] border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-[#2ECC71] transition-colors"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">Age Group</label>
                <select 
                  value={ageGroup} 
                  onChange={e => setAgeGroup(e.target.value as AgeGroup)}
                  className="w-full bg-[#08121E] border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-[#2ECC71] appearance-none"
                >
                  <option value="">Select...</option>
                  <option value="student">Student</option>
                  <option value="adult">Adult</option>
                  <option value="senior">Senior</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">Lifestyle</label>
                <select 
                  value={lifestyle} 
                  onChange={e => setLifestyle(e.target.value as LifestyleType)}
                  className="w-full bg-[#08121E] border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-[#2ECC71] appearance-none"
                >
                  <option value="">Select...</option>
                  <option value="student">Student</option>
                  <option value="professional">Professional</option>
                  <option value="homemaker">Homemaker</option>
                  <option value="retired">Retired</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">City</label>
                <input 
                  type="text" 
                  value={city} 
                  onChange={e => setCity(e.target.value)}
                  className="w-full bg-[#08121E] border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-[#2ECC71]"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1.5">Country</label>
                <input 
                  type="text" 
                  value={country} 
                  onChange={e => setCountry(e.target.value)}
                  className="w-full bg-[#08121E] border border-slate-700 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-[#2ECC71]"
                />
              </div>
            </div>
            <button 
              type="submit" 
              disabled={saving}
              className="btn-primary w-full mt-4 flex items-center justify-center gap-2"
            >
              {saving ? <i className="ti ti-loader animate-spin"></i> : <i className="ti ti-device-floppy"></i>}
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </form>
        </div>

        {/* 4. Preferences & Danger Zone */}
        <div className="space-y-8">
          
          <div className="card">
            <h2 className="heading-md text-white mb-6 flex items-center gap-2">
              <i className="ti ti-settings text-[#2ECC71]"></i> Preferences
            </h2>
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-200">Theme</p>
                  <p className="text-xs text-slate-500">Choose your visual aesthetic</p>
                </div>
                <select 
                  value={theme} 
                  onChange={e => setTheme(e.target.value as any)}
                  className="bg-[#08121E] border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none"
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                  <option value="system">System</option>
                </select>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-200">Measurement Unit</p>
                  <p className="text-xs text-slate-500">Metric (kg) or Imperial (lbs)</p>
                </div>
                <select 
                  value={unit} 
                  onChange={e => setUnit(e.target.value as any)}
                  className="bg-[#08121E] border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none"
                >
                  <option value="metric">Metric</option>
                  <option value="imperial">Imperial</option>
                </select>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-200">Notifications</p>
                  <p className="text-xs text-slate-500">Weekly reports and goal reminders</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" checked={notifications} onChange={e => setNotifications(e.target.checked)} />
                  <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#2ECC71]"></div>
                </label>
              </div>
              <button onClick={handlePreferencesSave} className="btn-outline w-full text-sm py-2">
                Save Preferences
              </button>
            </div>
          </div>

          <div className="card border-red-900/50 bg-red-950/10">
            <h2 className="heading-md text-red-500 mb-2 flex items-center gap-2">
              <i className="ti ti-alert-triangle"></i> Danger Zone
            </h2>
            <p className="text-xs text-slate-400 mb-4">Once you delete your account, there is no going back. Please be certain.</p>
            <button 
              onClick={() => { setShowDeleteModal(true); setDeleteStep(1); setDeleteConfirmText('') }} 
              className="px-4 py-2 bg-red-500/10 text-red-500 border border-red-500/20 rounded-xl w-full text-sm font-bold hover:bg-red-500 hover:text-white transition-colors"
            >
              Delete Account
            </button>
          </div>

        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-[#0F172A] border border-red-900/50 rounded-2xl p-6 md:p-8 max-w-md w-full shadow-2xl">
            <div className="flex items-center justify-center w-16 h-16 rounded-full bg-red-500/10 text-red-500 mx-auto mb-6">
              <i className="ti ti-trash text-3xl"></i>
            </div>
            <h3 className="heading-md text-white text-center mb-2">Delete Account?</h3>
            
            {deleteStep === 1 ? (
              <>
                <p className="text-slate-400 text-center text-sm mb-8">
                  This will permanently delete your account, assessment history, active goals, and all saved simulations.
                </p>
                <div className="flex gap-3">
                  <button onClick={() => setShowDeleteModal(false)} className="flex-1 btn-outline">Cancel</button>
                  <button onClick={() => setDeleteStep(2)} className="flex-1 px-4 py-3 bg-red-500 text-white rounded-xl font-bold hover:bg-red-600 transition-colors">
                    Yes, proceed
                  </button>
                </div>
              </>
            ) : (
              <>
                <p className="text-slate-400 text-center text-sm mb-6">
                  To confirm, type <span className="text-white font-mono bg-slate-800 px-2 py-0.5 rounded">DELETE</span> below.
                </p>
                <input 
                  type="text" 
                  value={deleteConfirmText}
                  onChange={e => setDeleteConfirmText(e.target.value)}
                  placeholder="DELETE"
                  className="w-full bg-[#08121E] border border-red-900/50 rounded-xl px-4 py-3 text-center text-white mb-6 focus:outline-none focus:border-red-500"
                />
                <div className="flex gap-3">
                  <button onClick={() => setShowDeleteModal(false)} className="flex-1 btn-outline">Cancel</button>
                  <button 
                    onClick={handleDeleteAccount}
                    disabled={deleteConfirmText !== 'DELETE' || deleting}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-red-500 text-white rounded-xl font-bold hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {deleting ? <i className="ti ti-loader animate-spin"></i> : null}
                    {deleting ? 'Deleting...' : 'Permanently Delete'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
