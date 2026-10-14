
import { useEffect, useState } from 'react'
import './CustomerDashboard.css'

const CUSTOMER_ID = 'CUST001'

function CustomerDashboard() {

  // Store information retrieved from FastAPI.
  const [customer, setCustomer] = useState(null)
  const [outage, setOutage] = useState(null)
  const [tickets, setTickets] = useState([])

  // track load and errors
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // track ticke updating
  const [updatingTicket, setUpdatingTicket] = useState(null)

  // display sucess
  const [ticketMessage, setTicketMessage] = useState('')

  // load info when dashboard
  useEffect(() => {

    // Emergency abort
    const controller = new AbortController()

    async function loadDashboard() {
      setLoading(true)
      setError('')

      try {
        // Request information
        const customerResponse = await fetch(
          `/api/customers/${CUSTOMER_ID}`,
          { signal: controller.signal }
        )

        if (!customerResponse.ok) {
          throw new Error('Unable to retrieve customer information.')
        }

        const customerData = await customerResponse.json()

        const city = encodeURIComponent(customerData.customer.city)

        const [outageResponse, ticketsResponse] = await Promise.all([
          fetch(`/api/outages/${city}`, {
            signal: controller.signal,
          }),
          fetch(`/api/customers/${CUSTOMER_ID}/tickets`, {
            signal: controller.signal,
          }),
        ])

        if (!outageResponse.ok || !ticketsResponse.ok) {
          throw new Error('Unable to load dashboard information.')
        }

        // Convert the responses into JavaScript
        const outageData = await outageResponse.json()
        const ticketsData = await ticketsResponse.json()

        // Save results in react
        setCustomer(customerData)
        setOutage(outageData)
        setTickets(ticketsData.tickets)

      } catch (err) {
        // Ignore cancellations
        if (err.name !== 'AbortError') {
          setError(err.message || 'An unexpected error occurred.')
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    loadDashboard()

    // Cancel in-progress requests when leaving this page.
    return () => controller.abort()

  }, [])

  
  // 
  // update supprt ticket status


  async function handleStatusChange(ticketId, newStatus) {

    if (updatingTicket !== null) return

    setUpdatingTicket(ticketId)
    setTicketMessage('')

    try {

      const response = await fetch(
        `/api/tickets/${encodeURIComponent(ticketId)}/status`,
        {
          method: 'PATCH',

          headers: {
            'Content-Type': 'application/json',
          },

          // send new status to backend
          body: JSON.stringify({
            status: newStatus,
          }),
        }
      )

      // read fastapi
      const data = await response.json()

      // show error upon rejection
      if (!response.ok) {
        throw new Error(
          data.detail || 'Failed to update support ticket.'
        )
      }

      // update ticket
      setTickets((previous) =>
        previous.map((ticket) =>
          ticket.ticket_id === ticketId
            ? data.ticket
            : ticket
        )
      )

      // tell user update sucess
      setTicketMessage(
        `${ticketId} successfully updated to ${data.ticket.status}.`
      )

    } catch (error) {
      setTicketMessage(error.message)

    } finally {

      setUpdatingTicket(null)
    }
  }


  if (loading) {
    return (
      <section className="dashboard">
        <p>Loading customer dashboard...</p>
      </section>
    )
  }


  if (error) {
    return (
      <section className="dashboard">
        <h1>Customer Dashboard</h1>
        <p role="alert">{error}</p>
      </section>
    )
  }

  return (
    <section className="dashboard">

      <header className="dashboard-header">
        <h1>Customer Dashboard</h1>
        <p>Account overview for {customer.customer.name}</p>
        <small>Fictional demonstration data</small>
      </header>

      <div className="dashboard-grid">


        <article className="dashboard-card">
          <h2>Customer Information</h2>

          <h3>{customer.customer.name}</h3>
          <p>Customer ID: {customer.customer_id}</p>
          <p>City: {customer.customer.city}</p>
          <p>Plan: {customer.customer.plan}</p>
          <p>Speed: {customer.customer.speed_mbps} Mbps</p>

          <span className="status-label">
            {customer.customer.account_status}
          </span>
        </article>


        <article className="dashboard-card">
          <h2>Network Status</h2>

          <h3>{customer.customer.city}</h3>

          {outage.outage.outage ? (
            <>
              <span className="outage-label">
                Simulated Outage
              </span>
              <p>{outage.outage.description}</p>
              <p>
                Estimated resolution:
                {' '}{outage.outage.estimated_resolution}
              </p>
            </>
          ) : (
            <p>No simulated outages reported.</p>
          )}
        </article>

        

<article className="dashboard-card tickets-card">

 
  <h2>Support Tickets ({tickets.length})</h2>


  {tickets.length === 0 ? (
    <p>No support tickets found.</p>
  ) : (

    <div className="ticket-list">

     
      {tickets.map((ticket) => (

        <div
          className="ticket-item"
          key={ticket.ticket_id}
        >

         
          <div className="ticket-heading">
            <strong>{ticket.ticket_id}</strong>

            <span className="ticket-status">
              {ticket.status}
            </span>
          </div>

          <p>{ticket.issue}</p>

       
          <small>
            Priority: {ticket.priority}
            {' | '}
            {new Date(ticket.created_at).toLocaleString()}
          </small>

          {/* NEW: Dropdown for updating the ticket status. */}
          <div className="ticket-actions">

            <label htmlFor={`status-${ticket.ticket_id}`}>
              Update status:
            </label>

            <select
              id={`status-${ticket.ticket_id}`}

           
              value={ticket.status}

            
              onChange={(event) =>
                handleStatusChange(
                  ticket.ticket_id,
                  event.target.value
                )
              }

            
              disabled={updatingTicket !== null}
            >
              <option value="Open">Open</option>
              <option value="In Progress">In Progress</option>
              <option value="Resolved">Resolved</option>
            </select>

          </div>

        </div>
      ))}

    </div>
  )}

</article>


      </div>

    </section>
  )
}

export default CustomerDashboard
