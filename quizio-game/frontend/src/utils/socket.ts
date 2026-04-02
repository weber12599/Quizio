import { io, Socket } from 'socket.io-client'

// Connect to the proxy address configured in Vite
const SOCKET_URL = '/'

export const socket: Socket = io(SOCKET_URL, {
    autoConnect: false, // Prevent auto connection before we are ready
    transports: ['websocket'] // Force websocket protocol
})

// Global socket event listeners can be added here
socket.on('connect', () => {
    console.log('Connected to Game Server with ID:', socket.id)
})

socket.on('disconnect', () => {
    console.log('Disconnected from Game Server')
})
