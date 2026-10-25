// FIXME: Must be reviewed by legal counsel before launch
import { Shield, Lock, Eye, FileText, CheckCircle2, UserX, Globe, Mail } from 'lucide-react'
import PublicLayout from '@/components/PublicLayout'
import Seo from '@/components/Seo'
import { SEO_PAGES } from '@/config/seo'

export default function PrivacyPage() {
  const effectiveDate = 'October 24, 2026'
  const lastUpdated = 'October 24, 2026'

  return (
    <PublicLayout>
      <Seo {...SEO_PAGES.privacy} />

      <article className="space-y-8 animate-fade-in">
        {/* Header Card */}
        <header className="glass-panel p-8 sm:p-10 border border-white/10 shadow-xl rounded-3xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-earth-green/10 rounded-full blur-3xl pointer-events-none" />
          <div className="flex items-center gap-3 text-earth-green mb-3">
            <Shield className="w-6 h-6" aria-hidden="true" />
            <span className="text-sm font-semibold uppercase tracking-wider">Privacy & Trust</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold font-poppins text-primary tracking-tight">
            Privacy Policy
          </h1>
          <div className="flex flex-wrap gap-4 text-xs sm:text-sm text-slate-400 mt-4">
            <span><strong>Effective Date:</strong> {effectiveDate}</span>
            <span aria-hidden="true">•</span>
            <span><strong>Last Updated:</strong> {lastUpdated}</span>
            <span aria-hidden="true">•</span>
            <span>Compliance: DPDP Act (India) & GDPR (EU)</span>
          </div>
        </header>

        {/* Section 1: Overview & Scope */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <FileText className="w-5 h-5 text-earth-green" aria-hidden="true" />
            1. Overview & Commitment
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            Carbon Horizon (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;) provides a personal and organizational climate intelligence platform that empowers users to calculate carbon footprints, model reduction scenarios, and build sustainable habits. We believe personal sustainability data deserves the highest standards of confidentiality, transparency, and user autonomy.
          </p>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            This Privacy Policy explains how we collect, use, store, and safeguard your data, and details your legal rights under India&apos;s Digital Personal Data Protection Act (DPDP Act 2023), the European Union&apos;s General Data Protection Regulation (GDPR), and applicable privacy laws globally.
          </p>
        </section>

        {/* Section 2: Data We Collect */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <Eye className="w-5 h-5 text-earth-green" aria-hidden="true" />
            2. What Data We Collect
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 pt-2">
            <div className="p-4 rounded-xl bg-white/5 border border-white/5">
              <h3 className="font-semibold text-primary text-sm mb-1.5">Account & Profile Information</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Full name, email address, cryptographic password hash, age, gender (optional), age group (Child, Student, Adult, Senior), and lifestyle/occupation classification.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-white/5 border border-white/5">
              <h3 className="font-semibold text-primary text-sm mb-1.5">Geographic Location</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Country, state/province, and city. We collect this solely to apply accurate regional electrical grid emission factors and local climate benchmarks. We do not track fine-grained GPS coordinates.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-white/5 border border-white/5">
              <h3 className="font-semibold text-primary text-sm mb-1.5">Carbon Assessment Inputs</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Answers provided in footprint assessments regarding vehicle mileage, flights, public transit, home electricity and heating consumption, dietary preferences, and household waste volume.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-white/5 border border-white/5">
              <h3 className="font-semibold text-primary text-sm mb-1.5">Habit Logs & Simulator Scenarios</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Daily or weekly eco-habit check-ins (e.g., meatless meals, bike commutes, reusable containers), reduction goals, and what-if simulation model parameters.
              </p>
            </div>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/5">
            <h3 className="font-semibold text-primary text-sm mb-1.5">AI Coach Conversations</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Queries submitted to our AI Sustainability Coach and the generated recommendations. All messages are routed through our secure backend proxy; your conversations are never used to train public foundation models without consent.
            </p>
          </div>
        </section>

        {/* Section 3: Why We Collect It */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-earth-green" aria-hidden="true" />
            3. Why We Collect Your Data
          </h2>
          <ul className="space-y-2.5 text-sm text-slate-300 leading-relaxed">
            <li className="flex items-start gap-2.5">
              <span className="text-earth-green font-bold">•</span>
              <span><strong>Calculations:</strong> Computing accurate greenhouse gas emission totals using calibrated national and regional factors.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="text-earth-green font-bold">•</span>
              <span><strong>Personalized Guidance:</strong> Tailoring action plans, simulator suggestions, and AI coach responses to your specific lifestyle and region.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="text-earth-green font-bold">•</span>
              <span><strong>Progress & Streaks:</strong> Retaining historical progress so you can benchmark your trajectory toward personal or organizational net-zero targets.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <span className="text-earth-green font-bold">•</span>
              <span><strong>Platform Security:</strong> Preventing automated abuse, brute-force attacks, and credential stuffing via rate limiting and session validation.</span>
            </li>
          </ul>
        </section>

        {/* Section 4: Data Storage & Infrastructure */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <Lock className="w-5 h-5 text-earth-green" aria-hidden="true" />
            4. Where and How Your Data Is Stored
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            Your data is stored within Google Cloud Platform (GCP) managed infrastructure utilizing Cloud Run and managed Cloud SQL PostgreSQL. All data is encrypted in transit using Transport Layer Security (TLS 1.3) and encrypted at rest using industry-standard AES-256 encryption. Access controls adhere to the principle of least privilege and strict service account isolation.
          </p>
        </section>

        {/* Section 5: Third-Party Service Providers */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <Globe className="w-5 h-5 text-earth-green" aria-hidden="true" />
            5. Third Parties & Processors
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm">
            We never sell, rent, or trade your personal data. We engage only trusted infrastructure processors under strict data processing agreements:
          </p>
          <div className="space-y-3 pt-1 text-xs sm:text-sm text-slate-300">
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/5">
              <p><strong>Cloud Infrastructure:</strong> Google Cloud Platform (Cloud Run, Cloud SQL, Secret Manager) for secure European/Indian and US hosting environments.</p>
            </div>
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/5">
              <p><strong>AI Sustainability Coach:</strong> Google Gemini API / Vertex AI. All requests are proxied server-to-server by our backend. API provider credentials and conversation data are subjected to zero-retention policies for foundation training.</p>
            </div>
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/5">
              <p><strong>Analytics (Plausible Analytics):</strong> We use privacy-friendly, cookieless Plausible Analytics. It collects aggregate telemetry with 100% anonymized IP addresses, creates no persistent cross-site identifiers, and never transmits personal data, passwords, or AI coach conversations. Analytics scripts only load if you affirmatively consent via our cookie banner, and are permanently disabled for Little Explorer child profiles.</p>
            </div>
          </div>
        </section>

        {/* Section 6: Children's Data & Little Explorer Tier */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border-2 border-earth-green/40 bg-earth-green/5 space-y-4">
          <h2 className="text-xl font-bold text-earth-green flex items-center gap-2">
            <Shield className="w-5 h-5 text-earth-green" aria-hidden="true" />
            6. Children&apos;s Data (Little Explorer Tier)
          </h2>
          <p className="text-slate-200 leading-relaxed text-sm sm:text-base font-medium">
            We are dedicated to safeguarding children&apos;s digital privacy. For our youngest users (ages 4 to 12), Carbon Horizon operates the dedicated &quot;Little Explorer&quot; interface:
          </p>
          <div className="space-y-2.5 text-xs sm:text-sm text-slate-300">
            <p className="flex items-start gap-2">
              <span className="text-earth-green font-bold">✓</span>
              <span><strong>Minimal Collection:</strong> Only basic non-identifying habit selections (e.g., turning off lights, watering plants) are stored to render cheerful progress badges.</span>
            </p>
            <p className="flex items-start gap-2">
              <span className="text-earth-green font-bold">✓</span>
              <span><strong>Zero Analytics & Zero Tracking:</strong> Analytics and tracking cookies are <em>strictly disabled</em> across all child profiles, regardless of banner consent settings.</span>
            </p>
            <p className="flex items-start gap-2">
              <span className="text-earth-green font-bold">✓</span>
              <span><strong>Parental / Guardian Consent:</strong> Children under 13 may only use Carbon Horizon with verifiable parental or guardian consent. Parents may review, edit, or delete child accounts at any time.</span>
            </p>
            <p className="flex items-start gap-2">
              <span className="text-earth-green font-bold">✓</span>
              <span><strong>No Carbon Guilt:</strong> The Little Explorer interface is free from complex emission statistics or anxiety-inducing terminology, focusing entirely on joyful nature stewardship.</span>
            </p>
          </div>
        </section>

        {/* Section 7: Retention & Deletion */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <UserX className="w-5 h-5 text-earth-green" aria-hidden="true" />
            7. Data Retention & Deletion
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            We retain your personal data only as long as your account is active or needed to provide you with sustainability insights. You may delete individual assessment logs, clear your AI conversation history, or initiate full account deletion from your Profile Settings. Upon account deletion, all personal data is permanently wiped from active databases within 30 days.
          </p>
        </section>

        {/* Section 8: Cookies & Consent */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <Lock className="w-5 h-5 text-earth-green" aria-hidden="true" />
            8. Cookies & Local Storage
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            We categorize cookies and browser storage into three transparent tiers:
          </p>
          <div className="grid gap-3 sm:grid-cols-3 text-xs text-slate-300">
            <div className="p-3 rounded-xl bg-white/5 border border-white/5">
              <p className="font-semibold text-primary mb-1">1. Strictly Necessary</p>
              <p>Essential for login tokens, CSRF protection, and HTTPS routing. Always enabled.</p>
            </div>
            <div className="p-3 rounded-xl bg-white/5 border border-white/5">
              <p className="font-semibold text-primary mb-1">2. Analytics (Optional)</p>
              <p>Measures aggregate page interactions to improve user experience. Disabled until consent is granted.</p>
            </div>
            <div className="p-3 rounded-xl bg-white/5 border border-white/5">
              <p className="font-semibold text-primary mb-1">3. Preferences (Optional)</p>
              <p>Remembers custom theme settings and calculator unit defaults.</p>
            </div>
          </div>
          <p className="text-xs text-slate-400">
            You can modify your consent choices at any time using the &quot;Cookie settings&quot; link in our website footer.
          </p>
        </section>

        {/* Section 9: Your Legal Rights */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <Shield className="w-5 h-5 text-earth-green" aria-hidden="true" />
            9. Your Legal Rights (DPDP Act & GDPR)
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            Regardless of your geographic location, Carbon Horizon guarantees the following fundamental privacy rights:
          </p>
          <ul className="grid sm:grid-cols-2 gap-3 text-xs sm:text-sm text-slate-300">
            <li className="p-3 rounded-xl bg-white/5 border border-white/5">
              <strong>Right to Access:</strong> Request a complete summary of your personal information held by us.
            </li>
            <li className="p-3 rounded-xl bg-white/5 border border-white/5">
              <strong>Right to Correction:</strong> Update inaccurate or incomplete profile and location details.
            </li>
            <li className="p-3 rounded-xl bg-white/5 border border-white/5">
              <strong>Right to Erasure:</strong> Request permanent deletion of your account and related records.
            </li>
            <li className="p-3 rounded-xl bg-white/5 border border-white/5">
              <strong>Right to Data Portability:</strong> Export your assessment records and logs in standard machine-readable JSON/CSV formats.
            </li>
            <li className="p-3 rounded-xl bg-white/5 border border-white/5">
              <strong>Right to Withdraw Consent:</strong> Revoke cookie or analytics consent at any time without penalty.
            </li>
            <li className="p-3 rounded-xl bg-white/5 border border-white/5">
              <strong>Right to Grievance Redressal:</strong> Contact our designated Data Protection Officer with questions or grievances.
            </li>
          </ul>
        </section>

        {/* Section 10: Contact */}
        <section className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4">
          <h2 className="text-xl font-bold text-primary flex items-center gap-2">
            <Mail className="w-5 h-5 text-earth-green" aria-hidden="true" />
            10. Contact Us & Grievance Officer
          </h2>
          <p className="text-slate-300 leading-relaxed text-sm sm:text-base">
            For privacy inquiries, rights requests, or questions regarding our data practices, please reach out to our privacy team:
          </p>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 inline-block text-sm">
            <p className="text-slate-200"><strong>Data Privacy Office</strong></p>
            <p className="text-slate-400">Carbon Horizon Technologies</p>
            <p className="text-earth-green font-mono mt-1">
              <a href="mailto:privacy@carbonhorizon.app" className="hover:underline">
                privacy@carbonhorizon.app
              </a>
            </p>
          </div>
        </section>
      </article>
    </PublicLayout>
  )
}
