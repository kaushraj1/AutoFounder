/**
 * Realistic mock data used as fallback / placeholder while the backend
 * returns real data. All shapes match the TypeScript types in lib/types.ts.
 */

import type {
  ArchitectureOutput,
  DeployOutput,
  FileNode,
  MarketingOutput,
  ReviewOutput,
  Run,
  StrategyOutput,
  TenantRow,
} from './types'

export const MOCK_RUNS: Run[] = [
  {
    id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    pillar: 'completed',
    status: 'completed',
    created_at: new Date(Date.now() - 3 * 86400_000).toISOString(),
    idea_text: 'AI-powered invoice automation for Indian SMBs — auto-reconcile GST, send reminders, integrate with Tally.',
  },
  {
    id: 'b2c3d4e5-f6a7-8901-bcde-fa2345678901',
    pillar: 'engineering',
    status: 'running',
    created_at: new Date(Date.now() - 6 * 3600_000).toISOString(),
    idea_text: 'Real-time crop disease detection via drone imagery + WhatsApp alerts for farmers.',
  },
  {
    id: 'c3d4e5f6-a7b8-9012-cdef-ab3456789012',
    pillar: 'strategy',
    status: 'paused',
    created_at: new Date(Date.now() - 1 * 3600_000).toISOString(),
    idea_text: 'B2B SaaS for hostel & PG management — tenant onboarding, rent collection, maintenance requests.',
  },
  {
    id: 'd4e5f6a7-b8c9-0123-defa-bc4567890123',
    pillar: 'review',
    status: 'queued',
    created_at: new Date(Date.now() - 15 * 60_000).toISOString(),
    idea_text: 'Carbon credit marketplace connecting Indian villages to ESG buyers.',
  },
  {
    id: 'e5f6a7b8-c9d0-1234-efab-cd5678901234',
    pillar: 'devops',
    status: 'failed',
    created_at: new Date(Date.now() - 2 * 86400_000).toISOString(),
    idea_text: 'SaaS for small CA firms — client document vault, deadline tracker, e-sign integration.',
  },
]

export const MOCK_STRATEGY: StrategyOutput = {
  viability_score: 82,
  recommendation: 'proceed',
  lean_canvas: [
    { title: 'Problem', content: ['GST reconciliation is manual and error-prone', 'Tally integrations cost ₹50k+/year', 'Late payments cost SMBs 15% revenue'] },
    { title: 'Solution', content: ['AI auto-matches invoices to GSTIN data', 'One-click Tally sync via REST API', 'WhatsApp payment reminders with UPI deep-links'] },
    { title: 'Unique Value Proposition', content: ['First AI-native GST invoice tool built for Indian SMBs', 'Save 8 hours/week per accountant'] },
    { title: 'Unfair Advantage', content: ['Proprietary GST pattern model trained on 2M+ invoices', 'Founding team ex-Zoho + IIT Bombay'] },
    { title: 'Customer Segments', content: ['SMBs with 10–200 employees in Tier-1/2 cities', 'CA firms serving multiple SMB clients'] },
    { title: 'Key Metrics', content: ['MRR', 'Invoices processed per month', 'GST error rate reduction'] },
    { title: 'Channels', content: ['Google Ads targeting CA professionals', 'Partnership with CA Institute chapters', 'Product Hunt + LinkedIn organic'] },
    { title: 'Cost Structure', content: ['AWS infra ~₹2L/month at 500 customers', 'LLM costs ~₹0.40/invoice', '3 engineers + 1 sales'] },
    { title: 'Revenue Streams', content: ['₹999/month Starter (up to 500 invoices)', '₹2,999/month Growth (unlimited + Tally)', '₹9,999/month Enterprise (white-label)'] },
  ],
  personas: [
    {
      name: 'Rajesh Mehta',
      role: 'Owner, 45-person textile export firm',
      pain_points: ['Spends 3 days/month on GST filing', 'Mismatch penalties cost ₹80k last year', 'Accountant resigned; can\'t find replacement'],
      goals: ['Automate reconciliation', 'Never miss GSTR-2B deadline', 'Single dashboard for all receivables'],
    },
    {
      name: 'Priya Desai',
      role: 'Senior CA, 150-client practice',
      pain_points: ['Client document chaos on WhatsApp', 'Manual data entry into Tally for each client', 'Deadline pressure during filing season'],
      goals: ['Reduce per-client time from 6h to 1h', 'Upsell advisory services freed from compliance grunt work'],
    },
  ],
}

