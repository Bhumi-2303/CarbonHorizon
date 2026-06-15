import { useEffect, useState } from 'react'
import { useLocation, useParams, Link } from 'react-router-dom'
import { Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TooltipItem
} from 'chart.js'
import { assessmentApi } from '@/api/assessment'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

export default function AssessmentResult() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  // const navigate = useNavigate()
  
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadData() {
      // 1. Check navigation state first
      if (location.state) {
        // Handle both raw state or wrapped state (like state.assessmentResult)
        const stateData = location.state.assessmentResult || location.state
        if (stateData && (stateData.assessment_id || stateData.id)) {
          setData(stateData)
          setLoading(false)
          return
        }
      }
      
      // 2. Fetch from API if ID is available
      if (id) {
        try {
          const res = await assessmentApi.getById(id)
          setData(res)
        } catch (err: any) {
          setError(err.message || 'Failed to load assessment')
        }
      } else {
        setError('No assessment data found')
      }
      setLoading(false)
    }
    
    loadData()
  }, [id, location.state])

  if (loading) {
    return (
      <div className="flex justify-center p-20">
        <i className="ti ti-loader animate-spin text-4xl text-[#2ECC71]"></i>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[60vh]">
        <div className="card text-center p-12 max-w-lg">
          <i className="ti ti-alert-triangle text-5xl text-red-500 mb-4"></i>
          <h2 className="heading-md text-white mb-2">Assessment Not Found</h2>
          <p className="body text-slate-400 mb-6">{error || 'Unable to load your results.'}</p>
          <Link to="/assessment" className="btn-primary">Take New Assessment</Link>
        </div>
      </div>
    )
  }

  // Normalize data keys since API and state might differ slightly
  const totalEmission = data.total_emission || 0
  const transport = data.transport_emission ?? data.transport ?? 0
  const energy = data.energy_emission ?? data.energy ?? 0
  const food = data.food_emission ?? data.food ?? 0
  const waste = data.waste_emission ?? data.waste ?? 0
  const score = data.carbon_score || 0
  
  // Scoring logic
  let bandColor = 'text-red-500'
  let bandRing = 'border-red-500'
  let bandLabel = 'Needs Improvement'
  
  if (score >= 80) {
    bandColor = 'text-[#2ECC71]'
    bandRing = 'border-[#2ECC71]'
    bandLabel = 'Excellent'
  } else if (score >= 60) {
    bandColor = 'text-yellow-500'
    bandRing = 'border-yellow-500'
    bandLabel = 'Good'
  } else if (score >= 40) {
    bandColor = 'text-orange-500'
    bandRing = 'border-orange-500'
    bandLabel = 'Moderate'
  }

  // Find largest category
  const categories = [
    { name: 'Transport', value: transport, icon: '🚗', tip: 'Consider carpooling, public transit, or biking to reduce transport emissions.' },
    { name: 'Energy', value: energy, icon: '⚡', tip: 'Switching to LED bulbs or adjusting your thermostat can make a huge impact.' },
    { name: 'Food', value: food, icon: '🥗', tip: 'Reducing meat consumption just a few days a week lowers food footprint significantly.' },
    { name: 'Waste', value: waste, icon: '🗑️', tip: 'Focus on recycling more and avoiding single-use plastics.' }
  ]
  const largest = categories.reduce((prev, current) => (prev.value > current.value) ? prev : current)

  // Doughnut Chart Configuration
  const donutData = {
    labels: ['Transport', 'Energy', 'Food', 'Waste'],
    datasets: [
      {
        data: [transport, energy, food, waste],
        backgroundColor: ['#3B82F6', '#F59E0B', '#2ECC71', '#8B5CF6'],
        borderWidth: 0,
        hoverOffset: 6
      }
    ]
  }

  const donutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const, labels: { color: '#cbd5e1', padding: 20 } },
      tooltip: {
        callbacks: {
          label: function(context: TooltipItem<'doughnut'>) {
            const val = context.raw as number
            const pct = totalEmission > 0 ? Math.round((val / totalEmission) * 100) : 0
            return ` ${context.label}: ${val.toFixed(1)} kg (${pct}%)`
          }
        }
      }
    }
  }

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8 animate-fade-in">
      
      {/* 1. Hero: Carbon Score */}
      <div className="card text-center flex flex-col items-center py-12 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#2ECC71]/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl"></div>
        
        <h1 className="heading-lg text-white mb-8 z-10">Your Carbon Score</h1>
        
        <div className={`w-48 h-48 rounded-full border-8 ${bandRing} flex flex-col items-center justify-center z-10 bg-[#08121E]`}>
          <span className={`text-6xl font-[Montserrat] font-semibold ${bandColor}`}>{Math.round(score)}</span>
        </div>
        
        <div className="mt-6 z-10">
          <span className={`px-4 py-2 rounded-full font-bold uppercase tracking-wider text-sm bg-[#08121E] border ${bandRing} ${bandColor}`}>
            {bandLabel}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* 2. Emission Breakdown Donut Chart */}
        <div className="card flex flex-col">
          <h2 className="heading-md text-white mb-6">Emission Breakdown</h2>
          <div className="flex-1 min-h-[300px] relative">
            <Doughnut data={donutData} options={donutOptions} />
          </div>
        </div>

        <div className="space-y-8">
          {/* 3. Metric Cards (Daily, Monthly, Annual) */}
          <div className="grid grid-cols-3 gap-4">
            <div className="card text-center p-4">
              <p className="text-xs text-slate-400 uppercase font-medium mb-2">Daily</p>
              <p className="text-xl font-bold text-[#2ECC71]">{(totalEmission / 30).toFixed(1)} <span className="text-xs text-slate-500 font-normal">kg</span></p>
            </div>
            <div className="card text-center p-4">
              <p className="text-xs text-slate-400 uppercase font-medium mb-2">Monthly</p>
              <p className="text-xl font-bold text-[#2ECC71]">{totalEmission.toFixed(1)} <span className="text-xs text-slate-500 font-normal">kg</span></p>
            </div>
            <div className="card text-center p-4">
              <p className="text-xs text-slate-400 uppercase font-medium mb-2">Annual</p>
              <p className="text-xl font-bold text-[#2ECC71]">{(totalEmission * 12).toFixed(1)} <span className="text-xs text-slate-500 font-normal">kg</span></p>
            </div>
          </div>

          {/* 4. Top Source Callout */}
          <div className="card border-l-4 border-l-orange-500 bg-orange-500/10">
            <div className="flex items-start gap-4">
              <div className="text-4xl">{largest.icon}</div>
              <div>
                <h3 className="heading-md text-orange-400 mb-1">Top Emission Source: {largest.name}</h3>
                <p className="body text-slate-300 text-sm">{largest.tip}</p>
              </div>
            </div>
          </div>

          {/* 5. CTAs */}
          <div className="grid grid-cols-2 gap-4 pt-4">
            <Link to="/dashboard" className="btn-outline flex items-center justify-center gap-2">
              <i className="ti ti-layout-dashboard"></i> View Dashboard
            </Link>
            <Link to="/simulator" className="btn-primary flex items-center justify-center gap-2">
              <i className="ti ti-flask"></i> Simulate Changes
            </Link>
          </div>
        </div>

      </div>
    </div>
  )
}
