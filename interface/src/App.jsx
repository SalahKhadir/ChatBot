import { useState, useEffect } from 'react'
import { Home } from './pages'
import AdminPanel from './pages/AdminPanel'
import { adminAPI, authService } from './services/api'
import './App.css'

function App() {
  const [currentRoute, setCurrentRoute] = useState('home')
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    return saved ? JSON.parse(saved) : false
  })

  useEffect(() => {
    // Simple client-side routing
    const updateRoute = () => {
      const path = window.location.pathname
      if (path === '/admin') {
        // Check if user is admin before showing admin panel
        if (authService.isAuthenticated() && adminAPI.isCurrentUserAdmin()) {
          setCurrentRoute('admin')
        } else {
          // Redirect non-admin users back to home
          window.history.pushState(null, '', '/')
          setCurrentRoute('home')
        }
      } else {
        setCurrentRoute('home')
      }
    }

    updateRoute()

    // Listen for browser back/forward navigation
    window.addEventListener('popstate', updateRoute)
    
    return () => {
      window.removeEventListener('popstate', updateRoute)
    }
  }, [])

  const handleNavigate = (route) => {
    setCurrentRoute(route)
  }

  const handleThemeToggle = () => {
    const newMode = !isDarkMode
    setIsDarkMode(newMode)
    localStorage.setItem('darkMode', JSON.stringify(newMode))
  }

  const renderCurrentPage = () => {
    switch (currentRoute) {
      case 'admin':
        return <AdminPanel onNavigate={handleNavigate} isDarkMode={isDarkMode} />
      default:
        return <Home onNavigate={handleNavigate} isDarkMode={isDarkMode} onThemeToggle={handleThemeToggle} />
    }
  }

  return (
    <div className="App">
      {renderCurrentPage()}
    </div>
  )
}

export default App
