import { useDispatch, useSelector } from 'react-redux'
import type { RootState, AppDispatch } from '.'

// Typed wrappers to avoid importing RootState/AppDispatch throughout the codebase
export const useAppDispatch = () => useDispatch<AppDispatch>()
export const useAppSelector = <T>(selector: (state: RootState) => T) => useSelector(selector)