export const MOCK_ARCHITECTURE: ArchitectureOutput = {
  diagram_mermaid: `graph TD
    A[React Frontend] -->|HTTPS| B[FastAPI Gateway]
    B --> C[Auth Service<br/>Supabase]
    B --> D[Invoice AI<br/>LangGraph]
    B --> E[Tally Connector<br/>REST Bridge]
    D --> F[(PostgreSQL<br/>+ pgvector)]
    D --> G[Redis Queue]
    G --> H[Worker Pods<br/>ECS Fargate]
    H --> I[OpenAI GPT-4o]
    H --> J[GST Portal API]
    F --> K[S3 Invoice Vault]`,
  stack: [
    { layer: 'Frontend', technology: 'Next.js 14 + Tailwind + shadcn/ui', rationale: 'SSR for SEO on marketing pages; App Router for dashboard SPA feel' },
    { layer: 'Backend API', technology: 'FastAPI + Python 3.12', rationale: 'Async-native, auto OpenAPI, 10x faster than Django REST' },
    { layer: 'AI Orchestration', technology: 'LangGraph + GPT-4o', rationale: 'Stateful multi-agent workflows with human-in-the-loop gates' },
    { layer: 'Database', technology: 'PostgreSQL 16 + pgvector', rationale: 'ACID compliance + vector similarity search for invoice matching' },
    { layer: 'Queue', technology: 'Redis Streams + BullMQ', rationale: 'Sub-50ms latency for invoice processing events' },
    { layer: 'Infrastructure', technology: 'AWS ECS Fargate + RDS + S3', rationale: 'Serverless containers; auto-scale to 10k concurrent invoices' },
  ],
  openapi_summary: [
    { path: '/v1/invoices', method: 'POST', summary: 'Upload and process an invoice' },
    { path: '/v1/invoices/{id}/match', method: 'GET', summary: 'Get GST match result' },
    { path: '/v1/reconciliation/run', method: 'POST', summary: 'Trigger full monthly reconciliation' },
    { path: '/v1/tally/sync', method: 'POST', summary: 'Push reconciled entries to Tally' },
    { path: '/v1/reminders/send', method: 'POST', summary: 'Dispatch WhatsApp payment reminders' },
  ],
}

export const MOCK_FILE_TREE: FileNode = {
  name: 'invoice-ai-saas',
  type: 'directory',
  children: [
    {
      name: 'backend',
      type: 'directory',
      children: [
        { name: 'main.py', type: 'file', language: 'python', content: `from fastapi import FastAPI\nfrom app.api.v1 import router\n\napp = FastAPI(title="InvoiceAI API")\napp.include_router(router, prefix="/v1")\n` },
        { name: 'requirements.txt', type: 'file', language: 'text', content: 'fastapi==0.115.0\nuvicorn==0.30.6\nlangchain==0.3.0\nopenai==1.50.0\n' },
        {
          name: 'app',
          type: 'directory',
          children: [
            { name: 'invoice_ai.py', type: 'file', language: 'python', content: `import openai\n\nasync def match_invoice(invoice_text: str) -> dict:\n    """Use GPT-4o to extract and match GST data from invoice text."""\n    response = await openai.chat.completions.create(\n        model="gpt-4o",\n        messages=[{"role": "user", "content": f"Extract GST data: {invoice_text}"}]\n    )\n    return {"matched": True, "gstin": "27AABCU9603R1ZM"}\n` },
          ],
        },
      ],
    },
    {
      name: 'frontend',
      type: 'directory',
      children: [
        { name: 'package.json', type: 'file', language: 'json', content: '{\n  "name": "invoice-ai-ui",\n  "version": "1.0.0"\n}\n' },
        { name: 'app/page.tsx', type: 'file', language: 'tsx', content: `export default function HomePage() {\n  return <main><h1>InvoiceAI Dashboard</h1></main>\n}\n` },
      ],
    },
    { name: 'Dockerfile', type: 'file', language: 'dockerfile', content: 'FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]\n' },
    { name: 'docker-compose.yml', type: 'file', language: 'yaml', content: 'version: "3.9"\nservices:\n  api:\n    build: ./backend\n    ports:\n      - "8000:8000"\n  redis:\n    image: redis:7-alpine\n' },
    { name: 'README.md', type: 'file', language: 'markdown', content: '# InvoiceAI SaaS\n\nAI-powered GST invoice automation for Indian SMBs.\n\n## Quick Start\n```bash\ndocker compose up -d\n```\n' },
  ],
}

