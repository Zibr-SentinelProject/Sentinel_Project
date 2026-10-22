CREATE TABLE IF NOT EXISTS user (
    id       UUID PRIMARY KEY DEFAULT UUID(),
    name     VARCHAR(100) NOT NULL,
    email    VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role     ENUM('EMPLOYEE', 'ANALYST') NOT NULL DEFAULT 'EMPLOYEE'
);

CREATE TABLE IF NOT EXISTS incident (
    id          UUID PRIMARY KEY DEFAULT UUID(),
    user_id     UUID NOT NULL,
    analyst_id  UUID NULL,
    title       VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    severity    ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    state       ENUM('OPEN', 'PENDING', 'CLOSED') NOT NULL DEFAULT 'OPEN',
    open_date   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    close_date  DATETIME NULL,
    CONSTRAINT fk_incidents_user FOREIGN KEY (user_id) REFERENCES users (id),
    CONSTRAINT fk_incidents_analyst FOREIGN KEY (analyst_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS comment (
    id          UUID PRIMARY KEY DEFAULT UUID(),
    content     TEXT NOT NULL,
    author_id   UUID NOT NULL,
    incident_id UUID NOT NULL,
    timestamp   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comments_author FOREIGN KEY (author_id) REFERENCES users (id),
    CONSTRAINT fk_comments_incident FOREIGN KEY (incident_id) REFERENCES incidents (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attachment (
    id          UUID PRIMARY KEY DEFAULT UUID(),
    incident_id UUID NOT NULL,
    filename    VARCHAR(255) NOT NULL,
    filetype    VARCHAR(100) NOT NULL,
    filesize    INT UNSIGNED NOT NULL,
    path        VARCHAR(500) NOT NULL,
    CONSTRAINT fk_attachments_incident FOREIGN KEY (incident_id) REFERENCES incidents (id) ON DELETE CASCADE
);
