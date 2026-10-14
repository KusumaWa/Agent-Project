
import { useState } from 'react'
import './SupportTools.css'

// The four available support tools.
const TOOL_TABS = [
  { id: 'customer', label: 'Customer Account Lookup' },
  { id: 'outage', label: 'Network Outage Checker' },
  { id: 'create', label: 'Support Ticket Creation' },
  { id: 'ticket', label: 'Support Ticket Lookup' },
]

// Send a request to FastAPI and return its JSON response.
async function apiRequest(url, options = {}) {
  const response = await fetch(url, options)

  // Read the response as text first so unexpected server
  // errors do not cause a JSON parsing exception.
  const raw = await response.text()

  let data

  try {
    data = JSON.parse(raw)
  } catch {
    throw new Error(`Backend returned HTTP ${response.status}.`)
  }

  // FastAPI returns error messages inside the detail field.
  if (!response.ok) {
    throw new Error(
      typeof data.detail === 'string'
        ? data.detail
        : 'Request failed.'
    )
  }

  return data
}


function SupportTools({ initialTool = 'customer' }) {

  // Track the selected support tool.
  const [activeTool, setActiveTool] = useState(initialTool)

  // Store form values for each tool.
  const [customerId, setCustomerId] = useState('CUST001')
  const [city, setCity] = useState('St. Louis')
  const [ticketId, setTicketId] = useState('TKT-0003')
  const [issue, setIssue] = useState('')
  const [priority, setPriority] = useState('Medium')
  const [confirmed, setConfirmed] = useState(false)

  // Store API results and loading/error states.
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')


  // Change tools and clear the previous tool's result.
  function selectTool(toolId) {
    setActiveTool(toolId)
    setResult(null)
    setError('')
  }


  // Handle requests for all four tools.
  async function handleSubmit(event) {

    // Prevent the browser from refreshing.
    event.preventDefault()

    if (loading) return

    setLoading(true)
    setError('')
    setResult(null)

    try {
      let data

      if (activeTool === 'customer') {

        // Retrieve a fictional customer record.
        data = await apiRequest(
          `/api/customers/${encodeURIComponent(customerId.trim())}`
        )

      } else if (activeTool === 'outage') {

        // Check the simulated outage records for the city.
        data = await apiRequest(
          `/api/outages/${encodeURIComponent(city.trim())}`
        )

      } else if (activeTool === 'ticket') {

        // Retrieve an existing support ticket.
        data = await apiRequest(
          `/api/tickets/${encodeURIComponent(ticketId.trim())}`
        )

      } else if (activeTool === 'create') {

        // Require the user to review and confirm ticket creation.
        if (!confirmed) {
          throw new Error('Please confirm the ticket details first.')
        }

        // Create a new ticket in SQLite without using Gemini.
        data = await apiRequest('/api/tickets', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            customer_id: customerId.trim(),
            issue: issue.trim(),
            priority,
            confirmed: true,
          }),
        })

        // Reset confirmation after a successful creation.
        // This discourages accidental duplicate submissions.
        setConfirmed(false)
      }

      // Show the resulting information.
      setResult(data)

    } catch (err) {
      setError(err.message || 'An unexpected error occurred.')

    } finally {
      setLoading(false)
    }
  }


  return (
    <section className="support-tools">

      <header className="tools-header">
        <h1>Support Tools</h1>
        <p>Manage fictional accounts, outages, and support tickets.</p>
      </header>

      {/* Choose which support tool to display. */}
      <div className="tools-tabs">
        {TOOL_TABS.map((tool) => (
          <button
            key={tool.id}
            type="button"
            className={activeTool === tool.id ? 'selected' : ''}
            onClick={() => selectTool(tool.id)}
          >
            {tool.label}
          </button>
        ))}
      </div>

      {/* Render the form corresponding to the active tool. */}
      <form className="tools-form" onSubmit={handleSubmit}>

        <h2>
          {TOOL_TABS.find((tool) => tool.id === activeTool)?.label}
        </h2>

        {/* Customer lookup and ticket creation need an account ID. */}
        {(activeTool === 'customer' || activeTool === 'create') && (
          <label>
            Customer ID
            <input
              value={customerId}
              onChange={(event) => setCustomerId(event.target.value)}
              placeholder="CUST001"
              required
            />
          </label>
        )}

        {/* Network outages are searched by city. */}
        {activeTool === 'outage' && (
          <label>
            City
            <input
              value={city}
              onChange={(event) => setCity(event.target.value)}
              placeholder="St. Louis"
              required
            />
          </label>
        )}

        {/* Ticket lookup uses its unique ticket identifier. */}
        {activeTool === 'ticket' && (
          <label>
            Ticket ID
            <input
              value={ticketId}
              onChange={(event) => setTicketId(event.target.value)}
              placeholder="TKT-0003"
              required
            />
          </label>
        )}

        {/* Additional information needed to create a ticket. */}
        {activeTool === 'create' && (
          <>
            <label>
              Issue Description
              <textarea
                value={issue}
                onChange={(event) => {
                  setIssue(event.target.value)

                  // Editing a confirmed ticket requires
                  // confirmation again before submission.
                  setConfirmed(false)
                }}
                placeholder="Describe the customer's issue..."
                rows={4}
                required
              />
            </label>

            <label>
              Priority
              <select
                value={priority}
                onChange={(event) => {
                  setPriority(event.target.value)
                  setConfirmed(false)
                }}
              >
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
              </select>
            </label>

            <label className="tools-checkbox">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(event) =>
                  setConfirmed(event.target.checked)
                }
              />
              I confirm these fictional ticket details are correct.
            </label>
          </>
        )}

        <button
          type="submit"
          className="tools-submit"
          disabled={loading}
        >
          {loading
            ? 'Processing...'
            : activeTool === 'create'
              ? 'Create Ticket'
              : 'Search'}
        </button>

      </form>

      {/* Display errors without removing the form. */}
      {error && (
        <p className="tools-error" role="alert">{error}</p>
      )}

      
        {/* ========================================================
            FORMATTED SUPPORT TOOL RESULTS
            ========================================================
            Display a different result card depending on the tool.
            All information comes from the FastAPI response.
        */}

        {result && (
        <div className="tools-result">

            {/* CUSTOMER ACCOUNT LOOKUP */}
            {activeTool === 'customer' && (
            <>
                <div className="result-heading">
                <h2>Customer Account</h2>

                {/* Show the account's current status. */}
                <span className="result-badge success">
                    {result.customer.account_status}
                </span>
                </div>

                <h3>{result.customer.name}</h3>

                <div className="result-details">
                <p><strong>Customer ID:</strong> {result.customer_id}</p>
                <p><strong>City:</strong> {result.customer.city}</p>
                <p><strong>Internet Plan:</strong> {result.customer.plan}</p>
                <p><strong>Speed:</strong> {result.customer.speed_mbps} Mbps</p>
                </div>
            </>
            )}

            {/* NETWORK OUTAGE CHECKER */}
            {activeTool === 'outage' && (
            <>
                <div className="result-heading">
                <h2>Network Status</h2>

                {/* Use different badges depending on outage status. */}
                <span
                    className={
                    result.outage.outage
                        ? 'result-badge warning'
                        : 'result-badge success'
                    }
                >
                    {result.outage.outage
                    ? 'Simulated Outage'
                    : 'No Simulated Outage'}
                </span>
                </div>

                <h3>{city}</h3>

                <div className="result-details">
                <p>
                    <strong>Description:</strong> {result.outage.description}
                </p>

                {/* Show an estimated resolution only if one exists. */}
                {result.outage.estimated_resolution && (
                    <p>
                    <strong>Estimated Resolution:</strong>
                    {' '}{result.outage.estimated_resolution}
                    </p>
                )}
                </div>

                <p className="result-note">
                This information is simulated and does not represent
                real-world network conditions.
                </p>
            </>
            )}

            {/* SUPPORT TICKET LOOKUP AND CREATION */}
            {(activeTool === 'ticket' || activeTool === 'create') && (
            <>
                <div className="result-heading">
                <h2>
                    {activeTool === 'create'
                    ? 'Ticket Created Successfully'
                    : 'Support Ticket Details'}
                </h2>

                <span className="result-badge info">
                    {result.ticket.status}
                </span>
                </div>

                <h3>{result.ticket.ticket_id}</h3>

                <div className="result-details">
                <p>
                    <strong>Customer:</strong> {result.ticket.customer_name}
                </p>

                <p>
                    <strong>Customer ID:</strong> {result.ticket.customer_id}
                </p>

                <p>
                    <strong>Issue:</strong> {result.ticket.issue}
                </p>

                <p>
                    <strong>Priority:</strong> {result.ticket.priority}
                </p>

                <p>
                    <strong>Created:</strong>
                    {' '}{new Date(result.ticket.created_at).toLocaleString()}
                </p>
                </div>

                {/* Confirm successful persistence for new tickets. */}
                {activeTool === 'create' && (
                <p className="result-note">
                    Your fictional support ticket was saved to SQLite.
                </p>
                )}
            </>
            )}

        </div>
        )}


      <p className="tools-disclaimer">
        Demonstration only. No real company account or outage data.
      </p>

    </section>
  )
}

export default SupportTools
