import { useState, useEffect } from 'react'

function Results({ roles, candidates, fetchCandidates, fetchRoles, apiBase }) {
  const [filterRole, setFilterRole] = useState('')
  const [expandedId, setExpandedId] = useState(null)

  useEffect(() => {
    fetchRoles()
    fetchCandidates()
  }, [])

  useEffect(() => {
    fetchCandidates(filterRole || null)
  }, [filterRole])

  const getScoreClass = (rec) => {
    if (rec === 'Strong Match') return 'strong'
    if (rec === 'Good Match') return 'good'
    if (rec === 'Partial Match') return 'partial'
    return 'weak'
  }

  const getBarColor = (score) => {
    if (score >= 80) return '#057642'
    if (score >= 60) return '#0a66c2'
    if (score >= 40) return '#b8860b'
    return '#b24020'
  }

  const handleDelete = async (id) => {
    await fetch(`${apiBase}/candidates/${id}`, { method: 'DELETE' })
    fetchCandidates(filterRole || null)
  }

  return (
    <div>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2>Screened Candidates ({candidates.length})</h2>
          <select
            value={filterRole}
            onChange={(e) => setFilterRole(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #e0e0e0' }}
          >
            <option value="">All Roles</option>
            {roles.map(role => (
              <option key={role.id} value={role.id}>{role.title}</option>
            ))}
          </select>
        </div>

        {candidates.length === 0 ? (
          <div className="empty-state">
            <h3>No candidates screened yet</h3>
            <p>Go to "Screen Candidate" or "Bulk Upload" to start screening</p>
          </div>
        ) : (
          candidates.map(item => (
            <div key={item.id} className="candidate-result">
              <div
                className="candidate-header"
                style={{ cursor: 'pointer' }}
                onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
              >
                <div>
                  <div className="candidate-name">
                    {item.candidate.name || 'Unknown'}
                    <span style={{ fontSize: 12, fontWeight: 400, color: '#666', marginLeft: 8 }}>
                      {item.candidate.experience_years > 0 && `${item.candidate.experience_years} yrs exp`}
                    </span>
                  </div>
                  <div className="candidate-headline">{item.candidate.headline}</div>
                  {item.candidate.location && (
                    <div style={{ fontSize: 12, color: '#666', marginTop: 2 }}>
                      📍 {item.candidate.location}
                    </div>
                  )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className={`score-badge ${getScoreClass(item.score.recommendation)}`}>
                    {item.score.total_score}% — {item.score.recommendation}
                  </span>
                  <button
                    className="btn btn-danger"
                    onClick={(e) => { e.stopPropagation(); handleDelete(item.id) }}
                    style={{ fontSize: 11, padding: '4px 8px' }}
                  >
                    ✗
                  </button>
                </div>
              </div>

              {expandedId === item.id && (
                <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid #eee' }}>
                  <div className="score-breakdown">
                    {[
                      { label: 'Required Skills', value: item.score.skills_required_score },
                      { label: 'Preferred Skills', value: item.score.skills_preferred_score },
                      { label: 'Experience', value: item.score.experience_score },
                      { label: 'Location', value: item.score.location_score },
                      { label: 'Keywords', value: item.score.keyword_score },
                    ].map(s => (
                      <div key={s.label} className="score-item">
                        <label>{s.label}: {s.value}%</label>
                        <div className="score-bar">
                          <div
                            className="score-bar-fill"
                            style={{ width: `${s.value}%`, backgroundColor: getBarColor(s.value) }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {item.score.matched_required_skills.length > 0 && (
                    <div style={{ marginTop: 12 }}>
                      <label style={{ fontSize: 11, fontWeight: 600, color: '#666' }}>MATCHED:</label>
                      <div className="skills-list">
                        {item.score.matched_required_skills.map((s, i) => (
                          <span key={i} className="skill-tag matched">✓ {s}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {item.score.missing_required_skills.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <label style={{ fontSize: 11, fontWeight: 600, color: '#666' }}>MISSING:</label>
                      <div className="skills-list">
                        {item.score.missing_required_skills.map((s, i) => (
                          <span key={i} className="skill-tag missing">✗ {s}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {item.candidate.skills.length > 0 && (
                    <div style={{ marginTop: 12 }}>
                      <label style={{ fontSize: 11, fontWeight: 600, color: '#666' }}>ALL SKILLS:</label>
                      <div className="skills-list">
                        {item.candidate.skills.map((s, i) => (
                          <span key={i} className="tag">{s}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default Results
