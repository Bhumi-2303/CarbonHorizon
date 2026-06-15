import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { simulatorApi, type SimulationSaved } from '@/api/simulator'

export default function SimulatorHistory() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<SimulationSaved[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadHistory = async () => {
    try {
      setLoading(true)
      const data = await simulatorApi.history()
      setHistory(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load simulation history')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this saved simulation?')) return
    try {
      await simulatorApi.delete(id)
      setHistory(prev => prev.filter(sim => sim.id !== id))
    } catch (err: any) {
      setError(err.message || 'Failed to delete simulation')
    }
  }

  const handleRerun = (sim: SimulationSaved) => {
    navigate('/simulator', { state: { prefill: sim } })
  }

  if (loading) {
    return (
      <div className="flex justify-center p-20">
        <i className="ti ti-loader animate-spin text-4xl text-[#2ECC71]"></i>
      </div>
    )
  }

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="heading-xl text-white m-0">Saved Simulations</h1>
          <p className="body text-slate-400 mt-1">Review and re-run your what-if scenarios.</p>
        </div>
        <Link to="/simulator" className="btn-primary flex items-center gap-2 self-start md:self-auto">
          <i className="ti ti-plus"></i> New Simulation
        </Link>
      </div>

      {error && (
        <div className="p-4 bg-red-900/20 text-red-400 border border-red-900/50 rounded-xl">
          {error}
        </div>
      )}

      {history.length === 0 ? (
        <div className="card text-center p-12 flex flex-col items-center">
          <i className="ti ti-flask text-6xl text-[#2ECC71] mb-6"></i>
          <h2 className="heading-lg text-white mb-2">No saved simulations</h2>
          <p className="body text-slate-400 max-w-md mb-8">
            You haven't saved any simulations yet. Run a what-if scenario to see how small changes can reduce your carbon footprint!
          </p>
          <Link to="/simulator" className="btn-primary">
            Start a Simulation
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {history.map(sim => {
            const isReduction = (sim.reduction_percentage || 0) >= 0;
            const reductionColor = isReduction ? 'text-[#2ECC71]' : 'text-red-500';

            return (
              <div key={sim.id} className="card flex flex-col justify-between group">
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="heading-md text-white mb-1">{sim.scenario_name}</h3>
                      <p className="text-xs text-slate-500">
                        {new Date(sim.created_at).toLocaleDateString(undefined, {
                          year: 'numeric', month: 'short', day: 'numeric',
                          hour: '2-digit', minute: '2-digit'
                        })}
                      </p>
                    </div>
                    <button 
                      onClick={() => handleDelete(sim.id)} 
                      className="text-slate-500 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                      title="Delete"
                    >
                      <i className="ti ti-trash text-xl"></i>
                    </button>
                  </div>

                  {sim.scenario_description && (
                    <p className="body text-sm text-slate-400 mb-6">{sim.scenario_description}</p>
                  )}

                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-[#08121E] border border-slate-800 rounded-xl p-3 text-center">
                      <p className="text-xs text-slate-500 uppercase font-medium mb-1">Current</p>
                      <p className="text-xl font-bold text-slate-300">
                        {sim.current_emission?.toFixed(1) || '0'} <span className="text-sm font-normal text-slate-600">kg</span>
                      </p>
                    </div>
                    <div className={`border rounded-xl p-3 text-center ${isReduction ? 'border-[#2ECC71]/30 bg-[#2ECC71]/5' : 'border-red-500/30 bg-red-500/5'}`}>
                      <p className="text-xs text-slate-500 uppercase font-medium mb-1">Projected</p>
                      <p className={`text-xl font-bold ${reductionColor}`}>
                        {sim.projected_emission?.toFixed(1) || '0'} <span className="text-sm font-normal text-slate-600">kg</span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <p className="text-xs text-slate-500 mb-1">Reduction</p>
                      <p className={`text-3xl font-bold ${reductionColor}`}>
                        {sim.reduction_percentage?.toFixed(1) || '0'}%
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-slate-500 mb-1">Est. Savings</p>
                      <p className="text-xl font-bold text-slate-300">
                        {sim.estimated_carbon_saved?.toFixed(1) || '0'} <span className="text-sm font-normal text-slate-500">kg CO2e</span>
                      </p>
                    </div>
                  </div>
                </div>

                <button 
                  onClick={() => handleRerun(sim)}
                  className="btn-outline w-full flex items-center justify-center gap-2 mt-auto"
                >
                  <i className="ti ti-reload"></i> Re-run Scenario
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
