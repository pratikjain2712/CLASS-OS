import { useState, useRef } from 'react'
import { Upload, FileSpreadsheet, Download, CheckCircle, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'

type ImportResult = { imported: number; errors: string[] } | null

export default function AdminQuestions() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ImportResult>(null)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = (f: File | null) => {
    if (!f) return
    setFile(f)
    setResult(null)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files[0] ?? null)
  }

  const handleSubmit = async () => {
    if (!file) return
    setLoading(true)
    setResult(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await api.post('/admin/questions/bulk-import', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(data)
    } catch (err: any) {
      const detail = err?.response?.data?.detail ?? 'Upload failed. Check the file format.'
      setResult({ imported: 0, errors: [detail] })
    } finally {
      setLoading(false)
    }
  }

  const downloadTemplate = () => {
    // Build a minimal CSV the user can convert to xlsx
    const header = 'chapter_id,question_type,marks,difficulty,question_text,options_json,answer,solution,concept_tags,source_type,cognitive_level,language'
    const example = '<chapter-uuid>,MCQ,1,Easy,"What is 2+2?","[{""key"":""A"",""text"":""3""},{""key"":""B"",""text"":""4""}]",B,"2+2=4","Arithmetic",publisher_bank,Knowledge,en'
    const blob = new Blob([header + '\n' + example], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'question_import_template.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-xl font-heading font-700 text-navy">Bulk Question Import</h1>
        <p className="text-slate-500 text-sm mt-0.5">Upload an Excel (.xlsx) file to import questions into the bank.</p>
      </div>

      {/* Template download */}
      <div className="card p-4 mb-6 flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-700">Download template</p>
          <p className="text-xs text-slate-400 mt-0.5">CSV template with required columns and an example row</p>
        </div>
        <button onClick={downloadTemplate} className="btn-outline flex items-center gap-2 text-sm">
          <Download size={14} /> Template
        </button>
      </div>

      {/* Required columns info */}
      <div className="card p-4 mb-6 bg-blue-50 border border-blue-100">
        <p className="text-xs font-semibold text-blue-800 mb-1">Required Excel columns (row 1 = header)</p>
        <p className="text-xs text-blue-700 font-mono leading-relaxed">
          chapter_id · question_type · marks · difficulty · question_text · answer · source_type
        </p>
        <p className="text-xs text-blue-600 mt-1">
          Optional: options_json · solution · concept_tags · cognitive_level · language
        </p>
      </div>

      {/* Drop zone */}
      <div
        className={`card p-8 mb-4 border-2 border-dashed cursor-pointer transition-colors text-center ${
          dragOver ? 'border-navy bg-navy-50' : 'border-slate-200 hover:border-navy'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
        />
        <FileSpreadsheet size={32} className="text-slate-300 mx-auto mb-3" />
        {file ? (
          <p className="text-sm font-medium text-navy">{file.name}</p>
        ) : (
          <>
            <p className="text-sm font-medium text-slate-600">Drop your .xlsx file here</p>
            <p className="text-xs text-slate-400 mt-1">or click to browse</p>
          </>
        )}
      </div>

      <button
        onClick={handleSubmit}
        disabled={!file || loading}
        className="btn-primary w-full flex items-center justify-center gap-2"
      >
        <Upload size={16} />
        {loading ? 'Importing…' : 'Import Questions'}
      </button>

      {/* Result */}
      {result && (
        <div className="mt-6 card p-5">
          <div className="flex items-center gap-2 mb-3">
            {result.imported > 0 ? (
              <CheckCircle size={18} className="text-green-500" />
            ) : (
              <AlertCircle size={18} className="text-red-400" />
            )}
            <span className="font-medium text-slate-700">
              {result.imported} question{result.imported !== 1 ? 's' : ''} imported successfully
            </span>
          </div>
          {result.errors.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-red-600 mb-1">{result.errors.length} error(s):</p>
              <ul className="text-xs text-red-500 space-y-0.5 max-h-48 overflow-y-auto">
                {result.errors.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
