const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
app.use(cors());
app.use(express.json());

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';
const PORT = process.env.WA_PORT || 3001;

// WhatsApp client state - simulation mode for preview environment
let isReady = false;
let connectedPhone = null;
let currentQR = null;
let syncProgress = { total: 0, synced: 0, status: 'idle' };

// Check if we can use real WhatsApp
const PREVIEW_MODE = true; // In preview, we can't run Chromium

// Generate a mock QR code image (base64 PNG)
function generateMockQR() {
    // Simple base64 placeholder for QR code visual
    return 'data:image/svg+xml;base64,' + Buffer.from(`
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
            <rect fill="#fff" width="200" height="200"/>
            <rect fill="#000" x="20" y="20" width="30" height="30"/>
            <rect fill="#000" x="150" y="20" width="30" height="30"/>
            <rect fill="#000" x="20" y="150" width="30" height="30"/>
            <rect fill="#000" x="60" y="20" width="10" height="10"/>
            <rect fill="#000" x="80" y="20" width="10" height="10"/>
            <rect fill="#000" x="110" y="20" width="10" height="10"/>
            <rect fill="#000" x="60" y="40" width="10" height="10"/>
            <rect fill="#000" x="100" y="40" width="10" height="10"/>
            <rect fill="#000" x="130" y="40" width="10" height="10"/>
            <rect fill="#000" x="20" y="60" width="10" height="10"/>
            <rect fill="#000" x="50" y="60" width="10" height="10"/>
            <rect fill="#000" x="80" y="60" width="10" height="10"/>
            <rect fill="#000" x="110" y="60" width="10" height="10"/>
            <rect fill="#000" x="140" y="60" width="10" height="10"/>
            <rect fill="#000" x="170" y="60" width="10" height="10"/>
            <rect fill="#000" x="40" y="80" width="10" height="10"/>
            <rect fill="#000" x="70" y="80" width="10" height="10"/>
            <rect fill="#000" x="100" y="80" width="30" height="30"/>
            <rect fill="#000" x="150" y="80" width="10" height="10"/>
            <rect fill="#000" x="20" y="100" width="10" height="10"/>
            <rect fill="#000" x="60" y="100" width="10" height="10"/>
            <rect fill="#000" x="160" y="100" width="10" height="10"/>
            <rect fill="#000" x="40" y="120" width="10" height="10"/>
            <rect fill="#000" x="70" y="120" width="10" height="10"/>
            <rect fill="#000" x="140" y="120" width="10" height="10"/>
            <rect fill="#000" x="170" y="120" width="10" height="10"/>
            <rect fill="#000" x="60" y="140" width="10" height="10"/>
            <rect fill="#000" x="90" y="140" width="10" height="10"/>
            <rect fill="#000" x="110" y="140" width="10" height="10"/>
            <rect fill="#000" x="140" y="140" width="10" height="10"/>
            <rect fill="#000" x="60" y="160" width="10" height="10"/>
            <rect fill="#000" x="80" y="160" width="10" height="10"/>
            <rect fill="#000" x="110" y="160" width="10" height="10"/>
            <rect fill="#000" x="150" y="160" width="30" height="10"/>
            <rect fill="#000" x="60" y="170" width="10" height="10"/>
            <rect fill="#000" x="100" y="170" width="10" height="10"/>
            <rect fill="#000" x="130" y="170" width="10" height="10"/>
            <text x="100" y="110" text-anchor="middle" font-family="Arial" font-size="8" fill="#666">PREVIEW</text>
        </svg>
    `).toString('base64');
}

// Initialize QR on startup
currentQR = generateMockQR();

// API Routes
app.get('/status', (req, res) => {
    res.json({
        connected: isReady,
        phone: connectedPhone,
        qrCode: isReady ? null : currentQR,
        syncProgress: syncProgress,
        previewMode: PREVIEW_MODE,
        message: PREVIEW_MODE ? 'WhatsApp Web requires Chrome browser - use simulation for testing. Deploy to production for real WhatsApp.' : null
    });
});

app.get('/qr', (req, res) => {
    if (isReady) {
        res.json({ message: 'Already connected', phone: connectedPhone });
    } else {
        res.json({ qrCode: currentQR, previewMode: PREVIEW_MODE });
    }
});

app.post('/send', async (req, res) => {
    try {
        const { phone, message } = req.body;
        if (PREVIEW_MODE) {
            // In preview mode, just log the message
            console.log(`[PREVIEW] Would send to ${phone}: ${message}`);
            res.json({ success: true, preview: true, message: 'Message logged in preview mode' });
        } else {
            // Real implementation would go here
            res.status(503).json({ error: 'Real WhatsApp not available in this environment' });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/disconnect', async (req, res) => {
    isReady = false;
    connectedPhone = null;
    currentQR = generateMockQR();
    res.json({ success: true });
});

app.post('/reconnect', (req, res) => {
    isReady = false;
    connectedPhone = null;
    currentQR = generateMockQR();
    res.json({ success: true, message: 'QR code regenerated', previewMode: PREVIEW_MODE });
});

// Simulate connection (for testing in preview)
app.post('/simulate-connect', (req, res) => {
    const { phone } = req.body;
    isReady = true;
    connectedPhone = phone || '919876543210';
    currentQR = null;
    syncProgress = { total: 0, synced: 0, status: 'complete' };
    console.log(`[PREVIEW] Simulated WhatsApp connection for: ${connectedPhone}`);
    res.json({ success: true, phone: connectedPhone });
});

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', preview: PREVIEW_MODE });
});

// Start server
app.listen(PORT, () => {
    console.log(`WhatsApp service running on port ${PORT} (Preview Mode: ${PREVIEW_MODE})`);
});
