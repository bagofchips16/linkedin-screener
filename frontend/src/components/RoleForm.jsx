import { useState, useEffect } from 'react'

function TagInput({ tags, setTags, placeholder }) {
  const [input, setInput] = useState('')

  const handleKeyDown = (e) => {
    if ((e.key === 'Enter' || e.key === ',') && input.trim()) {
      e.preventDefault()
      if (!tags.includes(input.trim())) {
        setTags([...tags, input.trim()])
      }
      setInput('')
    } else if (e.key === 'Backspace' && !input && tags.length) {
      setTags(tags.slice(0, -1))
    }
  }

  return (
    <div className="tag-input">
      {tags.map((tag, i) => (
        <span key={i} className="tag">
          {tag}
          <button onClick={() => setTags(tags.filter((_, idx) => idx !== i))}>×</button>
        </span>
      ))}
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={tags.length === 0 ? placeholder : ''}
      />
    </div>
  )
}

function RoleForm({ roles, selectedRole, setSelectedRole, fetchRoles, apiBase }) {
  const [title, setTitle] = useState('')
  const [requiredSkills, setRequiredSkills] = useState([])
  const [preferredSkills, setPreferredSkills] = useState([])
  const [minExp, setMinExp] = useState(0)
  const [maxExp, setMaxExp] = useState('')
  const [location, setLocation] = useState('')
  const [education, setEducation] = useState('')
  const [keywords, setKeywords] = useState([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchRoles()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)

    const role = {
      title,
      required_skills: requiredSkills,
      preferred_skills: preferredSkills,
      min_years_experience: parseInt(minExp) || 0,
      max_years_experience: maxExp ? parseInt(maxExp) : null,
      location: location || null,
      education: education || null,
      keywords,
    }

    await fetch(`${apiBase}/roles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(role),
    })

    // Reset form
    setTitle('')
    setRequiredSkills([])
    setPreferredSkills([])
    setMinExp(0)
    setMaxExp('')
    setLocation('')
    setEducation('')
    setKeywords([])
    setSaving(false)
    fetchRoles()
  }

  const handleDelete = async (roleId) => {
    await fetch(`${apiBase}/roles/${roleId}`, { method: 'DELETE' })
    if (selectedRole === roleId) setSelectedRole(null)
    fetchRoles()
  }

  return (
    <div>
      <div className="card">
        <h2>Create New Role</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Role Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Senior Frontend Engineer"
              required
            />
          </div>

          <div className="form-group">
            <label>Required Skills *</label>
            <TagInput tags={requiredSkills} setTags={setRequiredSkills} placeholder="Type a skill and press Enter" />
            <p className="hint">Skills the candidate must have. Press Enter or comma to add.</p>
          </div>

          <div className="form-group">
            <label>Preferred Skills</label>
            <TagInput tags={preferredSkills} setTags={setPreferredSkills} placeholder="Nice-to-have skills" />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Min Years Experience</label>
              <input
                type="number"
                min="0"
                value={minExp}
                onChange={(e) => setMinExp(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Max Years Experience</label>
              <input
                type="number"
                min="0"
                value={maxExp}
                onChange={(e) => setMaxExp(e.target.value)}
                placeholder="Leave empty for no max"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Location</label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Bangalore, India"
              />
            </div>
            <div className="form-group">
              <label>Education</label>
              <input
                type="text"
                value={education}
                onChange={(e) => setEducation(e.target.value)}
                placeholder="e.g. B.Tech, MBA"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Keywords</label>
            <TagInput tags={keywords} setTags={setKeywords} placeholder="Additional keywords to match" />
            <p className="hint">Extra keywords to search in candidate profiles (e.g. startup, fintech, SaaS)</p>
          </div>

          <div className="actions">
            <button type="submit" className="btn btn-primary" disabled={!title || requiredSkills.length === 0 || saving}>
              {saving ? 'Saving...' : 'Create Role'}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h2>Saved Roles ({roles.length})</h2>
        {roles.length === 0 ? (
          <div className="empty-state">
            <h3>No roles defined yet</h3>
            <p>Create a role above to start screening candidates</p>
          </div>
        ) : (
          roles.map(role => (
            <div
              key={role.id}
              className={`role-card ${selectedRole === role.id ? 'selected' : ''}`}
              onClick={() => setSelectedRole(role.id)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3>{role.title}</h3>
                  <div className="meta">
                    <span>{role.required_skills.length} required skills</span>
                    <span>{role.min_years_experience}+ years</span>
                    {role.location && <span>{role.location}</span>}
                  </div>
                  <div className="skills-list" style={{ marginTop: 8 }}>
                    {role.required_skills.map((s, i) => (
                      <span key={i} className="skill-tag matched">{s}</span>
                    ))}
                    {role.preferred_skills.map((s, i) => (
                      <span key={`p-${i}`} className="skill-tag" style={{ background: '#e8f4fd', color: '#0a66c2' }}>{s}</span>
                    ))}
                  </div>
                </div>
                <button
                  className="btn btn-danger"
                  onClick={(e) => { e.stopPropagation(); handleDelete(role.id) }}
                  style={{ fontSize: 12, padding: '6px 12px' }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default RoleForm
