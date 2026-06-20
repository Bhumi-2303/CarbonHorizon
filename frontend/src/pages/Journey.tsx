import React, { useEffect, useState } from 'react';
import { Target, Leaf, TrendingDown, Clipboard, Award, Shield, Sprout, Compass, Globe, Star } from 'lucide-react';
import { progressionApi, ProgressionData } from '@/api/progression';

const Journey: React.FC = () => {
  const [data, setData] = useState<ProgressionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProgression = async () => {
      try {
        const response = await progressionApi.getProgression();
        setData(response.data);
      } catch (err) {
        setError('Failed to load journey data');
      } finally {
        setLoading(false);
      }
    };
    fetchProgression();
  }, []);

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'Seedling':
        return <Sprout className="w-12 h-12 text-emerald-400" />;
      case 'Green Explorer':
        return <Compass className="w-12 h-12 text-emerald-400" />;
      case 'Earth Guardian':
        return <Shield className="w-12 h-12 text-emerald-400" />;
      case 'Climate Champion':
        return <Star className="w-12 h-12 text-emerald-400" />;
      case 'Planet Protector':
        return <Globe className="w-12 h-12 text-emerald-400" />;
      default:
        return <Award className="w-12 h-12 text-emerald-400" />;
    }
  };

  const getBadgeIcon = (iconStr: string, unlocked: boolean) => {
    const props = {
      className: `w-8 h-8 ${unlocked ? 'text-emerald-400' : 'text-slate-500'}`,
    };
    switch (iconStr) {
      case 'footprint': return <Target {...props} />;
      case 'target': return <Target {...props} />;
      case 'leaf': return <Leaf {...props} />;
      case 'trending_down': return <TrendingDown {...props} />;
      case 'clipboard': return <Clipboard {...props} />;
      default: return <Award {...props} />;
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center text-red-400 glass-card mx-auto mt-20 max-w-lg">
        {error || 'Unable to load progression.'}
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in pb-12">
      {/* Hero Section: Level and Progress */}
      <section className="glass-card p-8 md:p-12 relative overflow-hidden flex flex-col items-center text-center">
        {/* Glow effect */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-emerald-500/20 blur-[100px] rounded-full pointer-events-none"></div>
        
        <div className="relative z-10 flex flex-col items-center gap-4">
          <div className="p-6 rounded-full bg-emerald-500/10 border border-emerald-500/20 shadow-[0_0_30px_rgba(16,185,129,0.15)]">
            {getLevelIcon(data.level)}
          </div>
          
          <div>
            <h1 className="text-4xl font-bold text-primary mb-2 tracking-tight">
              {data.level}
            </h1>
            <p className="text-muted">
              {data.points} / {data.next_level_points} Carbon Points
            </p>
          </div>

          <div className="w-full max-w-md mt-6">
            <div className="h-4 bg-white/10/80 rounded-full overflow-hidden border border-white/5">
              <div 
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-1000 ease-out"
                style={{ width: `${data.progress_percentage}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-xs text-slate-400 mt-2 font-medium">
              <span>Current Level</span>
              <span>{data.progress_percentage}% to Next Level</span>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-panel p-6 text-center">
          <div className="text-3xl font-bold text-emerald-400 mb-1">{data.stats.assessments_count}</div>
          <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Assessments</div>
        </div>
        <div className="glass-panel p-6 text-center">
          <div className="text-3xl font-bold text-teal-400 mb-1">{data.stats.goals_completed}</div>
          <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Goals Hit</div>
        </div>
        <div className="glass-panel p-6 text-center">
          <div className="text-3xl font-bold text-green-400 mb-1">{data.stats.habits_logged}</div>
          <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Eco Habits</div>
        </div>
        <div className="glass-panel p-6 text-center">
          <div className="text-3xl font-bold text-cyan-400 mb-1">{data.stats.emission_reduction_tons}t</div>
          <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">CO₂ Reduced</div>
        </div>
      </section>

      {/* Badges Grid */}
      <section>
        <h2 className="text-2xl font-bold text-primary mb-6 flex items-center gap-2">
          <Award className="text-emerald-400" />
          Missions & Badges
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.badges.map((badge) => (
            <div 
              key={badge.id}
              className={`glass-panel p-6 transition-all duration-300 flex items-start gap-4
                ${badge.unlocked 
                  ? 'bg-emerald-900/10 border-emerald-500/30 hover:border-emerald-500/50 shadow-[0_4px_20px_rgba(16,185,129,0.05)]' 
                  : 'opacity-60 grayscale hover:grayscale-0'
                }`}
            >
              <div className={`p-3 rounded-xl flex-shrink-0 ${badge.unlocked ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-white/10/50 border border-white/5'}`}>
                {getBadgeIcon(badge.icon, badge.unlocked)}
              </div>
              <div>
                <h3 className={`font-semibold text-lg mb-1 ${badge.unlocked ? 'text-primary' : 'text-muted'}`}>
                  {badge.name}
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  {badge.description}
                </p>
                {!badge.unlocked && (
                  <div className="mt-3 inline-flex items-center text-xs font-medium text-slate-500 bg-white/10/80 px-2 py-1 rounded">
                    Locked
                  </div>
                )}
                {badge.unlocked && (
                  <div className="mt-3 inline-flex items-center text-xs font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-1 rounded">
                    Unlocked
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default Journey;
