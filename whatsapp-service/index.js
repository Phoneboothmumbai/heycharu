const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const qrcode = require('qrcode');

const app = express();
app.use(cors());
app.use(express.json());

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';
const PORT = process.env.WA_PORT || 3001;

// WhatsApp client state
let client = null;
let currentQR = null;
let isReady = false;
let connectedPhone = null;
let syncProgress = { total: 0, synced: 0, status: 'idle' };

// Initialize WhatsApp client
function initializeClient() {
    if (client) {
        client.destroy();
    }

    client = new Client({
        authStrategy: new LocalAuth({ dataPath: '/app/whatsapp-service/.wwebjs_auth' }),
        puppeteer: {
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        }
    });

    client.on('qr', async (qr) => {
        console.log('QR Code received');
        currentQR = await qrcode.toDataURL(qr);
        isReady = false;
        connectedPhone = null;
    });

    client.on('ready', async () => {
        console.log('WhatsApp client is ready!');
        isReady = true;
        currentQR = null;
        
        // Get connected phone number
        const info = client.info;
        connectedPhone = info.wid.user;
        console.log('Connected as:', connectedPhone);

        // Start syncing messages
        syncMessages();
    });

    client.on('authenticated', () => {
        console.log('WhatsApp authenticated');
    });

    client.on('auth_failure', (msg) => {
        console.error('Auth failure:', msg);
        isReady = false;
        currentQR = null;
    });

    client.on('disconnected', (reason) => {
        console.log('WhatsApp disconnected:', reason);
        isReady = false;
        connectedPhone = null;
        // Reinitialize after disconnect
        setTimeout(initializeClient, 5000);
    });

    // Handle incoming messages
    client.on('message', async (message) => {
        console.log('New message from:', message.from, '-', message.body.substring(0, 50));
        await processIncomingMessage(message);
    });

    client.initialize();
}

// Process incoming message and send to backend
async function processIncomingMessage(message) {
    try {
        const phone = message.from.replace('@c.us', '');
        const content = message.body;
        
        // Send to backend
        await axios.post(`${BACKEND_URL}/api/whatsapp/incoming`, {
            phone: phone,
            message: content,
            timestamp: message.timestamp,
            messageId: message.id._serialized,
            hasMedia: message.hasMedia
        });
        
        console.log('Message forwarded to backend');
    } catch (error) {
        console.error('Error processing message:', error.message);
    }
}

// Sync existing messages (slowly to avoid rate limits)
async function syncMessages() {
    try {
        syncProgress = { total: 0, synced: 0, status: 'syncing' };
        console.log('Starting message sync...');
        
        const chats = await client.getChats();
        syncProgress.total = chats.length;
        console.log(`Found ${chats.length} chats`);

        for (let i = 0; i < chats.length; i++) {
            const chat = chats[i];
            if (chat.isGroup) continue; // Skip groups for now
            
            try {
                // Fetch last 50 messages per chat
                const messages = await chat.fetchMessages({ limit: 50 });
                const phone = chat.id.user;
                
                // Send to backend for storage
                await axios.post(`${BACKEND_URL}/api/whatsapp/sync-messages`, {
                    phone: phone,
                    chatName: chat.name,
                    messages: messages.map(m => ({
                        id: m.id._serialized,
                        body: m.body,
                        fromMe: m.fromMe,
                        timestamp: m.timestamp,
                        hasMedia: m.hasMedia
                    }))
                });
                
                syncProgress.synced++;
                console.log(`Synced chat ${i + 1}/${chats.length}: ${chat.name || phone}`);
                
                // Slow down to avoid issues (500ms delay between chats)
                await new Promise(resolve => setTimeout(resolve, 500));
            } catch (chatError) {
                console.error(`Error syncing chat ${chat.name}:`, chatError.message);
            }
        }
        
        syncProgress.status = 'complete';
        console.log('Message sync complete!');
    } catch (error) {
        console.error('Error syncing messages:', error.message);
        syncProgress.status = 'error';
    }
}

// Send message via WhatsApp
async function sendMessage(phone, message) {
    if (!isReady) throw new Error('WhatsApp not connected');
    
    const chatId = phone.includes('@c.us') ? phone : `${phone.replace(/[^0-9]/g, '')}@c.us`;
    await client.sendMessage(chatId, message);
    return true;
}

// API Routes
app.get('/status', (req, res) => {
    res.json({
        connected: isReady,
        phone: connectedPhone,
        qrCode: currentQR,
        syncProgress: syncProgress
    });
});

app.get('/qr', (req, res) => {
    if (currentQR) {
        res.json({ qrCode: currentQR });
    } else if (isReady) {
        res.json({ message: 'Already connected', phone: connectedPhone });
    } else {
        res.json({ message: 'Initializing...', qrCode: null });
    }
});

app.post('/send', async (req, res) => {
    try {
        const { phone, message } = req.body;
        await sendMessage(phone, message);
        res.json({ success: true });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/disconnect', async (req, res) => {
    try {
        if (client) {
            await client.logout();
        }
        isReady = false;
        connectedPhone = null;
        currentQR = null;
        res.json({ success: true });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/reconnect', (req, res) => {
    initializeClient();
    res.json({ success: true, message: 'Reconnecting...' });
});

// Start server
app.listen(PORT, () => {
    console.log(`WhatsApp service running on port ${PORT}`);
    initializeClient();
});
