import { useState } from 'react'
import RoleForm from './components/RoleForm'
import CandidateScreen from './components/CandidateScreen'
import BulkUpload from './components/BulkUpload'
import Results from './components/Results'

const API_BASE = 'http://localhost:8000'

function App() {
  const [activeTab, setActiveTab] = useState('roles')
  const [roles, setRoles] = useState([])
  const [selectedRole, setSelectedRole] = useState(null)
  const [candidates, setCandidates] = useState([])

  const fetchRoles = async () => {
    const res = await fetch(`${API_BASE}/roles`)
    const data = await res.json()
    setRoles(data)
  }

  const fetchCandidates = async (roleId) => {
    const url = roleId ? `${API_BASE}/candidates?role_id=${roleId}` : `${API_BASE}/candidates`
    const res = await fetch(url)
    const data = await res.json()
    setCandidates(data)
  }

  const tabs = [
    { id: 'roles', label: 'Define Roles' },
    { id: 'screen', label: 'Screen Candidate' },
    { id: 'bulk', label: 'Bulk Upload' },
    { id: 'results', label: 'Results' },
  ]

  return (
    <div className="app">
      <div className="header">
        <div>
          <h1>LinkedIn Screener</h1>
          <p>AI-powered candidate screening for HR professionals</p>
        </div>
      </div>

      <div className="tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'roles' && (
        <RoleForm
          roles={roles}
          selectedRole={selectedRole}
          setSelectedRole={setSelectedRole}
          fetchRoles={fetchRoles}
          apiBase={API_BASE}
        />
      )}

      {activeTab === 'screen' && (
        <CandidateScreen
          roles={roles}
          selectedRole={selectedRole}
          setSelectedRole={setSelectedRole}
          fetchRoles={fetchRoles}
          fetchCandidates={fetchCandidates}
          apiBase={API_BASE}
        />
      )}

      {activeTab === 'bulk' && (
        <BulkUpload
          roles={roles}
          selectedRole={selectedRole}
          setSelectedRole={setSelectedRole}
          fetchRoles={fetchRoles}
          setCandidates={setCandidates}
          setActiveTab={setActiveTab}
          apiBase={API_BASE}
        />
      )}

      {activeTab === 'results' && (
        <Results
          roles={roles}
          candidates={candidates}
          fetchCandidates={fetchCandidates}
          fetchRoles={fetchRoles}
          apiBase={API_BASE}
        />
      )}
    </div>
  )
}

export default App
