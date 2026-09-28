import { useState } from 'react'

import { ApiError, login } from '../api'
import FieldError from './FieldError'

export default function LoginForm({ onLoggedIn, onGoToRegister }) {
  const [values, setValues] = useState({ username: '', password: '' })
  const [errors, setErrors] = useState(null)
  const [busy, setBusy] = useState(false)

  const update = (field) => (event) =>
    setValues((current) => ({ ...current, [field]: event.target.value }))

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setErrors(null)
    try {
      const user = await login(values)
      onLoggedIn(user)
    } catch (error) {
      if (!(error instanceof ApiError)) throw error
      setErrors(error)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit} noValidate>
      <h2>Welcome back</h2>
      <FieldError messages={errors?.general} />

      <label>
        Username
        <input value={values.username} onChange={update('username')} autoComplete="username" required />
      </label>
      <FieldError messages={errors?.for('username')} />

      <label>
        Password
        <input
          type="password"
          value={values.password}
          onChange={update('password')}
          autoComplete="current-password"
          required
        />
      </label>
      <FieldError messages={errors?.for('password')} />

      <button type="submit" disabled={busy}>
        {busy ? 'Logging in…' : 'Log in'}
      </button>

      <p className="switch">
        No account yet?{' '}
        <button type="button" className="link" onClick={onGoToRegister}>
          Register
        </button>
      </p>
    </form>
  )
}
