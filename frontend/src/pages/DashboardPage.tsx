import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Doughnut, Line } from 'react-chartjs-2'
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
import { dashboardApi, type DashboardData } from '@/api/dashboard'
import { assessmentApi, type AssessmentResult } from '@/api/assessment'
import { goalsApi, type Goal } from '@/api/goals'

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

function getScoreColorClass(score: number) {
  if (score >= 80) return 'text-[#2ECC71]'
  if (score >= 60) return 'text-[#EAB308]' // yellow
  if (score >= 40) return 'text-[#F97316]' // orange
  return 'text-[#EF4444]' // red
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [history, setHistory] = useState<AssessmentResult[]>([])
  const [goals, setGoals] = useState<Goal[]>([])

  useEffect(() => {
    async function loadData() {
      try {
        const [dashRes, histRes, goalsRes] = await Promise.all([
          dashboardApi.getDashboard().catch(() => null),
          assessmentApi.history().catch(() => []),
          goalsApi.listActive().catch(() => [])
        ])
        setDashboard(dashRes)
        setHistory(histRes)
        setGoals(goalsRes)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="p-8 space-y-6">
        <div className="h-8 w-48 bg-slate-800 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card h-32 animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card h-80 animate-pulse" />
          <div className="card h-80 animate-pulse" />
        </div>
      </div>
    )
  }

  const latest = dashboard?.latest_assessment

  if (!latest) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[80vh]">
        <div className="card w-full max-w-2xl text-center p-12">
          <i className="ti ti-leaf text-6xl text-emerald-500 mb-6 inline-block"></i>
          <h2 className="heading-xl mb-4 text-white">Welcome to Carbon Horizon</h2>
          <p className="body text-slate-300 mb-8">
            You haven't completed a carbon assessment yet. Calculate your footprint to unlock your dashboard, AI coach, and personalized goals.
          </p>
          <Link to="/assessment" className="btn-primary inline-flex items-center gap-2 text-lg px-8 py-4">
            <i className="ti ti-calculator"></i> Calculate Your Footprint
          </Link>
        </div>
      </div>
    )
  }

  // 1. Metric Cards Prep
  const annualTons = ((latest.total_emission * 12) / 1000).toFixed(2)
  const score = Math.round(latest.carbon_score)
  // trend_delta is negative for reduction
  const reductionPotential = dashboard?.trend_delta ? `${dashboard.trend_delta > 0 ? '+' : ''}${dashboard.trend_delta.toFixed(1)}%` : 'N/A'

  // 2. Donut Chart Data
  const donutData = {
    labels: ['Transport', 'Energy', 'Food', 'Waste'],
    datasets: [
      {
        data: [latest.transport_emission, latest.energy_emission, latest.food_emission, latest.waste_emission],
        backgroundColor: ['#3B82F6', '#F59E0B', '#2ECC71', '#8B5CF6'],
        borderWidth: 0,
        hoverOffset: 4
      }
    ]
  }
  const donutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' as const, labels: { color: '#cbd5e1' } },
      tooltip: {
        callbacks: {
          label: function(context: TooltipItem<'doughnut'>) {
            const val = context.raw as number
            const total = latest.total_emission
            const pct = total > 0 ? Math.round((val / total) * 100) : 0
            return ` ${context.label}: ${val.toFixed(1)} kg (${pct}%)`
          }
        }
      }
    }
  }

  // 3. Line Chart Data (Assessment History)
  const sortedHist = [...history].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
  const lineData = {
    labels: sortedHist.map(h => new Date(h.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })),
    datasets: [
      {
        label: 'Total Emissions (kg CO2e)',
        data: sortedHist.map(h => h.total_emission),
        borderColor: '#2ECC71',
        backgroundColor: 'rgba(46, 204, 113, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  }
  const lineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
      x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
    },
    plugins: {
      legend: { display: false }
    }
  }

  return (
    <div className="p-6 md:p-8 space-y-8 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="heading-xl text-white m-0">Dashboard</h1>
          <p className="body text-slate-400 mt-1">Your sustainability overview at a glance.</p>
        </div>
        <Link to="/assessment" className="btn-primary flex items-center gap-2 self-start md:self-auto">
          <i className="ti ti-plus"></i> New Assessment
        </Link>
      </div>

      {/* 1. Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card flex flex-col justify-between">
          <p className="text-sm text-slate-400 font-medium">Annual Emissions</p>
          <div className="mt-4 flex items-end justify-between">
            <span className="metric text-white">{annualTons} <span className="text-lg text-slate-500 font-normal">tons</span></span>
            <i className="ti ti-cloud text-slate-600 text-3xl"></i>
          </div>
        </div>
        
        <div className="card flex flex-col justify-between">
          <p className="text-sm text-slate-400 font-medium">Carbon Score</p>
          <div className="mt-4 flex items-end justify-between">
            <span className={`metric ${getScoreColorClass(score)}`}>{score}<span className="text-lg text-slate-500 font-normal">/100</span></span>
            <i className="ti ti-rosette text-slate-600 text-3xl"></i>
          </div>
        </div>

        <div className="card flex flex-col justify-between">
          <p className="text-sm text-slate-400 font-medium">Trend / Delta</p>
          <div className="mt-4 flex items-end justify-between">
            <span className={`metric ${dashboard?.trend_delta && dashboard.trend_delta <= 0 ? 'text-[#2ECC71]' : 'text-[#EF4444]'}`}>
              {reductionPotential}
            </span>
            <i className={`ti ${dashboard?.trend_delta && dashboard.trend_delta <= 0 ? 'ti-trending-down text-emerald-500' : 'ti-trending-up text-red-500'} text-3xl`}></i>
          </div>
        </div>

        <div className="card flex flex-col justify-between">
          <p className="text-sm text-slate-400 font-medium">Active Goals</p>
          <div className="mt-4 flex items-end justify-between">
            <span className="metric text-white">{dashboard?.active_goals_count || 0}</span>
            <i className="ti ti-target text-slate-600 text-3xl"></i>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* 2. Emission Breakdown */}
        <div className="card lg:col-span-1 flex flex-col">
          <h3 className="heading-md text-white mb-6">Footprint Breakdown</h3>
          <div className="flex-1 relative min-h-[250px]">
            <Doughnut data={donutData} options={donutOptions} />
          </div>
        </div>

        {/* 3. Assessment History */}
        <div className="card lg:col-span-2 flex flex-col">
          <h3 className="heading-md text-white mb-6">Emissions Trend</h3>
          <div className="flex-1 relative min-h-[250px]">
            {sortedHist.length > 1 ? (
              <Line data={lineData} options={lineOptions} />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center text-slate-500">
                <p>Complete another assessment to see your trend over time.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Habits & Forecast Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* 4. Habit Streak & Goals */}
        <div className="card space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="heading-md text-white">Current Progress</h3>
            <div className="bg-slate-800 rounded-full px-3 py-1 flex items-center gap-2">
              <i className="ti ti-flame text-orange-500"></i>
              <span className="text-sm font-bold text-white">{dashboard?.current_habit_streak || 0} Day Streak</span>
            </div>
          </div>
          
          <div className="space-y-4 mt-4">
            <p className="text-sm text-slate-400">Active Goals</p>
            {goals.length === 0 ? (
              <p className="text-sm text-slate-500">No active goals yet. <Link to="/goals" className="text-emerald-500 hover:underline">Set one up.</Link></p>
            ) : (
              goals.slice(0, 3).map(goal => (
                <div key={goal.id} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-200 truncate">{goal.goal_name}</span>
                    <span className="text-emerald-400">{Math.round(goal.current_progress)}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full"
                      style={{ width: `${Math.min(goal.current_progress, 100)}%` }}
                    />
                  </div>
                </div>
              ))
            )}
            {goals.length > 3 && (
              <Link to="/goals" className="text-sm text-slate-400 hover:text-emerald-400 block mt-2 text-center">
                View all {goals.length} goals
              </Link>
            )}
          </div>
        </div>

        {/* 5. Forecast Teaser */}
        <div className="card flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 -mt-8 -mr-8 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl transition-transform group-hover:scale-110"></div>
          
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="heading-md text-white">3-Month Forecast</h3>
              <i className="ti ti-stars text-emerald-400 text-xl"></i>
            </div>
            <p className="body text-slate-400 mb-6">Based on your current habits and baseline, here is your projected emission in 3 months.</p>
            
            {dashboard?.forecast_summary ? (
              <div className="flex items-end gap-3">
                <span className="metric text-emerald-400">
                  {dashboard.forecast_summary.month_3_emission.toFixed(0)} <span className="text-lg font-normal text-slate-500">kg CO2e</span>
                </span>
              </div>
            ) : (
              <p className="text-slate-500">Forecast data not available.</p>
            )}
          </div>

          <div className="mt-8">
            <Link to="/forecast" className="btn-outline inline-flex items-center gap-2 w-full justify-center">
              View Detailed Forecast <i className="ti ti-arrow-right"></i>
            </Link>
          </div>
        </div>

      </div>
    </div>
  )
}
