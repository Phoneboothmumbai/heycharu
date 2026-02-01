const express = require('express');
const cors = require('cors');
const axios = require('axios');
const qrcode = require('qrcode');
const pino = require('pino');
const fs = require('fs');
const path = require('path');

// Dynamic import for Baileys (ES module)
let makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion;

const app = express();
app.use(cors());
app.use(express.json());

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';
const PORT = process.env.WA_PORT || 3001;
const AUTH_FOLDER = path.join(__dirname, 'auth_info_baileys');

// Create a silent logger for Baileys
const logger = pino({ level: 'silent' });

// WhatsApp client state
let sock = null;
let currentQR = null;
let isReady = false;
let connectedPhone = null;
let syncProgress = { total: 0, synced: 0, status: 'idle' };
let connectionStatus = 'disconnected';

// CRITICAL: Connection timestamp - only messages AFTER this time get AI replies
let connectionTimestamp = null;

// Helper: Format phone number correctly
function formatPhoneNumber(phone) {
    // Remove all non-digits
    let clean = phone.replace(/[^0-9]/g, '');
    
    // Handle WhatsApp JID format
    if (clean.includes('@')) {
        clean = clean.split('@')[0];
    }
    
    // Remove leading zeros
    clean = clean.replace(/^0+/, '');
    
    // If it's just 10 digits, assume India (+91)
    if (clean.length === 10) {
        clean = '91' + clean;
    }
    
    // If it starts with 91 and is 12 digits, it's valid
    // Otherwise, take last 10 digits and prefix with 91
    if (clean.length > 12) {
        clean = '91' + clean.slice(-10);
    }
    
    return clean;
}

// Initialize Baileys
async function initializeBaileys() {
    try {
        // Dynamic import
        const baileys = await import('@whiskeysockets/baileys');
        makeWASocket = baileys.default;
        useMultiFileAuthState = baileys.useMultiFileAuthState;
        DisconnectReason = baileys.DisconnectReason;
        fetchLatestBaileysVersion = baileys.fetchLatestBaileysVersion;
        
        console.log('Baileys loaded successfully');
        await connectToWhatsApp();
    } catch (error) {
        console.error('Failed to load Baileys:', error.message);
        connectionStatus = 'error';
    }
}

