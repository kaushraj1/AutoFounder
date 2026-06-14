import { redirect } from 'next/navigation'
import { Shield, Users, Activity, DollarSign, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { MOCK_TENANTS } from '@/lib/mock-data'

// In a real implementation, check the user role from Supabase session server-side.
// For now, this is rendered for any authenticated user (role check is a TODO).
async function checkSuperAdmin() {
  // TODO: validate JWT claim role === 'superadmin' via Supabase cookies
  return true
}

export default async function AdminPage() {
  const isAdmin = await checkSuperAdmin()
  if (!isAdmin) redirect('/dashboard')

  const totalRuns = MOCK_TENANTS.reduce((sum, t) => sum + t.runs_count, 0)
  const totalTokens = MOCK_TENANTS.reduce((sum, t) => sum + t.tokens_used, 0)
  const activeCount = MOCK_TENANTS.filter((t) => t.status === 'active').length

  return (
    <div className="min-h-screen bg-background">
      {/* Admin header */}
      <header className="border-b bg-slate-900 px-6 py-3">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-yellow-400" />
          <span className="font-semibold text-white">Super Admin Console</span>
          <Badge className="ml-2 bg-yellow-400 text-slate-900">INTERNAL</Badge>
        </div>
      </header>

      <div className="space-y-6 p-6">
        <div>
          <h1 className="text-lg font-bold">System Overview</h1>
          <p className="text-sm text-muted-foreground">
            Platform health and tenant management — AutoFounder AI Ops.
          </p>
        </div>

        {/* Health cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <Users className="h-4 w-4" />
                Active Tenants
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{activeCount}</p>
              <p className="text-xs text-muted-foreground">{MOCK_TENANTS.length} total</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <Activity className="h-4 w-4" />
                Total Runs
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{totalRuns}</p>
              <p className="text-xs text-muted-foreground">All tenants, all time</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <DollarSign className="h-4 w-4" />
                Tokens Used
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{(totalTokens / 1_000_000).toFixed(1)}M</p>
              <p className="text-xs text-muted-foreground">
                ~${((totalTokens / 1_000_000) * 0.03).toFixed(2)} model cost
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <AlertTriangle className="h-4 w-4" />
                System Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-green-500" />
                <span className="text-sm font-medium text-green-700">All Systems OK</span>
              </div>
              <p className="mt-0.5 text-xs text-muted-foreground">API · DB · Redis · LLM</p>
            </CardContent>
          </Card>
        </div>

        {/* Tenant table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Tenant Registry</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-hidden rounded-b-xl">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Tenant</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Plan</th>
                    <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Runs</th>
                    <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Tokens</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Status</th>
                    <th className="px-4 py-2.5" />
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {MOCK_TENANTS.map((tenant) => (
                    <tr key={tenant.id} className="hover:bg-muted/30">
                      <td className="px-4 py-3 font-medium">{tenant.name}</td>
                      <td className="px-4 py-3">
                        <Badge variant="secondary">{tenant.plan}</Badge>
                      </td>
                      <td className="px-4 py-3 text-right text-muted-foreground">
                        {tenant.runs_count}
                      </td>
                      <td className="px-4 py-3 text-right text-muted-foreground">
                        {(tenant.tokens_used / 1000).toFixed(0)}k
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={tenant.status === 'active' ? 'success' : 'destructive'}>
                          {tenant.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <button className="text-xs text-primary hover:underline">Manage</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Model cost dashboard */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Model Cost Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-3">
              {[
                { model: 'GPT-4o', calls: 1_842, cost: 55.26 },
                { model: 'GPT-4o-mini', calls: 12_400, cost: 6.20 },
                { model: 'Claude 3.5 Sonnet', calls: 340, cost: 3.40 },
              ].map((m) => (
                <div key={m.model} className="rounded-lg border p-3">
                  <p className="text-sm font-medium">{m.model}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{m.calls.toLocaleString()} calls</p>
                  <p className="mt-0.5 text-lg font-bold">${m.cost.toFixed(2)}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
