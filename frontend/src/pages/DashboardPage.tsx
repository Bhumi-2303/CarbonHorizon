import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Doughnut, Line } from 'react-chartjs-2'
import { Globe, Target, TrendingDown, Car, Zap, Utensils, Trash2 } from 'lucide-react'
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
        <div className="h-8 w-48 bg-bg-secondary rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="glass-card h-32 animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="glass-card h-80 animate-pulse" />
          <div className="glass-card h-80 animate-pulse" />
        </div>
      </div>
    )
  }

  const latest = dashboard?.latest_assessment

  if (!latest) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[80vh]">
        <div className="glass-card w-full max-w-2xl text-center p-12">
          <i className="ti ti-leaf text-6xl text-earth-green mb-6 inline-block"></i>
          <h2 className="heading-xl mb-4 text-primary">Welcome to Carbon Horizon</h2>
          <p className="body text-muted mb-8">
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
  const reductionPotential = dashboard?.trend_delta ? `${dashboard.trend_delta > 0 ? '+' : ''}${dashboard.trend_delta.toFixed(1)}%` : '0%'

  const sources = [
    { name: 'Transportation', value: latest.transport_emission, icon: Car },
    { name: 'Energy', value: latest.energy_emission, icon: Zap },
    { name: 'Food', value: latest.food_emission, icon: Utensils },
    { name: 'Waste', value: latest.waste_emission, icon: Trash2 },
  ]
  const largestSource = sources.reduce((max, s) => s.value > max.value ? s : max, sources[0])
  const largestSourcePct = latest.total_emission > 0 ? Math.round((largestSource.value / latest.total_emission) * 100) : 0
  const SourceIcon = largestSource.icon

  // 2. Donut Chart Data
  const donutData = {
    labels: ['Transport', 'Energy', 'Food', 'Waste'],
    datasets: [
      {
        data: [latest.transport_emission, latest.energy_emission, latest.food_emission, latest.waste_emission],
        backgroundColor: ['#2ECC71', '#A3E635', '#1B5E20', '#94A3B8'],
        borderWidth: 0,
        hoverOffset: 6
      }
    ]
  }
  const donutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '75%',
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: '#94A3B8',
          font: { family: 'Inter', size: 12 },
          boxWidth: 10,
          boxHeight: 10,
        }
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleFont: { family: 'Inter', size: 13 },
        bodyFont: { family: 'Inter', size: 13 },
        borderColor: 'rgba(46, 204, 113, 0.2)',
        borderWidth: 1,
        padding: 12,
        callbacks: {
          label: function(context: TooltipItem<'doughnut'>) {
            const val = context.raw as number
            const total = latest.total_emission
            const pct = total > 0 ? Math.round((val / total) * 100) : 0
            const recs: Record<string, string> = {
              'Transport': 'Consider public transit or biking.',
              'Energy': 'Switch to renewables or reduce AC.',
              'Food': 'Try adding more plant-based meals.',
              'Waste': 'Improve recycling and reduce plastics.'
            }
            return [
              `${context.label}: ${val.toFixed(1)} kg CO₂e (${pct}%)`,
              recs[context.label] || ''
            ]
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
          <h1 className="heading-xl text-primary m-0">Dashboard</h1>
          <p className="body text-muted mt-1">Your sustainability overview at a glance.</p>
        </div>
        <Link to="/assessment" className="btn-primary flex items-center gap-2 self-start md:self-auto">
          <i className="ti ti-plus"></i> New Assessment
        </Link>
      </div>

      {/* 1. Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Card 1: Annual Footprint */}
        <div className="glass-card hover:scale-[1.02] transition-transform duration-200 cursor-pointer flex flex-col justify-between relative p-6">
          <div className="absolute top-6 right-6">
            <Globe className="w-8 h-8 text-earth-green/40" />
          </div>
          <div>
            <p className="font-inter text-sm text-muted uppercase tracking-widest">Annual Carbon Footprint</p>
            <p className="font-inter text-xs text-muted mt-1">Based on your latest assessment</p>
          </div>
          <div className="mt-6">
            <span className="font-montserrat font-semibold text-earth-green text-4xl">{annualTons} Tons CO₂e</span>
          </div>
        </div>
        
        {/* Card 2: Carbon Score */}
        <div className="glass-card hover:scale-[1.02] transition-transform duration-200 cursor-pointer flex flex-col justify-between relative p-6">
          <div className="absolute top-6 right-6">
            <Target className="w-8 h-8 text-earth-green/40" />
          </div>
          <div>
            <p className="font-inter text-sm text-muted uppercase tracking-widest">Carbon Score</p>
            <p className="font-inter text-xs text-muted mt-1 opacity-0">Spacer</p>
          </div>
          <div className="mt-6 flex items-center gap-4">
            <div className="relative w-14 h-14">
              <svg className="w-14 h-14 transform -rotate-90">
                <circle cx="28" cy="28" r="24" stroke="currentColor" strokeWidth="5" fill="transparent" className="text-forest-green/30" />
                <circle cx="28" cy="28" r="24" stroke="currentColor" strokeWidth="5" fill="transparent" strokeDasharray="150.8" strokeDashoffset={150.8 - (150.8 * score) / 100} className="text-earth-green transition-all duration-1000 ease-out" strokeLinecap="round" />
              </svg>
            </div>
            <span className="font-montserrat font-semibold text-earth-green text-4xl">{score}/100</span>
          </div>
        </div>

        {/* Card 3: Reduction Potential */}
        <div className="glass-card hover:scale-[1.02] transition-transform duration-200 cursor-pointer flex flex-col justify-between relative p-6">
          <div className="absolute top-6 right-6">
            <TrendingDown className="w-8 h-8 text-earth-green/40" />
          </div>
          <div>
            <p className="font-inter text-sm text-muted uppercase tracking-widest">Reduction Potential</p>
            <p className="font-inter text-xs text-muted mt-1">If you adopt all recommendations</p>
          </div>
          <div className="mt-6">
            <span className="font-montserrat font-semibold text-eco-lime text-4xl">{reductionPotential}</span>
          </div>
        </div>

        {/* Card 4: Largest Emission Source */}
        <div className="glass-card hover:scale-[1.02] transition-transform duration-200 cursor-pointer flex flex-col justify-between relative p-6">
          <div className="absolute top-6 right-6">
            <SourceIcon className="w-8 h-8 text-earth-green/40" />
          </div>
          <div>
            <p className="font-inter text-sm text-muted uppercase tracking-widest">Largest Source</p>
            <p className="font-inter text-xs text-muted mt-1">{largestSource.name}</p>
          </div>
          <div className="mt-6 flex items-baseline gap-2">
            <span className={`font-montserrat font-semibold text-4xl ${largestSourcePct > 40 ? 'text-warning' : 'text-earth-green'}`}>{largestSourcePct}%</span>
            <span className="font-inter text-sm text-muted">of footprint</span>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* 2. Emission Breakdown */}
        <div className="glass-card lg:col-span-1 flex flex-col">
          <h3 className="heading-md text-primary mb-6">Footprint Breakdown</h3>
          <div className="flex-1 relative min-h-[250px]">
            <Doughnut data={donutData} options={donutOptions} />
          </div>
        </div>

        {/* 3. Assessment History */}
        <div className="glass-card lg:col-span-2 flex flex-col">
          <h3 className="heading-md text-primary mb-6">Emissions Trend</h3>
          <div className="flex-1 relative min-h-[250px]">
            {sortedHist.length > 1 ? (
              <Line data={lineData} options={lineOptions} />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center text-muted">
                <p>Complete another assessment to see your trend over time.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Habits & Forecast Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* 4. Habit Streak & Goals */}
        <div className="glass-card space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="heading-md text-primary">Current Progress</h3>
            <div className="bg-bg-secondary rounded-full px-3 py-1 flex items-center gap-2">
              <i className="ti ti-flame text-orange-500"></i>
              <span className="text-sm font-bold text-primary">{dashboard?.current_habit_streak || 0} Day Streak</span>
            </div>
          </div>
          
          <div className="space-y-4 mt-4">
            <p className="text-sm text-muted">Active Goals</p>
            {goals.length === 0 ? (
              <p className="text-sm text-muted">No active goals yet. <Link to="/goals" className="text-earth-green hover:underline">Set one up.</Link></p>
            ) : (
              goals.slice(0, 3).map(goal => (
                <div key={goal.id} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-primary truncate">{goal.goal_name}</span>
                    <span className="text-earth-green">{Math.round(goal.current_progress)}%</span>
                  </div>
                  <div className="h-2 w-full bg-bg-secondary rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-earth-green rounded-full"
                      style={{ width: `${Math.min(goal.current_progress, 100)}%` }}
                    />
                  </div>
                </div>
              ))
            )}
            {goals.length > 3 && (
              <Link to="/goals" className="text-sm text-muted hover:text-earth-green block mt-2 text-center">
                View all {goals.length} goals
              </Link>
            )}
          </div>
        </div>

        {/* 5. Forecast Teaser */}
        <div className="glass-card flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 -mt-8 -mr-8 w-48 h-48 bg-earth-green/10 rounded-full blur-3xl transition-transform group-hover:scale-110"></div>
          
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="heading-md text-primary">3-Month Forecast</h3>
              <i className="ti ti-stars text-earth-green text-xl"></i>
            </div>
            <p className="body text-muted mb-6">Based on your current habits and baseline, here is your projected emission in 3 months.</p>
            
            {dashboard?.forecast_summary ? (
              <div className="flex items-end gap-3">
                <span className="metric text-earth-green">
                  {dashboard.forecast_summary.month_3_emission.toFixed(0)} <span className="text-lg font-normal text-muted">kg CO2e</span>
                </span>
              </div>
            ) : (
              <p className="text-muted">Forecast data not available.</p>
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
