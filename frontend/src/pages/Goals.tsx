import { useEffect, useState, FormEvent } from 'react'
import { goalsApi, type Goal, type GoalCreate } from '@/api/goals'

export default function Goals() {
  const [goals, setGoals] = useState<Goal[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)

  // Form State
  const [goalName, setGoalName] = useState('')
  const [targetReduction, setTargetReduction] = useState<number | ''>('')
  const [targetDate, setTargetDate] = useState('')

  const fetchGoals = async () => {
    try {
      setLoading(true)
      const data = await goalsApi.list()
      setGoals(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load goals')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchGoals()
  }, [])

  const resetForm = () => {
    setGoalName('')
    setTargetReduction('')
    setTargetDate('')
    setEditingId(null)
  }

  const handleEdit = (g: Goal) => {
    setEditingId(g.id)
    setGoalName(g.goal_name)
    setTargetReduction(g.target_reduction_percentage || '')
    setTargetDate(g.target_date || '')
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!goalName.trim()) return

    setIsSubmitting(true)
    setError(null)

    const payload: GoalCreate = {
      goal_name: goalName.trim(),
      target_reduction_percentage: typeof targetReduction === 'number' ? targetReduction : undefined,
      target_date: targetDate || undefined
    }

    try {
      if (editingId) {
        await goalsApi.update(editingId, payload)
      } else {
        await goalsApi.create(payload)
      }
      resetForm()
      await fetchGoals()
    } catch (err: any) {
      setError(err.message || 'Failed to save goal')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this goal?')) return
    try {
      await goalsApi.delete(id)
      setGoals(prev => prev.filter(g => g.id !== id))
    } catch (err: any) {
      setError(err.message || 'Failed to delete goal')
    }
  }

  const calculateDaysRemaining = (targetStr?: string) => {
    if (!targetStr) return null
    const target = new Date(targetStr)
    const today = new Date()
    const diffTime = target.getTime() - today.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4 lg:p-8">
      <div className="max-w-6xl mx-auto space-y-8 mt-16 lg:mt-0">
        
        <header>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Sustainability Goals
          </h1>
          <p className="mt-2 text-slate-600 dark:text-slate-400">
            Set targets to reduce your footprint and track your progress over time.
          </p>
        </header>

        {error && (
          <div className="p-4 bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400 rounded-xl border border-red-200 dark:border-red-800/30">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Form Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 sticky top-24">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                {editingId ? 'Edit Goal' : 'Create New Goal'}
              </h2>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Goal Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={goalName}
                    onChange={e => setGoalName(e.target.value)}
                    placeholder="e.g. Reduce Transport Emissions"
                    className="w-full rounded-xl border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2 text-sm focus:border-emerald-500 focus:ring-emerald-500 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Target Reduction (%)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={targetReduction}
                    onChange={e => setTargetReduction(e.target.value ? Number(e.target.value) : '')}
                    placeholder="e.g. 20"
                    className="w-full rounded-xl border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2 text-sm focus:border-emerald-500 focus:ring-emerald-500 dark:text-white"
                  />
                  <p className="mt-1 text-xs text-slate-500">How much do you want to reduce from your current footprint?</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Target Date
                  </label>
                  <input
                    type="date"
                    value={targetDate}
                    onChange={e => setTargetDate(e.target.value)}
                    className="w-full rounded-xl border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2 text-sm focus:border-emerald-500 focus:ring-emerald-500 dark:text-white [color-scheme:light] dark:[color-scheme:dark]"
                  />
                </div>

                <div className="pt-2 flex gap-3">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? 'Saving...' : (editingId ? 'Update Goal' : 'Save Goal')}
                  </button>
                  {editingId && (
                    <button
                      type="button"
                      onClick={resetForm}
                      className="px-4 py-2 rounded-xl text-sm font-medium border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>

          {/* Goals List Panel */}
          <div className="lg:col-span-2 space-y-4">
            {loading ? (
              <div className="flex justify-center p-12">
                <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-emerald-500"></div>
              </div>
            ) : goals.length === 0 ? (
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 border-dashed p-12 text-center flex flex-col items-center">
                <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 rounded-2xl flex items-center justify-center mb-4">
                  <span className="text-3xl">🎯</span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">No active goals yet</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm mb-6">
                  Setting goals helps you stay committed to reducing your carbon footprint over time. Create your first goal to get started!
                </p>
                <button
                  onClick={() => document.querySelector('form')?.scrollIntoView({ behavior: 'smooth' })}
                  className="text-emerald-600 dark:text-emerald-400 font-medium text-sm flex items-center gap-2 hover:underline"
                >
                  Create a goal <span aria-hidden="true">&rarr;</span>
                </button>
              </div>
            ) : (
              goals.map(goal => {
                const daysRemaining = calculateDaysRemaining(goal.target_date)
                
                return (
                  <div key={goal.id} className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-5 lg:p-6 transition-all hover:shadow-md group">
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div>
                        <div className="flex items-center gap-3 flex-wrap">
                          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                            {goal.goal_name}
                          </h3>
                          {goal.status === 'active' && <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">Active</span>}
                          {goal.status === 'completed' && <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">Completed</span>}
                          {goal.status === 'expired' && <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400">Expired</span>}
                        </div>
                        {goal.target_reduction_percentage && (
                          <p className="text-sm text-slate-500 mt-1">
                            Target: Reduce emissions by <span className="font-semibold text-slate-700 dark:text-slate-300">{goal.target_reduction_percentage}%</span>
                          </p>
                        )}
                      </div>
                      <div className="flex gap-2 opacity-100 lg:opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => handleEdit(goal)} className="p-1.5 text-slate-400 hover:text-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 rounded-lg">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                        </button>
                        <button onClick={() => handleDelete(goal.id)} className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </button>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-4">
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="font-medium text-slate-600 dark:text-slate-400">Progress</span>
                        <span className="font-bold text-slate-900 dark:text-white">{goal.current_progress.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
                        <div 
                          className={`h-2.5 rounded-full transition-all duration-1000 ${
                            goal.status === 'completed' ? 'bg-emerald-500' : 'bg-gradient-to-r from-emerald-400 to-teal-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(0, goal.current_progress))}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Footer / Meta */}
                    <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-3 border-t border-slate-100 dark:border-slate-800">
                      {goal.target_date ? (
                        <div className="flex items-center gap-1.5">
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                          <span>
                            Target: {new Date(goal.target_date).toLocaleDateString()}
                            {daysRemaining !== null && goal.status === 'active' && (
                              <span className={`ml-2 font-medium ${daysRemaining < 7 ? 'text-orange-500' : ''}`}>
                                ({daysRemaining >= 0 ? `${daysRemaining} days left` : `${Math.abs(daysRemaining)} days overdue`})
                              </span>
                            )}
                          </span>
                        </div>
                      ) : (
                        <span>No target date set</span>
                      )}
                    </div>

                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
