import { useEffect, useState } from 'react'
import { habitsApi, type Habit } from '@/api/habits'
import { Bus, RefreshCw, Lightbulb, Droplets, ShoppingBag, Flame, Lock, Award, Shield, CheckCircle, Target } from 'lucide-react'

const HABIT_DEFINITIONS = [
  { id: 'public_transport', label: 'Public Transport', icon: Bus, factor: 1.2 },
  { id: 'recycling', label: 'Recycling', icon: RefreshCw, factor: 0.5 },
  { id: 'save_electricity', label: 'Save Electricity', icon: Lightbulb, factor: 0.8 },
  { id: 'water_conservation', label: 'Water Conservation', icon: Droplets, factor: 0.3 },
  { id: 'plastic_reduction', label: 'Plastic Reduction', icon: ShoppingBag, factor: 0.4 },
]

export default function HabitTracker() {
  const [habits, setHabits] = useState<Habit[]>([])
  const [streak, setStreak] = useState(0)
  // weeklySummary removed because it's not currently displayed in the new UI design.
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [toggling, setToggling] = useState<string | null>(null)

  const todayStr = new Date().toISOString().split('T')[0]

  const fetchDashboard = async () => {
    try {
      setLoading(true)
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(endDate.getDate() - 34) // past 35 days inclusive

      const [habitsData, streakData] = await Promise.all([
        habitsApi.list(startDate.toISOString().split('T')[0], endDate.toISOString().split('T')[0]),
        habitsApi.getStreak()
      ])

      setHabits(habitsData)
      setStreak(streakData.streak)
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
    if (isCurrentlyCompleted) return
    setToggling(habitType)
    try {
      await habitsApi.log({
        habit_type: habitType,
        activity_date: todayStr
      })
      await fetchDashboard()
    } catch (err: any) {
      setError(err.message || 'Failed to log habit')
    } finally {
      setToggling(null)
    }
  }

  // Activity Grid logic (35 days = 5 weeks)
  const past35Days = Array.from({ length: 35 }, (_, i) => {
    const d = new Date()
    d.setDate(d.getDate() - (34 - i))
    return d.toISOString().split('T')[0]
  })
  
  const dateLogMap = new Map<string, boolean>()
  habits.forEach(h => {
    if (h.completed) {
      dateLogMap.set(h.activity_date, true)
    }
  })
  
  const gridRows = []
  for (let i = 0; i < 5; i++) {
    gridRows.push(past35Days.slice(i * 7, i * 7 + 7))
  }
  
  const totalCarbonSaved = habits.reduce((acc, h) => acc + (h.carbon_saved || 0), 0)

  return (
    <div className="min-h-screen bg-space-black p-4 lg:p-8 font-inter">
      <div className="max-w-5xl mx-auto space-y-10 mt-16 lg:mt-0">
        
        <header>
          <h1 className="font-poppins text-3xl font-bold tracking-tight text-white">Habit Tracker</h1>
          <p className="mt-2 text-muted">Build sustainable routines and track your daily impact.</p>
        </header>

        {error && (
          <div className="p-4 bg-danger/10 text-danger rounded-xl border border-danger/30">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center p-12">
            <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-earth-green"></div>
          </div>
        ) : (
          <div className="space-y-10">
            
            {/* 1. Habit Streak Cards (Horizontal Scroll) */}
            <section>
              <h2 className="font-poppins text-xl font-bold text-white mb-4">Habit Streaks</h2>
              <div className="flex overflow-x-auto gap-4 snap-x pb-4 custom-scrollbar">
                {HABIT_DEFINITIONS.map(def => {
                  const past7 = past35Days.slice(-7)
                  const completedDays = past7.filter(d => habits.find(h => h.activity_date === d && h.habit_type === def.id && h.completed)).length
                  const carbonThisWeek = habits.filter(h => past7.includes(h.activity_date) && h.habit_type === def.id && h.completed)
                                                .reduce((acc, h) => acc + (h.carbon_saved || 0), 0)
                  
                  const strokeOffset = 100.5 - (100.5 * completedDays) / 7
                  const Icon = def.icon

                  return (
                    <div key={def.id} className="glass-card snap-start min-w-[240px] p-5 flex flex-col justify-between shrink-0 hover:scale-[1.02] transition-transform duration-200 cursor-pointer">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <div className="p-2 bg-deep-ocean rounded-lg inline-block border border-forest-green/30 mb-2">
                            <Icon className="w-5 h-5 text-earth-green" />
                          </div>
                          <p className="text-sm font-semibold text-white">{def.label}</p>
                        </div>
                        <div className="relative w-12 h-12">
                          <svg className="w-12 h-12 transform -rotate-90">
                            <circle cx="24" cy="24" r="16" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-forest-green/30" />
                            <circle cx="24" cy="24" r="16" stroke="currentColor" strokeWidth="4" fill="transparent" strokeDasharray="100.5" strokeDashoffset={strokeOffset} className="text-earth-green transition-all duration-1000 ease-out" strokeLinecap="round" />
                          </svg>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="font-montserrat font-bold text-xs text-white">{completedDays}/7</span>
                          </div>
                        </div>
                      </div>
                      <div>
                        <p className="font-montserrat font-semibold text-earth-green text-lg">{completedDays} Day Streak</p>
                        <p className="text-xs text-muted">{carbonThisWeek.toFixed(1)} kg CO₂e saved</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            </section>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* 4. Mark Daily Completion */}
              <section>
                <h2 className="font-poppins text-xl font-bold text-white mb-4">Today's Habits</h2>
                <div className="space-y-3">
                  {HABIT_DEFINITIONS.map(def => {
                    const isCompleted = habits.some(h => h.activity_date === todayStr && h.habit_type === def.id && h.completed)
                    const isToggling = toggling === def.id
                    const Icon = def.icon

                    return (
                      <button 
                        key={def.id}
                        disabled={isCompleted || isToggling}
                        onClick={() => handleToggle(def.id, isCompleted)}
                        className={`w-full text-left relative overflow-hidden rounded-2xl border p-4 transition-all duration-200 flex items-center justify-between ${
                          isCompleted 
                            ? 'bg-earth-green/20 border-earth-green' 
                            : 'bg-deep-ocean border-forest-green/30 hover:border-earth-green/60'
                        } ${isToggling ? 'opacity-50 cursor-wait' : ''}`}
                      >
                        <div className="flex items-center gap-4">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isCompleted ? 'bg-earth-green text-deep-ocean' : 'bg-space-black text-earth-green'}`}>
                            <Icon className="w-5 h-5" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-white">{def.label}</h3>
                            <p className="text-xs text-muted mt-0.5">Saves ~{def.factor} kg CO₂e</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`text-sm font-medium ${isCompleted ? 'text-earth-green' : 'text-muted'}`}>
                            {isCompleted ? 'Completed' : 'Pending'}
                          </span>
                          <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${
                            isCompleted ? 'bg-earth-green border-earth-green text-deep-ocean' : 'border-muted text-transparent'
                          }`}>
                            <CheckCircle className="w-4 h-4" />
                          </div>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </section>

              {/* 2. Weekly Activity Grid */}
              <section>
                <h2 className="font-poppins text-xl font-bold text-white mb-4">Activity Map</h2>
                <div className="glass-card p-6">
                  <div className="grid grid-cols-7 gap-2 mb-2">
                    {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, i) => (
                      <div key={i} className="text-center text-xs text-muted font-medium">{day}</div>
                    ))}
                  </div>
                  <div className="space-y-2">
                    {gridRows.map((row, rowIdx) => (
                      <div key={rowIdx} className="grid grid-cols-7 gap-2">
                        {row.map(dateStr => {
                          const isLogged = dateLogMap.get(dateStr)
                          const carbonForDay = habits.filter(h => h.activity_date === dateStr && h.completed).reduce((acc, h) => acc + (h.carbon_saved || 0), 0)
                          
                          return (
                            <div 
                              key={dateStr}
                              title={`${dateStr}: ${isLogged ? carbonForDay.toFixed(1) + ' kg CO₂e saved' : 'No activity'}`}
                              className={`w-full aspect-square rounded-[4px] sm:rounded-md transition-colors duration-200 cursor-pointer ${
                                isLogged 
                                  ? 'bg-earth-green shadow-[0_0_8px_rgba(46,204,113,0.3)]' 
                                  : 'bg-deep-ocean border border-forest-green/30 hover:border-earth-green/50'
                              }`}
                            ></div>
                          )
                        })}
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex items-center justify-end gap-2 text-xs text-muted">
                    <span>Less</span>
                    <div className="w-3 h-3 rounded-[4px] bg-deep-ocean border border-forest-green/30"></div>
                    <div className="w-3 h-3 rounded-[4px] bg-earth-green/40"></div>
                    <div className="w-3 h-3 rounded-[4px] bg-earth-green/70"></div>
                    <div className="w-3 h-3 rounded-[4px] bg-earth-green shadow-[0_0_4px_rgba(46,204,113,0.5)]"></div>
                    <span>More</span>
                  </div>
                </div>
              </section>
            </div>

            {/* 3. Achievement Milestones */}
            <section>
              <h2 className="font-poppins text-xl font-bold text-white mb-4">Milestones</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                
                <div className={`glass-card p-5 relative overflow-hidden ${streak >= 7 ? 'border-earth-green/50' : 'opacity-40'}`}>
                  {streak < 7 && <Lock className="absolute top-4 right-4 w-4 h-4 text-muted" />}
                  <Flame className={`w-8 h-8 mb-3 ${streak >= 7 ? 'text-earth-green' : 'text-muted'}`} />
                  <h3 className="font-semibold text-white">7-Day Streak</h3>
                  <p className="text-xs text-muted mt-1">{streak >= 7 ? 'Unlocked' : 'Keep going'}</p>
                </div>

                <div className={`glass-card p-5 relative overflow-hidden ${streak >= 30 ? 'border-earth-green/50' : 'opacity-40'}`}>
                  {streak < 30 && <Lock className="absolute top-4 right-4 w-4 h-4 text-muted" />}
                  <Shield className={`w-8 h-8 mb-3 ${streak >= 30 ? 'text-earth-green' : 'text-muted'}`} />
                  <h3 className="font-semibold text-white">30-Day Streak</h3>
                  <p className="text-xs text-muted mt-1">{streak >= 30 ? 'Unlocked' : 'Requires 30 days'}</p>
                </div>

                <div className={`glass-card p-5 relative overflow-hidden ${totalCarbonSaved >= 100 ? 'border-earth-green/50' : 'opacity-40'}`}>
                  {totalCarbonSaved < 100 && <Lock className="absolute top-4 right-4 w-4 h-4 text-muted" />}
                  <Target className={`w-8 h-8 mb-3 ${totalCarbonSaved >= 100 ? 'text-earth-green' : 'text-muted'}`} />
                  <h3 className="font-semibold text-white">100kg CO₂ Saved</h3>
                  <p className="text-xs text-muted mt-1">{totalCarbonSaved >= 100 ? 'Unlocked' : `${(100 - totalCarbonSaved).toFixed(0)}kg remaining`}</p>
                </div>

                <div className={`glass-card p-5 relative overflow-hidden ${habits.length > 0 ? 'border-earth-green/50' : 'opacity-40'}`}>
                  {habits.length === 0 && <Lock className="absolute top-4 right-4 w-4 h-4 text-muted" />}
                  <Award className={`w-8 h-8 mb-3 ${habits.length > 0 ? 'text-earth-green' : 'text-muted'}`} />
                  <h3 className="font-semibold text-white">First Habit</h3>
                  <p className="text-xs text-muted mt-1">{habits.length > 0 ? 'Unlocked' : 'Log a habit'}</p>
                </div>

              </div>
            </section>

          </div>
        )}
      </div>
    </div>
  )
}
