import { useEffect, useState, useRef, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { v4 as uuidv4 } from 'uuid'
import { assessmentApi, type AssessmentResult } from '@/api/assessment'
import { coachApi } from '@/api/coach'
import { Leaf, MessageCircle, Send, MapPin } from 'lucide-react'

// Local interface to handle optimistic UI updates
interface UIContextMessage {
  id: string
  role: 'user' | 'assistant'
  message: string
  created_at: string
}

export default function AICoach() {
  const navigate = useNavigate()
  
  // App context state
  const [baseline, setBaseline] = useState<AssessmentResult | null>(null)
  const [contextLoading, setContextLoading] = useState(true)

  // Chat state
  const [conversationId, setConversationId] = useState<string>('')
  const [messages, setMessages] = useState<UIContextMessage[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Determine top emission source
  const getTopSource = (assessment: AssessmentResult) => {
    const sources = [
      { name: 'Transport', val: assessment.transport },
      { name: 'Energy', val: assessment.energy },
      { name: 'Food', val: assessment.food },
      { name: 'Waste', val: assessment.waste },
    ]
    sources.sort((a, b) => b.val - a.val)
    return sources[0]
  }

  // Load baseline context and conversation history on mount
  useEffect(() => {
    const init = async () => {
      // 1. Fetch latest assessment
      try {
        const history = await assessmentApi.history()
        if (history && history.length > 0) {
          const latest = [...history].sort(
            (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          )[0]
          setBaseline(latest)
        }
      } catch (err) {
        console.error('Failed to load assessment baseline', err)
      } finally {
        setContextLoading(false)
      }

      // 2. Initialize or load conversation
      const storedId = localStorage.getItem('coach_conversation_id')
      if (storedId) {
        setConversationId(storedId)

        try {
          const chatHistory = await coachApi.history(storedId)
          if (chatHistory && chatHistory.history) {
            setMessages(chatHistory.history.sort(
              (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
            ))
          }
        } catch (err) {
          console.error('Failed to load chat history', err)
        }
      }
    }

    init()
  }, [])

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSend = async (e?: FormEvent) => {
    if (e) e.preventDefault()
    if (!input.trim() || isTyping) return

    const userMsg = input.trim()
    setInput('')
    
    // Optimistic update
    const tempId = uuidv4()
    setMessages(prev => [
      ...prev, 
      { id: tempId, role: 'user', message: userMsg, created_at: new Date().toISOString() }
    ])
    setIsTyping(true)

    try {
      const response = await coachApi.chat({
        ...(conversationId ? { conversation_id: conversationId } : {}),
        message: userMsg
      })
      
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id)
        localStorage.setItem('coach_conversation_id', response.conversation_id)
      }
      
      // Update with assistant's response
      setMessages(prev => [
        ...prev,
        {
          id: uuidv4(),
          role: 'assistant',
          message: response.message,
          created_at: new Date().toISOString()
        }
      ])
    } catch (err) {
      console.error('Failed to send message', err)
      let errorMsg = 'AI Coach is temporarily busy. Please try again in a moment.'
      if (err instanceof Error && err.message) {
        // Prevent raw provider payloads from ever reaching the UI
        if (err.message.includes('503 UNAVAILABLE') || err.message.includes('{') || err.message.includes('error:')) {
          errorMsg = 'AI Coach is temporarily busy. Please try again in a moment.'
        } else {
          errorMsg = err.message
        }
      }
      // Add error message as system/assistant notification
      setMessages(prev => [
        ...prev,
        {
          id: uuidv4(),
          role: 'assistant',
          message: errorMsg,
          created_at: new Date().toISOString()
        }
      ])
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 flex flex-col pt-16 lg:pt-0">
      
      {/* Background orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden z-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-earth-green/5 blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full bg-earth-green/20 blur-3xl" />
      </div>

      <div className="flex-1 flex flex-col lg:flex-row relative z-10 max-w-7xl mx-auto w-full p-4 lg:p-8 gap-6 h-[100dvh]">
        
        {/* ── Context Panel (Left on Desktop, Top on Mobile) ── */}
        <div className="w-full lg:w-80 flex-shrink-0 flex flex-col gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-1.5 text-xs text-muted hover:text-slate-300 transition-colors self-start"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </button>
          
          <div className="bg-deep-ocean/50 border border-slate-700/50 rounded-2xl p-5 shadow-lg backdrop-blur-md">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/10
                border border-earth-green/30 flex items-center justify-center">
                <Leaf className="w-5 h-5 text-[#2ECC71]" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-100">AI Coach</h1>
                <p className="text-xs text-muted">Your sustainability guide</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold text-muted uppercase tracking-widest mb-2">
                  Current Profile
                </p>
                {contextLoading ? (
                  <div className="animate-pulse space-y-2">
                    <div className="h-10 bg-slate-700/50 rounded-xl" />
                    <div className="h-10 bg-slate-700/50 rounded-xl" />
                  </div>
                ) : baseline ? (
                  <div className="space-y-3">
                    <div className="flex justify-between items-center bg-deep-ocean/50 border border-slate-700/40 p-3 rounded-xl">
                      <span className="text-sm text-muted">Carbon Score</span>
                      <span className="text-lg font-bold text-earth-green">{baseline.carbon_score.toFixed(0)}</span>
                    </div>
                    <div className="flex justify-between items-center bg-deep-ocean/50 border border-slate-700/40 p-3 rounded-xl">
                      <span className="text-sm text-muted">Top Source</span>
                      <div className="text-right">
                        <p className="text-sm font-bold text-rose-400">{getTopSource(baseline).name}</p>
                        <p className="text-xs text-muted">{getTopSource(baseline).val.toFixed(1)} kg</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-deep-ocean/50 border border-slate-700/40 p-4 rounded-xl text-center">
                    <p className="text-sm text-muted mb-2">No assessment found.</p>
                    <button
                      onClick={() => navigate('/assessment/new')}
                      className="text-xs text-earth-green hover:text-emerald-300 underline underline-offset-2"
                    >
                      Complete your first assessment
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ── Chat Interface (Right side / Main) ── */}
        <div className="flex-1 flex flex-col bg-deep-ocean/40 border border-slate-700/50 rounded-2xl shadow-xl backdrop-blur-md overflow-hidden h-full min-h-0">
          
          {/* Chat Header */}
          <div className="px-6 py-4 border-b border-slate-700/50 bg-deep-ocean/60 flex justify-between items-center shrink-0">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Conversation</h2>
              <p className="text-xs text-muted">Ask me anything about your footprint or habits</p>
            </div>
            {isTyping && (
              <span className="text-xs font-medium text-earth-green animate-pulse bg-earth-green/10 px-2 py-1 rounded-md border border-earth-green/20">
                Coach is typing...
              </span>
            )}
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 scroll-smooth" role="log" aria-live="polite">
            {messages.length === 0 && !isTyping && (
              <div className="h-full flex flex-col items-center justify-center text-center opacity-70">
                <MessageCircle className="w-10 h-10 mb-4 text-muted" />
                <p className="text-slate-300 font-medium">No messages yet</p>
                <p className="text-sm text-muted mt-2 max-w-sm">
                  Try asking how you can reduce your top emission source or ask for an eco-friendly recipe!
                </p>
              </div>
            )}
            
            <div className="space-y-6">
              {messages.map(msg => {
                const isOutOfScope = msg.message.trim() === "That falls outside my area of expertise. I'm here to help you understand and reduce your carbon footprint. Is there a sustainability question I can help you with?";
                return (
                <div 
                  key={msg.id} 
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`
                    ${msg.role === 'user' ? 'bg-forest-green/90 backdrop-blur-sm text-white rounded-2xl rounded-br-sm px-4 py-3 max-w-xs ml-auto shadow-md' : ''}
                    ${msg.role === 'assistant' && !isOutOfScope ? 'bg-deep-ocean/70 backdrop-blur-md border border-earth-green/30 text-white rounded-2xl rounded-bl-sm px-5 py-4 max-w-[85%] shadow-lg' : ''}
                    ${msg.role === 'assistant' && isOutOfScope ? 'bg-deep-ocean/50 border-earth-green/20 border-l-4 border-warning text-muted italic rounded-2xl rounded-bl-sm px-4 py-3 max-w-sm' : ''}
                  `} aria-label={msg.role === 'user' ? 'You said' : 'Coach said'}>
                    {msg.role === 'assistant' ? (
                      <div className="text-sm leading-relaxed whitespace-pre-wrap 
                          prose prose-invert prose-p:my-2 prose-strong:text-white prose-a:text-earth-green max-w-none">
                        <ReactMarkdown
                          components={{
                            blockquote: ({ children }) => (
                                <blockquote className="localized-context border-l-4 border-emerald-400 bg-emerald-500/10 text-emerald-100 p-3 rounded-r my-4 text-sm font-medium shadow-[0_2px_10px_rgba(16,185,129,0.1)]">
                                <MapPin className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                                <div className="text-xs text-emerald-100/90 font-medium [&>p]:m-0">
                                  {children}
                                </div>
                              </blockquote>
                            ),
                            ul: ({ node, children, ...props }) => (
                              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3 my-4 pl-0" {...props}>
                                {children}
                              </ul>
                            ),
                            li: ({ node, children, ...props }) => (
                              <li className="bg-slate-800/40 border border-slate-700/50 p-3.5 rounded-xl shadow-sm text-slate-200 list-none m-0" {...props}>
                                {children}
                              </li>
                            )
                          }}
                        >
                          {msg.message}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.message}</p>
                    )}
                  </div>
                </div>
              )})}
              
              {/* Typing indicator */}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-deep-ocean border border-earth-green/20 text-white rounded-2xl rounded-bl-sm px-4 py-3 max-w-sm flex items-center gap-1.5 h-[52px]" aria-label="Coach is typing">
                    <span className="w-1.5 h-1.5 bg-earth-green rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="w-1.5 h-1.5 bg-earth-green rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                    <span className="w-1.5 h-1.5 bg-earth-green rounded-full animate-bounce"></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="p-4 bg-deep-ocean/80 border-t border-slate-700/50 shrink-0">
            <form onSubmit={handleSend} className="relative flex items-end gap-2 max-w-4xl mx-auto" aria-label="Send message to Coach">
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask your coach..."
                aria-label="Ask your coach"
                className="w-full bg-space-black border border-earth-green/30 text-white rounded-xl px-4 py-3 focus:border-earth-green focus:outline-none resize-none min-h-[52px] max-h-32"
                rows={1}
                style={{ height: 'auto', minHeight: '52px' }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement
                  target.style.height = '52px'
                  target.style.height = `${Math.min(target.scrollHeight, 128)}px`
                }}
              />
              <button
                type="submit"
                disabled={!input.trim() || isTyping}
                aria-label="Send message"
                className="flex-shrink-0 w-[52px] h-[52px] flex items-center justify-center bg-transparent text-earth-green disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
            <p className="text-[10px] text-muted text-center mt-2">
              Carbon Horizon Coach can make mistakes. Verify important sustainability facts.
            </p>
          </div>

        </div>
      </div>
    </div>
  )
}
