import Navbar from "./components/landing/Navbar";
import Hero from "./components/landing/Hero";
import VideoSection from "./components/landing/VideoSection";
import Problem from "./components/landing/Problem";
import Features from "./components/landing/Features";
import HowItWorks from "./components/landing/HowItWorks";
import Testimonials from "./components/landing/Testimonials";
import Pricing from "./components/landing/Pricing";
import Waitlist from "./components/landing/Waitlist";
import FAQ from "./components/landing/FAQ";
import Footer from "./components/landing/Footer";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Navbar />
      <main>
        <Hero />
        <VideoSection />
        <Problem />
        <Features />
        <HowItWorks />
        <Testimonials />
        <Pricing />
        <Waitlist />
        <FAQ />
      </main>
      <Footer />
    </div>
  );
}
