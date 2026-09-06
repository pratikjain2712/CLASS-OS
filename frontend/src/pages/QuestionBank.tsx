import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Library, Search } from 'lucide-react'
import type { Question } from '@/types'
import { clsx } from 'clsx'

const TYPES = ['', 'MCQ', 'VSA', 'SA', 'LA', 'Numerical']
const DIFFS = ['', 'Easy', 'Medium', 'Hard']

export default function QuestionBank() {
  const [qType, setQType] = useState('')
  const [diff, setDiff] = useState('')
  const [search, setSearch] = useState('')

  const { data: questions = [], isLoading } = useQuery<Question[]>({
    queryKey: ['questions', qType, diff],
    queryFn: () =>
      api.get('/questions', {
        params: {
          ...(qType ? { question_type: qType } : {}),
          ...(diff ? { difficulty: diff } : {}),
        },
      }).then((r) => r.data),
  })

  const filtered = questions.filter((q) =>
    !search || q.question_text.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-xl font-heading font-700 text-navy">Question Bank</h1>
        <p className="text-slate-500 text-sm mt-0.5">Browse approved questions available for paper generation.</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            className="input pl-8 w-64"
            placeholder="Search questions…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select className="select w-36" value={qType} onChange={(e) => setQType(e.target.value)}>
          {TYPES.map((t) => <option key={t} value={t}>{t || 'All types'}</option>)}
        </select>
        <select className="select w-36" value={diff} onChange={(e) => setDiff(e.target.value)}>
          {DIFFS.map((d) => <option key={d} value={d}>{d || 'All difficulties'}</option>)}
        </select>
      </div>

      {isLoading && <div className="text-slate-400 text-sm">Loading…</div>}

      {!isLoading && filtered.length === 0 && (
        <div className="card p-10 text-center">
          <Library size={32} className="text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 text-sm">No questions found.</p>
        </div>
      )}

      <div className="card divide-y divide-slate-100">
        {filtered.map((q) => (
          <div key={q.id} className="px-5 py-4">
            <div className="flex items-start justify-between gap-4">
              <p className="text-sm text-slate-800 flex-1">{q.question_text}</p>
              <div className="flex items-center gap-2 shrink-0">
                <span className={clsx(
                  'text-xs px-1.5 py-0.5 rounded font-medium',
                  q.difficulty === 'Easy' ? 'badge-easy' :
                  q.difficulty === 'Medium' ? 'badge-medium' : 'badge-hard'
                )}>
                  {q.difficulty}
                </span>
                <span className="text-xs text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">{q.question_type}</span>
                <span className="text-xs text-slate-400">{q.marks}M</span>
                <span className="text-xs text-slate-300">×{q.usage_count}</span>
              </div>
            </div>
            {q.question_type === 'MCQ' && q.options && (
              <div className="mt-2 grid grid-cols-2 gap-1">
                {q.options.map((opt) => (
                  <div key={opt.key} className={clsx(
                    'text-xs px-2 py-1 rounded border',
                    opt.key === q.answer ? 'border-green-200 bg-green-50 text-green-700' : 'border-slate-100 text-slate-500'
                  )}>
                    ({opt.key}) {opt.text}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
