import { useState } from 'react'
import Button from '../ui/Button'
import { exportReport } from '../../api/reports'

export default function ExportButtons({ reportKey, dateRange }) {
  const [exporting, setExporting] = useState(null)
  const [error, setError] = useState('')

  const handleExport = async (format) => {
    setExporting(format)
    setError('')
    try {
      await exportReport(reportKey, format, dateRange)
    } catch {
      setError('Export failed. Please try again.')
    } finally {
      setExporting(null)
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        variant="secondary"
        size="sm"
        disabled={!!exporting}
        onClick={() => handleExport('csv')}
      >
        {exporting === 'csv' ? 'Exporting...' : 'Export CSV'}
      </Button>
      <Button
        variant="secondary"
        size="sm"
        disabled={!!exporting}
        onClick={() => handleExport('xlsx')}
      >
        {exporting === 'xlsx' ? 'Exporting...' : 'Export Excel'}
      </Button>
      {error && <span className="text-sm text-red-600">{error}</span>}
    </div>
  )
}
