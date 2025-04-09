module.exports = {
  apps: [{
    name: "torrent-monitoring",
    script: "main.py",
    interpreter: "python3",
    cwd: "/Users/wojtasy/prv/torrent-monitoring",
    autorestart: false,
    watch: false,
    cron_restart: "0 */3 * * *", // Run every 3 hours
    env: {
      NODE_ENV: "production",
      PYTHONPATH: "/Users/wojtasy/prv/torrent-monitoring"
    }
  }]
};
