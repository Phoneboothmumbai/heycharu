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
let connectionStatus = 'disconnected';

// CRITICAL: Connection timestamp - only messages AFTER this time get AI replies
let connectionTimestamp = null;

// Reconnection control
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;
const BASE_RECONNECT_DELAY = 5000; // 5 seconds base delay

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
        
        // Ensure auth folder exists
        if (!fs.existsSync(AUTH_FOLDER)) {
            fs.mkdirSync(AUTH_FOLDER, { recursive: true });
        }
        
        // Load auth state
        const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);
        
        // Create socket with STABLE settings
        sock = makeWASocket({
            version,
            auth: state,
            logger,
            printQRInTerminal: false,
            browser: ['Sales Brain', 'Chrome', '120.0.0'],
            connectTimeoutMs: 60000,
            defaultQueryTimeoutMs: 0,
            keepAliveIntervalMs: 25000, // Keep alive every 25 seconds
            emitOwnEvents: false, // Don't emit own events to avoid loops
            fireInitQueries: false, // Don't fire init queries - causes rate limits
            generateHighQualityLinkPreview: false,
            syncFullHistory: false, // CRITICAL: Don't sync history
            markOnlineOnConnect: false, // Don't mark online - reduces API calls
            retryRequestDelayMs: 2000 // Delay between retries
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
                
                if (shouldReconnect && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                    reconnectAttempts++;
                    // Exponential backoff: 5s, 10s, 20s, 40s... up to 60s max
                    const delay = Math.min(BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts - 1), 60000);
                    console.log(`Reconnecting in ${delay/1000} seconds... (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
                    setTimeout(connectToWhatsApp, delay);
                } else if (!shouldReconnect) {
                    // Clear auth if logged out
                    console.log('Logged out - clearing auth');
                    if (fs.existsSync(AUTH_FOLDER)) {
                        fs.rmSync(AUTH_FOLDER, { recursive: true, force: true });
                    }
                    reconnectAttempts = 0;
                    // Start fresh connection
                    setTimeout(connectToWhatsApp, 3000);
                } else {
                    console.log('Max reconnect attempts reached. Please restart manually.');
                    connectionStatus = 'error';
                }
            } else if (connection === 'open') {
                console.log('WhatsApp connection opened!');
                isReady = true;
                currentQR = null;
                connectionStatus = 'connected';
                reconnectAttempts = 0; // Reset on successful connection
                
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
                
                // Notify backend of connection with timestamp (non-blocking)
                axios.post(`${BACKEND_URL}/api/whatsapp/connected`, {
                    phone: connectedPhone,
                    connectionTimestamp: connectionTimestamp
                }).then(() => {
                    console.log('Backend notified of connection');
                }).catch((err) => {
                    console.error('Failed to notify backend:', err.message);
                });
                
                // NO syncMessages() call - let messages come in real-time
                console.log('Ready to receive messages in real-time');
            }
        });
        
        // Save credentials when updated
        sock.ev.on('creds.update', async () => {
            console.log('Credentials updated, saving...');
            await saveCreds();
        });
        
        // Handle incoming messages
        sock.ev.on('messages.upsert', async ({ messages, type }) => {
            // Only handle notify type (real-time messages)
            if (type !== 'notify') return;
            
            for (const msg of messages) {
                // Skip own messages and status updates
                if (msg.key.fromMe) continue;
                if (msg.key.remoteJid === 'status@broadcast') continue;
                if (msg.key.remoteJid?.endsWith('@g.us')) continue; // Skip group messages
                
                // Format phone number correctly
                const rawPhone = msg.key.remoteJid.replace('@s.whatsapp.net', '');
                const phone = formatPhoneNumber(rawPhone);
                
                const content = msg.message?.conversation || 
                               msg.message?.extendedTextMessage?.text ||
                               msg.message?.imageMessage?.caption ||
                               '[Media message]';
                
                // Get message timestamp (Unix seconds)
                const msgTimestamp = parseInt(msg.messageTimestamp) || Math.floor(Date.now() / 1000);
                
                // CRITICAL: Check if this is a historical message (before connection)
                const isHistorical = connectionTimestamp && msgTimestamp < connectionTimestamp;
                
                console.log(`[MESSAGE] From: ${phone}`);
                console.log(`  Content: ${content.substring(0, 50)}...`);
                console.log(`  Timestamp: ${msgTimestamp}, Connection: ${connectionTimestamp}, Historical: ${isHistorical}`);
                
                // Forward to backend with historical flag
                try {
                    const response = await axios.post(`${BACKEND_URL}/api/whatsapp/incoming`, {
                        phone: phone,
                        message: content,
                        timestamp: msgTimestamp,
                        messageId: msg.key.id,
                        hasMedia: !!(msg.message?.imageMessage || msg.message?.videoMessage || msg.message?.audioMessage),
                        isHistorical: isHistorical
                    }, { timeout: 30000 });
                    console.log(`  Backend response: ${response.data?.mode || 'normal'}`);
                } catch (err) {
                    console.error(`  Failed to forward: ${err.message}`);
                    if (err.response) {
                        console.error(`  Backend error: ${JSON.stringify(err.response.data)}`);
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Connection error:', error.message);
        connectionStatus = 'error';
        
        // Retry with exponential backoff
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            const delay = Math.min(BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts - 1), 60000);
            console.log(`Retrying connection in ${delay/1000} seconds...`);
            setTimeout(connectToWhatsApp, delay);
        }
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
    
    console.log(`[SEND] To: ${cleanPhone}`);
    console.log(`  Message: ${message.substring(0, 50)}...`);
    
    try {
        const result = await sock.sendMessage(jid, { text: message });
        console.log(`  Sent successfully. ID: ${result?.key?.id}`);
        return true;
    } catch (err) {
        console.error(`  Send error: ${err.message}`);
        throw err;
    }
}

// API Routes
app.get('/health', (req, res) => {
    res.json({ status: 'ok', library: 'baileys', connected: isReady });
});

app.get('/status', (req, res) => {
    res.json({
        connected: isReady,
        phone: connectedPhone,
        qrCode: currentQR,
        connectionStatus: connectionStatus,
        connectionTimestamp: connectionTimestamp,
        reconnectAttempts: reconnectAttempts,
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
        console.log('[API] Send request. Phone:', phone);
        
        if (!phone || !message) {
            return res.status(400).json({ error: 'Phone and message are required' });
        }
        
        await sendMessage(phone, message);
        res.json({ success: true });
    } catch (error) {
        console.error('[API] Send error:', error.message);
        res.status(500).json({ error: error.message, connected: isReady });
    }
});

app.post('/disconnect', async (req, res) => {
    try {
        console.log('[API] Disconnect requested');
        if (sock) {
            await sock.logout();
        }
        isReady = false;
        connectedPhone = null;
        currentQR = null;
        connectionStatus = 'disconnected';
        reconnectAttempts = 0;
        
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
        console.log('[API] Reconnect requested');
        
        // Close existing connection gracefully
        if (sock) {
            try {
                sock.end();
            } catch (e) {
                // Ignore errors on close
            }
        }
        
        isReady = false;
        connectedPhone = null;
        currentQR = null;
        connectionTimestamp = null;
        reconnectAttempts = 0;
        
        // Clear old auth and start fresh
        if (fs.existsSync(AUTH_FOLDER)) {
            fs.rmSync(AUTH_FOLDER, { recursive: true, force: true });
            console.log('Auth folder cleared');
        }
        
        // Wait a moment before reconnecting
        setTimeout(connectToWhatsApp, 2000);
        
        res.json({ success: true, message: 'Reconnecting...' });
    } catch (error) {
        console.error('[API] Reconnect error:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`WhatsApp service (Baileys) running on port ${PORT}`);
    initializeBaileys();
});
