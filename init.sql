CREATE OR REPLACE TABLE user (
    id       UUID PRIMARY KEY DEFAULT UUID(),
    name     VARCHAR(100) NOT NULL,
    email    VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role     ENUM('EMPLOYEE', 'ANALYST') NOT NULL DEFAULT 'EMPLOYEE'
);

CREATE OR REPLACE TABLE con_severity (
    id          INT(1) NOT NULL,
    name        VARCHAR(8) NOT NULL
);

CREATE OR REPLACE TABLE con_state (
    id          INT(1) NOT NULL,
    name        VARCHAR(7) NOT NULL
);

CREATE OR REPLACE TABLE incident (
    id          UUID PRIMARY KEY DEFAULT UUID(),
    user_id     UUID NOT NULL,
    analyst_id  UUID NULL,
    title       VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    severity_id INT(1) NOT NULL,
    state_id    INT(1) NOT NULL DEFAULT 0,
    open_date   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    close_date  DATETIME NULL,
    CONSTRAINT fk_incidents_user FOREIGN KEY (user_id) REFERENCES user (id),
    CONSTRAINT fk_incidents_analyst FOREIGN KEY (analyst_id) REFERENCES user (id),
    CONSTRAINT fk_incidents_severity FOREIGN KEY (severity_id) REFERENCES con_severity (id),
    CONSTRAINT fk_incidents_state FOREIGN KEY (state_id) REFERENCES con_state (id)
);

CREATE OR REPLACETABLE comment (
    id          UUID PRIMARY KEY DEFAULT UUID(),
    content     TEXT NOT NULL,
    author_id   UUID NOT NULL,
    incident_id UUID NOT NULL,
    timestamp   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comments_author FOREIGN KEY (author_id) REFERENCES user (id),
    CONSTRAINT fk_comments_incident FOREIGN KEY (incident_id) REFERENCES incident (id) ON DELETE CASCADE
);

CREATE OR REPLACETABLE attachment (
    id          UUID PRIMARY KEY DEFAULT UUID(),
    incident_id UUID NOT NULL,
    filename    VARCHAR(255) NOT NULL,
    filetype    VARCHAR(100) NOT NULL,
    filesize    INT UNSIGNED NOT NULL,
    path        VARCHAR(500) NOT NULL,
    CONSTRAINT fk_attachments_incident FOREIGN KEY (incident_id) REFERENCES incident (id) ON DELETE CASCADE
);

INSERT INTO con_severity (id, name)
VALUES (1, "LOW"),(2, "MEDIUM"),(3, "HIGH"),(4, "CRITICAL");

INSERT INTO con_state (id, name)
VALUES (1, "OPEN"),(2, "PENDING"),(3, "CLOSE");