export const MOCK_REVIEW: ReviewOutput = {
  overall: 'APPROVED',
  coverage_pct: 87,
  self_heal_iterations: 2,
  test_results: [
    { name: 'test_invoice_upload_happy_path', status: 'pass', duration_ms: 142 },
    { name: 'test_gst_match_valid_gstin', status: 'pass', duration_ms: 87 },
    { name: 'test_gst_match_invalid_gstin', status: 'pass', duration_ms: 63 },
    { name: 'test_tally_sync_roundtrip', status: 'pass', duration_ms: 312 },
    { name: 'test_whatsapp_reminder_send', status: 'pass', duration_ms: 198 },
    { name: 'test_reconciliation_monthly', status: 'pass', duration_ms: 2104 },
    { name: 'test_multi_tenant_isolation', status: 'pass', duration_ms: 94 },
    { name: 'test_rate_limit_throttling', status: 'fail', duration_ms: 501, message: 'Expected 429 but received 200' },
    { name: 'test_audit_log_write', status: 'pass', duration_ms: 56 },
    { name: 'test_pdf_invoice_parse', status: 'skip', duration_ms: 0, message: 'PDF parser not yet implemented' },
  ],
  security_findings: [
    { severity: 'low', title: 'Dependency: requests 2.28.0 has CVE-2023-32681', file: 'requirements.txt' },
    { severity: 'info', title: 'Missing Content-Security-Policy header on /docs route' },
  ],
}

export const MOCK_DEPLOY: DeployOutput = {
  live_url: 'https://invoice-ai-mvp.euron.one',
  status: 'live',
  monthly_cost_usd: 47.20,
  deploy_log: [
    '[00:00] Building Docker image...',
    '[00:45] Pushing to ECR: 123456789.dkr.ecr.ap-south-1.amazonaws.com/invoice-ai:sha-abc1234',
    '[01:12] Registering new ECS task definition (revision 7)',
    '[01:15] Updating ECS service: invoice-ai-prod',
    '[02:30] Health check: GET /v1/health → 200 OK',
    '[02:31] Traffic shifted to new deployment',
    '[02:32] Deployment complete. Live at https://invoice-ai-mvp.euron.one',
  ],
}

export const MOCK_MARKETING: MarketingOutput = {
  landing_url: 'https://invoice-ai-mvp.euron.one',
  gtm_summary: 'Target 50,000 Indian SMBs via Google Ads (CA + GST keywords). Expected CAC ₹2,400. Payback period 3 months at ₹999/month Starter plan. LinkedIn organic through CA professional groups projected at 200 signups/month.',
  social_posts: [
    { platform: 'LinkedIn', copy: '🤖 Tired of GST reconciliation headaches? InvoiceAI auto-matches your GSTR-2B in seconds — not days. Try free for 30 days → link in bio', scheduled_at: new Date(Date.now() + 86400_000).toISOString() },
    { platform: 'Twitter/X', copy: 'We built an AI that reads your Tally invoices and auto-files GST. 8 hours saved per accountant per month. 🇮🇳 #GST #FinTech', scheduled_at: new Date(Date.now() + 2 * 86400_000).toISOString() },
    { platform: 'WhatsApp Broadcast', copy: 'Dear CA professional, InvoiceAI is now live! First 100 firms get 3 months free. Reply YES to this message.', scheduled_at: new Date(Date.now() + 3 * 86400_000).toISOString() },
  ],
}

export const MOCK_TENANTS: TenantRow[] = [
  { id: 't1', name: 'Euron AI (Demo)', plan: 'Enterprise', runs_count: 47, tokens_used: 4_200_000, status: 'active' },
  { id: 't2', name: 'BuildX Labs', plan: 'Growth', runs_count: 12, tokens_used: 890_000, status: 'active' },
  { id: 't3', name: 'Startup Studio Pune', plan: 'Starter', runs_count: 3, tokens_used: 120_000, status: 'active' },
  { id: 't4', name: 'Old Tenant Corp', plan: 'Starter', runs_count: 1, tokens_used: 40_000, status: 'suspended' },
]
