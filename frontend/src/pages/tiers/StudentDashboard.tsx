import { useEffect, useState } from 'react'
import { assessmentApi, AssessmentResult } from '@/api/assessment'
import { Link } from 'react-router-dom'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { Zap, Target, ArrowRight, Bus, Flame, PieChart as PieChartIcon } from 'lucide-react'

const COLORS = ['#10b981', '#38bdf8', '#fbbf24', '#f43f5e']

export default function StudentDashboard() {
  const [assessment, setAssessment] = useState<AssessmentResult | null>(null)
  const [streak] = useState([true, true, true, false, false, false, false]) // Dummy weekly streak data

  useEffect(() => {
    assessmentApi.history()
      .then(data => setAssessment(data[0] || null))
      .catch(console.error)
  }, [])

  const score = assessment ? Math.round(assessment.carbon_score) : 0

  // Derive pie chart data roughly from assessment values
  const pieData = assessment ? [
    { name: 'Transport', value: assessment.total_emission * 0.4 }, // Rough estimate for display
    { name: 'Electricity', value: assessment.total_emission * 0.3 },
    { name: 'Diet', value: assessment.total_emission * 0.2 },
    { name: 'Waste', value: assessment.total_emission * 0.1 }
  ] : []

  return (
    <div className="flex flex-col gap-6 animate-fade-shift-up pb-12">
      
      {/* Header Banner */}
      <div className="glass-card p-6 md:p-8 flex flex-col md:flex-row items-center gap-8 justify-between border-emerald-500/20 relative overflow-hidden">
        <div className="absolute -right-20 -top-20 opacity-5 pointer-events-none">
          <Zap className="w-96 h-96 text-emerald-400" />
        </div>
        
        <div className="flex-1 z-10">
          <h1 className="text-3xl font-black text-primary mb-2 font-poppins">Student Sustainability</h1>
          <p className="text-slate-400 mb-6 max-w-lg">
            Track your impact, complete weekly goals, and learn how small changes to your commute and habits make a massive difference.
          </p>
          {!assessment && (
            <Link to="/assessment" className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-slate-900 px-6 py-3 rounded-full font-bold transition-all shadow-lg shadow-emerald-500/20">
              Calculate My Footprint <ArrowRight className="w-5 h-5" />
            </Link>
          )}
        </div>

        {assessment && (
          <div className="relative flex flex-col items-center justify-center z-10 bg-bg-secondary/80 rounded-3xl p-8 border border-slate-700/50 min-w-[200px]">
            <span className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-2">Eco Score</span>
            <div className="flex items-baseline gap-1">
              <span className="text-6xl font-black text-emerald-400 font-poppins">{score}</span>
              <span className="text-xl font-bold text-slate-500">/100</span>
            </div>
            <div className="mt-4 px-4 py-1 bg-emerald-500/10 text-emerald-400 rounded-full text-sm font-bold border border-emerald-500/20">
              Top 20% of Students
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Breakdown Chart */}
        <div className="md:col-span-2 glass-card p-6 border-sky-500/20">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-sky-400/20 flex items-center justify-center">
              <Bus className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-primary">Impact Breakdown</h2>
              <p className="text-sm text-slate-400">Where do your emissions come from?</p>
            </div>
          </div>
          
          {assessment ? (
            <div className="h-64 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {pieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0B1215', borderColor: '#334155', borderRadius: '12px' }}
                    itemStyle={{ color: '#e2e8f0' }}
                    formatter={(val: number) => [`${val.toFixed(1)} kg CO2`, '']}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute flex flex-col items-center pointer-events-none">
                <span className="text-2xl font-bold text-primary">{assessment.total_emission.toFixed(1)}</span>
                <span className="text-xs text-slate-400 uppercase">kg CO2</span>
              </div>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-slate-500 border-2 border-dashed border-slate-700 rounded-2xl">
              <PieChartIcon className="w-8 h-8 mb-2 opacity-50" />
              <p>Take the assessment to see your chart</p>
            </div>
          )}
          
          {assessment && (
            <div className="flex flex-wrap justify-center gap-4 mt-2">
              {pieData.map((entry, index) => (
                <div key={entry.name} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index] }} />
                  <span className="text-sm text-muted">{entry.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Goals & Streaks */}
        <div className="glass-card p-6 border-amber-500/20 flex flex-col gap-6">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-amber-400/20 flex items-center justify-center">
                <Flame className="w-5 h-5 text-amber-400" />
              </div>
              <h2 className="text-xl font-bold text-primary">Weekly Streak</h2>
            </div>
            <div className="flex justify-between items-center bg-white/10/50 p-4 rounded-2xl border border-slate-700">
              {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, i) => (
                <div key={i} className="flex flex-col items-center gap-2">
                  <span className="text-xs font-bold text-slate-500">{day}</span>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all ${streak[i] ? 'bg-amber-400/20 border-amber-400 text-amber-400' : 'bg-white/10 border-slate-700 text-slate-700'}`}>
                    {streak[i] ? <Flame className="w-4 h-4" /> : null}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-rose-400/20 flex items-center justify-center">
                <Target className="w-5 h-5 text-rose-400" />
              </div>
              <h2 className="text-xl font-bold text-primary">This Week's Goal</h2>
            </div>
            <div className="bg-gradient-to-br from-rose-900/30 to-slate-900 p-5 rounded-2xl border border-rose-500/30 flex flex-col gap-3">
              <h3 className="font-bold text-rose-300">Meatless Monday</h3>
              <p className="text-sm text-slate-400">Try eating only vegetarian food for one entire day this week to drastically cut your diet emissions.</p>
              <button className="mt-2 py-2 w-full rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 font-bold border border-rose-500/50 transition-colors">
                Accept Challenge
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
