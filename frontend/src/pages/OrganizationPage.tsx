import { useState, useEffect } from 'react'
import apiClient from '@/api/client'

interface Organization {
  id: number
  name: string
  industry: string
  country: string
  created_at: string
}

const OrganizationPage = () => {
  const [org, setOrg] = useState<Organization | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchOrg = async () => {
      try {
        setLoading(true)
        // Adjust endpoint based on your actual API if different
        const response = await apiClient.get('/organization/me')
        setOrg(response.data)
      } catch (err: any) {
        // Fallback to empty state if 404 or just show error
        if (err.message?.includes('404')) {
          setOrg(null)
        } else {
          setError(err.message || 'Failed to load organization profile')
        }
      } finally {
        setLoading(false)
      }
    }
    fetchOrg()
  }, [])

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-gray-500 animate-pulse">Loading organization data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 mb-4 text-red-700 bg-red-100 rounded-lg">
        {error}
      </div>
    )
  }

  return (
    <main className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8 text-gray-800">Organization Profile</h1>
      
      {!org ? (
        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 text-center">
          <h2 className="text-xl font-semibold text-gray-700 mb-2">No Organization Found</h2>
          <p className="text-gray-500 mb-6">You are not currently associated with an organization.</p>
          <button className="bg-teal-600 hover:bg-teal-700 text-white px-6 py-2 rounded-lg font-medium transition-colors">
            Create Organization
          </button>
        </div>
      ) : (
        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">Company Name</h3>
              <p className="text-lg font-medium text-gray-900">{org.name}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">Industry</h3>
              <p className="text-lg text-gray-800">{org.industry || 'Not specified'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">Country</h3>
              <p className="text-lg text-gray-800">{org.country || 'Not specified'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">Member Since</h3>
              <p className="text-lg text-gray-800">
                {org.created_at ? new Date(org.created_at).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>
          <div className="mt-8 pt-6 border-t border-gray-100">
            <button className="text-teal-600 hover:text-teal-800 font-medium">
              Edit Profile
            </button>
          </div>
        </div>
      )}
    </main>
  )
}

export default OrganizationPage
