'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, ChevronRight, ChevronDown, File, Folder, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Header } from '@/components/layout/Header'
import { MOCK_FILE_TREE } from '@/lib/mock-data'
import { cn } from '@/lib/utils'
import type { FileNode } from '@/lib/types'

const LANG_COLORS: Record<string, string> = {
  python: 'bg-blue-100 text-blue-800',
  tsx: 'bg-cyan-100 text-cyan-800',
  typescript: 'bg-cyan-100 text-cyan-800',
  json: 'bg-yellow-100 text-yellow-800',
  yaml: 'bg-green-100 text-green-800',
  dockerfile: 'bg-orange-100 text-orange-800',
  markdown: 'bg-gray-100 text-gray-700',
  text: 'bg-gray-100 text-gray-700',
}

function TreeNode({
  node,
  depth,
  onSelect,
  selectedFile,
}: {
  node: FileNode
  depth: number
  onSelect: (n: FileNode) => void
  selectedFile: FileNode | null
}) {
  const [open, setOpen] = useState(depth < 1)

  if (node.type === 'file') {
    return (
      <button
        type="button"
        className={cn(
          'flex w-full items-center gap-1.5 rounded-md px-2 py-1 text-left text-xs transition-colors',
          selectedFile?.name === node.name && selectedFile?.content === node.content
            ? 'bg-primary/10 text-primary'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        )}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={() => onSelect(node)}
      >
        <File className="h-3 w-3 flex-shrink-0" />
        <span className="truncate">{node.name}</span>
      </button>
    )
  }

  return (
    <div>
      <button
        type="button"
        className="flex w-full items-center gap-1.5 rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={() => setOpen(!open)}
      >
        {open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        <Folder className="h-3 w-3" />
        <span className="font-medium">{node.name}</span>
      </button>
      {open && node.children?.map((child) => (
        <TreeNode
          key={`${child.name}-${depth}`}
          node={child}
          depth={depth + 1}
          onSelect={onSelect}
          selectedFile={selectedFile}
        />
      ))}
    </div>
  )
}

export default function CodePage() {
  const { id } = useParams<{ id: string }>()
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null)

  return (
    <div className="flex flex-col">
      <Header title="Generated Code" />
      <div className="flex-1 p-6">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" size="icon" className="h-8 w-8">
              <Link href={`/runs/${id}`}><ArrowLeft className="h-4 w-4" /></Link>
            </Button>
            <h2 className="text-base font-semibold">Generated Codebase</h2>
          </div>
          <Button variant="outline" size="sm" className="gap-1.5">
            <Download className="h-3.5 w-3.5" />
            Download ZIP
          </Button>
        </div>

        <div className="flex gap-4 overflow-hidden" style={{ height: 'calc(100vh - 160px)' }}>
          {/* File Tree */}
          <Card className="w-56 flex-shrink-0 overflow-hidden">
            <CardHeader className="px-3 py-2.5">
              <CardTitle className="text-xs text-muted-foreground">File Tree</CardTitle>
            </CardHeader>
            <CardContent className="overflow-y-auto px-1 pb-2 pt-0" style={{ maxHeight: 'calc(100% - 48px)' }}>
              <TreeNode
                node={MOCK_FILE_TREE}
                depth={0}
                onSelect={setSelectedFile}
                selectedFile={selectedFile}
              />
            </CardContent>
          </Card>

          {/* Code Viewer */}
          <Card className="flex flex-1 flex-col overflow-hidden">
            <CardHeader className="flex-shrink-0 flex-row items-center justify-between px-4 py-2.5">
              {selectedFile ? (
                <div className="flex items-center gap-2">
                  <File className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{selectedFile.name}</span>
                  {selectedFile.language && (
                    <Badge
                      className={cn('text-[10px]', LANG_COLORS[selectedFile.language] ?? 'bg-gray-100 text-gray-700')}
                    >
                      {selectedFile.language}
                    </Badge>
                  )}
                </div>
              ) : (
                <span className="text-sm text-muted-foreground">Select a file to view</span>
              )}
            </CardHeader>
            <CardContent className="flex-1 overflow-auto p-0">
              {selectedFile?.content ? (
                <pre className="h-full w-full overflow-auto bg-slate-950 p-4 font-mono text-xs leading-relaxed text-slate-200">
                  {selectedFile.content}
                </pre>
              ) : (
                <div className="flex h-full items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <File className="mx-auto mb-2 h-8 w-8 opacity-30" />
                    <p className="text-sm">Select a file from the tree</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
