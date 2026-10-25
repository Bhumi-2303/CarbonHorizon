/// <reference types="vite/client" />

interface ImportMetaEnv {
  /**
   * Base URL for the CarbonHorizon backend API.
   * Public client-side identifier only — NEVER put secrets in frontend environment variables.
   */
  readonly VITE_API_URL?: string
  /**
   * Canonical URL for SEO metadata (e.g. https://carbonhorizon.app)
   */
  readonly VITE_APP_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*check-links.mjs' {
  export interface LinkIssue {
    type: string
    file: string
    line?: number
    detail: string
  }
  export function runLinkCheck(): LinkIssue[]
}
