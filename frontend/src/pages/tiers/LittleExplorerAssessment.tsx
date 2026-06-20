import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { assessmentApi, AssessmentPayload } from '@/api/assessment'
import { Car, Bus, Footprints, Droplet, Lightbulb, Apple, Beef, Trash2, Recycle } from 'lucide-react'

type AnswerState = {
  transport: string
  lights: string
  plastic: string
  food: string
  recycle: string
}

export default function LittleExplorerAssessment() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [submitting, setSubmitting] = useState(false)
  
  const [answers, setAnswers] = useState<AnswerState>({
    transport: '',
    lights: '',
    plastic: '',
    food: '',
    recycle: ''
  })

  const handleSelect = (category: keyof AnswerState, value: string) => {
    setAnswers(prev => ({ ...prev, [category]: value }))
    setTimeout(() => {
      if (step < 5) setStep(step + 1)
    }, 400)
  }

  const handleSubmit = async () => {
    setSubmitting(true)

    // Map kid answers to adult AssessmentInputs
    const payload: AssessmentPayload = {
      transport_mode: answers.transport === 'walk' ? 'bicycle' : answers.transport === 'bus' ? 'bus' : 'car',
      distance_km: answers.transport === 'walk' ? 0 : 5,
      electricity_kwh: answers.lights === 'off' ? 20 : 100, // Dummy mapping to affect score
      ac_hours: 0,
      lpg_usage: 0,
      solar_usage: false,
      diet_type: answers.food === 'veggies' ? 'vegetarian' : 'non_vegetarian',
      recycling_score: answers.recycle === 'yes' ? 10 : 0,
      plastic_usage_score: answers.plastic === 'reusable' ? 0 : 8,
      household_size: 1,
      assessment_period: 'daily'
    }

    try {
      await assessmentApi.create(payload)
      navigate('/dashboard')
    } catch (error) {
      console.error("Failed to submit assessment:", error)
      setSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] max-w-2xl mx-auto px-4">
      
      {/* Progress Bar */}
      <div className="w-full bg-slate-800 rounded-full h-4 mb-8 overflow-hidden">
        <div 
          className="bg-emerald-400 h-4 rounded-full transition-all duration-500"
          style={{ width: `${(step / 5) * 100}%` }}
        />
      </div>

      <div className="glass-card w-full p-8 text-center animate-fade-shift-up">
        {step === 1 && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-8">How did you get around today?</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <button 
                onClick={() => handleSelect('transport', 'walk')}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.transport === 'walk' ? 'border-emerald-400 bg-emerald-400/20' : 'border-slate-700 hover:border-emerald-400/50 hover:bg-white/5'}`}
              >
                <Footprints className="w-16 h-16 text-emerald-400" />
                <span className="text-xl font-semibold text-slate-200">Walk / Bike</span>
              </button>
              <button 
                onClick={() => handleSelect('transport', 'bus')}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.transport === 'bus' ? 'border-sky-400 bg-sky-400/20' : 'border-slate-700 hover:border-sky-400/50 hover:bg-white/5'}`}
              >
                <Bus className="w-16 h-16 text-sky-400" />
                <span className="text-xl font-semibold text-slate-200">School Bus</span>
              </button>
              <button 
                onClick={() => handleSelect('transport', 'car')}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.transport === 'car' ? 'border-rose-400 bg-rose-400/20' : 'border-slate-700 hover:border-rose-400/50 hover:bg-white/5'}`}
              >
                <Car className="w-16 h-16 text-rose-400" />
                <span className="text-xl font-semibold text-slate-200">Car</span>
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-8">Did you turn off the lights when leaving a room?</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button 
                onClick={() => handleSelect('lights', 'off')}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.lights === 'off' ? 'border-amber-400 bg-amber-400/20' : 'border-slate-700 hover:border-amber-400/50 hover:bg-white/5'}`}
              >
                <Lightbulb className="w-16 h-16 text-amber-400" />
                <span className="text-xl font-semibold text-slate-200">Yes, I remembered!</span>
              </button>
              <button 
                onClick={() => handleSelect('lights', 'on')}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.lights === 'on' ? 'border-slate-500 bg-slate-500/20' : 'border-slate-700 hover:border-slate-500/50 hover:bg-white/5'}`}
              >
                <Lightbulb className="w-16 h-16 text-slate-500 opacity-50" />
                <span className="text-xl font-semibold text-slate-200">Oops, I forgot</span>
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-8">What did you drink from today?</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button 
                onClick={() => handleSelect('plastic', 'reusable')}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.plastic === 'reusable' ? 'border-sky-400 bg-sky-400/20' : 'border-slate-700 hover:border-sky-400/50 hover:bg-white/5'}`}
              >
                <Droplet className="w-16 h-16 text-sky-400" />
                <span className="text-xl font-semibold text-slate-200">My Reusable Bottle</span>
              </button>
              <button 
                onClick={() => handleSelect('plastic', 'plastic')}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.plastic === 'plastic' ? 'border-rose-400 bg-rose-400/20' : 'border-slate-700 hover:border-rose-400/50 hover:bg-white/5'}`}
              >
                <Trash2 className="w-16 h-16 text-rose-400" />
                <span className="text-xl font-semibold text-slate-200">A Plastic Bottle</span>
              </button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-8">What kind of food did you eat mostly?</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button 
                onClick={() => handleSelect('food', 'veggies')}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.food === 'veggies' ? 'border-emerald-400 bg-emerald-400/20' : 'border-slate-700 hover:border-emerald-400/50 hover:bg-white/5'}`}
              >
                <Apple className="w-16 h-16 text-emerald-400" />
                <span className="text-xl font-semibold text-slate-200">Fruits & Veggies</span>
              </button>
              <button 
                onClick={() => handleSelect('food', 'meat')}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.food === 'meat' ? 'border-rose-400 bg-rose-400/20' : 'border-slate-700 hover:border-rose-400/50 hover:bg-white/5'}`}
              >
                <Beef className="w-16 h-16 text-rose-400" />
                <span className="text-xl font-semibold text-slate-200">Meat & Dairy</span>
              </button>
            </div>
          </div>
        )}

        {step === 5 && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-8">Did you recycle any paper or plastic today?</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
              <button 
                onClick={() => setAnswers(prev => ({ ...prev, recycle: 'yes' }))}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.recycle === 'yes' ? 'border-emerald-400 bg-emerald-400/20' : 'border-slate-700 hover:border-emerald-400/50 hover:bg-white/5'}`}
              >
                <Recycle className="w-16 h-16 text-emerald-400" />
                <span className="text-xl font-semibold text-slate-200">Yes!</span>
              </button>
              <button 
                onClick={() => setAnswers(prev => ({ ...prev, recycle: 'no' }))}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.recycle === 'no' ? 'border-slate-500 bg-slate-500/20' : 'border-slate-700 hover:border-slate-500/50 hover:bg-white/5'}`}
              >
                <Trash2 className="w-16 h-16 text-slate-500" />
                <span className="text-xl font-semibold text-slate-200">Not today</span>
              </button>
            </div>
            
            {answers.recycle && (
              <button 
                onClick={handleSubmit}
                disabled={submitting}
                className="w-full py-4 bg-gradient-to-r from-earth-green to-forest-green hover:from-emerald-500 hover:to-emerald-600 text-white rounded-xl text-xl font-bold transition-all shadow-lg hover:shadow-emerald-500/25 disabled:opacity-50"
              >
                {submitting ? 'Saving...' : 'Finish!'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
