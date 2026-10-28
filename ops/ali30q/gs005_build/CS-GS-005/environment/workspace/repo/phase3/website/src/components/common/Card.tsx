import { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  hover?: boolean
}

export default function Card({ children, className = '', hover = false }: CardProps) {
  return (
    <div
      className={`glass rounded-xl p-6 ${
        hover ? 'hover:scale-105 transition-transform duration-300' : ''
      } ${className}`}
    >
      {children}
    </div>
  )
}
