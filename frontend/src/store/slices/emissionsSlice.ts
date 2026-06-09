/**
 * Emissions Redux slice — no logic yet, structure only.
 */
import { createSlice } from '@reduxjs/toolkit'

interface Emission {
  id: number
  source: string
  scope: 1 | 2 | 3
  quantity_kg_co2e: number
  recorded_at: string
  notes?: string
  organization_id: number
  created_at: string
}

interface EmissionsState {
  items: Emission[]
  loading: boolean
  error: string | null
}

const initialState: EmissionsState = {
  items: [],
  loading: false,
  error: null,
}

const emissionsSlice = createSlice({
  name: 'emissions',
  initialState,
  reducers: {
    // TODO: implement fetchEmissions, createEmission, updateEmission, deleteEmission
  },
})

export default emissionsSlice.reducer
