DROP TABLE IF EXISTS labels CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS dialogues CASCADE;
DROP TABLE IF EXISTS clients CASCADE;

CREATE TABLE clients (
    client_id 	  SERIAL PRIMARY KEY,
    name          TEXT NOT NULL,
    segment       TEXT NOT NULL CHECK (segment IN ('new', 'regular', 'vip')),
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE dialogues (
    dialogue_id   SERIAL PRIMARY KEY,
    client_id     INT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    channel       TEXT NOT NULL CHECK (channel IN ('chat', 'email', 'phone')),
    started_at    TIMESTAMP NOT NULL,
    ended_at      TIMESTAMP,
    status        TEXT NOT NULL CHECK (status IN ('resolved', 'escalated', 'abandoned'))
);

CREATE TABLE messages (
    message_id    SERIAL PRIMARY KEY,
    dialogue_id   INT NOT NULL REFERENCES dialogues(dialogue_id) ON DELETE CASCADE,
    sender        TEXT NOT NULL CHECK (sender IN ('client', 'agent')),
    text          TEXT NOT NULL,
    created_at    TIMESTAMP NOT NULL
);

CREATE TABLE labels (
    label_id      SERIAL PRIMARY KEY,
    dialogue_id   INT NOT NULL REFERENCES dialogues(dialogue_id) ON DELETE CASCADE,
    topic         TEXT,
    sentiment     TEXT,
    reason        TEXT,
    model_name    TEXT,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dialogues_client ON dialogues(client_id);
CREATE INDEX idx_dialogues_started ON dialogues(strated_at);
CREATE INDEX idx_messages_dialogue ON messages(dialogue_id);
CREATE INDEX idx_labels_dialogue ON labels(dialogue_id);
