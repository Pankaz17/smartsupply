import Input from '../ui/Input'
import Select from '../ui/Select'

const RANGE_OPTIONS = [
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: '90d', label: 'Last 90 Days' },
  { value: 'custom', label: 'Custom Date Range' },
]

export default function DateRangeFilter({ value, onChange }) {
  const handleRangeChange = (e) => {
    const range = e.target.value
    onChange({
      ...value,
      mode: range === 'custom' ? 'custom' : 'preset',
      range: range === 'custom' ? value.range : range,
    })
  }

  return (
    <div className="mb-6 flex flex-wrap items-end gap-4 rounded-xl border border-slate-200 bg-white p-4">
      <div className="min-w-[180px]">
        <Select
          id="report-range"
          label="Date Range"
          options={RANGE_OPTIONS}
          value={value.mode === 'custom' ? 'custom' : value.range}
          onChange={handleRangeChange}
        />
      </div>
      {value.mode === 'custom' && (
        <>
          <div className="min-w-[160px]">
            <Input
              id="start-date"
              label="Start Date"
              type="date"
              value={value.startDate || ''}
              onChange={(e) => onChange({ ...value, startDate: e.target.value })}
            />
          </div>
          <div className="min-w-[160px]">
            <Input
              id="end-date"
              label="End Date"
              type="date"
              value={value.endDate || ''}
              onChange={(e) => onChange({ ...value, endDate: e.target.value })}
            />
          </div>
        </>
      )}
    </div>
  )
}

export const DEFAULT_DATE_RANGE = { mode: 'preset', range: '30d', startDate: '', endDate: '' }
