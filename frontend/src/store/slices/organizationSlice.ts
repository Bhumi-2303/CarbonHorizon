/**
 * Organization Redux slice — no logic yet, structure only.
 */
import { createSlice } from '@reduxjs/toolkit'

interface Organization {
  id: number
  name: string
  industry?: string
  country?: string
  created_at: string
  updated_at: string
}

interface OrganizationState {
  current: Organization | null
  loading: boolean
  error: string | null
}

const initialState: OrganizationState = {
  current: null,
  loading: false,
  error: null,
}

const organizationSlice = createSlice({
  name: 'organization',
  initialState,
  reducers: {
    // TODO: implement fetchOrganization, updateOrganization
  },
})

export default organizationSlice.reducer
