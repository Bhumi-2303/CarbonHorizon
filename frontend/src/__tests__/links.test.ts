import { describe, it, expect } from 'vitest'
import { runLinkCheck, LinkIssue } from '../../../scripts/check-links.mjs'

describe('Link, Route, Anchor & Asset Integrity Suite (Task 16)', () => {
  it('passes complete repository link and integrity check with zero errors', () => {
    const issues = runLinkCheck()
    expect(issues).toEqual([])
  })

  it('prohibits placeholder hrefs and requires rel="noopener noreferrer" on target="_blank"', () => {
    const issues: LinkIssue[] = runLinkCheck()
    const placeholderIssues = issues.filter((i: LinkIssue) => i.type === 'PLACEHOLDER_HREF')
    const relIssues = issues.filter((i: LinkIssue) => i.type === 'MISSING_REL_NOOPENER')
    const deadImports = issues.filter((i: LinkIssue) => i.type === 'DEAD_IMPORT')
    const missingAssets = issues.filter((i: LinkIssue) => i.type === 'MISSING_ASSET')

    expect(placeholderIssues).toHaveLength(0)
    expect(relIssues).toHaveLength(0)
    expect(deadImports).toHaveLength(0)
    expect(missingAssets).toHaveLength(0)
  })
})
