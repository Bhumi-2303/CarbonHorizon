import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { simulatorApi, type SimulationSaved } from '@/api/simulator'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

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
        <i className="ti ti-loader animate-spin text-4xl text-accent"></i>
      </div>
    )
  }

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="heading-xl text-primary m-0">Saved Simulations</h1>
          <p className="body text-muted mt-1">Review and re-run your what-if scenarios.</p>
        </div>
        <Button onClick={() => navigate('/simulator')} variant="primary" className="flex items-center gap-2 self-start md:self-auto">
          <i className="ti ti-plus"></i> New Simulation
        </Button>
      </div>

      {error && (
        <div className="p-4 bg-danger/20 text-danger border border-danger/50 rounded-xl">
          {error}
        </div>
      )}

      {history.length === 0 ? (
        <Card className="text-center p-12 flex flex-col items-center">
          <i className="ti ti-flask text-6xl text-accent mb-6"></i>
          <h2 className="heading-lg text-primary mb-2">No saved simulations</h2>
          <p className="body text-muted max-w-md mb-8">
            You haven't saved any simulations yet. Run a what-if scenario to see how small changes can reduce your carbon footprint!
          </p>
          <Button onClick={() => navigate('/simulator')} variant="primary">
            Start a Simulation
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {history.map(sim => {
            const isReduction = (sim.reduction_percentage || 0) >= 0;
            const reductionColor = isReduction ? 'text-accent' : 'text-danger';

            return (
              <Card key={sim.id} className="flex flex-col justify-between group">
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="heading-md text-primary mb-1">{sim.scenario_name}</h3>
                      <p className="text-xs text-muted">
                        {new Date(sim.created_at).toLocaleDateString(undefined, {
                          year: 'numeric', month: 'short', day: 'numeric',
                          hour: '2-digit', minute: '2-digit'
                        })}
                      </p>
                    </div>
                    <button 
                      onClick={() => handleDelete(sim.id)} 
                      className="text-muted hover:text-danger transition-colors opacity-0 group-hover:opacity-100"
                      title="Delete"
                    >
                      <i className="ti ti-trash text-xl"></i>
                    </button>
                  </div>

                  {sim.scenario_description && (
                    <p className="body text-sm text-muted mb-6">{sim.scenario_description}</p>
                  )}

                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-bg-primary border border-white/10 rounded-xl p-3 text-center">
                      <p className="text-xs text-muted uppercase font-medium mb-1">Current</p>
                      <p className="text-xl font-bold text-muted">
                        {sim.current_emission?.toFixed(1) || '0'} <span className="text-sm font-normal text-muted">kg</span>
                      </p>
                    </div>
                    <div className={`border rounded-xl p-3 text-center ${isReduction ? 'border-accent/30 bg-accent/5' : 'border-danger/30 bg-danger/5'}`}>
                      <p className="text-xs text-muted uppercase font-medium mb-1">Projected</p>
                      <p className={`text-xl font-bold ${reductionColor}`}>
                        {sim.projected_emission?.toFixed(1) || '0'} <span className="text-sm font-normal text-muted">kg</span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <p className="text-xs text-muted mb-1">Reduction</p>
                      <p className={`text-3xl font-bold ${reductionColor}`}>
                        {sim.reduction_percentage?.toFixed(1) || '0'}%
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-muted mb-1">Est. Savings</p>
                      <p className="text-xl font-bold text-muted">
                        {sim.estimated_carbon_saved?.toFixed(1) || '0'} <span className="text-sm font-normal text-muted">kg CO2e</span>
                      </p>
                    </div>
                  </div>
                </div>

                <Button 
                  onClick={() => handleRerun(sim)}
                  variant="secondary"
                  className="w-full flex items-center justify-center gap-2 mt-auto"
                >
                  <i className="ti ti-reload"></i> Re-run Scenario
                </Button>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
