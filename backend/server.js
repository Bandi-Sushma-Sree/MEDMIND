const express = require('express');
const mongoose = require('mongoose');
const bcrypt = require('bcrypt');
const cors = require('cors');
const jwt = require('jsonwebtoken');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB Connection
const MONGODB_URI = 'mongodb://localhost:27017/medmind' || process.env.MONGODB_URI;
mongoose.connect(MONGODB_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

// User Schema
const userSchema = new mongoose.Schema({
    fullName: {
        type: String,
        required: true,
        trim: true
    },
    email: {
        type: String,
        required: true,
        unique: true,
        lowercase: true,
        trim: true
    },
    password: {
        type: String,
        required: true,
        minlength: 6
    }
}, {
    timestamps: true
});

// Feedback Schema
const feedbackSchema = new mongoose.Schema({
    rating: {
        type: Number,
        required: true,
        min: 1,
        max: 5
    },
    emotions: [{
        type: String,
        enum: ['happy', 'confused', 'surprised', 'frustrated']
    }],
    easeOfUse: {
        type: Number,
        min: 1,
        max: 5,
        default: 3
    },
    message: {
        type: String,
        required: true,
        trim: true
    },
    name: {
        type: String,
        trim: true
    },
    email: {
        type: String,
        lowercase: true,
        trim: true
    },
    wantsUpdates: {
        type: Boolean,
        default: false
    },
    userAgent: String,
    ipAddress: String
}, {
    timestamps: true
});

const User = mongoose.model('User', userSchema);
const Feedback = mongoose.model('Feedback', feedbackSchema);

// Routes

// Register Route
app.post('/api/register', async (req, res) => {
    try {
        const { fullName, email, password } = req.body;

        // Check if user already exists
        const existingUser = await User.findOne({ email });
        if (existingUser) {
            return res.status(400).json({ 
                success: false, 
                message: 'User already exists with this email' 
            });
        }

        // Hash password
        const saltRounds = 10;
        const hashedPassword = await bcrypt.hash(password, saltRounds);

        // Create new user
        const newUser = new User({
            fullName,
            email,
            password: hashedPassword
        });

        await newUser.save();

        // Generate JWT token
        const token = jwt.sign(
            { userId: newUser._id, email: newUser.email },
            'your-secret-key', // Change this to a secure secret
            { expiresIn: '24h' }
        );

        res.status(201).json({
            success: true,
            message: 'User registered successfully',
            token,
            user: {
                id: newUser._id,
                fullName: newUser.fullName,
                email: newUser.email
            }
        });

    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Server error during registration' 
        });
    }
});

// Login Route
app.post('/api/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        // Find user by email
        const user = await User.findOne({ email });
        if (!user) {
            return res.status(400).json({ 
                success: false, 
                message: 'Invalid email or password' 
            });
        }

        // Check password
        const isPasswordValid = await bcrypt.compare(password, user.password);
        if (!isPasswordValid) {
            return res.status(400).json({ 
                success: false, 
                message: 'Invalid email or password' 
            });
        }

        // Generate JWT token
        const token = jwt.sign(
            { userId: user._id, email: user.email },
            'your-secret-key', // Change this to a secure secret
            { expiresIn: '24h' }
        );

        res.json({
            success: true,
            message: 'Login successful',
            token,
            user: {
                id: user._id,
                fullName: user.fullName,
                email: user.email
            }
        });

    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Server error during login' 
        });
    }
});

// Feedback Submission Route
app.post('/api/feedback', async (req, res) => {
    try {
        const { rating, emotions, easeOfUse, message, name, email, wantsUpdates } = req.body;

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
            emotions: emotions || [],
            easeOfUse: parseInt(easeOfUse) || 3,
            message: message.trim(),
            name: name?.trim(),
            email: email?.trim(),
            wantsUpdates: Boolean(wantsUpdates),
            userAgent: req.get('User-Agent'),
            ipAddress: req.ip || req.connection.remoteAddress
        });

        await newFeedback.save();

        res.status(201).json({
            success: true,
            message: 'Feedback submitted successfully',
            feedbackId: newFeedback._id
        });

    } catch (error) {
        console.error('Feedback submission error:', error);
        res.status(500).json({
            success: false,
            message: 'Server error during feedback submission'
        });
    }
});

// Get All Feedback (Admin Route)
app.get('/api/feedback', async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 10;
        const skip = (page - 1) * limit;

        const feedbacks = await Feedback.find()
            .sort({ createdAt: -1 })
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
                total
            }
        });

    } catch (error) {
        console.error('Get feedback error:', error);
        res.status(500).json({
            success: false,
            message: 'Server error retrieving feedback'
        });
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

        res.json({
            success: true,
            analytics: analytics[0] || {},
            emotionStats
        });

    } catch (error) {
        console.error('Analytics error:', error);
        res.status(500).json({
            success: false,
            message: 'Server error retrieving analytics'
        });
    }
});

// Verify Token Route
app.get('/api/verify-token', async (req, res) => {
    try {
        const token = req.headers.authorization?.split(' ')[1];
        
        if (!token) {
            return res.status(401).json({ 
                success: false, 
                message: 'No token provided' 
            });
        }

        const decoded = jwt.verify(token, 'your-secret-key');
        const user = await User.findById(decoded.userId).select('-password');
        
        if (!user) {
            return res.status(401).json({ 
                success: false, 
                message: 'Invalid token' 
            });
        }

        res.json({
            success: true,
            user: {
                id: user._id,
                fullName: user.fullName,
                email: user.email
            }
        });

    } catch (error) {
        res.status(401).json({ 
            success: false, 
            message: 'Invalid token' 
        });
    }
});

app.listen(PORT, () => {
    console.log(`MedMind server running on port ${PORT}`);
});

module.exports = app;
