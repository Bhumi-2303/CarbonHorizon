import { useState, useEffect, useRef } from 'react'
import { coachApi } from '@/api/coach'
import { Send, Sparkles, MessageSquare } from 'lucide-react'

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export default function StudentCoach() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom on new message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, loading])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input.trim() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const response = await coachApi.chat({
        message: userMsg.content,
        conversation_id: conversationId || undefined
      })
      if (response.conversation_id) setConversationId(response.conversation_id)
      
      const aiMsg: Message = { id: Date.now().toString(), role: 'assistant', content: response.message }
      setMessages(prev => [...prev, aiMsg])
    } catch (error) {
      console.error("Coach error:", error)
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', content: "Connection error. Please try again later." }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-160px)] max-w-3xl mx-auto glass-card border-indigo-500/20 overflow-hidden">
      
      {/* Header */}
      <div className="p-4 border-b border-indigo-500/20 bg-indigo-900/20 flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-black text-white font-poppins">Student Coach</h2>
          <p className="text-sm text-indigo-200 font-medium">Your personal guide to low-cost, high-impact sustainability.</p>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full opacity-50">
            <MessageSquare className="w-16 h-16 text-indigo-400 mb-4" />
            <p className="text-indigo-200 font-medium text-lg text-center px-8">
              Hey there! I can help you figure out how to reduce your carbon footprint while staying on a student budget. What's on your mind?
            </p>
          </div>
        )}
        
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl p-4 text-md ${
              msg.role === 'user' 
                ? 'bg-indigo-500 text-white rounded-tr-sm' 
                : 'bg-slate-800 border border-slate-700 text-slate-200 rounded-tl-sm'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-2xl rounded-tl-sm bg-slate-800 border border-slate-700 p-4 text-slate-400 flex items-center gap-2">
              <Sparkles className="w-4 h-4 animate-spin text-indigo-400" /> Thinking...
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-slate-700/50 bg-slate-900/50">
        <div className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask me anything..."
            className="w-full bg-[#08121E] border border-slate-700 rounded-xl pl-4 pr-14 py-4 text-white focus:outline-none focus:border-indigo-500 transition-colors"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="absolute right-2 top-2 bottom-2 aspect-square bg-indigo-500 hover:bg-indigo-400 text-white rounded-lg flex items-center justify-center disabled:opacity-50 transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
