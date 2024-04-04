CREATE DATABASE project_manager;
\c project_manager;

CREATE TABLE projects(
	id SERIAL PRIMARY KEY,
	name varchar(100) NOT NULL,
	created_by integer NOT NULL,
	created_on timestamp DEFAULT NOW(),
	description varchar(500) NOT NULL,
	updated_by integer,
	updated_on timestamp,
	logo varchar(2048)
	);

CREATE TABLE users(
	id SERIAL PRIMARY KEY,
	name varchar(50) NOT NULL,
	email varchar(50) NOT NULL,
	password bytea NOT NULL
);

CREATE TABLE documents(
	id SERIAL PRIMARY KEY,
	name varchar(50) NOT NULL,
	project_id integer NOT NULL, 
	added_by integer NOT NULL,
	link_to_document varchar(2048) NOT NULL,
	FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE project_access(
	project_id integer NOT NULL,
	user_id integer NOT NULL,
	FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
	FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);