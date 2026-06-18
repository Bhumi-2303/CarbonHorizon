import { useEffect, useState, FormEvent } from 'react'
import { goalsApi, type Goal, type GoalCreate } from '@/api/goals'

export default function Goals() {
  const [goals, setGoals] = useState<Goal[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [showCompleted, setShowCompleted] = useState(false)

  // Form State
  const [goalName, setGoalName] = useState('')
  const [goalDesc, setGoalDesc] = useState('')
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

  const openModal = (g?: Goal) => {
    if (g) {
      setEditingId(g.id)
      setGoalName(g.goal_name)
      setGoalDesc(g.goal_description || '')
      setTargetReduction(g.target_reduction_percentage || '')
      setTargetDate(g.target_date || '')
    } else {
      setEditingId(null)
      setGoalName('')
      setGoalDesc('')
      setTargetReduction('')
      setTargetDate('')
    }
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!goalName.trim()) return

    setIsSubmitting(true)
    setError(null)

    const payload: GoalCreate = {
      goal_name: goalName.trim(),
      goal_description: goalDesc.trim() || undefined,
      target_reduction_percentage: typeof targetReduction === 'number' ? targetReduction : undefined,
      target_date: targetDate || undefined
    }

    try {
      if (editingId) {
        await goalsApi.update(editingId, payload)
      } else {
        await goalsApi.create(payload)
      }
      closeModal()
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

  const activeGoals = goals.filter(g => g.status === 'active')
  const completedGoals = goals.filter(g => g.status === 'completed')
  const expiredGoals = goals.filter(g => g.status === 'expired')

  const renderGoalCard = (goal: Goal) => {
    const daysRemaining = calculateDaysRemaining(goal.target_date)
    const isExpired = goal.status === 'expired'
    const isCompleted = goal.status === 'completed'
    
    return (
      <div key={goal.id} className={`glass-card group relative ${isExpired ? 'opacity-50 grayscale' : ''}`}>
        <div className="flex justify-between items-start mb-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h3 className="heading-md text-white m-0">{goal.goal_name}</h3>
              {isCompleted && <span className="bg-[#2ECC71]/20 text-[#2ECC71] px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider">Completed</span>}
              {isExpired && <span className="bg-slate-700/50 text-slate-300 px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider">Expired</span>}
              {goal.status === 'active' && <span className="bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider">Active</span>}
            </div>
            {goal.goal_description && <p className="body text-muted text-sm mt-1">{goal.goal_description}</p>}
          </div>
          <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button onClick={() => openModal(goal)} className="text-muted hover:text-[#2ECC71] p-1"><i className="ti ti-edit text-xl"></i></button>
            <button onClick={() => handleDelete(goal.id)} className="text-muted hover:text-red-500 p-1"><i className="ti ti-trash text-xl"></i></button>
          </div>
        </div>

        <div className="mb-4">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-muted">Progress</span>
            <span className="font-bold text-white">{goal.current_progress.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-[#08121E] rounded-full h-2 overflow-hidden border border-slate-800">
            <div 
              className={`h-full transition-all duration-1000 ${isCompleted ? 'bg-[#2ECC71]' : 'bg-[#2ECC71]'}`}
              style={{ width: `${Math.min(100, Math.max(0, goal.current_progress))}%` }}
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-sm text-muted border-t border-slate-700/50 pt-4 mt-4">
          {goal.target_reduction_percentage && (
            <div className="flex items-center gap-1.5">
              <i className="ti ti-trending-down text-[#2ECC71]"></i>
              <span className="text-slate-300 font-medium">{goal.target_reduction_percentage}% Target</span>
            </div>
          )}
          {goal.target_date && (
            <div className="flex items-center gap-1.5">
              <i className="ti ti-calendar text-[#2ECC71]"></i>
              <span>{new Date(goal.target_date).toLocaleDateString()}</span>
              {daysRemaining !== null && goal.status === 'active' && (
                <span className={`ml-1 font-medium ${daysRemaining < 7 ? 'text-orange-400' : 'text-slate-300'}`}>
                  ({daysRemaining >= 0 ? `${daysRemaining} days left` : `${Math.abs(daysRemaining)} days overdue`})
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 md:p-8 animate-fade-in max-w-5xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="heading-xl text-white m-0">Goals</h1>
          <p className="body text-muted mt-1">Set, track, and crush your sustainability targets.</p>
        </div>
        <button onClick={() => openModal()} className="btn-primary flex items-center gap-2 self-start md:self-auto">
          <i className="ti ti-plus"></i> New Goal
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-900/20 text-red-400 border border-red-900/50 rounded-xl">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center p-12">
          <i className="ti ti-loader animate-spin text-4xl text-[#2ECC71]"></i>
        </div>
      ) : goals.length === 0 ? (
        <div className="glass-card text-center p-12 flex flex-col items-center">
          <i className="ti ti-target text-6xl text-[#2ECC71] mb-6"></i>
          <h2 className="heading-lg text-white mb-2">No goals set yet</h2>
          <p className="body text-muted max-w-md mb-8">
            Setting goals is the first step towards a greener lifestyle. Challenge yourself to reduce emissions!
          </p>
          <button onClick={() => openModal()} className="btn-primary">
            Set your first sustainability goal
          </button>
        </div>
      ) : (
        <div className="space-y-8">
          <section>
            <h2 className="heading-md text-white mb-4">Active & Expired Goals</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {activeGoals.map(renderGoalCard)}
              {expiredGoals.map(renderGoalCard)}
              {activeGoals.length === 0 && expiredGoals.length === 0 && (
                <p className="text-muted">No active goals.</p>
              )}
            </div>
          </section>

          {completedGoals.length > 0 && (
            <section>
              <button 
                onClick={() => setShowCompleted(!showCompleted)} 
                className="flex items-center gap-2 text-muted hover:text-white transition-colors heading-md mb-4"
              >
                <i className={`ti ti-chevron-${showCompleted ? 'down' : 'right'}`}></i>
                Completed Goals ({completedGoals.length})
              </button>
              {showCompleted && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {completedGoals.map(renderGoalCard)}
                </div>
              )}
            </section>
          )}
        </div>
      )}

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#08121E]/80 backdrop-blur-sm">
          <div className="glass-card w-full max-w-lg animate-fade-in relative max-h-[90vh] overflow-y-auto">
            <button onClick={closeModal} className="absolute top-4 right-4 text-muted hover:text-white">
              <i className="ti ti-x text-2xl"></i>
            </button>
            <h2 className="heading-lg text-white mb-6">
              {editingId ? 'Edit Goal' : 'Create Goal'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Goal Name *</label>
                <input
                  type="text" required value={goalName} onChange={e => setGoalName(e.target.value)}
                  className="w-full bg-[#08121E] border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#2ECC71]"
                  placeholder="e.g. Reduce Car Usage"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Description</label>
                <textarea
                  value={goalDesc} onChange={e => setGoalDesc(e.target.value)}
                  className="w-full bg-[#08121E] border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#2ECC71] min-h-[80px]"
                  placeholder="Optional details..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Target Reduction (%) *</label>
                <input
                  type="number" min="1" max="100" required value={targetReduction} onChange={e => setTargetReduction(e.target.value ? Number(e.target.value) : '')}
                  className="w-full bg-[#08121E] border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#2ECC71]"
                  placeholder="e.g. 15"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Target Date</label>
                <input
                  type="date" value={targetDate} onChange={e => setTargetDate(e.target.value)}
                  className="w-full bg-[#08121E] border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-[#2ECC71] [color-scheme:dark]"
                />
              </div>
              <div className="flex gap-4 pt-4">
                <button type="submit" disabled={isSubmitting} className="btn-primary flex-1">
                  {isSubmitting ? 'Saving...' : 'Save Goal'}
                </button>
                <button type="button" onClick={closeModal} className="btn-outline flex-1">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
