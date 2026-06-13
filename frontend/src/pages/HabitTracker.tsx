import { useEffect, useState } from 'react'
import { habitsApi, type Habit, type SummaryResponse } from '@/api/habits'

const HABIT_DEFINITIONS = [
  { id: 'public_transport', label: 'Public Transport', icon: '🚌', factor: 1.2 },
  { id: 'recycling', label: 'Recycling', icon: '♻️', factor: 0.5 },
  { id: 'save_electricity', label: 'Save Electricity', icon: '💡', factor: 0.8 },
  { id: 'water_conservation', label: 'Water Conservation', icon: '💧', factor: 0.3 },
  { id: 'plastic_reduction', label: 'Plastic Reduction', icon: '🛍️', factor: 0.4 },
]

export default function HabitTracker() {
  const [habits, setHabits] = useState<Habit[]>([])
  const [streak, setStreak] = useState(0)
  const [weeklySummary, setWeeklySummary] = useState<SummaryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [toggling, setToggling] = useState<string | null>(null)

  const todayStr = new Date().toISOString().split('T')[0]

  const fetchDashboard = async () => {
    try {
      setLoading(true)
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(endDate.getDate() - 30) // last 30 days for calendar

      const [habitsData, streakData, weeklyData] = await Promise.all([
        habitsApi.list(startDate.toISOString().split('T')[0], endDate.toISOString().split('T')[0]),
        habitsApi.getStreak(),
        habitsApi.getWeeklySummary()
      ])

      setHabits(habitsData)
      setStreak(streakData.streak)
      setWeeklySummary(weeklyData)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load habit tracker data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [])

  const handleToggle = async (habitType: string, isCurrentlyCompleted: boolean) => {
    if (isCurrentlyCompleted) return // the backend logic currently overrides with completed=True. We won't do "un-complete" for now since backend log_habit sets completed=True. If needed, we'd add a DELETE / uncomplete. Actually, backend log_habit sets completed=True unconditionally. So we only allow checking it.
    
    setToggling(habitType)
    try {
      await habitsApi.log({
        habit_type: habitType,
        activity_date: todayStr
      })
      
      // Optimistic refresh
      await fetchDashboard()
    } catch (err: any) {
      setError(err.message || 'Failed to log habit')
    } finally {
      setToggling(null)
    }
  }

  // Get habits for today
  const todaysHabits = habits.filter(h => h.activity_date === todayStr && h.completed)
  const todaysCompletedTypes = new Set(todaysHabits.map(h => h.habit_type))

  // Generate 30 days calendar grid
  const past30Days = Array.from({ length: 30 }, (_, i) => {
    const d = new Date()
    d.setDate(d.getDate() - (29 - i))
    return d.toISOString().split('T')[0]
  })

  // Map each date to whether a habit was logged
  const dateLogMap = new Map<string, boolean>()
  habits.forEach(h => {
    if (h.completed) {
      dateLogMap.set(h.activity_date, true)
    }
  })

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4 lg:p-8">
      <div className="max-w-5xl mx-auto space-y-8 mt-16 lg:mt-0">
        
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Daily Habits
            </h1>
            <p className="mt-2 text-slate-600 dark:text-slate-400">
              Build sustainable routines and track your daily impact.
            </p>
          </div>
        </header>

        {error && (
          <div className="p-4 bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400 rounded-xl border border-red-200 dark:border-red-800/30">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center p-12">
            <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-emerald-500"></div>
          </div>
        ) : (
          <div className="space-y-8">
            
            {/* Top Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-6">
              <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">Current Streak</p>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white">
                    {streak} <span className="text-lg text-orange-500">🔥</span>
                  </p>
                </div>
                <div className="h-12 w-12 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center text-orange-500">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0113 13a2.99 2.99 0 01-.879 2.121z" clipRule="evenodd" /></svg>
                </div>
              </div>
              
              <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">Saved This Week</p>
                  <p className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">
                    {weeklySummary?.total_carbon_saved.toFixed(1)} <span className="text-lg font-medium text-slate-500 dark:text-slate-400">kg CO₂e</span>
                  </p>
                </div>
                <div className="h-12 w-12 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-500">
                  <span className="text-2xl">🌱</span>
                </div>
              </div>
            </div>

            {/* Daily Habit Cards */}
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Today's Habits</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {HABIT_DEFINITIONS.map(def => {
                  const isCompleted = todaysCompletedTypes.has(def.id)
                  const isToggling = toggling === def.id
                  return (
                    <div 
                      key={def.id}
                      className={`relative overflow-hidden rounded-2xl border p-5 transition-all ${
                        isCompleted 
                          ? 'bg-emerald-50/50 border-emerald-200 dark:bg-emerald-900/10 dark:border-emerald-800/40' 
                          : 'bg-white border-slate-200 dark:bg-slate-900 dark:border-slate-800 hover:border-emerald-300 dark:hover:border-emerald-700/50'
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${
                          isCompleted ? 'bg-emerald-100 dark:bg-emerald-900/40' : 'bg-slate-100 dark:bg-slate-800'
                        }`}>
                          {def.icon}
                        </div>
                        <div className="flex-1">
                          <h3 className={`font-semibold ${isCompleted ? 'text-emerald-900 dark:text-emerald-300' : 'text-slate-900 dark:text-white'}`}>
                            {def.label}
                          </h3>
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                            Saves {def.factor} kg CO₂e
                          </p>
                        </div>
                        <div>
                          <button
                            disabled={isCompleted || isToggling}
                            onClick={() => handleToggle(def.id, isCompleted)}
                            className={`w-8 h-8 rounded-full border-2 flex items-center justify-center transition-colors ${
                              isCompleted 
                                ? 'bg-emerald-500 border-emerald-500 text-white' 
                                : 'bg-transparent border-slate-300 dark:border-slate-600 hover:border-emerald-500 text-transparent hover:text-emerald-500/20'
                            } ${isToggling ? 'opacity-50 cursor-wait' : ''}`}
                          >
                            {isToggling ? (
                              <div className="w-4 h-4 border-2 border-slate-400 border-t-emerald-500 rounded-full animate-spin"></div>
                            ) : (
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* 30-Day Calendar */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">Past 30 Days</h2>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <div className="w-3 h-3 rounded-full bg-slate-100 dark:bg-slate-800"></div> Missed
                  <div className="w-3 h-3 rounded-full bg-emerald-500 ml-2"></div> Logged
                </div>
              </div>
              
              <div className="grid grid-cols-7 sm:grid-cols-10 md:grid-cols-15 gap-2 lg:gap-3">
                {past30Days.map((dateStr) => {
                  const isLogged = dateLogMap.get(dateStr)
                  const dateObj = new Date(dateStr)
                  const isToday = dateStr === todayStr
                  
                  return (
                    <div 
                      key={dateStr}
                      title={`${dateStr}${isLogged ? ' (Logged)' : ''}`}
                      className="group relative aspect-square flex flex-col items-center justify-center"
                    >
                      <div className={`w-full h-full rounded-lg transition-colors ${
                        isLogged 
                          ? 'bg-emerald-500 shadow-sm shadow-emerald-500/20' 
                          : 'bg-slate-100 dark:bg-slate-800'
                      } ${isToday ? 'ring-2 ring-emerald-500 ring-offset-2 dark:ring-offset-slate-900' : ''}`}>
                      </div>
                      <span className="absolute -bottom-5 text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap bg-slate-800 text-white px-2 py-0.5 rounded shadow-lg z-10 transition-opacity">
                        {dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  )
}
