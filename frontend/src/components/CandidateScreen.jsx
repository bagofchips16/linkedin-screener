import { useState, useEffect } from 'react'

function CandidateScreen({ roles, selectedRole, setSelectedRole, fetchRoles, fetchCandidates, apiBase }) {
  const [profileText, setProfileText] = useState('')
  const [screening, setScreening] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    fetchRoles()
  }, [])

  const handleScreen = async () => {
    if (!selectedRole || !profileText.trim()) return
    setScreening(true)
    setResult(null)

    const res = await fetch(`${apiBase}/candidates/screen`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        role_id: selectedRole,
        profile_text: profileText,
      }),
    })

    const data = await res.json()
    setResult(data)
    setScreening(false)
  }

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

  return (
    <div>
      <div className="card">
        <h2>Screen a Candidate</h2>
        <p style={{ color: '#666', marginBottom: 16, fontSize: 14 }}>
          Paste a LinkedIn profile text below to score the candidate against a role.
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
          {roles.length === 0 && (
            <p className="hint" style={{ color: '#b24020' }}>
              No roles defined. Go to "Define Roles" tab first.
            </p>
          )}
        </div>

        <div className="form-group">
          <label>LinkedIn Profile Text *</label>
          <textarea
            value={profileText}
            onChange={(e) => setProfileText(e.target.value)}
            placeholder={`Paste the candidate's LinkedIn profile here. Example format:\n\nJohn Smith\nSenior Software Engineer at Google\nBangalore, India\n\n5 years of experience in software development\n\nSkills: Python, React, AWS, Docker, Machine Learning\n\nEducation: B.Tech in Computer Science, IIT Delhi\n\nExperience:\n- Software Engineer at Google (2020-present)\n- Junior Developer at Startup (2018-2020)`}
            style={{ minHeight: 200 }}
          />
          <p className="hint">
            Copy text from a LinkedIn profile page. Include name, headline, skills, experience, and education.
          </p>
        </div>

        <div className="actions">
          <button
            className="btn btn-primary"
            onClick={handleScreen}
            disabled={!selectedRole || !profileText.trim() || screening}
          >
            {screening ? 'Screening...' : 'Screen Candidate'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => { setProfileText(''); setResult(null) }}
          >
            Clear
          </button>
        </div>
      </div>

      {result && (
        <div className="card">
          <h2>Screening Result</h2>
          <div className="candidate-result">
            <div className="candidate-header">
              <div>
                <div className="candidate-name">{result.candidate.name || 'Unknown'}</div>
                <div className="candidate-headline">{result.candidate.headline}</div>
                {result.candidate.location && (
                  <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                    📍 {result.candidate.location}
                  </div>
                )}
              </div>
              <span className={`score-badge ${getScoreClass(result.score.recommendation)}`}>
                {result.score.total_score}% — {result.score.recommendation}
              </span>
            </div>

            <div className="score-breakdown">
              {[
                { label: 'Required Skills', value: result.score.skills_required_score },
                { label: 'Preferred Skills', value: result.score.skills_preferred_score },
                { label: 'Experience', value: result.score.experience_score },
                { label: 'Location', value: result.score.location_score },
                { label: 'Keywords', value: result.score.keyword_score },
              ].map(item => (
                <div key={item.label} className="score-item">
                  <label>{item.label}: {item.value}%</label>
                  <div className="score-bar">
                    <div
                      className="score-bar-fill"
                      style={{ width: `${item.value}%`, backgroundColor: getBarColor(item.value) }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {result.score.matched_required_skills.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#666' }}>MATCHED SKILLS:</label>
                <div className="skills-list">
                  {result.score.matched_required_skills.map((s, i) => (
                    <span key={i} className="skill-tag matched">✓ {s}</span>
                  ))}
                </div>
              </div>
            )}

            {result.score.missing_required_skills.length > 0 && (
              <div style={{ marginTop: 8 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#666' }}>MISSING SKILLS:</label>
                <div className="skills-list">
                  {result.score.missing_required_skills.map((s, i) => (
                    <span key={i} className="skill-tag missing">✗ {s}</span>
                  ))}
                </div>
              </div>
            )}

            {result.candidate.skills.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: '#666' }}>DETECTED SKILLS:</label>
                <div className="skills-list">
                  {result.candidate.skills.map((s, i) => (
                    <span key={i} className="tag">{s}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default CandidateScreen
