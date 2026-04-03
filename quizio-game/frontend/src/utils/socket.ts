import { io, Socket } from 'socket.io-client'

const SOCKET_URL = '/'

export const socket: Socket = io(SOCKET_URL, {
    autoConnect: false,
    transports: ['websocket'],

    // --- Connection Persistence Configurations ---
    reconnection: true, // Enable auto-reconnection
    reconnectionAttempts: Infinity, // Keep trying to reconnect forever
    reconnectionDelay: 1000, // Start with 1 second delay between attempts
    reconnectionDelayMax: 5000, // Max delay of 5 seconds between attempts
    timeout: 20000 // Initial connection timeout
})

socket.on('connect', () => {
    console.log('Connected to Game Server with ID:', socket.id)
})

socket.on('disconnect', (reason) => {
    console.log('Disconnected from Game Server. Reason:', reason)
    // If disconnected due to server drop or network loss,
    // Socket.io will automatically try to reconnect in the background based on the settings above.
})
