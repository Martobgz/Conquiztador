import { useState } from 'react'

import { ApiError, register } from '../api'
import FieldError from './FieldError'

const EMPTY = {
  username: '',
  email: '',
  nickname: '',
  password: '',
  password_confirm: '',
}

export default function RegisterForm({ onRegistered, onGoToLogin }) {
  const [values, setValues] = useState(EMPTY)
  const [errors, setErrors] = useState(null)
  const [busy, setBusy] = useState(false)

  const update = (field) => (event) =>
    setValues((current) => ({ ...current, [field]: event.target.value }))

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setErrors(null)
    try {
      const user = await register(values)
      onRegistered(user)
    } catch (error) {
      if (!(error instanceof ApiError)) throw error
      setErrors(error)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card" onSubmit={handleSubmit} noValidate>
      <h2>Create an account</h2>
      <FieldError messages={errors?.general} />

      <label>
        Username
        <input value={values.username} onChange={update('username')} autoComplete="username" required />
      </label>
      <FieldError messages={errors?.for('username')} />

      <label>
        Email
        <input type="email" value={values.email} onChange={update('email')} autoComplete="email" required />
      </label>
      <FieldError messages={errors?.for('email')} />

      <label>
        Nickname
        <input value={values.nickname} onChange={update('nickname')} maxLength={30} required />
      </label>
      <FieldError messages={errors?.for('nickname')} />

      <label>
        Password
        <input
          type="password"
          value={values.password}
          onChange={update('password')}
          autoComplete="new-password"
          required
        />
      </label>
      <FieldError messages={errors?.for('password')} />

      <label>
        Confirm password
        <input
          type="password"
          value={values.password_confirm}
          onChange={update('password_confirm')}
          autoComplete="new-password"
          required
        />
      </label>
      <FieldError messages={errors?.for('password_confirm')} />

      <button type="submit" disabled={busy}>
        {busy ? 'Creating account…' : 'Register'}
      </button>

      <p className="switch">
        Already have an account?{' '}
        <button type="button" className="link" onClick={onGoToLogin}>
          Log in
        </button>
      </p>
    </form>
  )
}
