const express = require('express');
const mongoose = require('mongoose');
const bcrypt = require('bcrypt');
const cors = require('cors');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5001;

// Middleware
// Updated CORS for deployed services:
app.use(cors({
    origin: [
        "http://localhost:3000", 
        "http://localhost:5000", 
        "http://127.0.0.1:5000",
        "https://medmind-flask.onrender.com",
        "https://medmind-chatbot.onrender.com",
        "https://medmind-vte7.onrender.com"
    ],
    credentials: true
}));

app.use(express.json({ limit: '10mb' }));

// MongoDB Atlas Connection - FIXED FOR NODE.JS 22
// Replace the MONGODB_URI line with this corrected version:
const MONGODB_URI = 'mongodb+srv://sushmasreebandi92_db_user:Ramuindu%40123@cluster0.zkvvogz.mongodb.net/medmind?retryWrites=true&w=majority&appName=Cluster0';


mongoose.connect(MONGODB_URI, {
    // Removed deprecated options - they're default in newer versions
    serverSelectionTimeoutMS: 5000,
    socketTimeoutMS: 45000,
});

// Connection event listeners
mongoose.connection.on('connected', () => {
    console.log('✅ Connected to MongoDB Atlas');
});

mongoose.connection.on('error', (err) => {
    console.error('❌ MongoDB Atlas connection error:', err);
});

mongoose.connection.on('disconnected', () => {
    console.log('🔌 Disconnected from MongoDB Atlas');
});

// Enhanced User Schema
const userSchema = new mongoose.Schema({
    fullName: {
        type: String,
        required: [true, 'Full name is required'],
        trim: true,
        minlength: [2, 'Name must be at least 2 characters'],
        maxlength: [50, 'Name must be less than 50 characters']
    },
    email: {
        type: String,
        required: [true, 'Email is required'],
        unique: true,
        lowercase: true,
        trim: true,
        match: [/^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/, 'Please enter a valid email']
    },
    password: {
        type: String,
        required: [true, 'Password is required'],
        minlength: [6, 'Password must be at least 6 characters']
    },
    age: {
        type: Number,
        min: [1, 'Age must be positive'],
        max: [120, 'Age must be realistic']
    },
    gender: {
        type: String,
        enum: ['Male', 'Female', 'Other'],
        default: 'Other'
    },
    isActive: {
        type: Boolean,
        default: true
    },
    lastLogin: Date
}, {
    timestamps: true
});

// Enhanced Feedback Schema
const feedbackSchema = new mongoose.Schema({
    rating: {
        type: Number,
        required: [true, 'Rating is required'],
        min: [1, 'Rating must be at least 1'],
        max: [5, 'Rating must be at most 5']
    },
    emotions: [{
        type: String,
        enum: ['happy', 'confused', 'surprised', 'frustrated', 'satisfied', 'disappointed']
    }],
    easeOfUse: {
        type: Number,
        min: 1,
        max: 5,
        default: 3
    },
    message: {
        type: String,
        required: [true, 'Feedback message is required'],
        trim: true,
        maxlength: [1000, 'Message must be less than 1000 characters']
    },
    name: {
        type: String,
        trim: true,
        maxlength: [50, 'Name must be less than 50 characters']
    },
    email: {
        type: String,
        lowercase: true,
        trim: true,
        match: [/^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/, 'Please enter a valid email']
    },
    wantsUpdates: {
        type: Boolean,
        default: false
    },
    userAgent: String,
    ipAddress: String,
    category: {
        type: String,
        enum: ['general', 'bug', 'feature-request', 'complaint', 'compliment'],
        default: 'general'
    }
}, {
    timestamps: true
});

// Create Models
const User = mongoose.model('User', userSchema);
const Feedback = mongoose.model('Feedback', feedbackSchema);

// JWT Secret (use environment variable in production)
const JWT_SECRET = process.env.JWT_SECRET || 'medmind-super-secret-key-2025';

