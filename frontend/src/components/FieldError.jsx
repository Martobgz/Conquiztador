/** Validation messages for a single field, straight from the API envelope. */
export default function FieldError({ messages }) {
  if (!messages || messages.length === 0) return null

  return (
    <ul className="field-error" role="alert">
      {messages.map((message) => (
        <li key={message}>{message}</li>
      ))}
    </ul>
  )
}
