import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface WalletDetectorProps {
  onWalletDetected?: (hasWallet: boolean) => void
}

export default function WalletDetector({ onWalletDetected }: WalletDetectorProps) {
  const navigate = useNavigate()
  const [hasWallet, setHasWallet] = useState<boolean | null>(null)
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    const checkWallet = async () => {
      setIsChecking(true)

      // Check for MetaMask
      const hasMetaMask = typeof window.ethereum !== 'undefined' && window.ethereum.isMetaMask

      // Check for Coinbase Wallet
      const hasCoinbase = typeof window.ethereum !== 'undefined' && window.ethereum.isCoinbaseWallet

      // Check for any Web3 provider
      const hasAnyWallet = typeof window.ethereum !== 'undefined'

      const walletDetected = hasMetaMask || hasCoinbase || hasAnyWallet

      setHasWallet(walletDetected)
      setIsChecking(false)

      if (onWalletDetected) {
        onWalletDetected(walletDetected)
      }
    }

    // Check immediately
    checkWallet()

    // Also check after a short delay (in case wallet extension loads slowly)
    const timer = setTimeout(checkWallet, 1000)

    return () => clearTimeout(timer)
  }, [onWalletDetected])

  if (isChecking) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <p className="text-sm text-blue-800">检测钱包中...</p>
        </div>
      </div>
    )
  }

  if (hasWallet === false) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <div className="flex-1">
            <h3 className="font-semibold text-yellow-900 mb-2">未检测到Web3钱包</h3>
            <p className="text-sm text-yellow-800 mb-3">
              您需要安装Web3钱包才能注册Agent。我们推荐使用MetaMask或Coinbase Wallet。
            </p>
            <div className="flex flex-col sm:flex-row gap-2">
              <button
                onClick={() => navigate('/create-wallet')}
                className="px-4 py-2 bg-yellow-600 text-white rounded-lg font-semibold hover:bg-yellow-700 text-sm"
              >
                创建钱包指南
              </button>
              <a
                href="https://metamask.io/download/"
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-white border border-yellow-300 text-yellow-800 rounded-lg font-semibold hover:bg-yellow-50 text-sm text-center"
              >
                下载 MetaMask
              </a>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (hasWallet === true) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <p className="text-sm text-green-800 font-medium">
            ✓ 已检测到Web3钱包，可以继续注册
          </p>
        </div>
      </div>
    )
  }

  return null
}
