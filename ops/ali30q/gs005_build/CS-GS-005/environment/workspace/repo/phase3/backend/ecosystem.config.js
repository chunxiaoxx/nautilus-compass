module.exports = {
  apps: [
    {
      name: 'nautilus-backend',
      script: 'uvicorn',
      args: 'main:app --host 0.0.0.0 --port 8000',
      interpreter: 'python3',
      cwd: '/home/ubuntu/nautilus-mvp/phase3/backend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      kill_timeout: 5000,        // Wait 5s for old process to release port
      restart_delay: 3000,       // Wait 3s before restarting (port release grace)
      max_restarts: 10,          // Stop restart loop after 10 failures
      min_uptime: 10000,         // Must run 10s to count as "started"
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/pm2-error.log',
      out_file: './logs/pm2-out.log',
      log_file: './logs/pm2-combined.log',
      time: true
    },
    {
      name: 'kairos-agent',
      script: 'kairos_daemon.py',
      interpreter: 'python3',
      cwd: '/home/ubuntu/nautilus-mvp/phase3/backend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      kill_timeout: 10000,       // Daemon needs time to finish current cycle
      restart_delay: 5000,
      cron_restart: '0 */6 * * *',
      env: {
        KAIROS_CYCLE_INTERVAL: '120',
        NAUTILUS_API_URL: 'https://www.nautilus.social'
      },
      error_file: './logs/kairos-error.log',
      out_file: './logs/kairos-out.log',
      log_file: './logs/kairos-combined.log',
      time: true
    },
    // nautilus-agent runs LOCALLY on developer machine, not on server
    // Start locally: cd nautilus-agent && python -m nautilus_agent --daemon
    // Or: python nautilus-core/phase3/backend/nautilus_daemon.py
    {
      name: 'minimax-agent',
      script: 'minimax_daemon.py',
      interpreter: 'python3',
      cwd: '/home/ubuntu/nautilus-mvp/phase3/backend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      kill_timeout: 10000,
      restart_delay: 5000,
      cron_restart: '0 */6 * * *',
      env: {
        MINIMAX_CYCLE_INTERVAL: '60',
        NAUTILUS_API_URL: 'https://www.nautilus.social'
      },
      error_file: './logs/minimax-error.log',
      out_file: './logs/minimax-out.log',
      log_file: './logs/minimax-combined.log',
      time: true
    }
  ]
};
