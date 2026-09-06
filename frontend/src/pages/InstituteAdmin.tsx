import { useAuth } from '@/hooks/useAuth'
import { Users, Building2, CreditCard } from 'lucide-react'

export default function InstituteAdmin() {
  const { user } = useAuth()

  if (!user || user.role === 'teacher') {
    return <div className="p-8 text-slate-400 text-sm">Access denied.</div>
  }

  return (
    <div className="p-8">
      <h1 className="text-xl font-heading font-700 text-navy mb-6">Institute Admin</h1>

      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Teachers', icon: Users, desc: 'Manage teacher accounts' },
          { label: 'Branches', icon: Building2, desc: 'Manage branches' },
          { label: 'Credits', icon: CreditCard, desc: 'View credit balance' },
        ].map(({ label, icon: Icon, desc }) => (
          <div key={label} className="card p-5 cursor-pointer hover:shadow-md transition-shadow">
            <div className="w-10 h-10 bg-navy-50 rounded-lg flex items-center justify-center mb-3">
              <Icon size={20} className="text-navy" />
            </div>
            <div className="font-heading font-700 text-navy text-sm">{label}</div>
            <div className="text-xs text-slate-400 mt-0.5">{desc}</div>
          </div>
        ))}
      </div>

      <div className="card p-6">
        <p className="text-sm text-slate-500">
          Full admin features — teacher management, bulk question import, subscription management — are coming in the next build.
        </p>
      </div>
    </div>
  )
}
