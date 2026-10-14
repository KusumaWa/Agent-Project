
import { useState, useEffect, useRef } from 'react'

import ReactMarkdown from 'react-markdown'

import remarkGfm from 'remark-gfm'

import './App.css'

import CustomerDashboard from './CustomerDashboard'

import SupportTools from './SupportTools.jsx'

function App() {

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am a Support AI. How can I help you today?',
    },
  ])

  const [input, setInput] = useState('')

  const [loading, setLoading] = useState(false)

  const [error, setError] = useState('')

  const messagesEndRef = useRef(null)

  const [activePage, setActivePage] = useState('chat')


  useEffect(() => {

  
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'end',
    })

  }, [messages, loading])



  async function sendMessage(event) {


    event.preventDefault()

  
    const userMessage = input.trim()

  
    if (!userMessage || loading) return

  
    setMessages((previous) => [
      ...previous,
      {
        role: 'user',
        content: userMessage,
      },
    ])


    setInput('')

  
    setLoading(true)
    setError('')

    try {

      // Send the user's message to FastAPI backend
      const response = await fetch('/api/chat', {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json',
        },

        // Convert into JSON 
        body: JSON.stringify({
          message: userMessage,
        }),
      })

      
      const contentType = response.headers.get('content-type') || ''

      let data = null

      if (contentType.includes('application/json')) {

        data = await response.json()

      } else {

        const rawResponse = await response.text()

        console.error('Unexpected backend response:', rawResponse)

        throw new Error(
          `Backend returned HTTP ${response.status}. Check your FastAPI terminal.`
        )
      }

      if (!response.ok) {
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : `Request failed with HTTP ${response.status}.`
        )
      }

      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          content: data.response || 'No response was generated.',
        },
      ])

      if (!response.ok) {
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : 'Unable to contact the AI agent.'
        )
      }

      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          content: data.response || 'No response was generated.',
        },
      ])

    } catch (err) {

      setError(err.message || 'Something went wrong.')

    } finally {


      setLoading(false)
    }
  }


// React user interface vvvv

  return (
    <div className="app">

      {/* Sidebar */}
      <aside className="sidebar">

        <h2>Company Support AI</h2>

        <p className="sidebar-description">
          AI-powered internet service assistance
        </p>

        <div className="sidebar-section">
          <h3>Available Features</h3>

          
          {/* Switch between main apl page */}
          <nav className="sidebar-navigation" aria-label="Main navigation">

            <button
              type="button"
              className={activePage === 'chat' ? 'nav-active' : ''}
              onClick={() => setActivePage('chat')}
            >
              AI Chat
            </button>

            <button
              type="button"
              className={activePage === 'dashboard' ? 'nav-active' : ''}
              onClick={() => setActivePage('dashboard')}
            >
              Customer Dashboard
            </button>

            <button
              type="button"
              className={activePage === 'tools' ? 'nav-active' : ''}
              onClick={() => setActivePage('tools')}
            >
              Support Tools
            </button>

          </nav>

        </div>



        <div className="sidebar-footer">
          Fictional customer data only
        </div>

      </aside>

      {/* Choose between the dashboard, support tools, and chat */}
      {activePage === 'dashboard' ? (
        <CustomerDashboard />
      ) : activePage === 'tools' ? (
        <SupportTools />
      ) : (
        <main className="chat-container">

        <header className="chat-header">
          <div>
            <h1>AI Support Assistant</h1>
            <p>Ask questions about your internet service</p>
          </div>
        </header>


        <div className="messages">

          {messages.map((message, index) => (

            <div
              key={index}
              className={`message ${message.role}`}
            >

              <div className="message-bubble">

                {/* Convert Markdown into HTML for react*/}
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>

              </div>

            </div>
          ))}


          {loading && (

            <div className="message assistant">
              <div
                className="message-bubble typing-indicator"
                role="status"
                aria-label="AI is generating a response"
              >
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>

          )}


          <div ref={messagesEndRef} />

        </div>


        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}


        <form className="chat-input" onSubmit={sendMessage}>

          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask Company Support AI..."
            aria-label="Chat message"
          />

          <button
            type="submit"
            disabled={loading || !input.trim()}
          >
            {loading ? 'Sending...' : 'Send'}
          </button>

        </form>

       </main>
    )}

    </div>
  )
}

export default App
