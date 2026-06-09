// Layout component placeholder — no logic yet
import { type ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  return (
    <div id="layout">
      {/* TODO: Sidebar + Topbar navigation */}
      <main id="main-content">{children}</main>
    </div>
  )
}

export default Layout
