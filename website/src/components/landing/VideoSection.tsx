import { Play } from 'lucide-react'

export default function VideoSection() {
  return (
    <section id="video" className="py-24 section-gradient">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            See AutoFounder AI in Action
          </h2>
          <p className="text-slate-400 text-lg max-w-xl mx-auto">
            Watch how a single text idea becomes a fully deployed, marketed software business — in
            under 7 days.
          </p>
        </div>

        {/* Video embed placeholder */}
        {/* TODO: Replace the placeholder below with the actual YouTube embed URL */}
        <div className="relative rounded-2xl overflow-hidden border border-white/10 shadow-2xl glow-purple bg-slate-900 aspect-video group cursor-pointer">
          {/* Placeholder thumbnail background */}
          <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-900 to-blue-950 flex items-center justify-center">
            <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_center,#7c3aed_0%,transparent_70%)]" />

            {/* Play button */}
            <div className="relative flex flex-col items-center gap-4">
              <div className="w-20 h-20 rounded-full bg-blue-600 hover:bg-blue-500 flex items-center justify-center shadow-lg shadow-blue-900/60 group-hover:scale-110 transition-transform duration-200">
                <Play size={32} className="text-white ml-1" fill="white" />
              </div>
              <span className="text-slate-400 text-sm font-medium">Demo video coming soon</span>
            </div>

            {/* TODO: Replace with real thumbnail image once available */}
            <div className="absolute bottom-6 right-6">
              <div className="glass-card px-3 py-1.5 text-xs text-blue-400 font-medium">
                AutoFounder AI Demo
              </div>
            </div>
          </div>

          {/* Actual YouTube embed — swap in when ready */}
          {/*
          TODO: Uncomment and replace YOUTUBE_VIDEO_ID with the real ID:
          <iframe
            src="https://www.youtube.com/embed/YOUTUBE_VIDEO_ID?rel=0&modestbranding=1"
            title="AutoFounder AI Demo"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="absolute inset-0 w-full h-full"
          />
          */}
        </div>

        <p className="text-center text-slate-500 text-sm mt-6">
          {/* TODO: Update caption to match actual video content */}
          The demo shows the full end-to-end flow: entering a startup idea, watching agents validate the
          market, generate architecture, write and test code, deploy to AWS, and ship a launch campaign —
          all autonomously.
        </p>
      </div>
    </section>
  )
}
