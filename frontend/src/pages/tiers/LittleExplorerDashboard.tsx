import { useEffect, useState } from 'react'
import { assessmentApi, AssessmentResult } from '@/api/assessment'
import { Leaf, Award, CheckCircle2, Circle, Sun, Droplet, TreePine, Cloud, Flame, Wind } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function LittleExplorerDashboard() {
  const [assessment, setAssessment] = useState<AssessmentResult | null>(null)
  const [actions, setActions] = useState({
    water: false,
    lights: false,
    snack: false,
  })

  useEffect(() => {
    assessmentApi.history()
      .then(data => setAssessment(data[0] || null))
      .catch(console.error)
  }, [])

  const toggleAction = (key: keyof typeof actions) => {
    setActions(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const score = assessment ? Math.round(assessment.carbon_score) : 0

  let title = "Seedling"
  let titleColor = "text-amber-500"
  let message = "Let's learn how to help nature!"
  
  if (score >= 90) { title = "Planet Protector"; titleColor = "text-emerald-400"; message = "Wow! You are doing amazing things for our Earth!" }
  else if (score >= 75) { title = "Green Explorer"; titleColor = "text-emerald-500"; message = "Great job! You are finding new ways to help." }
  else if (score >= 60) { title = "Earth Helper"; titleColor = "text-teal-400"; message = "Thank you for being a good friend to nature." }
  else if (score >= 40) { title = "Nature Friend"; titleColor = "text-sky-400"; message = "Every little thing you do makes a big difference!" }

  // Animated circle stroke offset
  const radius = 60
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (score / 100) * circumference

  return (
    <div className="flex flex-col gap-8 pb-12 animate-fade-shift-up">
      
      {/* Top Banner: Score & Title */}
      <div className="glass-card p-6 md:p-8 flex flex-col md:flex-row items-center gap-8 justify-between relative overflow-hidden border-emerald-500/20">
        <div className="absolute -right-12 -top-12 opacity-10 pointer-events-none">
          <Sun className="w-64 h-64 text-amber-400" />
        </div>
        
        <div className="flex-1 text-center md:text-left z-10">
          <h1 className="text-4xl font-black text-primary mb-2 font-poppins">{title}</h1>
          <p className="text-xl text-muted mb-6">{message}</p>
          {!assessment && (
            <Link to="/assessment" className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-slate-900 px-6 py-3 rounded-full font-bold transition-all shadow-lg shadow-emerald-500/20">
              <Leaf className="w-5 h-5" /> Play the Nature Game!
            </Link>
          )}
        </div>

        <div className="relative flex items-center justify-center z-10 bg-bg-secondary/50 rounded-full p-4">
          <svg className="w-40 h-40 transform -rotate-90">
            <circle
              cx="80"
              cy="80"
              r={radius}
              stroke="currentColor"
              strokeWidth="12"
              fill="transparent"
              className="text-slate-700/50"
            />
            <circle
              cx="80"
              cy="80"
              r={radius}
              stroke="currentColor"
              strokeWidth="12"
              fill="transparent"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className={`transition-all duration-1000 ease-out ${titleColor}`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute flex flex-col items-center justify-center">
            <span className="text-4xl font-black text-primary font-poppins">{score}</span>
            <span className="text-xs text-slate-400 uppercase font-bold tracking-wider">Eco Score</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Today's Nature Mission */}
        <div className="glass-card p-6 border-sky-500/20">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-sky-400/20 flex items-center justify-center">
              <Wind className="w-5 h-5 text-sky-400" />
            </div>
            <h2 className="text-2xl font-bold text-primary font-poppins">Today's Nature Mission</h2>
          </div>
          <div className="space-y-4">
            <div className="bg-white/10/50 p-4 rounded-xl border border-slate-700">
              <h3 className="font-bold text-sky-300 text-lg">Turn off the water while brushing teeth!</h3>
              <p className="text-slate-400 mt-1 flex items-center gap-2"><Droplet className="w-4 h-4 text-blue-400"/> Keeps the rivers full for the fish.</p>
            </div>
            <div className="bg-white/10/50 p-4 rounded-xl border border-slate-700">
              <h3 className="font-bold text-amber-300 text-lg">Turn off the lights when leaving a room!</h3>
              <p className="text-slate-400 mt-1 flex items-center gap-2"><Sun className="w-4 h-4 text-amber-400"/> Helps the trees rest at night.</p>
            </div>
          </div>
        </div>

        {/* My Green Actions Today */}
        <div className="glass-card p-6 border-emerald-500/20">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-emerald-400/20 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            </div>
            <h2 className="text-2xl font-bold text-primary font-poppins">My Green Actions</h2>
          </div>
          <div className="space-y-3">
            <button onClick={() => toggleAction('water')} className={`w-full text-left flex items-center gap-4 p-4 rounded-xl border transition-all ${actions.water ? 'bg-emerald-400/10 border-emerald-400/30' : 'bg-white/10/50 border-slate-700 hover:border-slate-500'}`}>
              {actions.water ? <CheckCircle2 className="w-8 h-8 text-emerald-400 flex-shrink-0" /> : <Circle className="w-8 h-8 text-slate-500 flex-shrink-0" />}
              <span className={`text-lg font-medium ${actions.water ? 'text-primary' : 'text-muted'}`}>I saved water today</span>
            </button>
            <button onClick={() => toggleAction('lights')} className={`w-full text-left flex items-center gap-4 p-4 rounded-xl border transition-all ${actions.lights ? 'bg-amber-400/10 border-amber-400/30' : 'bg-white/10/50 border-slate-700 hover:border-slate-500'}`}>
              {actions.lights ? <CheckCircle2 className="w-8 h-8 text-amber-400 flex-shrink-0" /> : <Circle className="w-8 h-8 text-slate-500 flex-shrink-0" />}
              <span className={`text-lg font-medium ${actions.lights ? 'text-primary' : 'text-muted'}`}>I saved electricity today</span>
            </button>
            <button onClick={() => toggleAction('snack')} className={`w-full text-left flex items-center gap-4 p-4 rounded-xl border transition-all ${actions.snack ? 'bg-rose-400/10 border-rose-400/30' : 'bg-white/10/50 border-slate-700 hover:border-slate-500'}`}>
              {actions.snack ? <CheckCircle2 className="w-8 h-8 text-rose-400 flex-shrink-0" /> : <Circle className="w-8 h-8 text-slate-500 flex-shrink-0" />}
              <span className={`text-lg font-medium ${actions.snack ? 'text-primary' : 'text-muted'}`}>I ate all my healthy snack</span>
            </button>
          </div>
        </div>
      </div>

      {/* Nature Learning Corner */}
      <div className="glass-card p-6 border-purple-500/20">
        <h2 className="text-2xl font-bold text-primary font-poppins mb-6 flex items-center gap-3">
          <TreePine className="w-6 h-6 text-emerald-400" /> Nature Learning Corner
        </h2>
        <div className="flex gap-4 overflow-x-auto pb-4 snap-x">
          <div className="min-w-[250px] bg-gradient-to-br from-emerald-900/50 to-slate-900 p-6 rounded-2xl border border-emerald-500/30 snap-start">
            <Leaf className="w-12 h-12 text-emerald-400 mb-4" />
            <h3 className="text-xl font-bold text-primary mb-2">Planet Protector</h3>
            <p className="text-slate-400">The highest rank! You protect all animals and trees.</p>
          </div>
          <div className="min-w-[250px] bg-gradient-to-br from-sky-900/50 to-slate-900 p-6 rounded-2xl border border-sky-500/30 snap-start">
            <Cloud className="w-12 h-12 text-sky-400 mb-4" />
            <h3 className="text-xl font-bold text-primary mb-2">Green Explorer</h3>
            <p className="text-slate-400">Always learning new ways to keep the sky clear.</p>
          </div>
          <div className="min-w-[250px] bg-gradient-to-br from-teal-900/50 to-slate-900 p-6 rounded-2xl border border-teal-500/30 snap-start">
            <Droplet className="w-12 h-12 text-teal-400 mb-4" />
            <h3 className="text-xl font-bold text-primary mb-2">Earth Helper</h3>
            <p className="text-slate-400">Helping the rivers stay clean and full of fish.</p>
          </div>
          <div className="min-w-[250px] bg-gradient-to-br from-amber-900/50 to-slate-900 p-6 rounded-2xl border border-amber-500/30 snap-start">
            <Sun className="w-12 h-12 text-amber-400 mb-4" />
            <h3 className="text-xl font-bold text-primary mb-2">Nature Friend</h3>
            <p className="text-slate-400">A good friend to all the bugs, birds, and animals.</p>
          </div>
        </div>
      </div>

      {/* Achievement Badges */}
      <div className="glass-card p-6 border-amber-500/20">
        <h2 className="text-2xl font-bold text-primary font-poppins mb-6 flex items-center gap-3">
          <Award className="w-6 h-6 text-amber-400" /> My Badges
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-4">
          <div className={`flex flex-col items-center text-center p-4 rounded-xl ${score >= 10 ? 'bg-amber-400/20 border border-amber-400/50' : 'bg-white/10/30 opacity-50 border border-slate-700'}`}>
            <Sun className={`w-10 h-10 mb-2 ${score >= 10 ? 'text-amber-400' : 'text-slate-500'}`} />
            <span className="text-sm font-bold text-primary">First Step</span>
          </div>
          <div className={`flex flex-col items-center text-center p-4 rounded-xl ${score >= 20 ? 'bg-sky-400/20 border border-sky-400/50' : 'bg-white/10/30 opacity-50 border border-slate-700'}`}>
            <Droplet className={`w-10 h-10 mb-2 ${score >= 20 ? 'text-sky-400' : 'text-slate-500'}`} />
            <span className="text-sm font-bold text-primary">Water Saver</span>
          </div>
          <div className={`flex flex-col items-center text-center p-4 rounded-xl ${score >= 40 ? 'bg-emerald-400/20 border border-emerald-400/50' : 'bg-white/10/30 opacity-50 border border-slate-700'}`}>
            <Leaf className={`w-10 h-10 mb-2 ${score >= 40 ? 'text-emerald-400' : 'text-slate-500'}`} />
            <span className="text-sm font-bold text-primary">Tree Hugger</span>
          </div>
          <div className={`flex flex-col items-center text-center p-4 rounded-xl ${score >= 60 ? 'bg-rose-400/20 border border-rose-400/50' : 'bg-white/10/30 opacity-50 border border-slate-700'}`}>
            <Flame className={`w-10 h-10 mb-2 ${score >= 60 ? 'text-rose-400' : 'text-slate-500'}`} />
            <span className="text-sm font-bold text-primary">Energy Hero</span>
          </div>
          <div className={`flex flex-col items-center text-center p-4 rounded-xl ${score >= 75 ? 'bg-purple-400/20 border border-purple-400/50' : 'bg-white/10/30 opacity-50 border border-slate-700'}`}>
            <Wind className={`w-10 h-10 mb-2 ${score >= 75 ? 'text-purple-400' : 'text-slate-500'}`} />
            <span className="text-sm font-bold text-primary">Sky Cleaner</span>
          </div>
          <div className={`flex flex-col items-center text-center p-4 rounded-xl ${score >= 90 ? 'bg-teal-400/20 border border-teal-400/50' : 'bg-white/10/30 opacity-50 border border-slate-700'}`}>
            <TreePine className={`w-10 h-10 mb-2 ${score >= 90 ? 'text-teal-400' : 'text-slate-500'}`} />
            <span className="text-sm font-bold text-primary">Forest Friend</span>
          </div>
          <div className={`flex flex-col items-center text-center p-4 rounded-xl ${score >= 95 ? 'bg-amber-400/20 border border-amber-400/50 shadow-lg shadow-amber-400/20' : 'bg-white/10/30 opacity-50 border border-slate-700'}`}>
            <Award className={`w-10 h-10 mb-2 ${score >= 95 ? 'text-amber-400' : 'text-slate-500'}`} />
            <span className="text-sm font-bold text-primary">Earth Champion</span>
          </div>
        </div>
      </div>
    </div>
  )
}
