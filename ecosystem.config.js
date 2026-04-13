module.exports = {
  apps: [
    {
      name: 'aistorywriter',
      script: 'TelegramBot.py',
      interpreter: 'python3', // or 'python', depending on the environment
      env: {
        PORT: 8013,
        NODE_ENV: 'development'
      },
      env_production: {
        PORT: 8013,
        NODE_ENV: 'production'
      },
      watch: false,
      log_date_format: "YYYY-MM-DD HH:mm:ss"
    }
  ]
};
