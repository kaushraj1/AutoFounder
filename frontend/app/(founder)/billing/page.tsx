'use client'

import { Zap, CreditCard, TrendingUp, Package } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

const PLANS = [
  {
    name: 'Starter',
    price: '₹999',
    period: '/month',
    features: ['5 runs/month', '500 invoices', '1 team member', 'Email support'],
    current: false,
  },
  {
    name: 'Growth',
    price: '₹2,999',
    period: '/month',
    features: ['25 runs/month', 'Unlimited invoices', '5 team members', 'Priority support', 'HITL gates'],
    current: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    features: ['Unlimited runs', 'White-label', 'Dedicated infra', 'SLA', 'Custom integrations'],
    current: false,
  },
]

export default function BillingPage() {
  return (
    <div className="flex flex-col">
      <Header title="Billing" />
      <div className="flex-1 space-y-6 p-6">
        {/* Current plan */}
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-primary" />
                  Growth Plan
                </CardTitle>
                <CardDescription className="mt-1">
                  Your next billing date is July 14, 2026.
                </CardDescription>
              </div>
              <Badge variant="info" className="text-sm">Current</Badge>
            </div>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <div>
              <span className="text-3xl font-bold">₹2,999</span>
              <span className="text-muted-foreground">/month</span>
            </div>
            <Button variant="outline">Manage Subscription</Button>
          </CardContent>
        </Card>

        {/* Usage meters */}
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <Package className="h-4 w-4" />
                Runs This Month
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold">12</span>
                <span className="text-sm text-muted-foreground">/ 25</span>
              </div>
              <Progress value={48} />
              <p className="text-xs text-muted-foreground">13 remaining</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <TrendingUp className="h-4 w-4" />
                Tokens Used
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold">4.2M</span>
                <span className="text-sm text-muted-foreground">/ 10M</span>
              </div>
              <Progress value={42} />
              <p className="text-xs text-muted-foreground">~$0.85 spend today</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <CreditCard className="h-4 w-4" />
                Monthly Spend
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-end justify-between">
                <span className="text-2xl font-bold">₹1,840</span>
                <span className="text-sm text-muted-foreground">/ ₹2,999</span>
              </div>
              <Progress value={61} />
              <p className="text-xs text-muted-foreground">Resets July 14</p>
            </CardContent>
          </Card>
        </div>

        {/* Plan comparison */}
        <div>
          <h3 className="mb-4 text-sm font-semibold">Available Plans</h3>
          <div className="grid gap-4 sm:grid-cols-3">
            {PLANS.map((plan) => (
              <Card
                key={plan.name}
                className={plan.current ? 'border-primary ring-1 ring-primary/30' : ''}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-base">{plan.name}</CardTitle>
                    {plan.current && <Badge variant="info" className="text-xs">Current</Badge>}
                  </div>
                  <div className="mt-1">
                    <span className="text-2xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground">{plan.period}</span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ul className="space-y-1.5">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <Button
                    className="w-full"
                    variant={plan.current ? 'secondary' : 'default'}
                    disabled={plan.current}
                  >
                    {plan.current ? 'Current Plan' : plan.price === 'Custom' ? 'Contact Sales' : 'Upgrade'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Payment method */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Payment Method</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CreditCard className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Visa ending in 4242</p>
                <p className="text-xs text-muted-foreground">Expires 08/2027</p>
              </div>
            </div>
            <Button variant="outline" size="sm">Update</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
