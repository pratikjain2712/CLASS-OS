import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { clsx } from 'clsx'
import { ChevronRight, ChevronLeft, Check, AlertTriangle } from 'lucide-react'
import type { Publisher, Book, Chapter, Template, GenerateRequest } from '@/types'

const BOARDS = ['CBSE', 'Maharashtra SSC']
const CLASSES = [8, 9, 10]
const SUBJECTS = ['Mathematics', 'Science', 'English', 'Hindi', 'Social Science', 'Sanskrit', 'IT']
const DIFFICULTIES = ['Easy', 'Medium', 'Hard', 'Mixed']

const STEPS = ['Setup', 'Chapters', 'Template', 'Mode', 'Generate']

type Step = 1 | 2 | 3 | 4 | 5

interface FormState {
  board: string
  class_: number | null
  subject: string
  publisher_id: string
  book_id: string
  chapter_ids: string[]
  template_id: string
  difficulty: string
  generation_mode: 'bank' | 'ai'
  section: string
  title: string
}

const init: FormState = {
  board: '',
  class_: null,
  subject: '',
  publisher_id: '',
  book_id: '',
  chapter_ids: [],
  template_id: '',
  difficulty: 'Mixed',
  generation_mode: 'bank',
  section: '',
  title: '',
}

export default function GeneratePaper() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>(1)
  const [form, setForm] = useState<FormState>(init)

  // ── Data fetching ─────────────────────────────────────────────────────────

  const { data: publishers = [] } = useQuery<Publisher[]>({
    queryKey: ['publishers'],
    queryFn: () => api.get('/publishers').then((r) => r.data),
  })

  const { data: books = [] } = useQuery<Book[]>({
    queryKey: ['books', form.publisher_id, form.class_, form.subject, form.board],
    queryFn: () =>
      api.get(`/publishers/${form.publisher_id}/books`, {
        params: { class: form.class_, subject: form.subject, board: form.board },
      }).then((r) => r.data),
    enabled: !!form.publisher_id && !!form.class_ && !!form.subject,
  })

  const { data: chapters = [] } = useQuery<Chapter[]>({
    queryKey: ['chapters', form.book_id],
    queryFn: () => api.get(`/publishers/books/${form.book_id}/chapters`).then((r) => r.data),
    enabled: !!form.book_id,
  })

  const { data: templates = [] } = useQuery<Template[]>({
    queryKey: ['templates'],
    queryFn: () => api.get('/templates').then((r) => r.data),
  })

  const selectedTemplate = templates.find((t) => t.id === form.template_id)

  // ── Generation ────────────────────────────────────────────────────────────

  const generateMutation = useMutation({
    mutationFn: (req: GenerateRequest) => api.post('/papers/generate', req).then((r) => r.data),
    onSuccess: (data) => navigate(`/papers/${data.id}/review`),
  })

  const handleGenerate = () => {
    if (!form.publisher_id || !form.template_id || form.chapter_ids.length === 0) return
    generateMutation.mutate({
      title: form.title || `${form.subject} — Class ${form.class_} ${form.section}`.trim(),
      class_: form.class_!,
      section: form.section || undefined,
      subject: form.subject,
      board: form.board,
      publisher_id: form.publisher_id,
      template_id: form.template_id,
      chapter_ids: form.chapter_ids,
      difficulty: form.difficulty,
      generation_mode: form.generation_mode,
    })
    setStep(5)
  }

  // ── Chapter toggle ────────────────────────────────────────────────────────

  const toggleChapter = (id: string) =>
    setForm((f) => ({
      ...f,
      chapter_ids: f.chapter_ids.includes(id)
        ? f.chapter_ids.filter((c) => c !== id)
        : [...f.chapter_ids, id],
    }))

  const toggleAll = () =>
    setForm((f) => ({
      ...f,
      chapter_ids: f.chapter_ids.length === chapters.length ? [] : chapters.map((c) => c.id),
    }))

  // ── Step validity ─────────────────────────────────────────────────────────

  const canNext = (): boolean => {
    if (step === 1) return !!(form.board && form.class_ && form.subject && form.publisher_id && form.book_id)
    if (step === 2) return form.chapter_ids.length > 0
    if (step === 3) return !!form.template_id
    if (step === 4) return !!form.difficulty
    return false
  }

  return (
    <div className="p-8 max-w-3xl">
      {/* Page header */}
      <h1 className="text-xl font-heading font-700 text-navy mb-2">Generate Question Paper</h1>
      <p className="text-slate-500 text-sm mb-6">Complete the steps below to create your paper.</p>

      {/* Step indicators */}
      <div className="flex items-center gap-2 mb-8">
        {STEPS.map((label, i) => {
          const n = (i + 1) as Step
          const done = n < step
          const active = n === step
          return (
            <div key={label} className="flex items-center gap-2">
              <div className={clsx(
                'w-7 h-7 rounded-full flex items-center justify-center text-xs font-heading font-700 transition-colors',
                done ? 'bg-green text-white' :
                active ? 'bg-amber text-white' :
                'bg-slate-200 text-slate-400'
              )}>
                {done ? <Check size={12} /> : n}
              </div>
              <span className={clsx(
                'text-xs font-medium hidden sm:block',
                active ? 'text-navy' : done ? 'text-green' : 'text-slate-400'
              )}>{label}</span>
              {i < STEPS.length - 1 && <div className="w-6 h-px bg-slate-200 mx-1" />}
            </div>
          )
        })}
      </div>

      {/* Step 1: Board / Class / Subject / Publisher */}
      {step === 1 && (
        <div className="card p-6 space-y-4">
          <h2 className="font-heading font-700 text-navy">Step 1: Setup</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Board</label>
              <select className="select" value={form.board} onChange={(e) => setForm((f) => ({ ...f, board: e.target.value, publisher_id: '', book_id: '', chapter_ids: [] }))}>
                <option value="">Select board</option>
                {BOARDS.map((b) => <option key={b}>{b}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Class</label>
              <select className="select" value={form.class_ ?? ''} onChange={(e) => setForm((f) => ({ ...f, class_: Number(e.target.value), publisher_id: '', book_id: '', chapter_ids: [] }))}>
                <option value="">Select class</option>
                {CLASSES.map((c) => <option key={c} value={c}>Class {c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Subject</label>
              <select className="select" value={form.subject} onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value, publisher_id: '', book_id: '', chapter_ids: [] }))}>
                <option value="">Select subject</option>
                {SUBJECTS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Section <span className="text-slate-400">(optional)</span></label>
              <input className="input" value={form.section} onChange={(e) => setForm((f) => ({ ...f, section: e.target.value }))} placeholder="A, B, C…" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Publisher</label>
              <select className="select" value={form.publisher_id} onChange={(e) => setForm((f) => ({ ...f, publisher_id: e.target.value, book_id: '', chapter_ids: [] }))} disabled={!form.subject}>
                <option value="">Select publisher</option>
                {publishers.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Book</label>
              <select className="select" value={form.book_id} onChange={(e) => setForm((f) => ({ ...f, book_id: e.target.value, chapter_ids: [] }))} disabled={!form.publisher_id || books.length === 0}>
                <option value="">Select book</option>
                {books.map((b) => <option key={b.id} value={b.id}>{b.title}</option>)}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Chapters */}
      {step === 2 && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-heading font-700 text-navy">Step 2: Select Chapters</h2>
            <button className="text-xs text-amber hover:underline" onClick={toggleAll}>
              {form.chapter_ids.length === chapters.length ? 'Deselect all' : 'Select all'}
            </button>
          </div>
          {chapters.length === 0 ? (
            <p className="text-slate-400 text-sm py-4 text-center">No chapters found for this book.</p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {chapters.map((ch) => (
                <label key={ch.id} className={clsx(
                  'flex items-center gap-3 p-3 rounded-lg cursor-pointer border transition-colors',
                  form.chapter_ids.includes(ch.id)
                    ? 'border-amber bg-amber-50'
                    : 'border-slate-200 hover:border-slate-300'
                )}>
                  <input
                    type="checkbox"
                    checked={form.chapter_ids.includes(ch.id)}
                    onChange={() => toggleChapter(ch.id)}
                    className="accent-amber"
                  />
                  <div className="flex-1">
                    <span className="text-sm font-medium text-navy">
                      Ch {ch.chapter_number}. {ch.chapter_name}
                    </span>
                    {ch.processing_status !== 'done' && (
                      <span className="ml-2 text-xs text-slate-400">({ch.processing_status})</span>
                    )}
                  </div>
                </label>
              ))}
            </div>
          )}
          <div className="mt-3 text-xs text-slate-400">
            {form.chapter_ids.length} of {chapters.length} selected
          </div>
        </div>
      )}

      {/* Step 3: Template */}
      {step === 3 && (
        <div className="card p-6">
          <h2 className="font-heading font-700 text-navy mb-4">Step 3: Pick Template</h2>
          <div className="grid grid-cols-2 gap-3">
            {templates.map((t) => (
              <button
                key={t.id}
                onClick={() => setForm((f) => ({ ...f, template_id: t.id }))}
                className={clsx(
                  'p-4 rounded-xl border-2 text-left transition-colors',
                  form.template_id === t.id
                    ? 'border-amber bg-amber-50'
                    : 'border-slate-200 hover:border-slate-300'
                )}
              >
                <div className="text-2xl font-heading font-800 text-navy">{t.total_marks}M</div>
                <div className="text-sm text-slate-500 mt-0.5">{t.name}</div>
                <div className="mt-2 space-y-0.5">
                  {t.sections.map((s) => (
                    <div key={s.id} className="text-xs text-slate-400">
                      Sec {s.section_label}: {s.question_count}×{s.question_type} ({s.marks_per_question}M each)
                    </div>
                  ))}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 4: Mode + Difficulty */}
      {step === 4 && (
        <div className="card p-6 space-y-6">
          <h2 className="font-heading font-700 text-navy">Step 4: Mode &amp; Difficulty</h2>

          <div>
            <label className="text-xs font-medium text-slate-500 mb-2 block">Generation Mode</label>
            <div className="grid grid-cols-2 gap-3">
              {(['bank', 'ai'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setForm((f) => ({ ...f, generation_mode: mode }))}
                  className={clsx(
                    'p-4 rounded-xl border-2 text-left transition-colors',
                    form.generation_mode === mode ? 'border-amber bg-amber-50' : 'border-slate-200 hover:border-slate-300'
                  )}
                >
                  <div className="font-heading font-700 text-navy text-sm capitalize">{mode === 'bank' ? '📚 Bank Mode' : '✨ AI Generated'}</div>
                  <div className="text-xs text-slate-500 mt-1">
                    {mode === 'bank' ? 'Instant — from stored question bank' : 'Fresh AI questions — costs credits'}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-500 mb-2 block">Difficulty</label>
            <div className="flex flex-wrap gap-2">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d}
                  onClick={() => setForm((f) => ({ ...f, difficulty: d }))}
                  className={clsx(
                    'px-4 py-2 rounded-lg text-sm font-medium border-2 transition-colors',
                    form.difficulty === d ? 'border-amber bg-amber-50 text-amber' : 'border-slate-200 text-slate-600 hover:border-slate-300'
                  )}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          {selectedTemplate && (
            <div className="bg-slate-50 rounded-lg p-4 text-sm">
              <div className="font-medium text-navy mb-1">Summary</div>
              <div className="text-slate-500 text-xs space-y-0.5">
                <div>{form.chapter_ids.length} chapter(s) · {selectedTemplate.total_marks} marks · {form.difficulty} · {form.generation_mode === 'bank' ? 'Bank mode' : 'AI mode'}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Step 5: Generating */}
      {step === 5 && (
        <div className="card p-8 text-center">
          {generateMutation.isPending && (
            <>
              <div className="w-12 h-12 border-4 border-amber border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <h2 className="font-heading font-700 text-navy text-lg">Generating your paper…</h2>
              <p className="text-slate-500 text-sm mt-1">Selecting questions from the bank</p>
            </>
          )}
          {generateMutation.isError && (
            <>
              <AlertTriangle size={40} className="text-red-400 mx-auto mb-4" />
              <h2 className="font-heading font-700 text-navy text-lg">Generation failed</h2>
              <p className="text-slate-500 text-sm mt-1">
                {(generateMutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Please try again'}
              </p>
              <button className="btn-secondary mt-4" onClick={() => setStep(4)}>Go Back</button>
            </>
          )}
        </div>
      )}

      {/* Navigation */}
      {step < 5 && (
        <div className="flex justify-between mt-5">
          <button
            className="btn-secondary flex items-center gap-2"
            onClick={() => setStep((s) => Math.max(1, s - 1) as Step)}
            disabled={step === 1}
          >
            <ChevronLeft size={15} /> Back
          </button>
          {step < 4 ? (
            <button
              className="btn-primary flex items-center gap-2"
              onClick={() => setStep((s) => (s + 1) as Step)}
              disabled={!canNext()}
            >
              Next <ChevronRight size={15} />
            </button>
          ) : (
            <button
              className="btn-primary flex items-center gap-2"
              onClick={handleGenerate}
              disabled={!canNext()}
            >
              <ChevronRight size={15} /> Generate
            </button>
          )}
        </div>
      )}
    </div>
  )
}
