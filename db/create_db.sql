CREATE DATABASE project_manager;
\c project_manager;

CREATE TABLE users(
	username varchar(10) PRIMARY KEY,
	name varchar(50) NOT NULL,
	email varchar(50) NOT NULL,
	password bytea NOT NULL
);

CREATE TABLE projects(
	id SERIAL PRIMARY KEY,
	name varchar(100) NOT NULL,
	created_by varchar(10) NOT NULL,
	created_on timestamp DEFAULT NOW(),
	description varchar(500) NOT NULL,
	updated_by integer,
	updated_on timestamp,
	logo varchar(2048),
	FOREIGN KEY (created_by) REFERENCES users(username)
	);

CREATE TABLE documents(
	id SERIAL PRIMARY KEY,
	name varchar(50) NOT NULL,
	project_id integer NOT NULL, 
	added_by integer NOT NULL,
	link_to_document varchar(2048) NOT NULL,
	FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TYPE role AS ENUM('owner', 'participant');

CREATE TABLE project_access(
	project_id integer NOT NULL,
	username varchar(10) NOT NULL,
	access_type role,
	is_valid boolean DEFAULT TRUE,
	FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
	FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE,
	PRIMARY KEY (project_id, username)
);