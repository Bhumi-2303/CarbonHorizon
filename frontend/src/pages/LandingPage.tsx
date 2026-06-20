import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  User, GraduationCap, Briefcase, Home, Wrench, Sparkles, Building,
  UserPlus, ClipboardList, BrainCircuit, TrendingUp, Leaf,
  Calculator, MessageSquare, BarChart3, FileText, Lightbulb,
  ChevronDown, ChevronUp, Code, Mail, Globe2
} from 'lucide-react'

// ─── Header ─────────────────────────────────────────────────────────
function Header() {
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-bg-primary/80 backdrop-blur-xl border-b border-white/5 shadow-lg' : 'bg-transparent'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-earth-green to-forest-green flex items-center justify-center text-space-black shadow-lg shadow-earth-green/20" aria-hidden="true">
              <Leaf className="w-6 h-6" />
            </div>
            <span className="font-poppins font-bold text-xl tracking-tight text-primary">
              Carbon Horizon
            </span>
          </div>
          <nav className="flex items-center gap-4" aria-label="Primary Navigation">
            <Link to="/login" className="text-sm font-semibold text-muted hover:text-primary transition-colors">
              Log In
            </Link>
            <Link to="/register" className="btn-primary py-2 px-5 text-sm">
              Sign Up Free
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}

