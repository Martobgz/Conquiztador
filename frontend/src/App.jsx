import { useEffect, useState } from 'react'

import './App.css'
import { ensureCsrfToken, getCurrentUser } from './api'
import LoginForm from './components/LoginForm'
import ProfileScreen from './components/ProfileScreen'
import RegisterForm from './components/RegisterForm'

export default function App() {
  const [user, setUser] = useState(null)
  const [screen, setScreen] = useState('login')
  const [notice, setNotice] = useState(null)
  const [loading, setLoading] = useState(true)

  // On a reload, the session cookie is still there, so ask the API who we are.
  useEffect(() => {
    let cancelled = false

    async function restoreSession() {
      await ensureCsrfToken()
      try {
        const me = await getCurrentUser()
        if (!cancelled) setUser(me)
      } catch {
        // Not signed in: stay on the login screen.
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    restoreSession()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <h1>Conquiztador</h1>
        <p className="muted">Claim the map, one question at a time.</p>
      </header>

      <main>
        {notice && <p className="notice">{notice}</p>}

        {loading ? (
          <p className="loading">Loading…</p>
        ) : user ? (
          <ProfileScreen
            user={user}
            onUserChanged={setUser}
            onLoggedOut={() => {
              setUser(null)
              setNotice(null)
              setScreen('login')
            }}
          />
        ) : screen === 'register' ? (
          <RegisterForm
            onRegistered={(created) => {
              setNotice(`Account "${created.username}" created. Log in to continue.`)
              setScreen('login')
            }}
            onGoToLogin={() => {
              setNotice(null)
              setScreen('login')
            }}
          />
        ) : (
          <LoginForm
            onLoggedIn={(loggedIn) => {
              setNotice(null)
              setUser(loggedIn)
            }}
            onGoToRegister={() => {
              setNotice(null)
              setScreen('register')
            }}
          />
        )}
      </main>
    </div>
  )
}
