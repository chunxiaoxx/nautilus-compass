import { useState, useEffect } from 'react'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  suggestions?: string[]
}

export default function SearchBar({ value, onChange, suggestions = [] }: SearchBarProps) {
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([])

  useEffect(() => {
    if (value.length > 0 && suggestions.length > 0) {
      const filtered = suggestions.filter(s =>
        s.toLowerCase().includes(value.toLowerCase())
      )
      setFilteredSuggestions(filtered)
      setShowSuggestions(filtered.length > 0)
    } else {
      setShowSuggestions(false)
    }
  }, [value, suggestions])

  const handleSelectSuggestion = (suggestion: string) => {
    onChange(suggestion)
    setShowSuggestions(false)
  }

  return (
    <div className="relative w-full">
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="搜索任务关键词..."
          className="w-full px-6 py-4 pl-14 bg-dark-800 border border-dark-700 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-primary-500 transition-colors"
        />
        <svg
          className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      {showSuggestions && (
        <div className="absolute z-10 w-full mt-2 bg-dark-800 border border-dark-700 rounded-xl shadow-xl overflow-hidden">
          {filteredSuggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSelectSuggestion(suggestion)}
              className="w-full px-6 py-3 text-left text-white hover:bg-dark-700 transition-colors"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
