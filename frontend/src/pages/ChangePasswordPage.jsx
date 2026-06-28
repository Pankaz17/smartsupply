import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { changePassword } from '../api/auth'
import PageHeader from '../components/layout/PageHeader'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'

export default function ChangePasswordPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (form.newPassword.length < 8) {
      setError('New password must be at least 8 characters.')
      return
    }
    if (form.newPassword !== form.confirmPassword) {
      setError('New password and confirmation do not match.')
      return
    }

    setSubmitting(true)
    try {
      await changePassword(form.currentPassword, form.newPassword)
      setSuccess('Password updated successfully.')
      setForm({ currentPassword: '', newPassword: '', confirmPassword: '' })
      setTimeout(() => navigate('/'), 2000)
    } catch (err) {
      const data = err.response?.data
      setError(
        data?.current_password?.[0]
        || data?.new_password?.[0]
        || data?.detail
        || 'Failed to change password.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Change Password"
        subtitle="Update your account password."
      />

      <Alert type="error" message={error} />
      <Alert type="success" message={success} />

      <form
        onSubmit={handleSubmit}
        className="max-w-md space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <Input
          id="current-password"
          label="Current Password"
          type="password"
          required
          autoComplete="current-password"
          value={form.currentPassword}
          onChange={(e) => setForm({ ...form, currentPassword: e.target.value })}
        />
        <Input
          id="new-password"
          label="New Password"
          type="password"
          required
          autoComplete="new-password"
          minLength={8}
          value={form.newPassword}
          onChange={(e) => setForm({ ...form, newPassword: e.target.value })}
        />
        <Input
          id="confirm-password"
          label="Confirm New Password"
          type="password"
          required
          autoComplete="new-password"
          minLength={8}
          value={form.confirmPassword}
          onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
        />
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Updating...' : 'Update Password'}
        </Button>
      </form>
    </div>
  )
}
