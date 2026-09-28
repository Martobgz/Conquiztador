export const AVATAR_KEYS = ['knight-1', 'knight-2', 'knight-3', 'knight-4']

const CRESTS = {
  'knight-1': { body: '#b23a48', trim: '#f2c14e', label: 'Crimson' },
  'knight-2': { body: '#2f6690', trim: '#a9d6e5', label: 'Azure' },
  'knight-3': { body: '#3a7d44', trim: '#d8f3a3', label: 'Verdant' },
  'knight-4': { body: '#5f4b8b', trim: '#e0c3fc', label: 'Violet' },
}

export function avatarLabel(avatarKey) {
  return CRESTS[avatarKey]?.label ?? avatarKey
}

/** A small heraldic shield standing in for the knight artwork. */
export default function Avatar({ avatarKey, size = 64 }) {
  const crest = CRESTS[avatarKey] ?? CRESTS['knight-1']

  return (
    <svg
      viewBox="0 0 48 56"
      width={size}
      height={(size * 56) / 48}
      role="img"
      aria-label={`${crest.label} knight crest`}
      className="avatar"
    >
      <path
        d="M24 2 44 8v22c0 12-9 20-20 24C13 50 4 42 4 30V8L24 2Z"
        fill={crest.body}
        stroke={crest.trim}
        strokeWidth="2.5"
      />
      <path d="M24 2 24 54" stroke={crest.trim} strokeWidth="1.5" opacity="0.5" />
      <path d="M4 22h40" stroke={crest.trim} strokeWidth="1.5" opacity="0.5" />
      <circle cx="24" cy="22" r="6" fill={crest.trim} />
    </svg>
  )
}
