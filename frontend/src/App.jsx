
import { useState, useEffect, useRef } from 'react'

// Convert AI-generated Markdown into formatted React elements.
import ReactMarkdown from 'react-markdown'

// Support Markdown tables, lists, and other GitHub extensions.
import remarkGfm from 'remark-gfm'

import './App.css'

// Import the dashboard we created.
import CustomerDashboard from './CustomerDashboard'

// Import our new support tools interface.
import SupportTools from './SupportTools.jsx'

function App() {

  // Store the messages shown in the conversation.
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am a Support AI. How can I help you today?',
    },
  ])

  // Store the text the user is currently typing.
  const [input, setInput] = useState('')

  // Track whether the AI is processing a request.
  const [loading, setLoading] = useState(false)

  // Store any API errors so we can display them.
  const [error, setError] = useState('')

  // Create a reference to an invisible element at the
  // bottom of the chat. We'll scroll to this element
  // whenever a new message is added.
  const messagesEndRef = useRef(null)


  // Track which page the user is currently viewing.
  // "chat" shows Gemini; "dashboard" shows customer information.
  const [activePage, setActivePage] = useState('chat')

  // ========================================================
  // AUTOMATIC SCROLLING
  // ========================================================

  // This effect runs whenever the conversation changes
  // or the loading indicator appears/disappears.
  useEffect(() => {

    // Scroll to the invisible element at the bottom.
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'end',
    })

  }, [messages, loading])


  // ========================================================
  // SEND MESSAGES TO FASTAPI
  // ========================================================

  async function sendMessage(event) {

    // Prevent the form from refreshing the page.
    event.preventDefault()

    // Remove unnecessary spaces from the user's message.
    const userMessage = input.trim()

    // Don't send empty messages or overlapping requests.
    if (!userMessage || loading) return

    // Add the user's message to the chat immediately.
    setMessages((previous) => [
      ...previous,
      {
        role: 'user',
        content: userMessage,
      },
    ])

    // Clear the message input field.
    setInput('')

    // Show the loading animation and clear old errors.
    setLoading(true)
    setError('')

    try {

      // Send the user's message to our FastAPI backend.
      // Vite forwards /api/chat to http://127.0.0.1:8000/chat.
      const response = await fetch('/api/chat', {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json',
        },

        // Convert our message into a JSON request body.
        body: JSON.stringify({
          message: userMessage,
        }),
      })

      
      // Read the Content-Type header to determine whether
      // FastAPI returned JSON or another response format.
      const contentType = response.headers.get('content-type') || ''

      // Only parse the response as JSON when the server
      // explicitly says it is returning JSON.
      let data = null

      if (contentType.includes('application/json')) {

        // Convert the JSON response into a JavaScript object.
        data = await response.json()

      } else {

        // Read the raw response for debugging.
        // FastAPI may return plain text when an unexpected
        // internal server error occurs.
        const rawResponse = await response.text()

        console.error('Unexpected backend response:', rawResponse)

        // Throw a readable error instead of crashing
        // with "Unexpected token ... is not valid JSON".
        throw new Error(
          `Backend returned HTTP ${response.status}. Check your FastAPI terminal.`
        )
      }

      // Handle error responses returned by FastAPI.
      if (!response.ok) {
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : `Request failed with HTTP ${response.status}.`
        )
      }

      // Display Gemini's response in the chat interface.
      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          content: data.response || 'No response was generated.',
        },
      ])


      // If the API request failed, throw a readable error.
      if (!response.ok) {
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : 'Unable to contact the AI agent.'
        )
      }

      // Add Gemini's response to the conversation.
      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          content: data.response || 'No response was generated.',
        },
      ])

    } catch (err) {

      // Display the error without deleting chat history.
      setError(err.message || 'Something went wrong.')

    } finally {

      // Stop the loading animation when the request finishes.
      setLoading(false)
    }
  }


  // ========================================================
  // REACT USER INTERFACE
  // ========================================================

  return (
    <div className="app">

      {/* Sidebar displaying the application's features. */}
      <aside className="sidebar">

        <h2>Company Support AI</h2>

        <p className="sidebar-description">
          AI-powered internet service assistance
        </p>

        <div className="sidebar-section">
          <h3>Available Features</h3>

          
          {/* Switch between the main application pages. */}
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

      {/* Choose between the dashboard, support tools, and chat. */}
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


        {/* Display the conversation in chronological order. */}
        <div className="messages">

          {messages.map((message, index) => (

            <div
              key={index}
              className={`message ${message.role}`}
            >

              <div className="message-bubble">

                {/* Convert the message's Markdown into HTML
                    safely through React components.
                    We are not rendering raw HTML. */}
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>

              </div>

            </div>
          ))}


          {/* Show animated dots while waiting for Gemini. */}
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


          {/* Invisible target used for automatic scrolling. */}
          <div ref={messagesEndRef} />

        </div>


        {/* Show request failures above the message input. */}
        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}


        {/* Form used to send messages to the AI agent. */}
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
