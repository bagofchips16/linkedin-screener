import { useState, useEffect, useRef } from 'react'

function BulkUpload({ roles, selectedRole, setSelectedRole, fetchRoles, setCandidates, setActiveTab, apiBase }) {
  const [uploading, setUploading] = useState(false)
  const [fileName, setFileName] = useState('')
  const [uploadResult, setUploadResult] = useState(null)
  const fileRef = useRef()

  useEffect(() => {
    fetchRoles()
  }, [])

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setFileName(file.name)
    }
  }

  const handleUpload = async () => {
    const file = fileRef.current?.files[0]
    if (!file || !selectedRole) return

    setUploading(true)
    setUploadResult(null)

    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch(`${apiBase}/candidates/bulk-upload?role_id=${selectedRole}`, {
      method: 'POST',
      body: formData,
    })

    const data = await res.json()
    setUploadResult(data)
    setUploading(false)

    if (data.candidates) {
      setCandidates(data.candidates.map((c, i) => ({ id: i + 1, ...c })))
    }
  }

  const viewResults = () => {
    setActiveTab('results')
  }

  return (
    <div>
      <div className="card">
        <h2>Bulk Upload Candidates</h2>
        <p style={{ color: '#666', marginBottom: 16, fontSize: 14 }}>
          Upload a CSV file with multiple candidates to screen them all at once.
        </p>

        <div className="form-group">
          <label>Select Role *</label>
          <select
            value={selectedRole || ''}
            onChange={(e) => setSelectedRole(parseInt(e.target.value))}
          >
            <option value="">-- Select a role --</option>
            {roles.map(role => (
              <option key={role.id} value={role.id}>{role.title}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>CSV File *</label>
          <div
            className="file-upload"
            onClick={() => fileRef.current?.click()}
          >
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              onChange={handleFileChange}
            />
            {fileName ? (
              <p style={{ color: '#191919', fontWeight: 600 }}>📄 {fileName}</p>
            ) : (
              <>
                <p style={{ fontSize: 24 }}>📂</p>
                <p>Click to select a CSV file</p>
              </>
            )}
          </div>
          <p className="hint" style={{ marginTop: 8 }}>
            CSV columns: name, headline, location, skills (comma-separated), experience_years, education, profile_text
          </p>
        </div>

        <div className="actions">
          <button
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={!selectedRole || !fileName || uploading}
          >
            {uploading ? 'Uploading & Screening...' : 'Upload & Screen'}
          </button>
        </div>
      </div>

      {uploadResult && (
        <div className="card">
          <h2>Upload Complete</h2>
          <p style={{ fontSize: 14, marginBottom: 12 }}>
            Successfully screened <strong>{uploadResult.total}</strong> candidates.
          </p>

          {uploadResult.candidates && uploadResult.candidates.length > 0 && (
            <>
              <div style={{ marginBottom: 12 }}>
                <strong>Top Candidates:</strong>
              </div>
              {uploadResult.candidates.slice(0, 5).map((item, i) => (
                <div key={i} className="candidate-result" style={{ padding: 12 }}>
                  <div className="candidate-header">
                    <div>
                      <div className="candidate-name">{item.candidate.name}</div>
                      <div className="candidate-headline">{item.candidate.headline}</div>
                    </div>
                    <span className={`score-badge ${getScoreClass(item.score.recommendation)}`}>
                      {item.score.total_score}%
                    </span>
                  </div>
                </div>
              ))}
              <div className="actions">
                <button className="btn btn-secondary" onClick={viewResults}>
                  View All Results →
                </button>
              </div>
            </>
          )}
        </div>
      )}

      <div className="card">
        <h2>CSV Template</h2>
        <p style={{ fontSize: 13, color: '#666', marginBottom: 12 }}>
          Download or use this format for your CSV file:
        </p>
        <pre style={{
          background: '#f5f5f5',
          padding: 12,
          borderRadius: 6,
          fontSize: 12,
          overflow: 'auto',
          whiteSpace: 'pre-wrap'
        }}>
{`name,headline,location,skills,experience_years,education,profile_text
John Smith,Senior Software Engineer,Bangalore India,"python,react,aws,docker",5,B.Tech IIT Delhi,Experienced engineer with focus on cloud
Jane Doe,Product Manager,Mumbai India,"product management,agile,analytics,sql",7,MBA IIM Ahmedabad,Strategic PM with 7 years in SaaS`}
        </pre>
      </div>
    </div>
  )
}

function getScoreClass(rec) {
  if (rec === 'Strong Match') return 'strong'
  if (rec === 'Good Match') return 'good'
  if (rec === 'Partial Match') return 'partial'
  return 'weak'
}

export default BulkUpload
