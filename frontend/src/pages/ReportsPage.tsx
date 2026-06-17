import { useState, useEffect } from 'react'
import apiClient from '@/api/client'

interface Report {
  id: number
  title: string
  period_start: string
  period_end: string
  status: 'draft' | 'published' | 'archived'
  created_at: string
}

const ReportsPage = () => {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get('/reports')
        // Assume API returns an array or paginated object
        setReports(Array.isArray(response.data) ? response.data : response.data.items || [])
      } catch (err: any) {
        if (err.message?.includes('404')) {
          setReports([])
        } else {
          setError(err.message || 'Failed to load reports')
        }
      } finally {
        setLoading(false)
      }
    }
    fetchReports()
  }, [])

  const handleDownload = (reportId: number) => {
    // Implement standard download logic
    console.log(`Downloading report ${reportId}`)
    alert(`Downloading report ${reportId}...`)
  }

  return (
    <main className="max-w-6xl mx-auto p-6">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Sustainability Reports</h1>
        <button className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
          Generate New
        </button>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="text-gray-500 animate-pulse">Loading reports...</div>
        </div>
      ) : error ? (
        <div className="p-4 mb-4 text-red-700 bg-red-100 rounded-lg">{error}</div>
      ) : reports.length === 0 ? (
        <div className="bg-white p-12 rounded-xl shadow-sm border border-gray-100 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">No Reports Generated</h2>
          <p className="text-gray-500 mb-6">You haven't generated any sustainability reports yet.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                <th className="px-6 py-4 text-sm font-medium text-gray-500 uppercase tracking-wider">Report Title</th>
                <th className="px-6 py-4 text-sm font-medium text-gray-500 uppercase tracking-wider">Period</th>
                <th className="px-6 py-4 text-sm font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-sm font-medium text-gray-500 uppercase tracking-wider">Generated</th>
                <th className="px-6 py-4 text-sm font-medium text-gray-500 uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {reports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4 font-medium text-gray-900">{report.title}</td>
                  <td className="px-6 py-4 text-gray-500">
                    {new Date(report.period_start).toLocaleDateString()} - {new Date(report.period_end).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize
                      ${report.status === 'published' ? 'bg-green-100 text-green-800' : 
                        report.status === 'draft' ? 'bg-yellow-100 text-yellow-800' : 
                        'bg-gray-100 text-gray-800'}`}>
                      {report.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-500">
                    {new Date(report.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button 
                      onClick={() => handleDownload(report.id)}
                      className="text-teal-600 hover:text-teal-900 font-medium text-sm"
                    >
                      Download PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}

export default ReportsPage
