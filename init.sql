CREATE TABLE IF NOT EXISTS user (
    id       UUID PRIMARY KEY DEFAULT UUID(),
    name     VARCHAR(100) NOT NULL,
    email    VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role     ENUM('EMPLOYEE', 'ANALYST') NOT NULL DEFAULT 'EMPLOYEE'
);

CREATE TABLE IF NOT EXISTS severity (
    id          INT(1) NOT NULL,
    name        VARCHAR(8) NOT NULL
);

CREATE TABLE IF NOT EXISTS state (
    id          INT(1) NOT NULL,
    name        VARCHAR(7) NOT NULL
);

CREATE TABLE IF NOT EXISTS incident (
    id          UUID PRIMARY KEY DEFAULT UUID(),
    user_id     UUID NOT NULL,
    analyst_id  UUID NULL,
    title       VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    severity_id INT(1) NOT NULL,
    state_id    INT(1) NOT NULL DEFAULT 0,
    open_date   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    close_date  DATETIME NULL,
    CONSTRAINT fk_incidents_user FOREIGN KEY (user_id) REFERENCES users (id),
    CONSTRAINT fk_incidents_analyst FOREIGN KEY (analyst_id) REFERENCES users (id),
    CONSTRAINT fk_incidents_severity FOREIGN KEY (severity_id) REFERENCES severity (id),
    CONSTRAINT fk_incidents_state FOREIGN KEY (state_id) REFERENCES state (id)
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

INSERT INTO severity (id, name)
VALUES (1, "LOW"),(2, "MEDIUM"),(3, "HIGH"),(4, "CRITICAL");

INSERT INTO state (id, name)
VALUES (1, "OPEN"),(2, "PENDING"),(3, "CLOSE");