// Utility function for error handling
const handleError = (res, error, message = 'Server error') => {
    console.error(message + ':', error);
    res.status(500).json({
        success: false,
        message,
        error: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
};

// Routes

// Health Check Route
app.get('/', (req, res) => {
    res.json({
        success: true,
        message: '🩺 MedMind Backend API is running!',
        version: '2.0.0',
        timestamp: new Date().toISOString(),
        database: mongoose.connection.readyState === 1 ? 'Connected' : 'Disconnected'
    });
});

// Register Route
app.post('/api/register', async (req, res) => {
    try {
        const { fullName, email, password, age, gender } = req.body;

        // Input validation
        if (!fullName || !email || !password) {
            return res.status(400).json({
                success: false,
                message: 'Full name, email, and password are required'
            });
        }

        // Check if user already exists
        const existingUser = await User.findOne({ email: email.toLowerCase() });
        if (existingUser) {
            return res.status(409).json({
                success: false,
                message: 'User already exists with this email'
            });
        }

        // Hash password
        const saltRounds = 12;
        const hashedPassword = await bcrypt.hash(password, saltRounds);

        // Create new user
        const newUser = new User({
            fullName: fullName.trim(),
            email: email.toLowerCase().trim(),
            password: hashedPassword,
            age: age ? parseInt(age) : undefined,
            gender: gender || 'Other'
        });

        await newUser.save();

        // Generate JWT token
        const token = jwt.sign(
            { 
                userId: newUser._id, 
                email: newUser.email,
                fullName: newUser.fullName 
            },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        res.status(201).json({
            success: true,
            message: 'User registered successfully',
            token,
            user: {
                id: newUser._id,
                fullName: newUser.fullName,
                email: newUser.email,
                age: newUser.age,
                gender: newUser.gender
            }
        });

    } catch (error) {
        if (error.name === 'ValidationError') {
            const messages = Object.values(error.errors).map(err => err.message);
            return res.status(400).json({
                success: false,
                message: messages.join(', ')
            });
        }
        handleError(res, error, 'Registration failed');
    }
});

// Login Route
app.post('/api/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        // Input validation
        if (!email || !password) {
            return res.status(400).json({
                success: false,
                message: 'Email and password are required'
            });
        }

        // Find user by email
        const user = await User.findOne({ 
            email: email.toLowerCase(),
            isActive: true 
        });
        
        if (!user) {
            return res.status(401).json({
                success: false,
                message: 'Invalid email or password'
            });
        }

        // Check password
        const isPasswordValid = await bcrypt.compare(password, user.password);
        if (!isPasswordValid) {
            return res.status(401).json({
                success: false,
                message: 'Invalid email or password'
            });
        }

        // Update last login
        user.lastLogin = new Date();
        await user.save();

        // Generate JWT token
        const token = jwt.sign(
            { 
                userId: user._id, 
                email: user.email,
                fullName: user.fullName 
            },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        res.json({
            success: true,
            message: 'Login successful',
            token,
            user: {
                id: user._id,
                fullName: user.fullName,
                email: user.email,
                age: user.age,
                gender: user.gender,
                lastLogin: user.lastLogin
            }
        });

    } catch (error) {
        handleError(res, error, 'Login failed');
    }
});

// Feedback Submission Route
app.post('/api/feedback', async (req, res) => {
    try {
        const { 
            rating, 
            emotions, 
            easeOfUse, 
            message, 
            name, 
            email, 
            wantsUpdates,
            category 
        } = req.body;

        // Validate required fields
        if (!rating || !message) {
            return res.status(400).json({
                success: false,
                message: 'Rating and message are required'
            });
        }

        // Create new feedback
        const newFeedback = new Feedback({
            rating: parseInt(rating),
            emotions: Array.isArray(emotions) ? emotions : [],
            easeOfUse: easeOfUse ? parseInt(easeOfUse) : 3,
            message: message.trim(),
            name: name?.trim(),
            email: email?.toLowerCase().trim(),
            wantsUpdates: Boolean(wantsUpdates),
            category: category || 'general',
            userAgent: req.get('User-Agent'),
            ipAddress: req.ip || req.connection.remoteAddress || req.headers['x-forwarded-for']
        });

        await newFeedback.save();

        res.status(201).json({
            success: true,
            message: 'Thank you for your feedback! We appreciate your input.',
            feedbackId: newFeedback._id
        });

    } catch (error) {
        if (error.name === 'ValidationError') {
            const messages = Object.values(error.errors).map(err => err.message);
            return res.status(400).json({
                success: false,
                message: messages.join(', ')
            });
        }
        handleError(res, error, 'Feedback submission failed');
    }
});

// Get All Feedback (Admin Route)
app.get('/api/feedback', async (req, res) => {
    try {
        const page = Math.max(1, parseInt(req.query.page) || 1);
        const limit = Math.min(50, Math.max(1, parseInt(req.query.limit) || 10));
        const skip = (page - 1) * limit;
        const sortBy = req.query.sortBy || 'createdAt';
        const sortOrder = req.query.sortOrder === 'asc' ? 1 : -1;

        const feedbacks = await Feedback.find()
            .sort({ [sortBy]: sortOrder })
            .skip(skip)
            .limit(limit)
            .select('-ipAddress -userAgent'); // Hide sensitive data

        const total = await Feedback.countDocuments();

        res.json({
            success: true,
            data: feedbacks,
            pagination: {
                current: page,
                pages: Math.ceil(total / limit),
                total,
                hasNext: page < Math.ceil(total / limit),
                hasPrev: page > 1
            }
        });

    } catch (error) {
        handleError(res, error, 'Failed to retrieve feedback');
    }
});

// Get Feedback Analytics
app.get('/api/feedback/analytics', async (req, res) => {
    try {
        const analytics = await Feedback.aggregate([
            {
                $group: {
                    _id: null,
                    totalFeedbacks: { $sum: 1 },
                    averageRating: { $avg: '$rating' },
                    averageEaseOfUse: { $avg: '$easeOfUse' },
                    ratingDistribution: {
                        $push: '$rating'
                    }
                }
            }
        ]);

        const emotionStats = await Feedback.aggregate([
            { $unwind: '$emotions' },
            {
                $group: {
                    _id: '$emotions',
                    count: { $sum: 1 }
                }
            },
            { $sort: { count: -1 } }
        ]);

        const categoryStats = await Feedback.aggregate([
            {
                $group: {
                    _id: '$category',
                    count: { $sum: 1 },
                    avgRating: { $avg: '$rating' }
                }
            },
            { $sort: { count: -1 } }
        ]);

        res.json({
            success: true,
            analytics: analytics[0] || {
                totalFeedbacks: 0,
                averageRating: 0,
                averageEaseOfUse: 0,
                ratingDistribution: []
            },
            emotionStats,
            categoryStats
        });

    } catch (error) {
        handleError(res, error, 'Failed to retrieve analytics');
    }
});

// Verify Token Route
app.get('/api/verify-token', async (req, res) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];

        if (!token) {
            return res.status(401).json({
                success: false,
                message: 'Access token required'
            });
        }

        const decoded = jwt.verify(token, JWT_SECRET);
        const user = await User.findById(decoded.userId)
            .select('-password')
            .where({ isActive: true });

        if (!user) {
            return res.status(401).json({
                success: false,
                message: 'Invalid or expired token'
            });
        }

        res.json({
            success: true,
            user: {
                id: user._id,
                fullName: user.fullName,
                email: user.email,
                age: user.age,
                gender: user.gender,
                lastLogin: user.lastLogin
            }
        });

    } catch (error) {
        if (error.name === 'JsonWebTokenError' || error.name === 'TokenExpiredError') {
            return res.status(401).json({
                success: false,
                message: 'Invalid or expired token'
            });
        }
        handleError(res, error, 'Token verification failed');
    }
});

