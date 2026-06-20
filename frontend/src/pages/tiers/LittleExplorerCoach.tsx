import { useState, useEffect, useRef } from 'react'
import { coachApi } from '@/api/coach'
import { Send, Bird, Sun } from 'lucide-react'

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export default function LittleExplorerCoach() {
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
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', content: "Oops! My bird friends are having trouble talking right now. Try again later!" }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-160px)] max-w-3xl mx-auto glass-card border-sky-500/20 overflow-hidden">
      
      {/* Header */}
      <div className="p-4 border-b border-sky-500/20 bg-sky-900/20 flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-sky-400 flex items-center justify-center shadow-lg shadow-sky-400/20">
          <Bird className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h2 className="text-xl font-black text-primary font-poppins">Nature Guide</h2>
          <p className="text-sm text-sky-200 font-medium">Ask me how to help animals and trees!</p>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full opacity-50">
            <Sun className="w-16 h-16 text-amber-400 mb-4 animate-pulse" />
            <p className="text-amber-200 font-medium text-lg text-center px-8">
              Hello Little Explorer! <br/> I am your Nature Guide. How can we help the Earth today?
            </p>
          </div>
        )}
        
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl p-4 text-lg ${
              msg.role === 'user' 
                ? 'bg-sky-500 text-primary rounded-tr-sm' 
                : 'bg-white/10 border border-slate-700 text-primary rounded-tl-sm'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="max-w-[80%] rounded-2xl rounded-tl-sm bg-white/10 border border-slate-700 p-4 text-slate-400 flex items-center gap-2">
              <Bird className="w-5 h-5 animate-bounce text-sky-400" /> Thinking...
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-slate-700/50 bg-bg-secondary/50">
        <div className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your question..."
            className="w-full bg-[#08121E] border border-slate-700 rounded-xl pl-4 pr-14 py-4 text-primary text-lg focus:outline-none focus:border-sky-500 transition-colors"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="absolute right-2 top-2 bottom-2 aspect-square bg-sky-500 hover:bg-sky-400 text-primary rounded-lg flex items-center justify-center disabled:opacity-50 transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