// ─── Hero Section ───────────────────────────────────────────────────
function Hero() {
  return (
    <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
      {/* Background elements */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-earth-green/10 rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-ocean-blue/10 rounded-full blur-3xl" />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">
          <div className="max-w-2xl">
            <h1 className="heading-xl text-primary leading-tight mb-6">
              Track your impact. <br />
              <span className="gradient-text">Shape our horizon.</span>
            </h1>
            <p className="body text-muted text-lg mb-8 leading-relaxed">
              Carbon Horizon is an intelligent sustainability platform that helps individuals and organizations measure their carbon footprint, discover tailored reduction strategies, and build eco-friendly habits with the help of an AI Coach.
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <Link to="/register" className="btn-primary flex items-center gap-2 text-lg">
                Start Assessment <TrendingUp className="w-5 h-5" aria-hidden="true" />
              </Link>
              <a href="#about" className="btn-outline text-lg">
                Learn More
              </a>
            </div>
          </div>
          
          <div className="relative h-80 lg:h-[500px] flex items-center justify-center">
            {/* Animated SVG Globe representation */}
            <div className="relative w-72 h-72 lg:w-96 lg:h-96 rounded-full glass-card border border-earth-green/20 flex items-center justify-center animate-spin-slow">
              <Globe2 className="w-40 h-40 lg:w-56 lg:h-56 text-earth-green/40 drop-shadow-2xl" aria-hidden="true" />
            </div>
            {/* Floating glass cards to simulate dashboard metrics */}
            <div className="absolute top-10 right-0 glass-card p-4 animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-earth-green/20 rounded-lg text-earth-green">
                  <Leaf className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">Monthly Footprint</p>
                  <p className="font-bold text-primary">450 kg CO₂</p>
                </div>
              </div>
            </div>
            <div className="absolute bottom-10 left-0 glass-card p-4 animate-fade-in" style={{ animationDelay: '0.4s' }}>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-ocean-blue/20 rounded-lg text-ocean-blue">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">AI Coach Tips</p>
                  <p className="font-bold text-primary">3 new insights</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

// ─── About Section ──────────────────────────────────────────────────
function About() {
  return (
    <section id="about" className="py-20 bg-bg-secondary/30 relative">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="heading-lg text-primary mb-6">What is a Carbon Footprint?</h2>
        <p className="body text-muted leading-relaxed mb-8">
          Your carbon footprint is the total amount of greenhouse gases (including carbon dioxide and methane) that are generated by your actions. Everything from the electricity powering your home to the food on your plate and the vehicle you drive contributes to this total.
        </p>
        <p className="body text-muted leading-relaxed">
          Sustainability matters now more than ever. By understanding our individual and collective impact, we can make informed decisions to mitigate climate change. Carbon Horizon translates complex environmental science into personalized, actionable steps for a greener future.
        </p>
      </div>
    </section>
  )
}

// ─── Who Can Use It ─────────────────────────────────────────────────
const AUDIENCES = [
  { title: 'Children', icon: User, desc: 'Learn simple eco-habits early.' },
  { title: 'Students', icon: GraduationCap, desc: 'Budget-friendly sustainability.' },
  { title: 'Professionals', icon: Briefcase, desc: 'Optimize daily commutes & energy.' },
  { title: 'Homemakers', icon: Home, desc: 'Sustainable household management.' },
  { title: 'House Helpers', icon: Wrench, desc: 'Efficient resource usage.' },
  { title: 'Retired Citizens', icon: UserPlus, desc: 'Accessible eco-friendly practices.' },
  { title: 'Families', icon: () => <UserPlus className="w-8 h-8" />, desc: 'Track household collective impact.', rawIcon: true },
  { title: 'Organizations', icon: Building, desc: 'Manage enterprise sustainability.' },
]

function WhoCanUseIt() {
  return (
    <section className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="heading-lg text-primary mb-4">Built for Everyone</h2>
          <p className="text-slate-400">A flexible platform that adapts to your unique lifestyle and needs.</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {AUDIENCES.map((aud, i) => (
            <div key={i} className="glass-card p-6 text-center hover:-translate-y-1 transition-transform duration-300">
              <div className="mx-auto w-12 h-12 rounded-xl bg-earth-green/10 text-earth-green flex items-center justify-center mb-4">
                {aud.rawIcon ? aud.icon() : <aud.icon className="w-6 h-6" aria-hidden="true" />}
              </div>
              <h3 className="font-poppins font-semibold text-primary mb-2">{aud.title}</h3>
              <p className="text-xs text-slate-400">{aud.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── How It Works ───────────────────────────────────────────────────
const STEPS = [
  { step: '01', title: 'Create Profile', icon: UserPlus, desc: 'Sign up and set your baseline preferences.' },
  { step: '02', title: 'Assess Impact', icon: ClipboardList, desc: 'Answer a few questions about your lifestyle.' },
  { step: '03', title: 'AI Insights', icon: BrainCircuit, desc: 'Chat with our AI Coach for custom advice.' },
  { step: '04', title: 'Track Progress', icon: TrendingUp, desc: 'Log daily habits and watch your score improve.' },
  { step: '05', title: 'Reduce Footprint', icon: Leaf, desc: 'Reach your sustainability goals over time.' },
]

function HowItWorks() {
  return (
    <section className="py-24 bg-bg-secondary/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="heading-lg text-primary text-center mb-16">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
          {STEPS.map((s, i) => (
            <div key={i} className="relative text-center">
              {i !== STEPS.length - 1 && (
                <div className="hidden md:block absolute top-8 left-[60%] w-[80%] h-[2px] bg-gradient-to-r from-earth-green/50 to-transparent" />
              )}
              <div className="mx-auto w-16 h-16 rounded-2xl glass-card flex items-center justify-center mb-4 relative z-10 border-earth-green/30 text-earth-green">
                <s.icon className="w-8 h-8" aria-hidden="true" />
              </div>
              <h3 className="text-earth-green font-poppins font-bold text-sm mb-1">{s.step}</h3>
              <h4 className="text-primary font-semibold mb-2">{s.title}</h4>
              <p className="text-sm text-slate-400">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── Core Features ──────────────────────────────────────────────────
const FEATURES = [
  { title: 'Carbon Assessment', icon: Calculator, desc: 'Precise calculations across transport, energy, food, and waste.' },
  { title: 'AI Sustainability Coach', icon: MessageSquare, desc: 'A context-aware AI assistant powered by Google Gemini.' },
  { title: 'Analytics Dashboard', icon: BarChart3, desc: 'Visualize your historical data and footprint composition.' },
  { title: 'Detailed Reports', icon: FileText, desc: 'Exportable emissions data for personal or organizational use.' },
  { title: 'Smart Recommendations', icon: Lightbulb, desc: 'Actionable What-If simulator to forecast lifestyle changes.' },
]

function CoreFeatures() {
  return (
    <section className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="heading-lg text-primary text-center mb-16">Core Features</h2>
        <div className="grid md:grid-cols-3 gap-8">
          {FEATURES.map((f, i) => (
            <div key={i} className={`glass-card p-8 ${i >= 3 ? 'md:col-span-1.5' : ''}`}>
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-ocean-blue/20 to-ocean-blue/5 text-ocean-blue border border-ocean-blue/20 flex items-center justify-center mb-6">
                <f.icon className="w-7 h-7" aria-hidden="true" />
              </div>
              <h3 className="text-xl font-semibold text-primary mb-3">{f.title}</h3>
              <p className="text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── FAQ ────────────────────────────────────────────────────────────
function FAQ() {
  const [openIdx, setOpenIdx] = useState<number | null>(null)
  
  const faqs = [
    { q: 'Is the platform free to use?', a: 'Yes, the core personal assessment and tracking features are completely free for individual users.' },
    { q: 'How are my carbon emissions calculated?', a: 'We use established emission factors (such as IPCC guidelines) combined with the lifestyle data you provide regarding transportation, diet, and energy usage.' },
    { q: 'Is my data private?', a: 'Absolutely. Your data is encrypted and never sold to third parties. Our AI Coach only processes your anonymized assessment data to provide insights.' },
    { q: 'Can organizations use this?', a: 'Yes! We offer organizational tools to aggregate anonymized employee data and track corporate sustainability goals.' },
  ]

  return (
    <section className="py-24 bg-bg-secondary/30">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="heading-lg text-primary text-center mb-12">Frequently Asked Questions</h2>
        <div className="space-y-4">
          {faqs.map((faq, i) => (
            <div key={i} className="glass-card overflow-hidden transition-all duration-200">
              <button
                className="w-full flex items-center justify-between p-6 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                onClick={() => setOpenIdx(openIdx === i ? null : i)}
                aria-expanded={openIdx === i}
                aria-controls={`faq-answer-${i}`}
              >
                <span className="font-semibold text-primary">{faq.q}</span>
                {openIdx === i ? <ChevronUp className="w-5 h-5 text-earth-green" aria-hidden="true" /> : <ChevronDown className="w-5 h-5 text-slate-400" aria-hidden="true" />}
              </button>
              {openIdx === i && (
                <div id={`faq-answer-${i}`} className="px-6 pb-6 text-muted">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ─── Footer ─────────────────────────────────────────────────────────
function Footer() {
  return (
    <footer className="border-t border-white/10 bg-bg-primary pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <Leaf className="w-6 h-6 text-earth-green" aria-hidden="true" />
              <span className="font-poppins font-bold text-xl text-primary">Carbon Horizon</span>
            </div>
            <p className="text-slate-400 max-w-lg">
              Empowering individuals and organizations to measure, understand, and reduce their environmental impact through AI-driven insights.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-primary mb-4">Platform</h4>
            <ul className="space-y-2">
              <li><Link to="/login" className="text-slate-400 hover:text-earth-green transition-colors">Log In</Link></li>
              <li><Link to="/register" className="text-slate-400 hover:text-earth-green transition-colors">Sign Up</Link></li>
              <li><a href="#about" className="text-slate-400 hover:text-earth-green transition-colors">About Us</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-primary mb-4">Legal & Connect</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-slate-400 hover:text-earth-green transition-colors">Privacy Policy</a></li>
              <li><a href="#" className="text-slate-400 hover:text-earth-green transition-colors">Terms of Service</a></li>
              <li className="pt-2 flex gap-4">
                <a href="#" className="text-slate-400 hover:text-primary"><Code className="w-5 h-5" aria-hidden="true" /></a>
                <a href="#" className="text-slate-400 hover:text-primary"><Mail className="w-5 h-5" aria-hidden="true" /></a>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row items-center justify-between text-sm text-slate-500">
          <p>© {new Date().getFullYear()} Carbon Horizon. All rights reserved.</p>
          <p>Built for a sustainable future.</p>
        </div>
      </div>
    </footer>
  )
}

// ─── Main Page Assembly ─────────────────────────────────────────────
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-bg-primary font-sans text-muted selection:bg-earth-green/30">
      <Header />
      <main>
        <Hero />
        <About />
        <WhoCanUseIt />
        <HowItWorks />
        <CoreFeatures />
        <FAQ />
      </main>
      <Footer />
    </div>
  )
}
