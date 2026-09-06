import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { AlertTriangle, RefreshCw, CheckCircle, ArrowLeft } from 'lucide-react'
import type { PaperWithQuestions } from '@/types'
import { clsx } from 'clsx'
import { useState } from 'react'

export default function PaperReview() {
  const { paperId } = useParams<{ paperId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [swappingPqId, setSwappingPqId] = useState<string | null>(null)

  const { data: paper, isLoading } = useQuery<PaperWithQuestions>({
    queryKey: ['paper', paperId],
    queryFn: () => api.get(`/papers/${paperId}`).then((r) => r.data),
  })

  const finalizeMutation = useMutation({
    mutationFn: () => api.post(`/papers/${paperId}/finalize`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['paper', paperId] }),
  })

  if (isLoading) return <div className="p-8 text-slate-400 text-sm">Loading paper…</div>
  if (!paper) return <div className="p-8 text-red-400 text-sm">Paper not found.</div>

  // Group by section
  const sections = [...new Set(paper.paper_questions.map((pq) => pq.section_label))]

  const warningCount = paper.paper_questions.filter((pq) => pq.question.already_asked).length
  const shortfallCount = paper.shortfall?.length ?? 0

  return (
    <div className="p-8 max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <button onClick={() => navigate('/papers')} className="flex items-center gap-1.5 text-slate-400 hover:text-slate-600 text-sm mb-2 transition-colors">
            <ArrowLeft size={14} /> Back to papers
          </button>
          <h1 className="text-xl font-heading font-700 text-navy">{paper.title}</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            Class {paper.class_}{paper.section ? ` ${paper.section}` : ''} · {paper.subject} · {paper.board} · {paper.total_marks} marks
          </p>
        </div>
        <div className="flex items-center gap-2">
          {paper.status !== 'final' && (
            <button
              className="btn-primary flex items-center gap-1.5"
              onClick={() => finalizeMutation.mutate()}
              disabled={finalizeMutation.isPending}
            >
              <CheckCircle size={14} />
              {finalizeMutation.isPending ? 'Finalising…' : 'Finalise Paper'}
            </button>
          )}
          {paper.status === 'final' && (
            <span className="flex items-center gap-1.5 text-green text-sm font-medium">
              <CheckCircle size={14} /> Finalised
            </span>
          )}
        </div>
      </div>

      {/* Alerts */}
      {warningCount > 0 && (
        <div className="flex items-center gap-2 bg-orange-50 border border-orange-200 text-orange-700 text-sm px-4 py-3 rounded-lg mb-4">
          <AlertTriangle size={15} className="shrink-0" />
          <span>{warningCount} question{warningCount > 1 ? 's' : ''} may have been asked to this batch in the last 6 months.</span>
        </div>
      )}
      {shortfallCount > 0 && (
        <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 text-amber-700 text-sm px-4 py-3 rounded-lg mb-4">
          <AlertTriangle size={15} className="shrink-0 mt-0.5" />
          <div>
            <strong>Shortfall in {shortfallCount} section(s):</strong> not enough questions in the bank.
            {paper.shortfall.map((s) => (
              <div key={s.section_label} className="text-xs mt-0.5">
                Section {s.section_label}: requested {s.requested}, available {s.available}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Questions by section */}
      {sections.map((section) => {
        const pqs = paper.paper_questions.filter((pq) => pq.section_label === section)
        const sectionMarks = pqs.reduce((sum, pq) => sum + pq.marks, 0)
        return (
          <div key={section} className="card mb-4">
            <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between">
              <h3 className="font-heading font-700 text-navy text-sm">
                Section {section}
              </h3>
              <span className="text-xs text-slate-400">{pqs.length} questions · {sectionMarks} marks</span>
            </div>
            <div className="divide-y divide-slate-100">
              {pqs.map((pq) => (
                <div key={pq.id} className={clsx('p-5', pq.question.already_asked && 'bg-orange-50/40')}>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center text-xs font-medium text-slate-500 shrink-0 mt-0.5">
                      {pq.question_order}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm text-slate-800 leading-relaxed">{pq.question.question_text}</p>
                        <div className="flex items-center gap-1.5 shrink-0">
                          {pq.question.already_asked && (
                            <span className="badge-warned whitespace-nowrap">Already asked</span>
                          )}
                          <span className={clsx(
                            'text-xs px-1.5 py-0.5 rounded font-medium',
                            pq.question.difficulty === 'Easy' ? 'badge-easy' :
                            pq.question.difficulty === 'Medium' ? 'badge-medium' : 'badge-hard'
                          )}>
                            {pq.question.difficulty}
                          </span>
                          <span className="text-xs text-slate-400">{pq.marks}M</span>
                        </div>
                      </div>

                      {pq.question.question_type === 'MCQ' && pq.question.options && (
                        <div className="mt-2 grid grid-cols-2 gap-1">
                          {pq.question.options.map((opt) => (
                            <div key={opt.key} className={clsx(
                              'text-xs px-2 py-1 rounded border',
                              opt.key === pq.question.answer ? 'border-green-200 bg-green-50 text-green-700' : 'border-slate-100 text-slate-500'
                            )}>
                              ({opt.key}) {opt.text}
                            </div>
                          ))}
                        </div>
                      )}

                      {pq.question.question_type !== 'MCQ' && (
                        <div className="mt-2 text-xs text-slate-400 italic">
                          Answer: {pq.question.answer}
                        </div>
                      )}

                      {swappingPqId !== pq.id && (
                        <button
                          className="mt-2 text-xs text-amber hover:underline flex items-center gap-1"
                          onClick={() => setSwappingPqId(swappingPqId === pq.id ? null : pq.id)}
                        >
                          <RefreshCw size={11} /> Swap question
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
