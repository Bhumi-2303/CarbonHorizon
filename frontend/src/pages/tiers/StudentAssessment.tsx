import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { assessmentApi, AssessmentPayload } from '@/api/assessment'
import { Car, Bus, Footprints, Bike, Monitor, Lightbulb, Snowflake, Apple, Beef, Trash2, Recycle } from 'lucide-react'

type AnswerState = {
  commute: string
  distance: number
  ac: string
  electronics: string
  food: string
  waste: string
}

export default function StudentAssessment() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [submitting, setSubmitting] = useState(false)
  
  const [answers, setAnswers] = useState<AnswerState>({
    commute: 'bus',
    distance: 5,
    ac: 'rarely',
    electronics: 'medium',
    food: 'mixed',
    waste: 'some'
  })

  const nextStep = () => {
    if (step < 4) setStep(step + 1)
  }

  const prevStep = () => {
    if (step > 1) setStep(step - 1)
  }

  const handleSubmit = async () => {
    setSubmitting(true)

    let electricityKwh = 10
    if (answers.electronics === 'high') electricityKwh = 25
    else if (answers.electronics === 'low') electricityKwh = 5

    let acHours = 0
    if (answers.ac === 'frequently') acHours = 6
    else if (answers.ac === 'sometimes') acHours = 2

    let plasticScore = 5
    let recycleScore = 5
    if (answers.waste === 'great') { plasticScore = 1; recycleScore = 10 }
    else if (answers.waste === 'poor') { plasticScore = 9; recycleScore = 0 }

    const payload: AssessmentPayload = {
      transport_mode: answers.commute as any,
      distance_km: answers.distance,
      electricity_kwh: electricityKwh,
      ac_hours: acHours,
      lpg_usage: 0,
      solar_usage: false,
      diet_type: answers.food === 'vegetarian' ? 'vegetarian' : 'non_vegetarian',
      recycling_score: recycleScore,
      plastic_usage_score: plasticScore,
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
      <div className="w-full bg-white/10 rounded-full h-2 mb-8 overflow-hidden">
        <div 
          className="bg-emerald-400 h-full transition-all duration-500"
          style={{ width: `${(step / 4) * 100}%` }}
        />
      </div>

      <div className="glass-card w-full p-8 animate-fade-shift-up border-emerald-500/20">
        
        {step === 1 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-primary mb-2">How do you get to school or college?</h2>
            <p className="text-slate-400 mb-6">Transportation makes up a huge part of a student's carbon footprint.</p>
            
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
              {[
                { id: 'walk', icon: Footprints, label: 'Walk' },
                { id: 'bicycle', icon: Bike, label: 'Bike' },
                { id: 'bus', icon: Bus, label: 'Bus' },
                { id: 'car', icon: Car, label: 'Car' }
              ].map(mode => (
                <button 
                  key={mode.id}
                  onClick={() => setAnswers(prev => ({ ...prev, commute: mode.id }))}
                  className={`p-4 rounded-2xl border-2 flex flex-col items-center gap-3 transition-all ${answers.commute === mode.id ? 'border-emerald-400 bg-emerald-400/10 text-emerald-400' : 'border-slate-700 text-slate-400 hover:border-slate-500 hover:bg-white/5'}`}
                >
                  <mode.icon className="w-8 h-8" />
                  <span className="font-semibold text-sm">{mode.label}</span>
                </button>
              ))}
            </div>

            {(answers.commute === 'car' || answers.commute === 'bus' || answers.commute === 'bicycle') && (
              <div className="space-y-4 bg-white/10/30 p-6 rounded-2xl border border-slate-700/50">
                <label className="text-primary font-medium block">Round trip distance (km)</label>
                <input 
                  type="range" 
                  min="1" max="50" 
                  value={answers.distance} 
                  onChange={(e) => setAnswers(prev => ({ ...prev, distance: Number(e.target.value) }))}
                  className="w-full accent-emerald-400"
                />
                <div className="text-center text-emerald-400 font-bold text-xl">{answers.distance} km</div>
              </div>
            )}
          </div>
        )}

        {step === 2 && (
          <div className="space-y-8">
            <h2 className="text-2xl font-bold text-primary mb-2">Dorm & Bedroom Energy</h2>
            <p className="text-slate-400 mb-6">Laptops, gaming consoles, and AC units use more energy than you think.</p>
            
            <div className="space-y-4">
              <label className="text-primary font-medium flex items-center gap-2"><Monitor className="w-5 h-5 text-sky-400"/> Daily Electronics & Light Usage</label>
              <div className="flex bg-white/10 rounded-xl p-1 border border-slate-700">
                <button onClick={() => setAnswers(prev => ({...prev, electronics: 'low'}))} className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${answers.electronics === 'low' ? 'bg-sky-500 text-primary shadow-lg' : 'text-slate-400 hover:text-primary'}`}>Low (Mostly offline)</button>
                <button onClick={() => setAnswers(prev => ({...prev, electronics: 'medium'}))} className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${answers.electronics === 'medium' ? 'bg-sky-500 text-primary shadow-lg' : 'text-slate-400 hover:text-primary'}`}>Medium (Average)</button>
                <button onClick={() => setAnswers(prev => ({...prev, electronics: 'high'}))} className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${answers.electronics === 'high' ? 'bg-sky-500 text-primary shadow-lg' : 'text-slate-400 hover:text-primary'}`}>High (Always plugged in)</button>
              </div>
            </div>

            <div className="space-y-4">
              <label className="text-primary font-medium flex items-center gap-2"><Snowflake className="w-5 h-5 text-sky-400"/> Air Conditioning / Heating</label>
              <div className="flex bg-white/10 rounded-xl p-1 border border-slate-700">
                <button onClick={() => setAnswers(prev => ({...prev, ac: 'rarely'}))} className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${answers.ac === 'rarely' ? 'bg-sky-500 text-primary shadow-lg' : 'text-slate-400 hover:text-primary'}`}>Rarely</button>
                <button onClick={() => setAnswers(prev => ({...prev, ac: 'sometimes'}))} className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${answers.ac === 'sometimes' ? 'bg-sky-500 text-primary shadow-lg' : 'text-slate-400 hover:text-primary'}`}>A few hours</button>
                <button onClick={() => setAnswers(prev => ({...prev, ac: 'frequently'}))} className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${answers.ac === 'frequently' ? 'bg-sky-500 text-primary shadow-lg' : 'text-slate-400 hover:text-primary'}`}>Most of the day</button>
              </div>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-8">
            <h2 className="text-2xl font-bold text-primary mb-2">Food & Diet</h2>
            <p className="text-slate-400 mb-6">Meat and dairy production create significant greenhouse gases.</p>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button 
                onClick={() => setAnswers(prev => ({ ...prev, food: 'vegetarian' }))}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.food === 'vegetarian' ? 'border-emerald-400 bg-emerald-400/10 text-emerald-400' : 'border-slate-700 text-slate-400 hover:border-slate-500 hover:bg-white/5'}`}
              >
                <Apple className="w-12 h-12" />
                <span className="font-bold text-lg">Vegetarian / Vegan</span>
              </button>
              <button 
                onClick={() => setAnswers(prev => ({ ...prev, food: 'mixed' }))}
                className={`p-6 rounded-2xl border-2 flex flex-col items-center gap-4 transition-all ${answers.food === 'mixed' ? 'border-rose-400 bg-rose-400/10 text-rose-400' : 'border-slate-700 text-slate-400 hover:border-slate-500 hover:bg-white/5'}`}
              >
                <Beef className="w-12 h-12" />
                <span className="font-bold text-lg">Mixed (Meat & Dairy)</span>
              </button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-8">
            <h2 className="text-2xl font-bold text-primary mb-2">Waste & Recycling</h2>
            <p className="text-slate-400 mb-6">How often do you use reusable bottles and recycle paper/plastics?</p>
            
            <div className="space-y-4">
              <div className="flex flex-col gap-3">
                <button onClick={() => setAnswers(prev => ({...prev, waste: 'great'}))} className={`p-4 rounded-xl border text-left flex items-center gap-4 transition-all ${answers.waste === 'great' ? 'border-emerald-400 bg-emerald-400/10 text-emerald-400' : 'border-slate-700 text-muted hover:border-slate-500 hover:bg-white/5'}`}>
                  <Recycle className="w-6 h-6 flex-shrink-0" />
                  <div>
                    <div className="font-bold">Always</div>
                    <div className="text-sm opacity-70">I always use a reusable bottle and recycle my notes.</div>
                  </div>
                </button>
                <button onClick={() => setAnswers(prev => ({...prev, waste: 'some'}))} className={`p-4 rounded-xl border text-left flex items-center gap-4 transition-all ${answers.waste === 'some' ? 'border-amber-400 bg-amber-400/10 text-amber-400' : 'border-slate-700 text-muted hover:border-slate-500 hover:bg-white/5'}`}>
                  <Lightbulb className="w-6 h-6 flex-shrink-0" />
                  <div>
                    <div className="font-bold">Sometimes</div>
                    <div className="text-sm opacity-70">I try my best, but sometimes I forget.</div>
                  </div>
                </button>
                <button onClick={() => setAnswers(prev => ({...prev, waste: 'poor'}))} className={`p-4 rounded-xl border text-left flex items-center gap-4 transition-all ${answers.waste === 'poor' ? 'border-rose-400 bg-rose-400/10 text-rose-400' : 'border-slate-700 text-muted hover:border-slate-500 hover:bg-white/5'}`}>
                  <Trash2 className="w-6 h-6 flex-shrink-0" />
                  <div>
                    <div className="font-bold">Rarely</div>
                    <div className="text-sm opacity-70">I mostly use single-use plastics and don't recycle much.</div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-10 pt-6 border-t border-slate-700/50">
          {step > 1 ? (
            <button onClick={prevStep} className="px-6 py-2 text-slate-400 hover:text-primary font-bold transition-colors">
              Back
            </button>
          ) : <div></div>}
          
          {step < 4 ? (
            <button onClick={nextStep} className="px-8 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-900 rounded-full font-bold shadow-lg shadow-emerald-500/20 transition-all">
              Next
            </button>
          ) : (
            <button 
              onClick={handleSubmit} 
              disabled={submitting}
              className="px-8 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-900 rounded-full font-bold shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
            >
              {submitting ? 'Calculating...' : 'See My Footprint'}
            </button>
          )}
        </div>

      </div>
    </div>
  )
}
