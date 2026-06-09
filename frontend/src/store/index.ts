import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import emissionsReducer from './slices/emissionsSlice'
import reportsReducer from './slices/reportsSlice'
import organizationReducer from './slices/organizationSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    emissions: emissionsReducer,
    reports: reportsReducer,
    organization: organizationReducer,
  },
})

// Inferred types for use throughout the app
export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