// Get User Profile
app.get('/api/profile', async (req, res) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];
        
        if (!token) {
            return res.status(401).json({
                success: false,
                message: 'Access token required'
            });
        }

        const decoded = jwt.verify(token, JWT_SECRET);
        const user = await User.findById(decoded.userId).select('-password');

        if (!user) {
            return res.status(404).json({
                success: false,
                message: 'User not found'
            });
        }

        res.json({
            success: true,
            user: {
                id: user._id,
                fullName: user.fullName,
                email: user.email,
                age: user.age,
                gender: user.gender,
                createdAt: user.createdAt,
                lastLogin: user.lastLogin
            }
        });

    } catch (error) {
        if (error.name === 'JsonWebTokenError' || error.name === 'TokenExpiredError') {
            return res.status(401).json({
                success: false,
                message: 'Invalid or expired token'
            });
        }
        handleError(res, error, 'Failed to get profile');
    }
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({
        success: false,
        message: 'Internal server error'
    });
});

// 404 handler
// Remove the app.use('*') line completely and use this instead:
app.all('/*splat', (req, res) => {
    res.status(404).json({
        success: false,
        message: 'API endpoint not found',
        path: req.path
    });
});


// Start server
app.listen(PORT, () => {
    console.log(`🚀 MedMind Backend Server running on port ${PORT}`);
    console.log(`🌐 API Base URL: https://medmind-api.onrender.com`);
    console.log(`📊 Health Check: https://medmind-api.onrender.com/`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('🔄 SIGTERM received, shutting down gracefully');
    mongoose.connection.close(() => {
        console.log('📴 MongoDB connection closed');
        process.exit(0);
    });
});

module.exports = app;
