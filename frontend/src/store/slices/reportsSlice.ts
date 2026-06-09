/**
 * Reports Redux slice — no logic yet, structure only.
 */
import { createSlice } from '@reduxjs/toolkit'

interface Report {
  id: number
  title: string
  period_start: string
  period_end: string
  status: 'draft' | 'published' | 'archived'
  summary?: string
  organization_id: number
  created_at: string
  updated_at: string
}

interface ReportsState {
  items: Report[]
  loading: boolean
  error: string | null
}

const initialState: ReportsState = {
  items: [],
  loading: false,
  error: null,
}

const reportsSlice = createSlice({
  name: 'reports',
  initialState,
  reducers: {
    // TODO: implement fetchReports, createReport, updateReport, deleteReport
  },
})

export default reportsSlice.reducer
