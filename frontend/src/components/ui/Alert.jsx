export default function Alert({ type = 'error', message }) {
  if (!message) return null
  const styles = {
    error: 'bg-red-50 text-red-700',
    success: 'bg-green-50 text-green-700',
    info: 'bg-brand-50 text-brand-800',
  }
  return (
    <div className={`mb-4 rounded-lg px-4 py-3 text-sm ${styles[type]}`}>{message}</div>
  )
}
