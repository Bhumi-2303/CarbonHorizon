/**
 * On-demand lazy loader for the location database (country-state-city).
 *
 * The full global geography database contains ~150,000 cities and is ~8.6 MB
 * uncompressed. To guarantee sub-1.5s mobile LCP and 95+ Lighthouse performance
 * on /register and /profile, this module defers loading until user interaction
 * or browser idle time.
 */

export interface GeoDataModule {
  Country: {
    getAllCountries: () => Array<{ isoCode: string; name: string }>
    getCountryByCode: (code: string) => { isoCode: string; name: string } | undefined
  }
  State: {
    getStatesOfCountry: (countryCode: string) => Array<{ isoCode: string; name: string }>
    getStateByCodeAndCountry: (stateCode: string, countryCode: string) => { isoCode: string; name: string } | undefined
  }
  City: {
    getCitiesOfState: (countryCode: string, stateCode: string) => Array<{ name: string }>
  }
}

let cachedGeoModule: GeoDataModule | null = null
let pendingLoadPromise: Promise<GeoDataModule> | null = null

export function getCachedGeoData(): GeoDataModule | null {
  return cachedGeoModule
}

export function loadGeoDataOnDemand(): Promise<GeoDataModule> {
  if (cachedGeoModule) {
    return Promise.resolve(cachedGeoModule)
  }
  if (!pendingLoadPromise) {
    pendingLoadPromise = import('country-state-city')
      .then((mod) => {
        cachedGeoModule = {
          Country: mod.Country,
          State: mod.State,
          City: mod.City,
        }
        return cachedGeoModule
      })
      .catch((err) => {
        pendingLoadPromise = null
        throw err
      })
  }
  return pendingLoadPromise
}

/**
 * Schedule geo data loading during idle browser periods without
 * competing with initial paint, LCP, or input responsiveness.
 */
export function preloadGeoDataIdle(callback?: (data: GeoDataModule) => void): () => void {
  if (cachedGeoModule) {
    callback?.(cachedGeoModule)
    return () => {}
  }

  let handle: number | null = null
  const trigger = () => {
    loadGeoDataOnDemand().then((data) => {
      callback?.(data)
    })
  }

  if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
    handle = window.requestIdleCallback(trigger, { timeout: 3500 })
    return () => {
      if (handle !== null && 'cancelIdleCallback' in window) {
        window.cancelIdleCallback(handle)
      }
    }
  } else {
    const timer = setTimeout(trigger, 2500)
    return () => clearTimeout(timer)
  }
}
