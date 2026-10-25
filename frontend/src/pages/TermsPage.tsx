// FIXME: Must be reviewed by legal counsel before launch
import { Scale, CheckCircle2, AlertTriangle, ShieldAlert, Cpu, Sparkles, BookOpen, Mail } from 'lucide-react'
import PublicLayout from '@/components/PublicLayout'
import Seo from '@/components/Seo'
import { SEO_PAGES } from '@/config/seo'

export default function TermsPage() {
  const effectiveDate = 'October 24, 2026'
  const lastUpdated = 'October 24, 2026'

  return (
    <PublicLayout>
      <Seo {...SEO_PAGES.terms} />

      <article className="space-y-8 animate-fade-in">
        {/* Header Card */}
        <header className="glass-panel p-8 sm:p-10 border border-white/10 shadow-xl rounded-3xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-earth-green/10 rounded-full blur-3xl pointer-events-none" />
          <div className="flex items-center gap-3 text-earth-green mb-3">
            <Scale className="w-6 h-6" aria-hidden="true" />
            <span className="text-sm font-semibold uppercase tracking-wider">Legal Terms</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold font-poppins text-primary tracking-tight">
            Terms of Service
          </h1>
          <div className="flex flex-wrap gap-4 text-xs sm:text-sm text-slate-400 mt-4">
            <span><strong>Effective Date:</strong> {effectiveDate}</span>
            <span aria-hidden="true">•</span>
            <span><strong>Last Updated:</strong> {lastUpdated}</span>
            <span aria-hidden="true">•</span>
            <span>Version: 2026-v1</span>
          </div>
        </header>

        {/* Section 1: Acceptance */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-earth-green" aria-hidden="true" />
            1. Acceptance of Terms
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            By creating an account, accessing, or using the Carbon Horizon application and related services (&quot;Service&quot;), you agree to be bound by these Terms of Service (&quot;Terms&quot;). If you do not agree to these Terms, you may not use the Service.
          </p>
        </section>

        {/* Section 2: Eligibility & Age Rules */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-earth-green" aria-hidden="true" />
            2. Eligibility & Age Requirements
          </h2>
          <div className="space-y-3 text-sm text-slate-300">
            <p>
              Carbon Horizon is structured with tailored experiences for different age brackets:
            </p>
            <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2">
              <h3 className="font-semibold text-primary text-sm">Children Under 13 (Little Explorer Tier)</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Children under 13 years of age may only access the platform through the supervised &quot;Little Explorer&quot; mode with verified parental or guardian consent. Parents and legal guardians assume full responsibility for their child&apos;s activity.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2">
              <h3 className="font-semibold text-primary text-sm">Students Aged 13 to 17</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Users between 13 and 17 years of age may register with parental or guardian awareness and consent to build environmental literacy.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-white/5 border border-white/5 space-y-2">
              <h3 className="font-semibold text-primary text-sm">Adults (18+)</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                You represent that you have legal capacity to enter into a binding contract in your jurisdiction.
              </p>
            </div>
          </div>
        </section>

        {/* Section 3: Account Responsibilities */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-earth-green" aria-hidden="true" />
            3. Account Responsibilities & Security
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            You agree to provide true, accurate, and current profile information. You are solely responsible for maintaining the confidentiality of your login credentials and for all activities that occur under your account. You agree to notify us immediately at <a href="mailto:security@carbonhorizon.app" className="text-earth-green hover:underline">security@carbonhorizon.app</a> of any suspected unauthorized access or breach of security.
          </p>
        </section>

        {/* Section 4: Acceptable Use & AI Coach Rules */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <Cpu className="w-5 h-5 text-earth-green" aria-hidden="true" />
            4. Acceptable Use & AI Sustainability Coach Policy
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm">
            You agree to use Carbon Horizon only for lawful environmental awareness and habit-building purposes. Specifically regarding our AI Sustainability Coach:
          </p>
          <div className="p-4 rounded-xl bg-earth-green/10 border border-earth-green/30 space-y-2 text-xs sm:text-sm text-slate-800 dark:text-slate-200">
            <p className="font-semibold text-earth-green flex items-center gap-1.5">
              <Sparkles className="w-4 h-4" />
              Sustainability Topics Only
            </p>
            <p>
              The AI Sustainability Coach is dedicated exclusively to climate, ecological habits, energy conservation, circular economy, and carbon reduction guidance. You agree not to attempt jailbreaks, prompt injection, automated scraping, or misuse the AI feature for off-topic, harmful, sexually explicit, abusive, or unlawful outputs.
            </p>
          </div>
        </section>

        {/* Section 5: Carbon Estimates Disclaimer */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border-2 border-amber-500/40 bg-amber-500/5 space-y-4">
          <h2 className="text-xl font-bold text-amber-700 dark:text-amber-400 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-700 dark:text-amber-400" aria-hidden="true" />
            5. Disclaimer: Carbon Estimates Are Approximations
          </h2>
          <p className="text-slate-200 leading-relaxed text-sm sm:text-base">
            <strong>Educational & Awareness Purpose Only:</strong> All emission calculations, carbon footprint assessments, reduction forecasts, and simulator figures provided on Carbon Horizon are approximations derived from generalized mathematical models and regional emission factor averages (e.g., IPCC, DEFRA, CEA India).
          </p>
          <p className="text-slate-300 leading-relaxed text-xs sm:text-sm">
            They do <strong>NOT</strong> constitute certified carbon accounting, regulatory ESG compliance filings, auditable carbon offset verification, or professional environmental engineering advice. We make no warranty that your actual emissions match these estimates exactly.
          </p>
        </section>

        {/* Section 6: Intellectual Property */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <Scale className="w-5 h-5 text-earth-green" aria-hidden="true" />
            6. Intellectual Property Rights
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            The Carbon Horizon platform, including our software, user interface design, glassmorphic styling tokens, calculation algorithms, brand logos, and content, is protected by intellectual property laws. You retain full ownership of your personal profile data and logs.
          </p>
        </section>

        {/* Section 7: Limitation of Liability */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-earth-green" aria-hidden="true" />
            7. Limitation of Liability
          </h2>
          <p className="text-slate-300 leading-relaxed text-xs sm:text-sm">
            TO THE MAXIMUM EXTENT PERMITTED BY LAW, CARBON HORIZON AND ITS AFFILIATES SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS, DATA, OR USE, ARISING FROM OR CONNECTED WITH YOUR USE OF OR INABILITY TO USE THE PLATFORM. THE SERVICE IS PROVIDED ON AN &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; BASIS WITHOUT WARRANTIES OF ANY KIND.
          </p>
        </section>

        {/* Section 8: Termination */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-earth-green" aria-hidden="true" />
            8. Termination
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            You may terminate your account at any time via Profile Settings. We reserve the right to suspend or terminate accounts that breach these Terms, attempt platform exploitation, or abuse AI endpoints.
          </p>
        </section>

        {/* Section 9: Governing Law & Jurisdiction */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <Scale className="w-5 h-5 text-earth-green" aria-hidden="true" />
            9. Governing Law & Jurisdiction
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            These Terms shall be governed by and construed in accordance with the laws of the Republic of India, without regard to its conflict of law principles. Any dispute arising out of or in connection with these Terms shall be subject to the exclusive jurisdiction of the competent courts of New Delhi or Mumbai, India.
          </p>
        </section>

        {/* Section 10: Changes to Terms */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-earth-green" aria-hidden="true" />
            10. Changes to These Terms
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            We may update these Terms periodically to reflect evolving features or legal requirements. Material revisions will be highlighted on the platform or communicated via your registered email address. Continued use of Carbon Horizon following such updates constitutes your acceptance of the revised Terms.
          </p>
        </section>

        {/* Section 11: Contact */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <Mail className="w-5 h-5 text-earth-green" aria-hidden="true" />
            11. Legal Contact
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            If you have questions regarding these Terms of Service or legal notices, please write to us at:
          </p>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 inline-block text-sm">
            <p className="text-slate-200"><strong>Legal Affairs & Compliance</strong></p>
            <p className="text-slate-400">Carbon Horizon Technologies</p>
            <p className="text-earth-green font-mono mt-1">
              <a href="mailto:legal@carbonhorizon.app" className="hover:underline">
                legal@carbonhorizon.app
              </a>
            </p>
          </div>
        </section>
      </article>
    </PublicLayout>
  )
}
