import { useEffect, useState, FormEvent, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi, type UserProfile, type AgeGroup, type LifestyleType, type Gender } from '@/api/auth'
import { dashboardApi, type DashboardData } from '@/api/dashboard'
import { useAuth } from '@/context/AuthContext'
import { useTheme } from '@/context/ThemeContext'
import { OCCUPATIONS, isOccupationValidForAge, getOccupationLockReason } from '@/config/occupations'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { FormField } from '@/components/ui/FormField'

export default function Profile() {
  const { logout, setUser } = useAuth()
  const { theme: currentTheme, setTheme: updateGlobalTheme } = useTheme()
  const navigate = useNavigate()

  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  // Form State
  const [fullName, setFullName] = useState('')
  const [age, setAge] = useState<number | ''>('')
  const [gender, setGender] = useState<Gender | ''>('')
  const [ageGroup, setAgeGroup] = useState<AgeGroup | ''>('')
  const [lifestyle, setLifestyle] = useState<LifestyleType | ''>('')
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>('')
  const [selectedStateCode, setSelectedStateCode] = useState<string>('')
  const [selectedCityName, setSelectedCityName] = useState<string>('')

  // Preferences State
  const [theme, setTheme] = useState<'light' | 'dark' | 'high-contrast' | 'system'>(currentTheme)
  const [unit, setUnit] = useState<'metric' | 'imperial'>(
    (localStorage.getItem('ch_unit') as any) || 'metric'
  )
  const [notifications, setNotifications] = useState<boolean>(
    localStorage.getItem('ch_notifications') !== 'false'
  )

  const [geoData, setGeoData] = useState<{ Country: any, State: any, City: any } | null>(null)

  useEffect(() => {
    import('country-state-city').then((mod) => {
      setGeoData({ Country: mod.Country, State: mod.State, City: mod.City })
    })
  }, [])

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
        setAge(profRes.age || '')
        setGender(profRes.gender || '')
        setAgeGroup(profRes.age_group || '')
        setLifestyle(profRes.lifestyle_type || '')
        
        if (profRes.country && geoData) {
          const c = geoData.Country.getAllCountries().find((x: any) => x.name === profRes.country)
          if (c) {
            setSelectedCountryCode(c.isoCode)
            if (profRes.state_province) {
              const s = geoData.State.getStatesOfCountry(c.isoCode).find((x: any) => x.name === profRes.state_province)
              if (s) {
                setSelectedStateCode(s.isoCode)
              }
            }
          }
        }
        if (profRes.city) {
          setSelectedCityName(profRes.city)
        }
      } catch (_err: unknown) {
        setMessage({ type: 'error', text: 'Failed to load profile data.' })
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const countryOptions = useMemo(() => {
    if (!geoData) return []
    return geoData.Country.getAllCountries().map((c: any) => ({
      value: c.isoCode,
      label: c.name
    }))
  }, [geoData])

  const stateOptions = useMemo(() => {
    if (!selectedCountryCode || !geoData) return []
    return geoData.State.getStatesOfCountry(selectedCountryCode).map((s: any) => ({
      value: s.isoCode,
      label: s.name
    }))
  }, [selectedCountryCode, geoData])

  const cityOptions = useMemo(() => {
    if (!selectedCountryCode || !selectedStateCode || !geoData) return []
    return geoData.City.getCitiesOfState(selectedCountryCode, selectedStateCode).map((c: any) => ({
      value: c.name,
      label: c.name
    }))
  }, [selectedCountryCode, selectedStateCode, geoData])

  const lifestyleOptions = useMemo(() => {
    return OCCUPATIONS.map((occ) => {
      const isValid = isOccupationValidForAge(occ.id, age)
      return {
        value: occ.id,
        label: occ.label,
        disabled: !isValid,
        title: !isValid ? getOccupationLockReason(occ.id) : undefined,
      }
    })
  }, [age])

  const handleProfileSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      const countryObj = (selectedCountryCode && geoData) ? geoData.Country.getCountryByCode(selectedCountryCode) : null
      const stateObj = (selectedCountryCode && selectedStateCode && geoData) 
        ? geoData.State.getStateByCodeAndCountry(selectedStateCode, selectedCountryCode) 
        : null

      const updated = await authApi.updateProfile({
        full_name: fullName,
        age: age ? Number(age) : undefined,
        gender: gender ? (gender as Gender) : undefined,
        age_group: ageGroup ? (ageGroup as AgeGroup) : undefined,
        lifestyle_type: lifestyle ? (lifestyle as LifestyleType) : undefined,
        country: countryObj ? countryObj.name : undefined,
        state_province: stateObj ? stateObj.name : undefined,
        city: selectedCityName || undefined
      })
      setProfile(updated)
      setUser(updated)
      setMessage({ type: 'success', text: 'Profile updated successfully!' })
    } catch (_err: unknown) {
        const err = _err instanceof Error ? _err : new Error(String(_err));
      setMessage({ type: 'error', text: err.message || 'Failed to update profile.' })
    } finally {
      setSaving(false)
    }
  }

  const handlePreferencesSave = () => {
    updateGlobalTheme(theme)
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
    } catch (_err: unknown) {
        const err = _err instanceof Error ? _err : new Error(String(_err));
      setMessage({ type: 'error', text: err.message || 'Failed to delete account.' })
      setShowDeleteModal(false)
    } finally {
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center p-20">
        <i className="ti ti-loader animate-spin text-4xl text-accent"></i>
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
        <div className={`p-4 rounded-xl border ${message.type === 'success' ? 'bg-accent/10 border-accent/30 text-accent' : 'bg-danger/10 border-danger/30 text-danger'}`}>
          {message.text}
        </div>
      )}

      {/* 1. Header Profile */}
      <Card className="flex items-center gap-6 p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-accent/5 rounded-full blur-3xl"></div>
        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-accent to-emerald-700 flex items-center justify-center shadow-lg shadow-accent/20 border-4 border-bg-primary z-10">
          <span className="text-3xl font-bold text-bg-primary">{initials}</span>
        </div>
        <div className="z-10">
          <h1 className="heading-lg text-primary mb-1">{profile.full_name}</h1>
          <p className="text-muted mb-2">{profile.email}</p>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-bg-primary border border-white/10 text-xs text-muted font-medium">
            <i className="ti ti-calendar"></i>
            Member since {new Date(profile.created_at).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })}
          </div>
        </div>
      </Card>

      {/* 2. Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="text-center py-8">
          <p className="text-xs text-muted uppercase font-medium mb-2 tracking-wider">Carbon Score</p>
          <p className="text-4xl font-[Montserrat] font-bold text-accent">{Math.round(carbonScore)}</p>
        </Card>
        <Card className="text-center py-8">
          <p className="text-xs text-muted uppercase font-medium mb-2 tracking-wider">Assessments</p>
          <p className="text-4xl font-[Montserrat] font-bold text-primary">{totalAssessments}</p>
        </Card>
        <Card className="text-center py-8">
          <p className="text-xs text-muted uppercase font-medium mb-2 tracking-wider">Active Goals</p>
          <p className="text-4xl font-[Montserrat] font-bold text-primary">{activeGoals}</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* 3. Edit Profile Form */}
        <Card>
          <h2 className="heading-md text-primary mb-6 flex items-center gap-2">
            <i className="ti ti-user-edit text-accent"></i> Personal Details
          </h2>
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <FormField
              as="input"
              fieldId="fullName"
              label="Full Name"
              type="text"
              required
              value={fullName}
              onChange={e => setFullName(e.target.value)}
            />
            
            <div className="grid grid-cols-2 gap-4">
              <FormField
                as="input"
                fieldId="age"
                label="Age"
                type="number"
                value={age}
                onChange={e => setAge(e.target.value ? Number(e.target.value) : '')}
              />
              <FormField
                as="select"
                fieldId="gender"
                label="Gender"
                value={gender}
                onChange={e => setGender(e.target.value as Gender)}
                options={[
                  { value: 'Male', label: 'Male' },
                  { value: 'Female', label: 'Female' },
                  { value: 'Non-Binary', label: 'Non-Binary' },
                  { value: 'Prefer Not to Say', label: 'Prefer Not to Say' }
                ]}
                placeholder="Select..."
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <FormField
                as="select"
                fieldId="ageGroup"
                label="Age Group"
                value={ageGroup}
                onChange={e => setAgeGroup(e.target.value as AgeGroup)}
                options={[
                  { value: 'student', label: 'Student' },
                  { value: 'adult', label: 'Adult' },
                  { value: 'senior', label: 'Senior' }
                ]}
                placeholder="Select..."
              />
              <FormField
                as="select"
                fieldId="lifestyle"
                label="Lifestyle / Occupation"
                value={lifestyle}
                onChange={e => setLifestyle(e.target.value as LifestyleType)}
                options={lifestyleOptions}
                placeholder="Select..."
              />
            </div>
            
            <div className="space-y-4">
              <FormField
                as="select"
                fieldId="country"
                label="Country"
                value={selectedCountryCode}
                onChange={e => {
                  setSelectedCountryCode(e.target.value)
                  setSelectedStateCode('')
                  setSelectedCityName('')
                }}
                options={countryOptions}
                placeholder="Select Country..."
              />
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  as="select"
                  fieldId="state"
                  label="State / Province"
                  value={selectedStateCode}
                  onChange={e => {
                    setSelectedStateCode(e.target.value)
                    setSelectedCityName('')
                  }}
                  disabled={!selectedCountryCode}
                  hint={!selectedCountryCode ? "Select a country first" : undefined}
                  options={stateOptions}
                  placeholder="Select State..."
                />
                <FormField
                  as="select"
                  fieldId="city"
                  label="City"
                  value={selectedCityName}
                  onChange={e => setSelectedCityName(e.target.value)}
                  disabled={!selectedStateCode}
                  hint={!selectedStateCode ? "Select a state first" : undefined}
                  options={cityOptions}
                  placeholder="Select City..."
                />
              </div>
            </div>
            
            <Button 
              type="submit" 
              variant="primary"
              disabled={saving}
              className="w-full mt-4"
            >
              {saving ? <i className="ti ti-loader animate-spin mr-2"></i> : <i className="ti ti-device-floppy mr-2"></i>}
              {saving ? 'Saving...' : 'Save Profile'}
            </Button>
          </form>
        </Card>

        {/* 4. Preferences & Danger Zone */}
        <div className="space-y-8">
          
          <Card>
            <h2 className="heading-md text-primary mb-6 flex items-center gap-2">
              <i className="ti ti-settings text-accent"></i> Preferences
            </h2>
            <div className="space-y-5">
              
              <FormField
                as="select"
                fieldId="theme"
                label="Theme (Visual Aesthetic)"
                value={theme}
                onChange={e => setTheme(e.target.value as any)}
                options={[
                  { value: 'dark', label: 'Dark' },
                  { value: 'light', label: 'Light' },
                  { value: 'high-contrast', label: 'High Contrast' },
                  { value: 'system', label: 'System' }
                ]}
              />

              <FormField
                as="select"
                fieldId="unit"
                label="Measurement Unit"
                value={unit}
                onChange={e => setUnit(e.target.value as any)}
                options={[
                  { value: 'metric', label: 'Metric (kg)' },
                  { value: 'imperial', label: 'Imperial (lbs)' }
                ]}
              />

              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-primary">Notifications</p>
                  <p className="text-xs text-muted">Weekly reports and goal reminders</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" checked={notifications} onChange={e => setNotifications(e.target.checked)} />
                  <div className="w-11 h-6 border-white/20 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-bg-primary after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                </label>
              </div>
              
              <Button onClick={handlePreferencesSave} variant="secondary" className="w-full">
                Save Preferences
              </Button>
            </div>
          </Card>

          <Card className="border-danger/50 bg-danger/10">
            <h2 className="heading-md text-danger mb-2 flex items-center gap-2">
              <i className="ti ti-alert-triangle"></i> Danger Zone
            </h2>
            <p className="text-xs text-muted mb-4">Once you delete your account, there is no going back. Please be certain.</p>
            <Button 
              onClick={() => { setShowDeleteModal(true); setDeleteStep(1); setDeleteConfirmText('') }} 
              variant="danger"
              className="w-full font-bold"
            >
              Delete Account
            </Button>
          </Card>

        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-bg-primary border border-danger/50 rounded-2xl p-6 md:p-8 max-w-md w-full shadow-2xl">
            <div className="flex items-center justify-center w-16 h-16 rounded-full bg-danger/10 text-danger mx-auto mb-6">
              <i className="ti ti-trash text-3xl"></i>
            </div>
            <h3 className="heading-md text-primary text-center mb-2">Delete Account?</h3>
            
            {deleteStep === 1 ? (
              <>
                <p className="text-muted text-center text-sm mb-8">
                  This will permanently delete your account, assessment history, active goals, and all saved simulations.
                </p>
                <div className="flex gap-3">
                  <Button onClick={() => setShowDeleteModal(false)} variant="secondary" className="flex-1">Cancel</Button>
                  <Button onClick={() => setDeleteStep(2)} variant="danger" className="flex-1 font-bold">
                    Yes, proceed
                  </Button>
                </div>
              </>
            ) : (
              <>
                <p className="text-muted text-center text-sm mb-6">
                  To confirm, type <span className="text-primary font-mono bg-bg-secondary px-2 py-0.5 rounded border border-white/10">DELETE</span> below.
                </p>
                <input 
                  type="text" 
                  value={deleteConfirmText}
                  onChange={e => setDeleteConfirmText(e.target.value)}
                  placeholder="DELETE"
                  className="w-full bg-white/5 border border-danger/50 rounded-xl px-4 py-3 text-center text-primary mb-6 focus:outline-none focus:border-danger transition-colors"
                />
                <div className="flex gap-3">
                  <Button onClick={() => setShowDeleteModal(false)} variant="secondary" className="flex-1">Cancel</Button>
                  <Button 
                    onClick={handleDeleteAccount}
                    variant="danger"
                    disabled={deleteConfirmText !== 'DELETE' || deleting}
                    className="flex-1 font-bold"
                  >
                    {deleting ? <i className="ti ti-loader animate-spin mr-2"></i> : null}
                    {deleting ? 'Deleting...' : 'Permanently Delete'}
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
