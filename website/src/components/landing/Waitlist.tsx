import { useState } from "react";
import { ArrowRight, Mail } from "lucide-react";

export default function Waitlist() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);

    // TODO: Replace with real API call to waitlist endpoint (e.g. POST /v1/waitlist or Mailchimp/Resend integration)
    await new Promise((r) => setTimeout(r, 800));
    setSubmitted(true);
    setLoading(false);
  };

  return (
    <section id="waitlist" className="py-24">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Glow backdrop */}
        <div className="relative rounded-3xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-600/20 via-blue-600/10 to-transparent" />
          <div className="absolute inset-0 border border-blue-500/20 rounded-3xl" />

          <div className="relative px-8 py-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Ready to build your startup with AI?
            </h2>
            <p className="text-slate-400 text-lg mb-10 max-w-xl mx-auto">
              Join 500+ founders on the waitlist. Early access cohort launching soon.
              {/* TODO: Update waitlist count with real number */}
            </p>

            {submitted ? (
              <div className="inline-flex items-center gap-3 px-8 py-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-base font-medium">
                ✓ You're on the list! We'll be in touch soon.
              </div>
            ) : (
              <form
                onSubmit={handleSubmit}
                className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto"
              >
                <div className="relative flex-1">
                  <Mail
                    size={16}
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"
                  />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    className="w-full pl-10 pr-4 py-3.5 rounded-xl bg-white/5 border border-white/10 focus:border-blue-500/50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-white placeholder-slate-500 text-sm transition-all"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-semibold text-sm transition-all duration-200 shadow-lg shadow-blue-900/50 whitespace-nowrap"
                >
                  {loading ? "Joining…" : "Get Early Access"}
                  {!loading && <ArrowRight size={16} />}
                </button>
              </form>
            )}

            <p className="text-slate-600 text-xs mt-6">
              No credit card required · Unsubscribe any time ·{" "}
              {/* TODO: Link to real privacy policy */}
              <a
                href="#"
                className="underline underline-offset-2 hover:text-slate-400 transition-colors"
              >
                Privacy Policy
              </a>
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
