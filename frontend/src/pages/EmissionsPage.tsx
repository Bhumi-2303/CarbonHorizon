import { useState, useEffect } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts'
import apiClient from '@/api/client'
import { Leaf, AlertTriangle } from 'lucide-react'

interface ChartData {
  period: string
  Total: number
  Scope1: number
  Scope2: number
  Scope3: number
}

const EmissionsPage = () => {
  const [data, setData] = useState<ChartData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAssessments = async () => {
      try {
        setLoading(true)
        // Assume backend returns historical assessment data
        const response = await apiClient.get('/assessment/')
        const items = Array.isArray(response.data) ? response.data : response.data.items || []
        
        // Map to a format Recharts can use easily
        const chartData = items.map((item: any) => ({
          period: item.period || new Date(item.created_at).toLocaleString('default', { month: 'short', year: 'numeric' }),
          Scope1: item.scope_1 || 0,
          Scope2: item.scope_2 || 0,
          Scope3: item.scope_3 || 0,
          Total: item.total_emissions || (item.scope_1 + item.scope_2 + item.scope_3) || 0,
        }))
        
        // Reverse if API returns newest first, so timeline goes left to right
        setData(chartData.reverse())
      } catch (err: any) {
        if (err.message?.includes('404')) {
          setData([])
        } else {
          setError(err.message || 'Failed to load emissions data')
        }
      } finally {
        setLoading(false)
      }
    }
    fetchAssessments()
  }, [])

  const currentTotal = data.length > 0 ? data[data.length - 1].Total : 0
  const previousTotal = data.length > 1 ? data[data.length - 2].Total : 0
  const percentChange = previousTotal ? ((currentTotal - previousTotal) / previousTotal) * 100 : 0
  const trend = percentChange > 0 ? 'up' : percentChange < 0 ? 'down' : 'flat'

  return (
    <main className="max-w-7xl mx-auto p-6 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-800">Emissions Dashboard</h1>
        <button className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
          Record Data
        </button>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="text-gray-500 animate-pulse">Loading dashboard...</div>
        </div>
      ) : error ? (
        <div className="p-4 text-red-700 bg-red-100 rounded-lg">{error}</div>
      ) : data.length === 0 ? (
        <div className="bg-deep-ocean p-12 rounded-xl shadow-sm border border-gray-100 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">No Emissions Data</h2>
          <p className="text-gray-500 mb-6">Complete your first carbon assessment to see your dashboard.</p>
        </div>
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-deep-ocean p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Latest Period Total</h3>
              <div className="flex items-baseline">
                <span className="text-4xl font-bold text-gray-900">{currentTotal.toFixed(1)}</span>
                <span className="ml-2 text-sm text-gray-500 font-medium">kg CO₂e</span>
              </div>
            </div>

            <div className="bg-deep-ocean p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Trend vs Previous</h3>
              <div className="flex items-baseline">
                <span className={`text-4xl font-bold ${trend === 'down' ? 'text-earth-green' : trend === 'up' ? 'text-red-600' : 'text-gray-900'}`}>
                  {trend === 'up' ? '+' : ''}{percentChange.toFixed(1)}%
                </span>
                <span className="ml-2 text-sm text-gray-500 font-medium">
                  {trend === 'down' ? <><Leaf className="w-4 h-4 inline-block mr-1 text-[#2ECC71]" /> Decrease</> : trend === 'up' ? <><AlertTriangle className="w-4 h-4 inline-block mr-1 text-amber-500" /> Increase</> : 'No Change'}
                </span>
              </div>
            </div>

            <div className="bg-deep-ocean p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Largest Scope</h3>
              <div className="flex items-baseline">
                <span className="text-4xl font-bold text-gray-900">
                  {
                    Object.entries({
                      'Scope 1': data[data.length - 1].Scope1,
                      'Scope 2': data[data.length - 1].Scope2,
                      'Scope 3': data[data.length - 1].Scope3,
                    }).sort((a, b) => b[1] - a[1])[0][0]
                  }
                </span>
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="bg-deep-ocean p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-bold text-gray-800 mb-6">Historical Emissions by Scope</h3>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                  <XAxis 
                    dataKey="period" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#6B7280', fontSize: 12 }} 
                    dy={10}
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#6B7280', fontSize: 12 }} 
                    dx={-10}
                  />
                  <Tooltip 
                    cursor={{ fill: '#F3F4F6' }}
                    contentStyle={{ borderRadius: '0.5rem', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)' }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }} />
                  <Bar dataKey="Scope1" name="Scope 1 (Direct)" stackId="a" fill="#14B8A6" radius={[0, 0, 4, 4]} />
                  <Bar dataKey="Scope2" name="Scope 2 (Indirect Energy)" stackId="a" fill="#0EA5E9" />
                  <Bar dataKey="Scope3" name="Scope 3 (Value Chain)" stackId="a" fill="#6366F1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </main>
  )
}

export default EmissionsPage
