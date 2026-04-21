const { app, BrowserWindow, ipcMain, shell, dialog } = require('electron')
const path = require('path')
const fs = require('fs')
const { exec, spawn } = require('child_process')

// Fix macOS GUI app PATH issue
if (process.platform === 'darwin') {
    process.env.PATH = process.env.PATH + ':/usr/local/bin:/opt/homebrew/bin'
}

let mainWindow
let isQuiting = false

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 600,
        height: 750,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        autoHideMenuBar: true
    })

    mainWindow.loadFile('index.html')

    // Prevent closing the app directly, hide it instead (macOS style)
    mainWindow.on('close', (event) => {
        if (!isQuiting) {
            event.preventDefault()
            mainWindow.hide()
        }
    })
}

// Ensure the app shows up when clicking the dock icon
app.on('activate', () => {
    if (mainWindow) mainWindow.show()
})

// Allow actual quit when Cmd+Q or App Quit is triggered
app.on('before-quit', () => {
    isQuiting = true
})

// Get App Version for About Modal
ipcMain.handle('get-version', () => {
    return app.getVersion()
})

// Check Docker status
ipcMain.handle('check-docker', () => {
    return new Promise((resolve) => {
        exec('docker info', (error) => {
            if (error) {
                if (fs.existsSync('/Applications/Docker.app')) {
                    resolve({
                        status: 'stopped',
                        message: 'Docker is installed but not running.'
                    })
                } else {
                    resolve({
                        status: 'missing',
                        message: 'Docker Desktop is not installed.'
                    })
                }
            } else {
                resolve({
                    status: 'running',
                    message: 'Docker is running normally.'
                })
            }
        })
    })
})

// Auto-start Docker Desktop application
ipcMain.on('start-docker-app', () => {
    exec('open -a Docker')
})

// Open Docker download page
ipcMain.on('download-docker', () => {
    shell.openExternal('https://www.docker.com/products/docker-desktop/')
})

// Open save dialog and write logs to file
ipcMain.handle('export-logs', async (event, logContent) => {
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
        title: 'Export Quizio Logs',
        defaultPath: 'quizio-server-logs.txt',
        filters: [{ name: 'Text Files', extensions: ['txt'] }]
    })

    if (!canceled && filePath) {
        fs.writeFileSync(filePath, logContent)
        return true
    }
    return false
})

// Receive config, write to .env and start Docker Compose
ipcMain.on('start-server', (event, config) => {
    let url = config.databaseUrl
    if (!url.startsWith('http')) {
        url = `https://${url}`
    }
    url = url.replace(/\/$/, '')

    const frontendPort = config.frontendPort
    const backendPort = config.backendPort

    const envContent = `
DATA_SERVICE_BASE_URL=${url}

GAME_BASE_URL=http://frontend:${frontendPort}

VITE_API_PROXY_BASE_URL=http://backend:${backendPort}
VITE_SOCKET_PROXY_BASE_URL=http://backend:${backendPort}
VITE_MEDIA_PROXY_BASE_URL=${url}
`.trim()

    const gameRootDir = path.join(__dirname, '..')
    const envPath = path.join(gameRootDir, '.env')

    try {
        fs.writeFileSync(envPath, envContent)
        event.reply(
            'log',
            '✅ Environment configuration generated successfully.'
        )

        const dockerProcess = spawn(
            'docker',
            ['compose', 'up', '-d', '--build'],
            { cwd: gameRootDir }
        )

        dockerProcess.stdout.on('data', (data) =>
            event.reply('log', data.toString())
        )
        dockerProcess.stderr.on('data', (data) =>
            event.reply('log', data.toString())
        )

        dockerProcess.on('close', (code) => {
            if (code === 0) {
                event.reply(
                    'log',
                    '✅ Containers started successfully! Fetching secure tunnel URL...'
                )
                fetchCloudflareUrl(gameRootDir, event)
            } else {
                event.reply('log', `❌ Startup failed. Error code: ${code}`)
            }
        })
    } catch (err) {
        event.reply('log', `❌ Failed to write config: ${err.message}`)
    }
})

// Stop server and remove containers
ipcMain.on('stop-server', (event) => {
    const gameRootDir = path.join(__dirname, '..')
    event.reply('log', '🛑 Stopping and removing containers. Please wait...')

    const dockerProcess = spawn('docker', ['compose', 'down'], {
        cwd: gameRootDir
    })

    dockerProcess.stdout.on('data', (data) =>
        event.reply('log', data.toString())
    )
    dockerProcess.stderr.on('data', (data) =>
        event.reply('log', data.toString())
    )

    dockerProcess.on('close', (code) => {
        event.reply('log', '✅ All services stopped and containers removed.')
        event.reply('server-stopped')
    })
})

// Fetch Cloudflare tunnel URL
function fetchCloudflareUrl(gameRootDir, event) {
    let attempts = 0
    const maxAttempts = 15

    const interval = setInterval(() => {
        attempts++
        exec(
            'docker compose logs cloudflared',
            { cwd: gameRootDir },
            (error, stdout, stderr) => {
                const output = stdout + stderr
                const match = output.match(
                    /https:\/\/[a-zA-Z0-9-]+\.trycloudflare\.com/
                )

                if (match) {
                    clearInterval(interval)
                    event.reply('tunnel-url', match[0])
                    event.reply(
                        'log',
                        `🎉 URL fetched successfully: ${match[0]}`
                    )
                } else if (attempts >= maxAttempts) {
                    clearInterval(interval)
                    event.reply(
                        'log',
                        '⚠️ Cannot fetch Cloudflare URL. Please check the logs.'
                    )
                }
            }
        )
    }, 2000)
}

ipcMain.on('open-external', (event, url) => {
    shell.openExternal(url)
})

app.whenReady().then(createWindow)

// macOS typically keeps the app running even if all windows are closed
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
})