// Connect to WhatsApp
async function connectToWhatsApp() {
    try {
        connectionStatus = 'connecting';
        console.log('Connecting to WhatsApp...');
        
        // Get latest version
        const { version, isLatest } = await fetchLatestBaileysVersion();
        console.log(`Using WA v${version.join('.')}, isLatest: ${isLatest}`);
        
        // Load auth state
        const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);
        
        // Create socket
        sock = makeWASocket({
            version,
            auth: state,
            logger,
            printQRInTerminal: false,
            browser: ['Sales Brain', 'Chrome', '120.0.0'],
            connectTimeoutMs: 60000,
            defaultQueryTimeoutMs: 0,
            keepAliveIntervalMs: 30000,
            emitOwnEvents: true,
            fireInitQueries: true,
            generateHighQualityLinkPreview: false,
            syncFullHistory: false,
            markOnlineOnConnect: true
        });
        
        // Handle connection updates
        sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;
            
            if (qr) {
                console.log('QR Code received, generating image...');
                try {
                    currentQR = await qrcode.toDataURL(qr);
                    connectionStatus = 'waiting_for_scan';
                    isReady = false;
                    connectedPhone = null;
                    console.log('QR Code ready for scanning');
                } catch (err) {
                    console.error('QR generation error:', err);
                }
            }
            
            if (connection === 'close') {
                const statusCode = lastDisconnect?.error?.output?.statusCode;
                const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
                
                console.log('Connection closed. Status:', statusCode, 'Reconnect:', shouldReconnect);
                
                isReady = false;
                currentQR = null;
                connectionStatus = 'disconnected';
                
                if (shouldReconnect) {
                    console.log('Reconnecting in 3 seconds...');
                    setTimeout(connectToWhatsApp, 3000);
                } else {
                    // Clear auth if logged out
                    if (fs.existsSync(AUTH_FOLDER)) {
                        fs.rmSync(AUTH_FOLDER, { recursive: true, force: true });
                        console.log('Auth cleared due to logout');
                    }
                }
            } else if (connection === 'open') {
                console.log('WhatsApp connection opened!');
                isReady = true;
                currentQR = null;
                connectionStatus = 'connected';
                
                // CRITICAL: Set connection timestamp - only messages AFTER this get AI replies
                connectionTimestamp = Math.floor(Date.now() / 1000);
                console.log('Connection timestamp set:', connectionTimestamp, '- Only messages after this will get AI replies');
                
                // Get connected phone number
                if (sock.user) {
                    // Format: 919876543210:XX@s.whatsapp.net - extract just the number
                    const rawId = sock.user.id.split(':')[0];
                    connectedPhone = formatPhoneNumber(rawId);
                    console.log('Connected as:', connectedPhone);
                }
                
                // Notify backend of connection with timestamp
                try {
                    await axios.post(`${BACKEND_URL}/api/whatsapp/connected`, {
                        phone: connectedPhone,
                        connectionTimestamp: connectionTimestamp
                    });
                    console.log('Backend notified of connection');
                } catch (err) {
                    console.error('Failed to notify backend:', err.message);
                }
                
                // Start syncing messages (read-only historical data)
                syncMessages();
            }
        });
        
        // Save credentials
        sock.ev.on('creds.update', saveCreds);
        
        // Handle incoming messages
        sock.ev.on('messages.upsert', async ({ messages, type }) => {
            if (type !== 'notify') return;
            
            for (const msg of messages) {
                // Skip own messages and status updates
                if (msg.key.fromMe || msg.key.remoteJid === 'status@broadcast') continue;
                
                // Format phone number correctly
                const rawPhone = msg.key.remoteJid.replace('@s.whatsapp.net', '').replace('@g.us', '');
                const phone = formatPhoneNumber(rawPhone);
                
                const content = msg.message?.conversation || 
                               msg.message?.extendedTextMessage?.text ||
                               msg.message?.imageMessage?.caption ||
                               '[Media message]';
                
                // Get message timestamp (Unix seconds)
                const msgTimestamp = parseInt(msg.messageTimestamp) || Math.floor(Date.now() / 1000);
                
                // CRITICAL: Check if this is a historical message (before connection)
                const isHistorical = connectionTimestamp && msgTimestamp < connectionTimestamp;
                
                console.log(`Incoming message from: ${phone} - ${content.substring(0, 50)}`);
                console.log(`  Message timestamp: ${msgTimestamp}, Connection timestamp: ${connectionTimestamp}`);
                console.log(`  Is historical (read-only): ${isHistorical}`);
                
                // Forward to backend with historical flag
                try {
                    const response = await axios.post(`${BACKEND_URL}/api/whatsapp/incoming`, {
                        phone: phone,
                        message: content,
                        timestamp: msgTimestamp,
                        messageId: msg.key.id,
                        hasMedia: !!(msg.message?.imageMessage || msg.message?.videoMessage || msg.message?.audioMessage),
                        isHistorical: isHistorical  // Backend will NOT auto-reply if true
                    });
                    console.log('Message forwarded to backend:', response.data?.mode || 'normal');
                } catch (err) {
                    console.error('Failed to forward message:', err.message);
                    if (err.response) {
                        console.error('Backend error:', err.response.data);
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Connection error:', error.message);
        connectionStatus = 'error';
        // Retry after 5 seconds
        setTimeout(connectToWhatsApp, 5000);
    }
}

// Sync existing messages (slowly to avoid rate limits)
async function syncMessages() {
    if (!sock || !isReady) return;
    
    try {
        syncProgress = { total: 0, synced: 0, status: 'syncing' };
        console.log('Starting message sync...');
        
        // Get all chats
        const chats = await sock.groupFetchAllParticipating();
        const chatIds = Object.keys(chats || {});
        
        // Also include recent direct chats from store
        // Note: Baileys doesn't store chat history like whatsapp-web.js
        // We'll sync on message receipt instead
        
        console.log(`Found ${chatIds.length} group chats`);
        syncProgress.total = chatIds.length;
        
        // For now, mark sync as complete
        // Real-time messages will be handled by messages.upsert event
        syncProgress.status = 'complete';
        console.log('Sync setup complete - messages will sync in real-time');
        
    } catch (error) {
        console.error('Sync error:', error.message);
        syncProgress.status = 'error';
    }
}

// Send message via WhatsApp
async function sendMessage(phone, message) {
    if (!sock || !isReady) {
        console.error('Send failed: WhatsApp not connected. isReady:', isReady, 'sock:', !!sock);
        throw new Error('WhatsApp not connected');
    }
    
    // Format phone number correctly
    const cleanPhone = formatPhoneNumber(phone);
    const jid = cleanPhone + '@s.whatsapp.net';
    
    console.log(`Sending message to: ${cleanPhone} (JID: ${jid})`);
    console.log(`Message preview: ${message.substring(0, 100)}...`);
    
    try {
        const result = await sock.sendMessage(jid, { text: message });
        console.log('Message sent successfully. ID:', result?.key?.id);
        return true;
    } catch (err) {
        console.error('Send message error:', err.message);
        throw err;
    }
}

// API Routes
app.get('/health', (req, res) => {
    res.json({ status: 'ok', library: 'baileys' });
});

app.get('/status', (req, res) => {
    res.json({
        connected: isReady,
        phone: connectedPhone,
        qrCode: currentQR,
        syncProgress: syncProgress,
        connectionStatus: connectionStatus,
        connectionTimestamp: connectionTimestamp,  // When session started
        previewMode: false,
        library: 'baileys'
    });
});

app.get('/qr', (req, res) => {
    if (isReady) {
        res.json({ message: 'Already connected', phone: connectedPhone });
    } else if (currentQR) {
        res.json({ qrCode: currentQR });
    } else {
        res.json({ message: 'Generating QR code...', qrCode: null });
    }
});

app.post('/send', async (req, res) => {
    try {
        const { phone, message } = req.body;
        console.log('Send API called. Phone:', phone, 'Message length:', message?.length);
        
        if (!phone || !message) {
            return res.status(400).json({ error: 'Phone and message are required' });
        }
        
        await sendMessage(phone, message);
        res.json({ success: true });
    } catch (error) {
        console.error('Send API error:', error.message);
        res.status(500).json({ error: error.message, connected: isReady });
    }
});

app.post('/disconnect', async (req, res) => {
    try {
        if (sock) {
            await sock.logout();
        }
        isReady = false;
        connectedPhone = null;
        currentQR = null;
        connectionStatus = 'disconnected';
        
        // Clear auth
        if (fs.existsSync(AUTH_FOLDER)) {
            fs.rmSync(AUTH_FOLDER, { recursive: true, force: true });
        }
        
        res.json({ success: true });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/reconnect', async (req, res) => {
    try {
        console.log('Reconnect requested...');
        
        // Close existing connection
        if (sock) {
            sock.end();
        }
        
        isReady = false;
        connectedPhone = null;
        currentQR = null;
        connectionTimestamp = null;  // Reset connection timestamp
        
        // Clear old auth and start fresh
        if (fs.existsSync(AUTH_FOLDER)) {
            fs.rmSync(AUTH_FOLDER, { recursive: true, force: true });
            console.log('Auth folder cleared');
        }
        
        // Reconnect
        await connectToWhatsApp();
        
        res.json({ success: true, message: 'Reconnecting...' });
    } catch (error) {
        console.error('Reconnect error:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`WhatsApp service (Baileys) running on port ${PORT}`);
    initializeBaileys();
});
