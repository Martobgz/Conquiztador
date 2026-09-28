import { useState } from 'react'

import { ApiError, logout, updateProfile } from '../api'
import Avatar, { AVATAR_KEYS, avatarLabel } from './Avatar'
import FieldError from './FieldError'

export default function ProfileScreen({ user, onUserChanged, onLoggedOut }) {
  const [nickname, setNickname] = useState(user.profile?.nickname ?? '')
  const [avatarKey, setAvatarKey] = useState(user.profile?.avatar_key ?? AVATAR_KEYS[0])
  const [errors, setErrors] = useState(null)
  const [saved, setSaved] = useState(false)
  const [busy, setBusy] = useState(false)

  const dirty =
    nickname !== user.profile?.nickname || avatarKey !== user.profile?.avatar_key

  async function handleSave(event) {
    event.preventDefault()
    setBusy(true)
    setErrors(null)
    setSaved(false)
    try {
      const updated = await updateProfile({ nickname, avatar_key: avatarKey })
      onUserChanged(updated)
      setSaved(true)
    } catch (error) {
      if (!(error instanceof ApiError)) throw error
      setErrors(error)
    } finally {
      setBusy(false)
    }
  }

  async function handleLogout() {
    setBusy(true)
    try {
      await logout()
    } finally {
      setBusy(false)
      onLoggedOut()
    }
  }

  return (
    <section className="card profile">
      <header className="profile-header">
        <Avatar avatarKey={user.profile?.avatar_key} size={72} />
        <div>
          <h2>{user.profile?.nickname ?? user.username}</h2>
          <p className="muted">
            {user.username} · {user.email}
          </p>
        </div>
      </header>

      <form onSubmit={handleSave} noValidate>
        <FieldError messages={errors?.general} />

        <label>
          Nickname
          <input
            value={nickname}
            onChange={(event) => setNickname(event.target.value)}
            maxLength={30}
            required
          />
        </label>
        <FieldError messages={errors?.for('nickname')} />

        <fieldset className="avatars">
          <legend>Avatar</legend>
          <div className="avatar-grid">
            {AVATAR_KEYS.map((key) => (
              <label key={key} className={key === avatarKey ? 'avatar-option selected' : 'avatar-option'}>
                <input
                  type="radio"
                  name="avatar_key"
                  value={key}
                  checked={key === avatarKey}
                  onChange={() => setAvatarKey(key)}
                />
                <Avatar avatarKey={key} size={52} />
                <span>{avatarLabel(key)}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <FieldError messages={errors?.for('avatar_key')} />

        <div className="actions">
          <button type="submit" disabled={busy || !dirty}>
            {busy ? 'Saving…' : 'Save changes'}
          </button>
          <button type="button" className="secondary" onClick={handleLogout} disabled={busy}>
            Log out
          </button>
        </div>
        {saved && !dirty && <p className="saved">Profile saved.</p>}
      </form>
    </section>
  )
}
