-- Create users table for coaches
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create athletes table
CREATE TABLE athletes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    grade INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create time_trials table
CREATE TABLE time_trials (
    id SERIAL PRIMARY KEY,
    athlete_id INTEGER REFERENCES athletes(id),
    coach_id INTEGER REFERENCES users(id),
    trial_date DATE NOT NULL,
    time_seconds DECIMAL(6,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create notifications table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_time_trials_athlete ON time_trials(athlete_id);
CREATE INDEX idx_time_trials_date ON time_trials(trial_date);
CREATE INDEX idx_athletes_grade ON athletes(grade);
CREATE INDEX idx_notifications_user ON notifications(user_id);

-- Create view for fastest times by grade
CREATE VIEW fastest_times_by_grade AS
SELECT 
    a.grade,
    a.name as athlete_name,
    tt.time_seconds,
    tt.trial_date,
    ROW_NUMBER() OVER (PARTITION BY a.grade ORDER BY tt.time_seconds) as rank
FROM time_trials tt
JOIN athletes a ON tt.athlete_id = a.id;

-- Create view for most improved athletes
CREATE VIEW most_improved_athletes AS
WITH athlete_improvements AS (
    SELECT 
        a.id,
        a.name,
        a.grade,
        MIN(tt.time_seconds) as first_time,
        MAX(tt.time_seconds) as latest_time,
        COUNT(tt.id) as trial_count
    FROM athletes a
    JOIN time_trials tt ON a.id = tt.athlete_id
    GROUP BY a.id, a.name, a.grade
    HAVING COUNT(tt.id) >= 2
)
SELECT 
    id,
    name,
    grade,
    first_time,
    latest_time,
    (first_time - latest_time) as improvement,
    trial_count
FROM athlete_improvements
ORDER BY improvement DESC;
