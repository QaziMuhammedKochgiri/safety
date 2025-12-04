/**
 * SafeChild WhatsApp Service
 * Production-ready WhatsApp Web automation for evidence extraction
 */

const express = require('express');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const fs = require('fs-extra');
const path = require('path');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Configuration
const PORT = process.env.PORT || 8002;
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8001';
const SHARED_DIR = process.env.SHARED_DIR || '/tmp/forensics_uploads';
const NODE_ENV = process.env.NODE_ENV || 'development';

// Logging helper
const log = (level, message, data = {}) => {
    const timestamp = new Date().toISOString();
    const logEntry = { timestamp, level, message, ...data };
    if (NODE_ENV === 'production') {
        console.log(JSON.stringify(logEntry));
    } else {
        console.log(`[${timestamp}] ${level.toUpperCase()}: ${message}`, data);
    }
};

// Store active clients in memory
const sessions = new Map();

// Session status enum
const SessionStatus = {
    INITIALIZING: 'initializing',
    QR_READY: 'qr_ready',
    PAIRING_CODE_READY: 'pairing_code_ready',
    CONNECTED: 'connected',
    EXTRACTING: 'extracting',
    COMPLETED: 'completed',
    FAILED: 'failed',
    TIMEOUT: 'timeout'
};

// Helper: Generate a unique ID
const generateId = () => `wa_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'whatsapp-service',
        activeSessions: sessions.size,
        timestamp: new Date().toISOString()
    });
});

// Start a new WhatsApp session (supports both QR and pairing code)
app.post('/session/start', async (req, res) => {
    const { clientNumber, phoneNumber, usePairingCode } = req.body;

    if (!clientNumber) {
        return res.status(400).json({ error: 'clientNumber is required' });
    }

    // If pairing code requested, phone number is required
    if (usePairingCode && !phoneNumber) {
        return res.status(400).json({ error: 'phoneNumber is required for pairing code authentication' });
    }

    const sessionId = generateId();
    log('info', 'Starting WhatsApp session', { sessionId, clientNumber, usePairingCode: !!usePairingCode });

    try {
        const client = new Client({
            authStrategy: new LocalAuth({ clientId: sessionId }),
            puppeteer: {
                headless: true,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu'
                ]
            }
        });

        // Initialize session data
        sessions.set(sessionId, {
            client,
            clientNumber,
            phoneNumber: phoneNumber || null,
            usePairingCode: !!usePairingCode,
            qr: null,
            pairingCode: null,
            status: SessionStatus.INITIALIZING,
            createdAt: new Date(),
            error: null
        });

        // QR Code event (only used if not using pairing code)
        client.on('qr', async (qr) => {
            const session = sessions.get(sessionId);
            if (!session) return;

            // If using pairing code, request it instead of showing QR
            if (session.usePairingCode && session.phoneNumber) {
                log('info', 'Requesting pairing code', { sessionId, phoneNumber: session.phoneNumber });
                try {
                    // Format: remove + and spaces, just digits with country code
                    const formattedPhone = session.phoneNumber.replace(/[^0-9]/g, '');
                    const code = await client.requestPairingCode(formattedPhone);
                    log('info', 'Pairing code generated', { sessionId, code });
                    session.pairingCode = code;
                    session.status = SessionStatus.PAIRING_CODE_READY;
                } catch (err) {
                    log('error', 'Failed to request pairing code', { sessionId, error: err.message });
                    // Fallback to QR
                    try {
                        const qrDataUrl = await qrcode.toDataURL(qr);
                        session.qr = qrDataUrl;
                        session.status = SessionStatus.QR_READY;
                        session.error = 'Pairing code failed, showing QR instead';
                    } catch (qrErr) {
                        log('error', 'Failed to generate QR code', { sessionId, error: qrErr.message });
                    }
                }
            } else {
                // Standard QR code flow
                log('info', 'QR code received', { sessionId });
                try {
                    const qrDataUrl = await qrcode.toDataURL(qr);
                    session.qr = qrDataUrl;
                    session.status = SessionStatus.QR_READY;
                } catch (err) {
                    log('error', 'Failed to generate QR code', { sessionId, error: err.message });
                }
            }
        });

        // Ready event - client connected
        client.on('ready', async () => {
            log('info', 'WhatsApp client ready', { sessionId });
            const session = sessions.get(sessionId);
            if (session) {
                session.status = SessionStatus.CONNECTED;
                session.qr = null;
                session.pairingCode = null;

                // Start extraction automatically
                await extractData(sessionId);
            }
        });

        // Authentication failure
        client.on('auth_failure', (msg) => {
            log('error', 'Authentication failed', { sessionId, error: msg });
            const session = sessions.get(sessionId);
            if (session) {
                session.status = SessionStatus.FAILED;
                session.error = 'Authentication failed';
            }
        });

        // Disconnected
        client.on('disconnected', (reason) => {
            log('warn', 'Client disconnected', { sessionId, reason });
            const session = sessions.get(sessionId);
            if (session && session.status !== SessionStatus.COMPLETED) {
                session.status = SessionStatus.FAILED;
                session.error = `Disconnected: ${reason}`;
            }
        });

        // Initialize the client
        client.initialize();

        // Set timeout (3 minutes for QR, 5 minutes for pairing code)
        const timeoutMs = usePairingCode ? 300000 : 180000;
        setTimeout(() => {
            const session = sessions.get(sessionId);
            if (session && (session.status === SessionStatus.QR_READY || session.status === SessionStatus.PAIRING_CODE_READY)) {
                log('warn', 'Authentication timeout', { sessionId });
                session.status = SessionStatus.TIMEOUT;
                session.error = 'Authentication timeout';
                cleanupSession(sessionId);
            }
        }, timeoutMs);

        res.json({
            success: true,
            sessionId,
            usePairingCode: !!usePairingCode,
            message: usePairingCode
                ? 'Session started. Poll /session/:sessionId/status for pairing code.'
                : 'Session started. Poll /session/:sessionId/status for QR code.'
        });

    } catch (err) {
        log('error', 'Failed to start session', { sessionId, error: err.message });
        sessions.delete(sessionId);
        res.status(500).json({ error: 'Failed to start WhatsApp session', details: err.message });
    }
});

// Get session status
app.get('/session/:sessionId/status', (req, res) => {
    const { sessionId } = req.params;
    const session = sessions.get(sessionId);

    if (!session) {
        return res.status(404).json({ error: 'Session not found' });
    }

    res.json({
        sessionId,
        status: session.status,
        qr: session.qr,
        pairingCode: session.pairingCode,
        usePairingCode: session.usePairingCode,
        error: session.error,
        createdAt: session.createdAt
    });
});

// Cancel/stop a session
app.delete('/session/:sessionId', async (req, res) => {
    const { sessionId } = req.params;
    const session = sessions.get(sessionId);

    if (!session) {
        return res.status(404).json({ error: 'Session not found' });
    }

    log('info', 'Cancelling session', { sessionId });
    await cleanupSession(sessionId);

    res.json({ success: true, message: 'Session cancelled' });
});

// Extract WhatsApp data
async function extractData(sessionId) {
    const session = sessions.get(sessionId);
    if (!session) return;

    const { client, clientNumber } = session;
    session.status = SessionStatus.EXTRACTING;

    log('info', 'Starting data extraction', { sessionId, clientNumber });

    try {
        const chats = await client.getChats();
        log('info', 'Chats retrieved', { sessionId, count: chats.length });

        let fullTranscript = `=== WHATSAPP FORENSIC EXPORT ===\n`;
        fullTranscript += `Date: ${new Date().toISOString()}\n`;
        fullTranscript += `Client Number: ${clientNumber}\n`;
        fullTranscript += `Total Chats: ${chats.length}\n`;
        fullTranscript += `${'='.repeat(50)}\n\n`;

        // Process chats (limit to 50 for performance)
        const chatLimit = Math.min(chats.length, 50);
        let totalMessages = 0;

        for (let i = 0; i < chatLimit; i++) {
            const chat = chats[i];
            const chatName = chat.name || chat.id.user || 'Unknown';

            fullTranscript += `\n${'─'.repeat(40)}\n`;
            fullTranscript += `CHAT: ${chatName}\n`;
            fullTranscript += `Type: ${chat.isGroup ? 'Group' : 'Individual'}\n`;
            fullTranscript += `${'─'.repeat(40)}\n`;

            try {
                // Fetch messages (limit to 100 per chat)
                const messages = await chat.fetchMessages({ limit: 100 });
                totalMessages += messages.length;

                for (const msg of messages) {
                    const date = new Date(msg.timestamp * 1000).toLocaleString('de-DE');
                    const sender = msg.fromMe ? 'ME' : (msg.author || chatName);
                    const body = msg.body || '[Media/Sticker]';

                    fullTranscript += `[${date}] ${sender}: ${body}\n`;
                }
            } catch (msgErr) {
                fullTranscript += `[Error fetching messages: ${msgErr.message}]\n`;
            }
        }

        fullTranscript += `\n${'='.repeat(50)}\n`;
        fullTranscript += `END OF EXPORT\n`;
        fullTranscript += `Total Messages Extracted: ${totalMessages}\n`;
        fullTranscript += `Chats Processed: ${chatLimit}\n`;

        // Ensure shared directory exists
        await fs.ensureDir(SHARED_DIR);

        // Save to file
        const filename = `WHATSAPP_AUTO_${clientNumber}_${Date.now()}.txt`;
        const filePath = path.join(SHARED_DIR, filename);

        await fs.writeFile(filePath, fullTranscript, 'utf8');
        log('info', 'Transcript saved', { sessionId, filePath, totalMessages });

        // Notify backend
        try {
            await axios.post(`${BACKEND_URL}/api/forensics/analyze-internal`, {
                file_path: filePath,
                client_number: clientNumber,
                source: 'whatsapp_automation',
                statistics: {
                    total_chats: chatLimit,
                    total_messages: totalMessages
                }
            });
            log('info', 'Backend notified successfully', { sessionId });
            session.status = SessionStatus.COMPLETED;
        } catch (backendErr) {
            log('error', 'Failed to notify backend', { sessionId, error: backendErr.message });
            session.status = SessionStatus.COMPLETED; // Still mark as completed, file is saved
            session.error = 'Data extracted but backend notification failed';
        }

        // Cleanup after delay
        setTimeout(() => cleanupSession(sessionId), 60000);

    } catch (err) {
        log('error', 'Extraction failed', { sessionId, error: err.message });
        session.status = SessionStatus.FAILED;
        session.error = `Extraction failed: ${err.message}`;
        cleanupSession(sessionId);
    }
}

// Cleanup session resources
async function cleanupSession(sessionId) {
    const session = sessions.get(sessionId);
    if (!session) return;

    log('info', 'Cleaning up session', { sessionId });

    try {
        if (session.client) {
            await session.client.destroy();
        }
    } catch (err) {
        log('warn', 'Error destroying client', { sessionId, error: err.message });
    }

    // Keep session data for a while for status checks
    setTimeout(() => {
        sessions.delete(sessionId);
        log('info', 'Session removed from memory', { sessionId });
    }, 300000); // 5 minutes
}

// List all active sessions (admin endpoint)
app.get('/sessions', (req, res) => {
    const sessionList = [];
    sessions.forEach((session, id) => {
        sessionList.push({
            sessionId: id,
            clientNumber: session.clientNumber,
            status: session.status,
            createdAt: session.createdAt,
            hasQr: !!session.qr
        });
    });

    res.json({
        total: sessionList.length,
        sessions: sessionList
    });
});

// Start server
app.listen(PORT, () => {
    log('info', 'WhatsApp Service started', { port: PORT, env: NODE_ENV });
});

// Graceful shutdown
process.on('SIGTERM', async () => {
    log('info', 'Received SIGTERM, shutting down gracefully');

    // Cleanup all sessions
    for (const [sessionId] of sessions) {
        await cleanupSession(sessionId);
    }

    process.exit(0);
});
