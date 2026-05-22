import { Play } from 'lucide-react'

export function VideoSection() {
  return (
    <section id="video" className="bg-slate-950 py-24">
      <div className="mx-auto max-w-4xl px-6">
        <div className="mb-10 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">See it in action</h2>
          <p className="text-slate-400">
            Watch AutoFounder AI turn a raw idea into a deployed product in under 30 minutes
          </p>
        </div>

        {/* Video embed container */}
        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl shadow-black/50">
          <div className="relative aspect-video">
            {/*
              TODO: Replace this placeholder with a real YouTube embed.
              1. Upload your demo video to YouTube
              2. Get the video ID (e.g. "dQw4w9WgXcQ")
              3. Replace the div below with:
                 <iframe
                   className="absolute inset-0 h-full w-full"
                   src="https://www.youtube-nocookie.com/embed/YOUR_VIDEO_ID?rel=0"
                   title="AutoFounder AI Demo"
                   allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                   allowFullScreen
                 />
            */}
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-gradient-to-b from-slate-800 to-slate-900">
              {/* Decorative grid */}
              <div
                className="absolute inset-0 opacity-10"
                style={{
                  backgroundImage:
                    'linear-gradient(rgba(124,58,237,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(124,58,237,0.3) 1px, transparent 1px)',
                  backgroundSize: '40px 40px',
                }}
              />
              <div className="relative flex h-20 w-20 items-center justify-center rounded-full border border-violet-500/40 bg-violet-600/20 ring-8 ring-violet-500/10">
                <Play className="h-8 w-8 translate-x-0.5 text-violet-400" />
              </div>
              {/* TODO: Update text once demo video is recorded */}
              <p className="relative text-sm font-medium text-slate-400">Demo video coming soon</p>
              <p className="relative text-xs text-slate-600">product@euron.one to request a walkthrough</p>
            </div>
          </div>
        </div>

        {/* Caption */}
        <p className="mt-4 text-center text-sm text-slate-500">
          {/* TODO: Update caption once real demo is recorded */}
          Full walkthrough: idea submission → market validation → code generation → live deployment
        </p>
      </div>
    </section>
  )
}
